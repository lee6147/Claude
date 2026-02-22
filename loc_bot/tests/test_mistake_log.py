"""mistake_log CRUD 함수 테스트."""
from __future__ import annotations

from src.db.models import (
    add_mistake,
    get_mistakes,
    search_mistakes,
    delete_mistake,
)


class TestMistakeLog:
    async def test_add_and_get(self, db):
        mid = await add_mistake(
            "src/bot/handlers.py",
            "빈 문자열 split",
            "빈 입력 시 IndexError 발생",
        )
        assert mid is not None

        mistakes = await get_mistakes()
        assert len(mistakes) == 1
        assert mistakes[0]["file_path"] == "src/bot/handlers.py"
        assert mistakes[0]["pattern"] == "빈 문자열 split"
        assert mistakes[0]["description"] == "빈 입력 시 IndexError 발생"

    async def test_get_empty(self, db):
        mistakes = await get_mistakes()
        assert mistakes == []

    async def test_get_limit(self, db):
        for i in range(5):
            await add_mistake(f"file{i}.py", f"pattern{i}")
        mistakes = await get_mistakes(limit=3)
        assert len(mistakes) == 3

    async def test_get_order_desc(self, db):
        await add_mistake("a.py", "first")
        await add_mistake("b.py", "second")
        mistakes = await get_mistakes()
        # 최신 순이므로 second가 먼저
        assert mistakes[0]["pattern"] == "second"
        assert mistakes[1]["pattern"] == "first"

    async def test_search_by_pattern(self, db):
        await add_mistake("x.py", "TypeError 발생", "")
        await add_mistake("y.py", "IndexError 발생", "")
        await add_mistake("z.py", "기타 실수", "")

        results = await search_mistakes("TypeError")
        assert len(results) == 1
        assert results[0]["pattern"] == "TypeError 발생"

    async def test_search_by_description(self, db):
        await add_mistake("a.py", "패턴1", "timeout 에러 처리 누락")
        await add_mistake("b.py", "패턴2", "정상 동작")

        results = await search_mistakes("timeout")
        assert len(results) == 1
        assert results[0]["description"] == "timeout 에러 처리 누락"

    async def test_search_by_file_path(self, db):
        await add_mistake("src/claude/executor.py", "패턴A", "")
        await add_mistake("src/bot/handlers.py", "패턴B", "")

        results = await search_mistakes("executor")
        assert len(results) == 1
        assert results[0]["file_path"] == "src/claude/executor.py"

    async def test_search_no_match(self, db):
        await add_mistake("a.py", "패턴", "설명")
        results = await search_mistakes("존재하지않는키워드")
        assert results == []

    async def test_delete(self, db):
        mid = await add_mistake("d.py", "삭제할 패턴")
        assert mid is not None

        deleted = await delete_mistake(mid)
        assert deleted is True

        mistakes = await get_mistakes()
        assert len(mistakes) == 0

    async def test_delete_nonexistent(self, db):
        deleted = await delete_mistake(9999)
        assert deleted is False

    async def test_default_description_empty(self, db):
        await add_mistake("f.py", "패턴만")
        mistakes = await get_mistakes()
        assert mistakes[0]["description"] == ""
