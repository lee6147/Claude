import asyncio
import aiosqlite
from pathlib import Path
from config.settings import DB_PATH

# 싱글턴 DB 연결 (앱 수명 동안 유지)
_db: aiosqlite.Connection | None = None
_db_lock = asyncio.Lock()


async def get_db() -> aiosqlite.Connection:
    """싱글턴 DB 연결을 반환한다. 첫 호출 시 연결을 생성하고 WAL 모드를 활성화한다."""
    global _db
    if _db is not None:
        return _db
    async with _db_lock:
        if _db is None:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            _db = await aiosqlite.connect(DB_PATH)
            _db.row_factory = aiosqlite.Row
            await _db.execute("PRAGMA journal_mode=WAL")
            await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def close_db():
    """앱 종료 시 DB 연결을 닫는다."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None


async def init_db():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            path TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            result TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (project_name) REFERENCES projects(name)
        );

        CREATE TABLE IF NOT EXISTS mistake_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            pattern TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_state (
            user_id INTEGER PRIMARY KEY,
            current_project TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_messages (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            project_name TEXT NOT NULL,
            session_id TEXT,
            parent_id TEXT,
            correlation_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            processed_at TEXT,
            error TEXT,
            FOREIGN KEY (project_name) REFERENCES projects(name),
            FOREIGN KEY (parent_id) REFERENCES agent_messages(id)
        );

        CREATE INDEX IF NOT EXISTS idx_agent_messages_correlation
            ON agent_messages(correlation_id);
        CREATE INDEX IF NOT EXISTS idx_agent_messages_project_type
            ON agent_messages(project_name, type);
        CREATE INDEX IF NOT EXISTS idx_agent_messages_target_status
            ON agent_messages(target, status);
        CREATE INDEX IF NOT EXISTS idx_agent_messages_created
            ON agent_messages(created_at);
    """)
    await db.commit()
