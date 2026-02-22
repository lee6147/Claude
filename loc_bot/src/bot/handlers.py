import asyncio
import functools
import hashlib
import io
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from telegram import Message, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import RetryAfter, BadRequest

from config.settings import (
    AGENT_ENGINE_CLI,
    ALLOWED_USER_IDS,
    AUTO_REVIEW_ENABLED,
    MAX_IMAGE_SIZE,
    MAX_OUTPUT_LENGTH,
    MAX_QUEUE_SIZE,
    STREAM_UPDATE_INTERVAL,
)
from src.claude.executor import run_claude
from src.projects.manager import (
    register_project,
    get_project_path,
    scan_workspace,
)
from src.db.models import (
    add_task,
    complete_task,
    get_project,
    get_recent_tasks,
    get_all_user_states,
    get_project_by_id,
    set_user_state,
    list_projects,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 봇 시작 시각 (업타임 계산용)
# ---------------------------------------------------------------------------
_bot_start_time: float = time.time()

# ---------------------------------------------------------------------------
# 사용자별 현재 선택된 프로젝트 (DB에서 로드, 메모리 캐시)
# ---------------------------------------------------------------------------
current_project: dict[int, str] = {}

# ---------------------------------------------------------------------------
# 하단 고정 메뉴 키보드
# ---------------------------------------------------------------------------
MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["프로젝트 목록", "스캔"],
        ["상태", "히스토리"],
        ["중지", "전체중지", "도움말"],
    ],
    resize_keyboard=True,
    is_persistent=True,
    input_field_placeholder="Claude Code에 보낼 명령을 입력하세요",
)

# ---------------------------------------------------------------------------
# 큐 시스템
# ---------------------------------------------------------------------------

@dataclass
class QueueItem:
    user_id: int
    proj_name: str
    prompt: str
    wait_msg: Message
    context: ContextTypes.DEFAULT_TYPE
    image_paths: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


_project_queues: dict[str, asyncio.Queue[QueueItem]] = {}
_queue_workers: dict[str, asyncio.Task] = {}
_active_cancels: dict[str, asyncio.Event] = {}


def _norm_key(proj_name: str) -> str:
    """프로젝트 키 정규화 (B8)."""
    return proj_name.strip().lower()


def _get_or_create_queue(proj_name: str) -> asyncio.Queue[QueueItem]:
    key = _norm_key(proj_name)
    if key not in _project_queues:
        _project_queues[key] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
    return _project_queues[key]


def _get_or_create_worker(proj_name: str) -> asyncio.Task:
    key = _norm_key(proj_name)
    task = _queue_workers.get(key)
    if task is None or task.done():
        task = asyncio.create_task(_queue_worker(key))
        _queue_workers[key] = task
    return task


async def shutdown_workers() -> None:
    """모든 큐 워커를 정리한다. main.py 종료 시 호출."""
    for _name, task in _queue_workers.items():
        task.cancel()
    for _name, task in _queue_workers.items():
        try:
            await task
        except asyncio.CancelledError:
            pass
    _queue_workers.clear()


# ---------------------------------------------------------------------------
# DraftState — Status Card 실시간 업데이트
# ---------------------------------------------------------------------------

@dataclass
class DraftState:
    buffer: str = ""
    last_hash: str = ""
    last_edit_time: float = 0.0
    start_time: float = field(default_factory=time.time)


DRAFT_MAX_CHARS = 3800  # 4096 여유분


async def _safe_edit(msg: Message, text: str, last_hash: str) -> str:
    """메시지를 편집한다. 변경 없으면 건너뛰고, 오류 시 안전하게 무시."""
    h = hashlib.md5(text.encode()).hexdigest()
    if h == last_hash:
        return last_hash
    try:
        await msg.edit_text(text)
        return h
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        try:
            await msg.edit_text(text)
            return h
        except Exception:
            return last_hash
    except BadRequest:
        return last_hash
    except Exception:
        logger.warning("edit 실패", exc_info=True)
        return last_hash


def _format_elapsed(seconds: float) -> str:
    """경과시간을 30초 단위로 표시."""
    s = int(seconds)
    s = (s // 30) * 30  # 30초 단위 절사
    if s < 60:
        return f"{s}초"
    m, sec = divmod(s, 60)
    if sec == 0:
        return f"{m}분"
    return f"{m}분 {sec}초"


# ---------------------------------------------------------------------------
# 마크다운 스트립
# ---------------------------------------------------------------------------

_CODEBLOCK_RE = re.compile(r"```([^\n]*)\r?\n(.*?)```", re.DOTALL)
_PLACEHOLDER_RE = re.compile(r"\x00CB:(\d+)\x00")


def _strip_markdown(text: str) -> str:
    """최종 결과 표시용. 마크다운 → plain text. 코드블록 내부 보호."""
    if not text:
        return text

    # Phase 1: 코드블록 추출 → 널문자 placeholder 치환
    code_blocks: list[str] = []

    def _extract_code_block(m: re.Match) -> str:
        lang = (m.group(1) or "").strip() or "code"
        block = f"--- {lang} ---\n{m.group(2)}\n-----------"
        idx = len(code_blocks)
        code_blocks.append(block)
        return f"\x00CB:{idx}\x00"

    text = _CODEBLOCK_RE.sub(_extract_code_block, text)

    # Phase 2: 마크다운 strip (코드블록은 이미 placeholder)
    text = re.sub(r"`([^`]+)`", r"\1", text)                           # 인라인 코드
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)                       # 볼드 **
    text = re.sub(r"__(.+?)__", r"\1", text)                           # 볼드 __
    text = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"\1", text)           # 이탤릭 *
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)         # 헤딩
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)        # 링크
    text = re.sub(r"^[-*]{3,}\s*$", "\u2500" * 20, text, flags=re.MULTILINE)  # 수평선

    # Phase 3: placeholder → 코드블록 복원 (regex 1회)
    if code_blocks:
        text = _PLACEHOLDER_RE.sub(
            lambda m: code_blocks[int(m.group(1))], text
        )

    return text


def _strip_markdown_light(text: str) -> str:
    """Status Card용. 코드블록/백틱 유지, 볼드/헤딩만 제거."""
    if not text:
        return text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    return text


def _build_status_card(proj_name: str, draft: DraftState) -> str:
    """Status Card 텍스트를 조립한다."""
    elapsed = time.time() - draft.start_time
    elapsed_text = _format_elapsed(elapsed)
    tail = draft.buffer[-DRAFT_MAX_CHARS:] if len(draft.buffer) > DRAFT_MAX_CHARS else draft.buffer
    tail = _strip_markdown_light(tail)
    header = f"[{proj_name}] 답변 생성 중... ({elapsed_text})"
    sep = "─" * 20
    return f"{header}\n{sep}\n{tail}" if tail else header


async def _draft_loop(msg: Message, proj_name: str, draft: DraftState) -> None:
    """STREAM_UPDATE_INTERVAL마다 Status Card를 편집한다."""
    try:
        while True:
            await asyncio.sleep(STREAM_UPDATE_INTERVAL)
            card = _build_status_card(proj_name, draft)
            draft.last_hash = await _safe_edit(msg, card, draft.last_hash)
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# 워커 루프
# ---------------------------------------------------------------------------

async def _queue_worker(proj_key: str) -> None:
    """프로젝트별 큐 워커. 아이템을 순서대로 실행한다."""
    queue = _project_queues[proj_key]
    while True:
        item: QueueItem = await queue.get()
        try:
            await _execute_queued_item(item)
        except Exception:
            logger.exception("워커 예외 (project=%s)", proj_key)
        finally:
            queue.task_done()


async def _execute_queued_item(item: QueueItem) -> None:
    """큐 아이템을 실행한다: DraftState 생성 → run_claude → 최종 결과 전송."""
    proj_name = item.proj_name
    proj_key = _norm_key(proj_name)
    user_id = item.user_id
    prompt = item.prompt
    wait_msg = item.wait_msg
    context = item.context

    path = await get_project_path(proj_name)
    if not path:
        await _safe_edit(wait_msg, f"[{proj_name}] 프로젝트 경로를 찾을 수 없습니다.", "")
        return

    # cancel event
    cancel_event = asyncio.Event()
    _active_cancels[proj_key] = cancel_event

    # DraftState + draft task
    draft = DraftState()
    draft_task = asyncio.create_task(_draft_loop(wait_msg, proj_name, draft))

    task_id = None
    output_text = ""

    async def _on_output(chunk: str) -> None:
        draft.buffer += chunk

    try:
        task_id = await add_task(proj_name, prompt)
        session_ids = context.user_data.get("session_ids", {})
        prev_session = session_ids.get(proj_name)

        result = await run_claude(
            prompt,
            path,
            continue_session=bool(prev_session),
            session_id=prev_session,
            on_output=_on_output,
            cancel_event=cancel_event,
        )

        if result.session_id:
            session_ids[proj_name] = result.session_id
            context.user_data["session_ids"] = session_ids

        output_text = result.output
        status = "error" if output_text.startswith("오류:") else "done"
        if task_id is not None:
            try:
                await complete_task(task_id, output_text, status=status)
            except Exception:
                logger.warning("DB complete_task 실패 (무시)", exc_info=True)
    except Exception as e:
        output_text = f"오류 발생: {type(e).__name__}: {e}"
        if task_id is not None:
            try:
                await complete_task(task_id, output_text, status="error")
            except Exception:
                logger.warning("DB complete_task 실패 (무시)", exc_info=True)
    finally:
        _active_cancels.pop(proj_key, None)
        draft_task.cancel()
        try:
            await draft_task
        except asyncio.CancelledError:
            pass
        _cleanup_images(item.image_paths)

    # 최종 결과 전송 (항상 실행 보장)
    await _send_final_result(wait_msg, proj_name, output_text)

    # 자동 Codex 리뷰 (정상 완료 시만, 백그라운드 실행)
    if (
        AUTO_REVIEW_ENABLED
        and path
        and not output_text.startswith("오류")
        and "취소되었습니다" not in output_text
    ):
        asyncio.create_task(_auto_review(wait_msg, proj_name, path, prompt))


_review_running = False


async def _auto_review(
    wait_msg: Message, proj_name: str, project_path: str, reason: str,
) -> None:
    """agent-engine review CLI를 subprocess로 호출하여 자동 리뷰를 실행한다."""
    global _review_running
    import json as _json

    # asyncio 싱글 스레드: await 없이 check-and-set → 원자적
    if _review_running:
        logger.info("자동 리뷰 이미 실행 중 — 건너뜀")
        return
    _review_running = True

    try:
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                AGENT_ENGINE_CLI, "review",
                "--project-path", project_path,
                "--reason", reason[:200],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=360)
            raw = stdout.decode(errors="replace").strip()

            if not raw:
                return

            try:
                result = _json.loads(raw)
            except _json.JSONDecodeError:
                logger.warning("agent-engine review JSON 파싱 실패: %s", raw[:200])
                return

            verdict = result.get("verdict", "?")
            summary = result.get("summary", "")
            duration = result.get("duration_seconds", 0)
            issues = result.get("issues", [])

            if verdict == "pass":
                review_text = f"[{proj_name}] Codex 리뷰: PASS\n{summary}\n({duration:.0f}초)"
            elif verdict == "fail":
                issue_lines = "\n".join(
                    f"  [{i.get('severity', '?')}] {i.get('description', '')}"
                    for i in issues[:5]
                )
                review_text = f"[{proj_name}] Codex 리뷰: FAIL\n{summary}\n{issue_lines}\n({duration:.0f}초)"
            else:
                logger.warning("Codex 리뷰 에러: %s", summary)
                review_text = f"[{proj_name}] Codex 리뷰 에러: {summary}"

            await wait_msg.reply_text(review_text)
        except asyncio.TimeoutError:
            logger.warning("agent-engine review 타임아웃")
            if proc and proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=10)
                except asyncio.TimeoutError:
                    proc.kill()
                await proc.wait()
        except FileNotFoundError:
            logger.warning("agent-engine CLI를 찾을 수 없음: %s", AGENT_ENGINE_CLI)
        except Exception:
            logger.warning("자동 리뷰 실패 (무시)", exc_info=True)
    finally:
        _review_running = False


def _cleanup_images(image_paths: list[str]) -> None:
    """성공 시 임시 이미지 파일을 정리한다."""
    for p in image_paths:
        try:
            path = Path(p)
            if path.exists():
                path.unlink()
            parent = path.parent
            if parent.name == ".tmp_images" and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
        except Exception:
            logger.debug("이미지 정리 실패 (무시): %s", p)


async def _send_final_result(wait_msg: Message, proj_name: str, output_text: str) -> None:
    """실행 결과를 전송한다. 길이에 따라 분할 또는 파일 첨부."""
    try:
        cleaned = _strip_markdown(output_text)
        reply = f"[{proj_name}] 완료:\n\n{cleaned}"

        if len(reply) > 8000:
            summary = cleaned[:500]
            if len(cleaned) > 500:
                summary += "\n\n... (전체 결과는 첨부 파일 참조)"
            card_text = f"[{proj_name}] 완료 (긴 출력 — 파일 첨부):\n\n{summary}"
            await _safe_edit(wait_msg, card_text, "")
            file_bytes = output_text.encode("utf-8")
            await wait_msg.reply_document(
                document=io.BytesIO(file_bytes),
                filename=f"{proj_name}_result.txt",
            )
        else:
            chunks = _split_message(reply)
            if len(chunks) == 1:
                await _safe_edit(wait_msg, chunks[0], "")
            else:
                await _safe_edit(wait_msg, f"[1/{len(chunks)}]\n{chunks[0]}", "")
                for i, chunk in enumerate(chunks[1:], start=2):
                    await wait_msg.reply_text(f"[{i}/{len(chunks)}]\n{chunk}")
    except Exception:
        logger.warning("최종 결과 전송 실패", exc_info=True)
        try:
            await _safe_edit(wait_msg, f"[{proj_name}] 완료 (결과 전송 중 오류 발생)", "")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 메시지 분할
# ---------------------------------------------------------------------------

def _split_message(text: str, max_len: int = MAX_OUTPUT_LENGTH, prefix_reserve: int = 20) -> list[str]:
    """긴 텍스트를 max_len 이하 조각으로 분할한다."""
    if not text:
        return ["(빈 출력)"]
    if len(text) <= max_len:
        return [text]

    effective_max = max_len - prefix_reserve
    chunks: list[str] = []
    while text:
        if len(text) <= effective_max:
            chunks.append(text)
            break
        split_pos = text.rfind("\n", 0, effective_max)
        if split_pos <= 0:
            split_pos = effective_max
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")

    return chunks


# ---------------------------------------------------------------------------
# 인증 데코레이터
# ---------------------------------------------------------------------------

def auth_required(func):
    """허용된 사용자만 접근 가능하도록 제한한다."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or user.id not in ALLOWED_USER_IDS:
            if update.message:
                await update.message.reply_text("권한이 없습니다.")
            elif update.callback_query:
                await update.callback_query.answer("권한이 없습니다.")
            return
        return await func(update, context)
    return wrapper


# ---------------------------------------------------------------------------
# 봇 시작 시 DB에서 사용자 상태 로드
# ---------------------------------------------------------------------------

async def load_user_states() -> None:
    """봇 시작 시 DB에서 사용자별 프로젝트 선택 상태를 로드한다."""
    states = await get_all_user_states()
    current_project.update(states)


# ---------------------------------------------------------------------------
# 명령어 핸들러
# ---------------------------------------------------------------------------

@auth_required
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "loc_bot 시작됨\n\n"
        "아래 버튼으로 조작하거나, 텍스트를 보내면 Claude Code가 실행됩니다.",
        reply_markup=MAIN_MENU,
    )


@auth_required
async def cmd_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = await list_projects()
    if not projects:
        await update.message.reply_text("등록된 프로젝트가 없습니다.\n'스캔' 버튼을 눌러 등록하세요.")
        return

    user_id = update.effective_user.id
    cur = current_project.get(user_id)

    buttons = []
    for p in projects:
        name = p["name"]
        label = f"{'> ' if name == cur else ''}{name}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"use:{p['id']}")])

    await update.message.reply_text(
        "프로젝트를 선택하세요:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@auth_required
async def cmd_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("사용법: /register <이름> [경로]")
        return

    name = args[0]
    path = args[1] if len(args) > 1 else None
    result = await register_project(name, path)
    await update.message.reply_text(result)


@auth_required
async def cmd_use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /use <프로젝트이름>")
        return

    name = context.args[0]
    await _select_project(update.effective_user.id, name, update.message)


@auth_required
async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dirs = scan_workspace()
    if not dirs:
        await update.message.reply_text("Desktop에 디렉토리가 없습니다.")
        return

    context.user_data["scan_dirs"] = dirs

    buttons = []
    for i, d in enumerate(dirs):
        buttons.append([InlineKeyboardButton(f"등록: {d}", callback_data=f"reg:{i}")])

    await update.message.reply_text(
        "Desktop 디렉토리 — 버튼을 눌러 등록:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@auth_required
async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    proj_name = current_project.get(user_id)
    if not proj_name:
        await update.message.reply_text("먼저 프로젝트를 선택하세요.")
        return

    tasks = await get_recent_tasks(proj_name, limit=5)
    if not tasks:
        await update.message.reply_text("작업 이력이 없습니다.")
        return

    lines = [f"최근 작업 ({proj_name}):"]
    for t in tasks:
        status = t["status"]
        prompt_preview = t["prompt"][:60]
        lines.append(f"  [{status}] {prompt_preview}")
    await update.message.reply_text("\n".join(lines))


@auth_required
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    proj_name = current_project.get(user_id, "(없음)")

    # 업타임
    elapsed = int(time.time() - _bot_start_time)
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime = f"{hours}시간 {minutes}분 {seconds}초"

    # 실행 중 프로젝트
    running = [k for k, ev in _active_cancels.items() if not ev.is_set()]
    running_text = ", ".join(running) if running else "없음"

    # 대기열 현황
    queue_info = []
    for key, q in _project_queues.items():
        sz = q.qsize()
        if sz > 0:
            queue_info.append(f"{key}: {sz}건")
    queue_text = ", ".join(queue_info) if queue_info else "없음"

    await update.message.reply_text(
        f"현재 프로젝트: {proj_name}\n"
        f"업타임: {uptime}\n"
        f"실행 중: {running_text}\n"
        f"대기열: {queue_text}"
    )


@auth_required
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """사용 가능한 명령어 목록을 보여준다."""
    await update.message.reply_text(
        "사용 가능한 명령어:\n\n"
        "프로젝트 관리:\n"
        "  /projects — 프로젝트 목록 + 선택\n"
        "  /scan — Desktop 디렉토리 스캔 + 등록\n"
        "  /register <이름> [경로] — 프로젝트 수동 등록\n"
        "  /use <이름> — 프로젝트 전환\n\n"
        "세션 제어:\n"
        "  /new — Claude 세션 초기화\n"
        "  /stop — 실행 중인 작업 중지\n"
        "  /stop_all — 모든 프로젝트 작업 + 대기열 중지\n"
        "  /restart — 봇 재시작\n"
        "  /status — 상태 + 업타임 + 대기열\n"
        "  /history — 최근 작업 이력\n\n"
        "하단 버튼으로도 조작 가능합니다.\n"
        "텍스트를 보내면 현재 프로젝트에서 Claude Code가 실행됩니다.",
        reply_markup=MAIN_MENU,
    )


@auth_required
async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claude 세션을 초기화한다."""
    user_id = update.effective_user.id
    proj_name = current_project.get(user_id)
    if not proj_name:
        await update.message.reply_text("먼저 프로젝트를 선택하세요.")
        return

    session_ids = context.user_data.get("session_ids", {})
    session_ids.pop(proj_name, None)
    context.user_data["session_ids"] = session_ids
    await update.message.reply_text(
        f"[{proj_name}] 세션 초기화 완료.\n다음 메시지부터 새 세션으로 실행됩니다."
    )


@auth_required
async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """현재 프로젝트의 실행 중인 작업을 중지한다."""
    user_id = update.effective_user.id
    proj_name = current_project.get(user_id)
    if not proj_name:
        await update.message.reply_text("먼저 프로젝트를 선택하세요.")
        return

    proj_key = _norm_key(proj_name)
    cancel_ev = _active_cancels.get(proj_key)
    if cancel_ev is None or cancel_ev.is_set():
        await update.message.reply_text(f"[{proj_name}] 실행 중인 작업이 없습니다.")
        return

    cancel_ev.set()
    # 큐에 남아있는 대기 작업 수 안내
    queue = _project_queues.get(proj_key)
    pending = queue.qsize() if queue else 0
    extra = f"\n대기열에 {pending}건 남아있습니다." if pending > 0 else ""
    await update.message.reply_text(f"[{proj_name}] 작업 중지 요청됨.{extra}")


@auth_required
async def cmd_stop_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """모든 프로젝트의 실행 + 대기열을 중지한다."""
    # 실행 중인 모든 작업 취소
    cancelled = 0
    for key, ev in _active_cancels.items():
        if not ev.is_set():
            ev.set()
            cancelled += 1

    # 모든 큐 비우기
    drained = 0
    for key, queue in _project_queues.items():
        while not queue.empty():
            try:
                item = queue.get_nowait()
                _cleanup_images(item.image_paths)
                queue.task_done()
                drained += 1
            except asyncio.QueueEmpty:
                break

    await update.message.reply_text(
        f"전체 중지 완료.\n"
        f"중지된 작업: {cancelled}건\n"
        f"제거된 대기열: {drained}건"
    )


@auth_required
async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇을 재시작한다. 현재 프로세스를 동일 인자로 다시 실행."""
    await update.message.reply_text("봇을 재시작합니다...")
    try:
        await shutdown_workers()
        from src.db.database import close_db
        await close_db()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception:
        logger.exception("봇 재시작 실패")
        await update.message.reply_text("재시작에 실패했습니다. 수동으로 재시작해주세요.")


@auth_required
async def cmd_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """등록되지 않은 /명령어를 처리한다."""
    await update.message.reply_text(
        f"알 수 없는 명령어: {update.message.text}\n"
        "/help 로 사용 가능한 명령어를 확인하세요."
    )


# ---------------------------------------------------------------------------
# 버튼 텍스트 핸들러
# ---------------------------------------------------------------------------

@auth_required
async def handle_button_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """하단 메뉴 버튼 텍스트를 처리한다."""
    text = update.message.text
    menu_routes = {
        "프로젝트 목록": cmd_projects,
        "스캔": cmd_scan,
        "상태": cmd_status,
        "히스토리": cmd_history,
        "중지": cmd_stop,
        "전체중지": cmd_stop_all,
        "도움말": cmd_help,
    }
    handler = menu_routes.get(text)
    if handler:
        return await handler(update, context)
    return await handle_message(update, context)


# ---------------------------------------------------------------------------
# 인라인 버튼 콜백
# ---------------------------------------------------------------------------

@auth_required
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """인라인 버튼 콜백을 처리한다."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    if data.startswith("reg:"):
        try:
            idx = int(data[4:])
        except ValueError:
            await query.edit_message_text("잘못된 요청입니다.")
            return
        scan_dirs = context.user_data.get("scan_dirs", [])
        if idx < 0 or idx >= len(scan_dirs):
            await query.edit_message_text("스캔 결과가 만료되었습니다. 다시 스캔해주세요.")
            return
        name = scan_dirs[idx]
        result = await register_project(name)
        await query.edit_message_text(f"{result}\n\n아래 버튼으로 선택하세요.")
        proj = await get_project(name)
        if proj:
            buttons = [[InlineKeyboardButton(f"선택: {name}", callback_data=f"use:{proj['id']}")]]
            await query.message.reply_text(
                f"{name} 프로젝트를 선택할까요?",
                reply_markup=InlineKeyboardMarkup(buttons),
            )

    elif data.startswith("use:"):
        try:
            project_id = int(data[4:])
        except ValueError:
            await query.edit_message_text("잘못된 프로젝트 ID입니다.")
            return
        proj = await get_project_by_id(project_id)
        if not proj:
            await query.edit_message_text("프로젝트를 찾을 수 없습니다.")
            return
        await _select_project(user_id, proj["name"], query.message, edit=True)


# ---------------------------------------------------------------------------
# 프로젝트 선택 헬퍼
# ---------------------------------------------------------------------------

async def _select_project(user_id: int, name: str, message: Message, edit: bool = False):
    """프로젝트를 선택하고 결과를 메시지로 보낸다."""
    path = await get_project_path(name)
    if not path:
        text = f"등록되지 않은 프로젝트: {name}"
    else:
        current_project[user_id] = name
        await set_user_state(user_id, name)
        text = (
            f"현재 프로젝트: {name}\n경로: {path}\n\n"
            "이제 텍스트를 보내면 이 프로젝트에서 Claude Code가 실행됩니다."
        )

    if edit:
        await message.edit_text(text)
    else:
        await message.reply_text(text)


# ---------------------------------------------------------------------------
# 큐 삽입 헬퍼
# ---------------------------------------------------------------------------

async def _enqueue_item(
    message: Message,
    proj_name: str,
    item: QueueItem,
    on_full_cleanup: list[str] | None = None,
) -> bool:
    """큐에 아이템을 넣는다. 성공 시 True, 실패 시 False."""
    queue = _get_or_create_queue(proj_name)
    try:
        queue.put_nowait(item)
    except asyncio.QueueFull:
        # 실패 시 임시 파일 정리
        if on_full_cleanup:
            for p in on_full_cleanup:
                try:
                    Path(p).unlink(missing_ok=True)
                except OSError:
                    logger.debug("큐 full 정리 실패 (무시): %s", p)
        await message.reply_text(
            f"대기열이 가득 찼습니다 ({MAX_QUEUE_SIZE}개). 잠시 후 다시 시도하세요."
        )
        return False
    _get_or_create_worker(proj_name)
    return True


# ---------------------------------------------------------------------------
# 일반 메시지 → Claude Code 실행 (큐 기반)
# ---------------------------------------------------------------------------

@auth_required
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """일반 텍스트 메시지를 받으면 큐에 넣고 Claude Code를 실행한다."""
    user_id = update.effective_user.id
    proj_name = current_project.get(user_id)

    if not proj_name:
        projects = await list_projects()
        if projects:
            buttons = [[InlineKeyboardButton(p["name"], callback_data=f"use:{p['id']}")] for p in projects]
            await update.message.reply_text(
                "먼저 프로젝트를 선택하세요:",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        else:
            await update.message.reply_text(
                "등록된 프로젝트가 없습니다.\n'스캔' 버튼을 눌러 등록하세요."
            )
        return

    proj_key = _norm_key(proj_name)
    prompt = update.message.text

    # 대기열 위치 안내
    queue = _get_or_create_queue(proj_name)
    position = queue.qsize()
    if position == 0 and proj_key not in _active_cancels:
        status_text = f"[{proj_name}] 답변 생성 중..."
    else:
        status_text = f"[{proj_name}] 대기열 {position + 1}번째..."

    wait_msg = await update.message.reply_text(status_text)

    item = QueueItem(
        user_id=user_id,
        proj_name=proj_name,
        prompt=prompt,
        wait_msg=wait_msg,
        context=context,
    )

    await _enqueue_item(update.message, proj_name, item)


# ---------------------------------------------------------------------------
# 이미지 수신 핸들러
# ---------------------------------------------------------------------------

@auth_required
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """사진 또는 이미지 문서를 받아 Claude Code에 전달한다."""
    user_id = update.effective_user.id
    proj_name = current_project.get(user_id)
    if not proj_name:
        await update.message.reply_text("먼저 /use 로 프로젝트를 선택하세요.")
        return

    project_root = await get_project_path(proj_name)
    if not project_root:
        await update.message.reply_text("프로젝트 경로를 찾을 수 없습니다.")
        return

    # Document.ALL로 받되, 이미지가 아니면 거부
    if update.message.document:
        mime = update.message.document.mime_type or ""
        if not mime.startswith("image/"):
            await update.message.reply_text("이미지 파일만 지원합니다.")
            return

    # photo/document 분기에서 unique_id + file_size 안전 추출
    if update.message.photo:
        photo_obj = update.message.photo[-1]
        unique_id = photo_obj.file_unique_id
        file_size = photo_obj.file_size or 0
        file = await photo_obj.get_file()
    elif update.message.document:
        doc = update.message.document
        unique_id = getattr(doc, "file_unique_id", None) or doc.file_id
        file_size = doc.file_size or 0
        file = await doc.get_file()
    else:
        await update.message.reply_text("지원하지 않는 파일 형식입니다.")
        return

    # 파일 크기 제한
    if file_size > MAX_IMAGE_SIZE:
        size_mb = MAX_IMAGE_SIZE // (1024 * 1024)
        await update.message.reply_text(f"이미지가 너무 큽니다 (최대 {size_mb}MB).")
        return

    # 파일 확장자 결정
    ext = Path(file.file_path).suffix if file.file_path else ".jpg"
    if not ext:
        ext = ".jpg"
    filename = f"tg_{unique_id}_{int(time.time())}{ext}"

    # 이미지 저장: project_root 하위
    tmp_dir = Path(project_root) / ".tmp_images"
    try:
        tmp_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.exception("임시 디렉토리 생성 실패: %s", tmp_dir)
        await update.message.reply_text("임시 디렉토리 생성에 실패했습니다.")
        return
    image_path = tmp_dir / filename

    try:
        await file.download_to_drive(str(image_path))
    except Exception:
        logger.exception("이미지 다운로드 실패: %s", filename)
        await update.message.reply_text("이미지 다운로드에 실패했습니다. 다시 보내주세요.")
        return

    # 다운로드 후 실제 파일 크기 재검증
    actual_size = image_path.stat().st_size
    if actual_size > MAX_IMAGE_SIZE:
        image_path.unlink(missing_ok=True)
        size_mb = MAX_IMAGE_SIZE // (1024 * 1024)
        await update.message.reply_text(f"이미지가 너무 큽니다 (최대 {size_mb}MB).")
        return

    # 상대경로 검증
    try:
        rel_path = image_path.relative_to(Path(project_root))
    except ValueError:
        logger.error("이미지 경로 불일치: %s vs %s", image_path, project_root)
        await update.message.reply_text("경로 오류가 발생했습니다.")
        image_path.unlink(missing_ok=True)
        return

    # 프롬프트 생성 (캡션 1000자 제한)
    caption = (update.message.caption or "").strip()
    if len(caption) > 1000:
        caption = caption[:1000] + "..."
    if caption:
        prompt = f"{caption}\n\n(Attached image: {rel_path.as_posix()})"
    else:
        prompt = f"이 이미지를 분석해주세요.\n\n(Attached image: {rel_path.as_posix()})"

    # 큐에 추가
    wait_msg = await update.message.reply_text("이미지 수신 — 대기열에 추가됨...")
    item = QueueItem(
        user_id=user_id,
        proj_name=proj_name,
        prompt=prompt,
        wait_msg=wait_msg,
        context=context,
        image_paths=[str(image_path)],
    )
    await _enqueue_item(
        update.message, proj_name, item,
        on_full_cleanup=[str(image_path)],
    )
