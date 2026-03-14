"""에이전트 간 메시지 스키마 (Pydantic v2).

모든 에이전트 간 통신은 MessageEnvelope으로 래핑되며,
payload 필드에 구체적 메시지 타입이 들어간다.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Union

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentRole(str, Enum):
    """에이전트 역할 식별자."""
    ORCHESTRATOR = "orchestrator"
    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"
    PLANNER = "planner"
    DOCUMENTER = "documenter"
    DESIGNER = "designer"
    TESTER = "tester"
    QA = "qa"


class MessageType(str, Enum):
    """메시지 유형."""
    TASK_SPEC = "task_spec"
    TASK_RESULT = "task_result"
    REVIEW_REQUEST = "review_request"
    REVIEW_RESULT = "review_result"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESPONSE = "approval_response"
    ERROR_REPORT = "error_report"


class TaskStatus(str, Enum):
    """작업 상태."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_REVIEW = "needs_review"
    NEEDS_APPROVAL = "needs_approval"


class ReviewVerdict(str, Enum):
    """리뷰 판정."""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL_PASS = "conditional_pass"


class ApprovalDecision(str, Enum):
    """승인 결정."""
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class Severity(str, Enum):
    """에러/이슈 심각도."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# 종료 조건
# ---------------------------------------------------------------------------

class ExecutionBudget(BaseModel):
    """에이전트 실행 제한. 무한루프/비용 폭발 방지."""
    max_turns: int = 10
    timeout_seconds: int = 600
    token_budget: int | None = None
    max_retries: int = 2


# ---------------------------------------------------------------------------
# Payload 모델
# ---------------------------------------------------------------------------

class TaskSpec(BaseModel):
    """작업 명세. Orchestrator → Worker."""
    title: str
    description: str
    requirements: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    context_files: list[str] = Field(default_factory=list)
    image_paths: list[str] = Field(default_factory=list)
    budget: ExecutionBudget = Field(default_factory=ExecutionBudget)
    priority: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactRef(BaseModel):
    """작업 산출물 참조."""
    path: str
    artifact_type: str
    description: str = ""


class TaskResult(BaseModel):
    """작업 결과. Worker → Orchestrator."""
    status: TaskStatus
    output: str
    summary: str = ""
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    turns_used: int = 0
    execution_time_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    """리뷰 요청. 기존 .agents/claude/review-request-latest.md를 구조화."""
    changed_files: list[str]
    change_reason: str
    review_focus: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(
        default_factory=lambda: [
            "문법 오류 없음",
            "타입 안정성",
            "보안 취약점 없음",
            "에러 처리 적절함",
            "코드 중복 없음",
        ]
    )
    diff_summary: str = ""
    related_task_id: str | None = None
    budget: ExecutionBudget = Field(
        default_factory=lambda: ExecutionBudget(max_turns=5, timeout_seconds=300)
    )


class ReviewIssue(BaseModel):
    """리뷰에서 발견된 개별 이슈."""
    file_path: str
    line: int | None = None
    severity: Severity
    description: str
    suggestion: str = ""


class ReviewResult(BaseModel):
    """리뷰 결과. 기존 .agents/codex/review-result-*.md를 구조화."""
    verdict: ReviewVerdict
    summary: str
    issues: list[ReviewIssue] = Field(default_factory=list)
    checklist_results: dict[str, bool] = Field(default_factory=dict)
    round_number: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    """승인 요청. Telegram 인라인 키보드로 사용자에게 표시."""
    question: str
    context_summary: str
    options: list[str] = Field(
        default_factory=lambda: ["승인", "거부", "수정 요청"]
    )
    timeout_seconds: int = 3600
    auto_action: ApprovalDecision | None = None


class ApprovalResponse(BaseModel):
    """승인 응답. Telegram 콜백에서 생성."""
    decision: ApprovalDecision
    comment: str = ""
    responded_by: int = 0
    responded_at: datetime = Field(default_factory=datetime.now)


class ErrorReport(BaseModel):
    """에러 보고. 에이전트 실행 중 에러 발생 시 Orchestrator에게 보고."""
    severity: Severity
    error_type: str
    message: str
    traceback: str = ""
    recoverable: bool = True
    suggested_action: str = ""


# ---------------------------------------------------------------------------
# Payload 유니온 타입
# ---------------------------------------------------------------------------

PayloadType = Union[
    TaskSpec,
    TaskResult,
    ReviewRequest,
    ReviewResult,
    ApprovalRequest,
    ApprovalResponse,
    ErrorReport,
]

# MessageType → Payload 클래스 매핑
PAYLOAD_TYPE_MAP: dict[MessageType, type[BaseModel]] = {
    MessageType.TASK_SPEC: TaskSpec,
    MessageType.TASK_RESULT: TaskResult,
    MessageType.REVIEW_REQUEST: ReviewRequest,
    MessageType.REVIEW_RESULT: ReviewResult,
    MessageType.APPROVAL_REQUEST: ApprovalRequest,
    MessageType.APPROVAL_RESPONSE: ApprovalResponse,
    MessageType.ERROR_REPORT: ErrorReport,
}


# ---------------------------------------------------------------------------
# 메시지 엔벨로프
# ---------------------------------------------------------------------------

class MessageEnvelope(BaseModel):
    """모든 에이전트 메시지의 공통 래퍼."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    type: MessageType
    source: AgentRole
    target: AgentRole
    project_name: str
    session_id: str | None = None
    parent_id: str | None = None
    correlation_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    payload: PayloadType

    @model_validator(mode="after")
    def _check_type_payload_match(self) -> MessageEnvelope:
        expected_cls = PAYLOAD_TYPE_MAP.get(self.type)
        if expected_cls is not None and not isinstance(self.payload, expected_cls):
            raise ValueError(
                f"type={self.type!r} 에 대한 payload는 "
                f"{expected_cls.__name__}이어야 하지만 "
                f"{type(self.payload).__name__}이(가) 전달됨"
            )
        return self

    def to_db_dict(self) -> dict[str, Any]:
        """DB 저장용 딕셔너리로 변환한다."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source.value,
            "target": self.target.value,
            "project_name": self.project_name,
            "session_id": self.session_id,
            "parent_id": self.parent_id,
            "correlation_id": self.correlation_id,
            "payload": self.payload.model_dump_json(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> MessageEnvelope:
        """DB 행에서 MessageEnvelope을 복원한다."""
        import json

        msg_type = MessageType(row["type"])
        payload_cls = PAYLOAD_TYPE_MAP[msg_type]
        payload_data = json.loads(row["payload"])
        payload = payload_cls.model_validate(payload_data)

        return cls(
            id=row["id"],
            type=msg_type,
            source=AgentRole(row["source"]),
            target=AgentRole(row["target"]),
            project_name=row["project_name"],
            session_id=row.get("session_id"),
            parent_id=row.get("parent_id"),
            correlation_id=row.get("correlation_id"),
            created_at=datetime.fromisoformat(row["created_at"]),
            payload=payload,
        )
