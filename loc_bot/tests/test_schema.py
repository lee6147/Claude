"""schema.py 에이전트 메시지 스키마 테스트."""
from __future__ import annotations

import json
import pytest
from datetime import datetime

from src.agents.schema import (
    AgentRole,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalResponse,
    ArtifactRef,
    ErrorReport,
    ExecutionBudget,
    MessageEnvelope,
    MessageType,
    ReviewIssue,
    ReviewRequest,
    ReviewResult,
    ReviewVerdict,
    Severity,
    TaskResult,
    TaskSpec,
    TaskStatus,
    PAYLOAD_TYPE_MAP,
)


# ---------------------------------------------------------------------------
# Enum 테스트
# ---------------------------------------------------------------------------

class TestEnums:
    def test_agent_role_values(self):
        assert AgentRole.ORCHESTRATOR == "orchestrator"
        assert AgentRole.IMPLEMENTER == "implementer"
        assert AgentRole.REVIEWER == "reviewer"

    def test_message_type_values(self):
        assert MessageType.TASK_SPEC == "task_spec"
        assert MessageType.TASK_RESULT == "task_result"
        assert MessageType.REVIEW_REQUEST == "review_request"

    def test_task_status_values(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"

    def test_review_verdict_values(self):
        assert ReviewVerdict.PASS == "pass"
        assert ReviewVerdict.FAIL == "fail"
        assert ReviewVerdict.CONDITIONAL_PASS == "conditional_pass"

    def test_severity_values(self):
        assert Severity.INFO == "info"
        assert Severity.CRITICAL == "critical"


# ---------------------------------------------------------------------------
# ExecutionBudget 테스트
# ---------------------------------------------------------------------------

class TestExecutionBudget:
    def test_defaults(self):
        budget = ExecutionBudget()
        assert budget.max_turns == 10
        assert budget.timeout_seconds == 600
        assert budget.token_budget is None
        assert budget.max_retries == 2

    def test_custom_values(self):
        budget = ExecutionBudget(max_turns=3, timeout_seconds=120, token_budget=5000)
        assert budget.max_turns == 3
        assert budget.timeout_seconds == 120
        assert budget.token_budget == 5000


# ---------------------------------------------------------------------------
# TaskSpec 테스트
# ---------------------------------------------------------------------------

class TestTaskSpec:
    def test_minimal(self):
        spec = TaskSpec(title="버그 수정", description="로그인 오류 해결")
        assert spec.title == "버그 수정"
        assert spec.requirements == []
        assert spec.context_files == []
        assert spec.priority == 0

    def test_full(self):
        spec = TaskSpec(
            title="기능 추가",
            description="다크모드 토글",
            requirements=["CSS 변수 사용"],
            acceptance_criteria=["토글 버튼 동작"],
            context_files=["src/theme.py"],
            image_paths=["/tmp/mockup.png"],
            priority=3,
            metadata={"sprint": 5},
        )
        assert len(spec.requirements) == 1
        assert spec.priority == 3
        assert spec.metadata["sprint"] == 5


# ---------------------------------------------------------------------------
# TaskResult 테스트
# ---------------------------------------------------------------------------

class TestTaskResult:
    def test_minimal(self):
        result = TaskResult(status=TaskStatus.COMPLETED, output="완료됨")
        assert result.status == TaskStatus.COMPLETED
        assert result.artifacts == []
        assert result.turns_used == 0

    def test_with_artifacts(self):
        art = ArtifactRef(path="dist/app.js", artifact_type="build", description="빌드 결과물")
        result = TaskResult(
            status=TaskStatus.COMPLETED,
            output="빌드 성공",
            artifacts=[art],
            changed_files=["src/app.ts"],
            turns_used=3,
            execution_time_seconds=45.2,
        )
        assert len(result.artifacts) == 1
        assert result.artifacts[0].path == "dist/app.js"


# ---------------------------------------------------------------------------
# ReviewRequest / ReviewResult 테스트
# ---------------------------------------------------------------------------

class TestReview:
    def test_review_request_defaults(self):
        req = ReviewRequest(
            changed_files=["src/main.py"],
            change_reason="리팩토링",
        )
        assert len(req.checklist) == 5
        assert req.budget.max_turns == 5
        assert req.budget.timeout_seconds == 300

    def test_review_result(self):
        issue = ReviewIssue(
            file_path="src/main.py",
            line=42,
            severity=Severity.WARNING,
            description="미사용 import",
            suggestion="삭제하세요",
        )
        result = ReviewResult(
            verdict=ReviewVerdict.CONDITIONAL_PASS,
            summary="경미한 이슈 1건",
            issues=[issue],
            checklist_results={"문법 오류 없음": True, "보안 취약점 없음": True},
        )
        assert result.verdict == ReviewVerdict.CONDITIONAL_PASS
        assert len(result.issues) == 1
        assert result.issues[0].line == 42


# ---------------------------------------------------------------------------
# Approval 테스트
# ---------------------------------------------------------------------------

class TestApproval:
    def test_approval_request_defaults(self):
        req = ApprovalRequest(question="배포할까요?", context_summary="v1.2 릴리스")
        assert len(req.options) == 3
        assert req.timeout_seconds == 3600

    def test_approval_response(self):
        resp = ApprovalResponse(
            decision=ApprovalDecision.APPROVED,
            comment="LGTM",
            responded_by=12345,
        )
        assert resp.decision == ApprovalDecision.APPROVED
        assert isinstance(resp.responded_at, datetime)


# ---------------------------------------------------------------------------
# ErrorReport 테스트
# ---------------------------------------------------------------------------

class TestErrorReport:
    def test_basic(self):
        err = ErrorReport(
            severity=Severity.ERROR,
            error_type="FileNotFoundError",
            message="파일을 찾을 수 없습니다",
            recoverable=False,
        )
        assert err.severity == Severity.ERROR
        assert err.recoverable is False


# ---------------------------------------------------------------------------
# PAYLOAD_TYPE_MAP 테스트
# ---------------------------------------------------------------------------

class TestPayloadTypeMap:
    def test_all_message_types_mapped(self):
        for mt in MessageType:
            assert mt in PAYLOAD_TYPE_MAP, f"{mt} 가 PAYLOAD_TYPE_MAP에 없음"

    def test_map_values_are_classes(self):
        for mt, cls in PAYLOAD_TYPE_MAP.items():
            assert isinstance(cls, type), f"{mt} → {cls} 는 클래스가 아님"


# ---------------------------------------------------------------------------
# MessageEnvelope 테스트
# ---------------------------------------------------------------------------

class TestMessageEnvelope:
    def _make_envelope(self, **kwargs) -> MessageEnvelope:
        defaults = dict(
            type=MessageType.TASK_SPEC,
            source=AgentRole.ORCHESTRATOR,
            target=AgentRole.IMPLEMENTER,
            project_name="test-project",
            payload=TaskSpec(title="테스트", description="테스트 작업"),
        )
        defaults.update(kwargs)
        return MessageEnvelope(**defaults)

    def test_auto_id(self):
        env = self._make_envelope()
        assert len(env.id) == 12

    def test_auto_created_at(self):
        env = self._make_envelope()
        assert isinstance(env.created_at, datetime)

    def test_type_payload_mismatch_raises(self):
        with pytest.raises(ValueError, match="payload는"):
            MessageEnvelope(
                type=MessageType.TASK_SPEC,
                source=AgentRole.ORCHESTRATOR,
                target=AgentRole.IMPLEMENTER,
                project_name="test",
                payload=ErrorReport(
                    severity=Severity.ERROR,
                    error_type="Test",
                    message="mismatch",
                ),
            )

    def test_to_db_dict(self):
        env = self._make_envelope()
        d = env.to_db_dict()
        assert d["type"] == "task_spec"
        assert d["source"] == "orchestrator"
        assert d["project_name"] == "test-project"
        # payload는 JSON 문자열
        parsed = json.loads(d["payload"])
        assert parsed["title"] == "테스트"

    def test_from_db_row_roundtrip(self):
        env = self._make_envelope(session_id="s1", correlation_id="c1")
        db_dict = env.to_db_dict()
        restored = MessageEnvelope.from_db_row(db_dict)
        assert restored.id == env.id
        assert restored.type == env.type
        assert restored.source == env.source
        assert restored.target == env.target
        assert restored.session_id == "s1"
        assert restored.correlation_id == "c1"
        assert isinstance(restored.payload, TaskSpec)
        assert restored.payload.title == "테스트"

    def test_all_payload_types_roundtrip(self):
        """모든 메시지 타입에 대해 to_db_dict → from_db_row 라운드트립 테스트."""
        payloads = {
            MessageType.TASK_SPEC: TaskSpec(title="t", description="d"),
            MessageType.TASK_RESULT: TaskResult(status=TaskStatus.COMPLETED, output="ok"),
            MessageType.REVIEW_REQUEST: ReviewRequest(changed_files=["a.py"], change_reason="fix"),
            MessageType.REVIEW_RESULT: ReviewResult(verdict=ReviewVerdict.PASS, summary="ok"),
            MessageType.APPROVAL_REQUEST: ApprovalRequest(question="?", context_summary="ctx"),
            MessageType.APPROVAL_RESPONSE: ApprovalResponse(decision=ApprovalDecision.APPROVED),
            MessageType.ERROR_REPORT: ErrorReport(severity=Severity.ERROR, error_type="E", message="m"),
        }
        for msg_type, payload in payloads.items():
            env = MessageEnvelope(
                type=msg_type,
                source=AgentRole.ORCHESTRATOR,
                target=AgentRole.REVIEWER,
                project_name="roundtrip-test",
                payload=payload,
            )
            restored = MessageEnvelope.from_db_row(env.to_db_dict())
            assert restored.type == msg_type
            assert type(restored.payload) == type(payload)
