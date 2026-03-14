"""테스트 공통 fixture."""
from __future__ import annotations

import pytest
import aiosqlite

from src.db import database as db_module


@pytest.fixture
async def db():
    """각 테스트마다 인메모리 DB로 교체하고 테스트 후 정리."""
    # 기존 연결 닫기
    await db_module.close_db()

    # 인메모리 DB로 교체
    db_module._db = await aiosqlite.connect(":memory:")
    db_module._db.row_factory = aiosqlite.Row
    await db_module._db.execute("PRAGMA foreign_keys=ON")

    # 스키마 초기화
    from src.db.database import init_db
    await init_db()

    yield db_module._db

    # 정리
    await db_module.close_db()
