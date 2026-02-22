"""models.py CRUD 함수 테스트."""
from __future__ import annotations

import pytest

from src.db.models import (
    add_project,
    get_project,
    get_project_by_id,
    list_projects,
    add_task,
    complete_task,
    get_recent_tasks,
    get_user_state,
    set_user_state,
    get_all_user_states,
    save_message,
    get_message,
    get_pending_messages,
    mark_message_processed,
    get_messages_by_correlation,
)
from src.agents.schema import (
    AgentRole,
    MessageEnvelope,
    MessageType,
    TaskSpec,
    TaskResult,
    TaskStatus,
    ErrorReport,
    Severity,
)


# ---------------------------------------------------------------------------
# projects CRUD
# ---------------------------------------------------------------------------

class TestProjects:
    async def test_add_and_get(self, db):
        pid = await add_project("myapp", "/home/user/myapp", "테스트 앱")
        assert pid is not None
        proj = await get_project("myapp")
        assert proj is not None
        assert proj["name"] == "myapp"
        assert proj["path"] == "/home/user/myapp"
        assert proj["description"] == "테스트 앱"

    async def test_get_nonexistent(self, db):
        proj = await get_project("nope")
        assert proj is None

    async def test_get_by_id(self, db):
        pid = await add_project("proj1", "/p1")
        proj = await get_project_by_id(pid)
        assert proj is not None
        assert proj["name"] == "proj1"

    async def test_list_projects(self, db):
        await add_project("aaa", "/a")
        await add_project("bbb", "/b")
        projects = await list_projects()
        names = [p["name"] for p in projects]
        assert "aaa" in names
        assert "bbb" in names

    async def test_duplicate_name_raises(self, db):
        import aiosqlite
        await add_project("dup", "/d1")
        with pytest.raises(aiosqlite.IntegrityError):
            await add_project("dup", "/d2")


# ---------------------------------------------------------------------------
# task_history CRUD
# ---------------------------------------------------------------------------

class TestTaskHistory:
    async def test_add_and_complete(self, db):
        await add_project("taskproj", "/tp")
        tid = await add_task("taskproj", "버그를 고쳐줘")
        assert tid is not None

        await complete_task(tid, "수정 완료", "done")
        tasks = await get_recent_tasks("taskproj")
        assert len(tasks) == 1
        assert tasks[0]["status"] == "done"
        assert tasks[0]["result"] == "수정 완료"

    async def test_recent_tasks_limit(self, db):
        await add_project("limitproj", "/lp")
        for i in range(5):
            await add_task("limitproj", f"task {i}")
        tasks = await get_recent_tasks("limitproj", limit=3)
        assert len(tasks) == 3

    async def test_recent_tasks_empty(self, db):
        await add_project("empty", "/e")
        tasks = await get_recent_tasks("empty")
        assert tasks == []


# ---------------------------------------------------------------------------
# user_state CRUD
# ---------------------------------------------------------------------------

class TestUserState:
    async def test_set_and_get(self, db):
        await add_project("stateproj", "/sp")
        await set_user_state(111, "stateproj")
        state = await get_user_state(111)
        assert state == "stateproj"

    async def test_get_nonexistent(self, db):
        state = await get_user_state(999)
        assert state is None

    async def test_update_overwrites(self, db):
        await add_project("p1", "/p1")
        await add_project("p2", "/p2")
        await set_user_state(222, "p1")
        await set_user_state(222, "p2")
        state = await get_user_state(222)
        assert state == "p2"

    async def test_get_all_user_states(self, db):
        await add_project("x1", "/x1")
        await add_project("x2", "/x2")
        await set_user_state(10, "x1")
        await set_user_state(20, "x2")
        states = await get_all_user_states()
        assert states[10] == "x1"
        assert states[20] == "x2"


# ---------------------------------------------------------------------------
# agent_messages CRUD
# ---------------------------------------------------------------------------

class TestAgentMessages:
    def _make_envelope(self, **kwargs) -> MessageEnvelope:
        defaults = dict(
            type=MessageType.TASK_SPEC,
            source=AgentRole.ORCHESTRATOR,
            target=AgentRole.IMPLEMENTER,
            project_name="test-project",
            payload=TaskSpec(title="작업", description="테스트"),
        )
        defaults.update(kwargs)
        return MessageEnvelope(**defaults)

    async def test_save_and_get(self, db):
        await add_project("test-project", "/tp")
        env = self._make_envelope()
        msg_id = await save_message(env)
        assert msg_id == env.id

        row = await get_message(msg_id)
        assert row is not None
        assert row["type"] == "task_spec"
        assert row["source"] == "orchestrator"
        assert row["status"] == "pending"

    async def test_get_nonexistent(self, db):
        row = await get_message("nonexistent")
        assert row is None

    async def test_pending_messages(self, db):
        await add_project("test-project", "/tp")
        env1 = self._make_envelope()
        env2 = self._make_envelope(
            type=MessageType.ERROR_REPORT,
            payload=ErrorReport(severity=Severity.ERROR, error_type="E", message="m"),
        )
        await save_message(env1)
        await save_message(env2)

        pending = await get_pending_messages("implementer", "test-project")
        assert len(pending) == 2

    async def test_pending_messages_filter_by_project(self, db):
        await add_project("proj-a", "/a")
        await add_project("proj-b", "/b")
        env_a = self._make_envelope(project_name="proj-a")
        env_b = self._make_envelope(project_name="proj-b")
        await save_message(env_a)
        await save_message(env_b)

        pending_a = await get_pending_messages("implementer", "proj-a")
        assert len(pending_a) == 1
        assert pending_a[0]["project_name"] == "proj-a"

    async def test_mark_processed(self, db):
        await add_project("test-project", "/tp")
        env = self._make_envelope()
        msg_id = await save_message(env)

        await mark_message_processed(msg_id)
        row = await get_message(msg_id)
        assert row["status"] == "processed"
        assert row["processed_at"] is not None
        assert row["error"] is None

    async def test_mark_processed_with_error(self, db):
        await add_project("test-project", "/tp")
        env = self._make_envelope()
        msg_id = await save_message(env)

        await mark_message_processed(msg_id, error="타임아웃 발생")
        row = await get_message(msg_id)
        assert row["status"] == "error"
        assert row["error"] == "타임아웃 발생"

    async def test_processed_excluded_from_pending(self, db):
        await add_project("test-project", "/tp")
        env = self._make_envelope()
        msg_id = await save_message(env)
        await mark_message_processed(msg_id)

        pending = await get_pending_messages("implementer", "test-project")
        assert len(pending) == 0

    async def test_correlation_id_query(self, db):
        await add_project("test-project", "/tp")
        corr = "flow-001"
        env1 = self._make_envelope(correlation_id=corr)
        env2 = self._make_envelope(
            type=MessageType.TASK_RESULT,
            source=AgentRole.IMPLEMENTER,
            target=AgentRole.ORCHESTRATOR,
            correlation_id=corr,
            payload=TaskResult(status=TaskStatus.COMPLETED, output="done"),
        )
        env3 = self._make_envelope(correlation_id="other-flow")
        await save_message(env1)
        await save_message(env2)
        await save_message(env3)

        msgs = await get_messages_by_correlation(corr)
        assert len(msgs) == 2
        assert all(m["correlation_id"] == corr for m in msgs)

    async def test_pending_messages_limit(self, db):
        await add_project("test-project", "/tp")
        for _ in range(5):
            await save_message(self._make_envelope())

        pending = await get_pending_messages("implementer", limit=3)
        assert len(pending) == 3
