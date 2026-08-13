from datetime import datetime

from pydantic import BaseModel, Field


class RemediationAction(BaseModel):
    action: str
    description: str
    risk: str
    requires_approval: bool = True


class RemediationPlan(BaseModel):
    root_cause: str

    actions: list[RemediationAction] = Field(
        default_factory=list
    )

    requires_human_approval: bool = True


class RemediationApproval(BaseModel):
    approved: bool
    approved_by: str
    reason: str | None = None
    approved_at: datetime   