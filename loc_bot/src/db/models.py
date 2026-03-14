from __future__ import annotations

from src.db.database import get_db
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.schema import MessageEnvelope


async def add_project(name: str, path: str, description: str = "") -> int | None:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO projects (name, path, description) VALUES (?, ?, ?)",
        (name, path, description),
    )
    await db.commit()
    return cursor.lastrowid


async def get_project(name: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM projects WHERE name = ?", (name,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_project_by_id(project_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def list_projects() -> list[dict]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM projects ORDER BY name")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def add_task(project_name: str, prompt: str) -> int | None:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO task_history (project_name, prompt) VALUES (?, ?)",
        (project_name, prompt),
    )
    await db.commit()
    return cursor.lastrowid


async def complete_task(task_id: int, result: str, status: str = "done") -> bool:
    """작업을 완료 처리한다. 반환: 업데이트 성공 여부."""
    db = await get_db()
    cursor = await db.execute(
        "UPDATE task_history SET result = ?, status = ?, completed_at = ? WHERE id = ?",
        (result, status, datetime.now().isoformat(), task_id),
    )
    await db.commit()
    return cursor.rowcount > 0


async def get_recent_tasks(project_name: str, limit: int = 10) -> list[dict]:
    db = await get_db()
    limit = max(1, limit)
    cursor = await db.execute(
        "SELECT * FROM task_history WHERE project_name = ? ORDER BY created_at DESC LIMIT ?",
        (project_name, limit),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- user_state ---


async def get_user_state(user_id: int) -> str | None:
    """사용자가 현재 선택한 프로젝트 이름을 반환한다. 없으면 None."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT current_project FROM user_state WHERE user_id = ?", (user_id,)
    )
    row = await cursor.fetchone()
    return row["current_project"] if row else None


async def set_user_state(user_id: int, project_name: str) -> None:
    """사용자의 현재 프로젝트 선택을 저장한다."""
    db = await get_db()
    await db.execute(
        "INSERT INTO user_state (user_id, current_project, updated_at) VALUES (?, ?, ?)"
        " ON CONFLICT(user_id) DO UPDATE SET current_project = excluded.current_project,"
        " updated_at = excluded.updated_at",
        (user_id, project_name, datetime.now().isoformat()),
    )
    await db.commit()


async def get_all_user_states() -> dict[int, str]:
    """모든 사용자의 현재 프로젝트 상태를 반환한다. 봇 시작 시 로드용."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT user_id, current_project FROM user_state WHERE current_project IS NOT NULL"
    )
    rows = await cursor.fetchall()
    return {row["user_id"]: row["current_project"] for row in rows}


# --- agent_messages ---


async def save_message(envelope: MessageEnvelope) -> str:
    """에이전트 메시지를 저장한다. 반환: message id."""
    db = await get_db()
    data = envelope.to_db_dict()
    await db.execute(
        """INSERT INTO agent_messages
           (id, type, source, target, project_name, session_id,
            parent_id, correlation_id, status, payload, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
        (
            data["id"],
            data["type"],
            data["source"],
            data["target"],
            data["project_name"],
            data["session_id"],
            data["parent_id"],
            data["correlation_id"],
            data["payload"],
            data["created_at"],
        ),
    )
    await db.commit()
    return data["id"]


async def get_message(message_id: str) -> dict | None:
    """메시지 ID로 조회."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM agent_messages WHERE id = ?", (message_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_pending_messages(
    target: str,
    project_name: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """특정 에이전트의 미처리 메시지 목록."""
    db = await get_db()
    limit = max(1, limit)
    if project_name:
        cursor = await db.execute(
            """SELECT * FROM agent_messages
               WHERE target = ? AND project_name = ? AND status = 'pending'
               ORDER BY created_at LIMIT ?""",
            (target, project_name, limit),
        )
    else:
        cursor = await db.execute(
            """SELECT * FROM agent_messages
               WHERE target = ? AND status = 'pending'
               ORDER BY created_at LIMIT ?""",
            (target, limit),
        )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def mark_message_processed(
    message_id: str,
    error: str | None = None,
) -> bool:
    """메시지를 처리 완료로 표시. 반환: 업데이트 성공 여부."""
    db = await get_db()
    status = "error" if error else "processed"
    cursor = await db.execute(
        """UPDATE agent_messages
           SET status = ?, processed_at = ?, error = ?
           WHERE id = ?""",
        (status, datetime.now().isoformat(), error, message_id),
    )
    await db.commit()
    return cursor.rowcount > 0


async def get_messages_by_correlation(
    correlation_id: str,
) -> list[dict]:
    """같은 작업 흐름의 모든 메시지 조회 (시간순)."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM agent_messages
           WHERE correlation_id = ?
           ORDER BY created_at""",
        (correlation_id,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- mistake_log ---


async def add_mistake(file_path: str, pattern: str, description: str = "") -> int | None:
    """실수 패턴을 기록한다. 반환: row id."""
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO mistake_log (file_path, pattern, description) VALUES (?, ?, ?)",
        (file_path, pattern, description),
    )
    await db.commit()
    return cursor.lastrowid


async def get_mistakes(limit: int = 50) -> list[dict]:
    """최근 실수 패턴 목록을 반환한다."""
    db = await get_db()
    limit = max(1, limit)
    cursor = await db.execute(
        "SELECT * FROM mistake_log ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def search_mistakes(keyword: str) -> list[dict]:
    """패턴이나 설명에서 키워드를 검색한다."""
    db = await get_db()
    like = f"%{keyword}%"
    cursor = await db.execute(
        """SELECT * FROM mistake_log
           WHERE pattern LIKE ? OR description LIKE ? OR file_path LIKE ?
           ORDER BY created_at DESC""",
        (like, like, like),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def delete_mistake(mistake_id: int) -> bool:
    """실수 기록을 삭제한다. 반환: 삭제 성공 여부."""
    db = await get_db()
    cursor = await db.execute(
        "DELETE FROM mistake_log WHERE id = ?", (mistake_id,)
    )
    await db.commit()
    return cursor.rowcount > 0
