import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from collections.abc import Callable
from pathlib import Path
from typing import Any

from config.settings import CLAUDE_CLI_PATH, CLAUDE_TIMEOUT, CLAUDE_INACTIVITY_TIMEOUT

logger = logging.getLogger(__name__)

GRACEFUL_SHUTDOWN_TIMEOUT = 10  # terminate() 후 kill() 전 대기 시간 (초)


@dataclass
class ClaudeResult:
    """Claude Code CLI 실행 결과."""
    output: str
    session_id: str | None = None


@dataclass
class StreamState:
    """NDJSON 스트림 파싱 상태."""
    session_id: str | None = None
    text_chunks: list[str] = field(default_factory=list)
    result_text: str | None = None
    is_error: bool = False


def _summarize_tool_use(tool_name: Any, tool_input: Any) -> str:
    """tool_use 블록을 사람이 읽기 쉬운 한 줄 요약으로 변환한다."""
    if not isinstance(tool_input, dict):
        tool_input = {}
    if not isinstance(tool_name, str):
        tool_name = str(tool_name) if tool_name else "unknown"
    name = tool_name.lower()

    def _safe_filename(val: Any) -> str:
        if not isinstance(val, str) or not val:
            return "?"
        return Path(val).name

    if name in ("read", "readfile"):
        return f"  파일 읽는 중... ({_safe_filename(tool_input.get('file_path'))})"

    if name in ("edit", "editfile"):
        return f"  코드 수정 중... ({_safe_filename(tool_input.get('file_path'))})"

    if name in ("write", "writefile"):
        return f"  파일 작성 중... ({_safe_filename(tool_input.get('file_path'))})"

    if name in ("bash", "execute", "shell"):
        cmd = tool_input.get("command", "")
        if not isinstance(cmd, str):
            cmd = str(cmd)
        preview = cmd[:60] + "..." if len(cmd) > 60 else cmd
        return f"  명령 실행 중... ({preview})"

    if name in ("glob", "search", "grep"):
        pattern = tool_input.get("pattern", "")
        if not isinstance(pattern, str):
            pattern = str(pattern)
        return f"  검색 중... ({pattern[:40]})"

    if name in ("task", "todowrite"):
        return "  작업 정리 중..."

    # 기타 도구: 이름만 표시
    return f"  {tool_name} 실행 중..."


def _parse_stream_line(line: str, state: StreamState) -> str | None:
    """NDJSON 한 줄을 파싱하여 사용자에게 보낼 텍스트를 반환한다.

    반환값이 None이면 사용자에게 보낼 내용이 없는 것.
    """
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None

    msg_type = data.get("type")

    if msg_type == "system" and data.get("subtype") == "init":
        sid = data.get("session_id")
        if isinstance(sid, str):
            state.session_id = sid
        return None

    if msg_type == "assistant":
        # content blocks에서 text/tool_use 추출
        message = data.get("message", {})
        if not isinstance(message, dict):
            return None
        content = message.get("content", [])
        if not isinstance(content, list):
            return None
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text":
                text = block.get("text", "")
                if text and isinstance(text, str):
                    parts.append(text)
            elif block_type == "tool_use":
                tool_name = block.get("name") or block.get("tool_name", "?")
                tool_input = block.get("input", {})
                summary = _summarize_tool_use(tool_name, tool_input)
                parts.append(summary)
        if parts:
            combined = "\n".join(parts)
            state.text_chunks.append(combined)
            return combined
        return None

    if msg_type == "result":
        # result.result가 dict/list면 json.dumps, None이면 "(no result)"
        raw_result = data.get("result")
        if raw_result is None:
            state.result_text = "(no result)"
        elif isinstance(raw_result, (dict, list)):
            state.result_text = json.dumps(raw_result, ensure_ascii=False)
        else:
            state.result_text = str(raw_result)

        state.is_error = data.get("subtype") == "error"
        # session_id 최종 캡처
        sid = data.get("session_id")
        if isinstance(sid, str):
            state.session_id = sid

        state.text_chunks.append(state.result_text)
        return state.result_text

    # 나머지 type (tool_result 등)은 무시
    return None


async def _safe_callback(
    on_output: Callable[[str], Any],
    text: str,
) -> None:
    """on_output 콜백을 안전하게 호출한다. 예외를 절대 전파하지 않는다."""
    try:
        result = on_output(text)
        if asyncio.iscoroutine(result):
            await result
    except Exception:
        logger.warning("on_output 콜백 실패 (무시)", exc_info=True)


async def _drain_stderr(proc: asyncio.subprocess.Process) -> str:
    """stderr를 읽어 반환한다. Traceback/ERROR 키워드 포함 시에만 사용자에게 요약 표시."""
    if proc.stderr is None:
        return ""
    try:
        raw = await proc.stderr.read()
        text = raw.decode("utf-8", errors="replace").strip()
    except Exception:
        return ""

    if text:
        logger.warning("CLI stderr: %s", text[:500])
    return text


async def run_claude(
    prompt: str,
    work_dir: str | Path,
    continue_session: bool = False,
    session_id: str | None = None,
    on_process_start: Callable[[asyncio.subprocess.Process], None] | None = None,
    on_output: Callable[[str], Any] | None = None,
    cancel_event: asyncio.Event | None = None,
) -> ClaudeResult:
    """Claude Code CLI를 stream-json 모드로 실행한다.

    Args:
        prompt: Claude에게 보낼 프롬프트
        work_dir: 작업 디렉토리 경로
        continue_session: True면 이전 세션 이어서 진행
        session_id: 특정 세션 ID로 재개
        on_process_start: 프로세스 시작 시 호출할 콜백
        on_output: 스트리밍 출력마다 호출할 async 콜백
        cancel_event: set되면 작업 취소

    Returns:
        ClaudeResult: 실행 결과 텍스트와 세션 ID
    """
    work_dir = Path(work_dir)
    if not work_dir.is_dir():
        return ClaudeResult(f"오류: 작업 디렉토리가 존재하지 않습니다: {work_dir}")

    cmd = [
        CLAUDE_CLI_PATH,
        "--print",
        "--verbose",
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
    ]
    if session_id and isinstance(session_id, str):
        cmd.extend(["--resume", session_id])
    elif continue_session:
        cmd.append("--continue")

    # 프롬프트를 stdin으로 전달 (명령줄 길이 제한 및 특수문자 문제 방지)
    use_stdin = True
    if not use_stdin:
        cmd.append(prompt)

    # 중첩 세션 감지 방지: 부모의 Claude Code 환경변수 제거
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)

    proc: asyncio.subprocess.Process | None = None
    try:
        logger.info("CLI 실행 (cwd=%s, prompt_len=%d, stdin=%s)", work_dir, len(prompt), use_stdin)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(work_dir),
            env=env,
            stdin=subprocess.PIPE if use_stdin else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            limit=1024 * 1024,  # 1MB 버퍼
        )
        logger.info("프로세스 시작됨 (PID=%s), 스트리밍 대기 중...", proc.pid)
        if on_process_start:
            try:
                on_process_start(proc)
            except Exception:
                logger.warning("on_process_start 콜백 실패 (무시)", exc_info=True)

        # stdin으로 프롬프트 전달 후 닫기
        if use_stdin and proc.stdin:
            try:
                proc.stdin.write(prompt.encode("utf-8"))
                await proc.stdin.drain()
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                logger.warning("stdin 전달 실패: %s", e)
            finally:
                proc.stdin.close()

        # stdout/stderr 스트림 보장
        assert proc.stdout is not None, "stdout가 PIPE로 열리지 않음"

        # stderr를 백그라운드로 동시에 drain (파이프 버퍼 데드락 방지)
        stderr_task = asyncio.create_task(_drain_stderr(proc))

        state = StreamState()
        last_output_time = asyncio.get_event_loop().time()
        start_time = last_output_time
        inactivity_warned = False

        while True:
            now = asyncio.get_event_loop().time()

            # 글로벌 타임아웃 체크 (0 = 무제한)
            if CLAUDE_TIMEOUT > 0 and (now - start_time) >= CLAUDE_TIMEOUT:
                logger.error("CLI 글로벌 타임아웃 (%s초)", CLAUDE_TIMEOUT)
                await _graceful_shutdown(proc)
                stderr_task.cancel()
                return ClaudeResult(
                    f"오류: Claude Code 실행 시간 초과 ({CLAUDE_TIMEOUT}초)\n"
                    f"작업 디렉토리: {work_dir}"
                )

            # cancel_event 체크
            if cancel_event and cancel_event.is_set():
                logger.info("cancel_event 감지, 프로세스 종료 중...")
                await _graceful_shutdown(proc)
                stderr_task.cancel()
                return ClaudeResult("작업이 취소되었습니다.")

            # 비활성 경고 체크
            inactivity = now - last_output_time
            if inactivity >= CLAUDE_INACTIVITY_TIMEOUT and not inactivity_warned:
                inactivity_warned = True
                warning_text = f"({int(inactivity)}초간 출력 없음 - 경고)"
                if on_output:
                    await _safe_callback(on_output, warning_text)

            # 프로세스 종료 체크
            if proc.returncode is not None:
                # drain 남은 stdout
                if proc.stdout:
                    remaining = await proc.stdout.read()
                    for remaining_line in remaining.decode("utf-8", errors="replace").splitlines():
                        remaining_line = remaining_line.strip()
                        if remaining_line:
                            text = _parse_stream_line(remaining_line, state)
                            if text and on_output:
                                await _safe_callback(on_output, text)
                break

            # readline을 1초 타임아웃으로 폴링
            try:
                raw_line = await asyncio.wait_for(
                    proc.stdout.readline(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            if not raw_line:
                # EOF
                if proc.returncode is not None:
                    break
                # stdout 닫혔지만 프로세스 아직 실행 중일 수 있음
                await asyncio.sleep(0.1)
                if proc.returncode is not None:
                    break
                continue

            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            text = _parse_stream_line(line, state)
            if text:
                last_output_time = asyncio.get_event_loop().time()
                inactivity_warned = False
                if on_output:
                    await _safe_callback(on_output, text)

        # stderr 백그라운드 태스크 결과 수집
        stderr_text = await stderr_task

        # 최종 결과 조합
        if state.result_text is not None:
            output = state.result_text
        elif state.text_chunks:
            output = "\n".join(state.text_chunks)
        else:
            output = "(출력 없음)"

        # 비정상 종료 시 에러 표시 + stderr 무조건 포함
        if proc.returncode and proc.returncode != 0:
            output = f"오류: Claude Code가 비정상 종료됨 (exit code {proc.returncode})\n\n{output}"
            if stderr_text:
                stderr_summary = stderr_text[:500]
                output += f"\n\n[stderr]\n{stderr_summary}"
        elif stderr_text and any(kw in stderr_text for kw in ("Traceback", "ERROR")):
            # 정상 종료지만 stderr에 에러 키워드가 있으면 요약 추가
            stderr_summary = stderr_text[:500]
            output += f"\n\n[stderr 요약]\n{stderr_summary}"

        return ClaudeResult(
            output=output,
            session_id=state.session_id,
        )

    except FileNotFoundError:
        logger.error("CLI를 찾을 수 없음: %s", CLAUDE_CLI_PATH)
        return ClaudeResult(
            f"오류: Claude Code CLI를 찾을 수 없습니다. 경로: {CLAUDE_CLI_PATH}"
        )
    except Exception as e:
        logger.exception("CLI 실행 중 예외 발생")
        return ClaudeResult(f"오류: {type(e).__name__}: {e}")
    finally:
        if proc is not None and proc.returncode is None:
            await _graceful_shutdown(proc)


async def _graceful_shutdown(proc: asyncio.subprocess.Process) -> None:
    """프로세스를 단계적으로 종료한다.

    Windows에서는 SIGTERM이 없으므로 terminate()를 사용하고,
    일정 시간 대기 후에도 종료되지 않으면 kill()로 강제종료한다.
    """
    try:
        proc.terminate()
    except ProcessLookupError:
        return

    try:
        await asyncio.wait_for(proc.wait(), timeout=GRACEFUL_SHUTDOWN_TIMEOUT)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            return
        await proc.wait()
