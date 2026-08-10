from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    approved_by: str


class RejectionRequest(BaseModel):
    rejected_by: str