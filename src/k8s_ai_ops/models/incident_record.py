from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from k8s_ai_ops.models.diagnosis import Diagnosis
from k8s_ai_ops.models.incident import IncidentRequest
from k8s_ai_ops.models.remediation import RemediationPlan


class IncidentStatus(str, Enum):
    CREATED = "CREATED"
    DIAGNOSED = "DIAGNOSED"
    PLAN_CREATED = "PLAN_CREATED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class IncidentRecord(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    incident: IncidentRequest

    status: IncidentStatus = IncidentStatus.CREATED

    diagnosis: Diagnosis | None = None

    remediation_plan: RemediationPlan | None = None

    approval_required: bool = False

    approved_by: str | None = None

    approved_at: datetime | None = None

    rejected_by: str | None = None

    rejected_at: datetime | None = None

    execution_results: list[dict] = Field(
        default_factory=list
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)