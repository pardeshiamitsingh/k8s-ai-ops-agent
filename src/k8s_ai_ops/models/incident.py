from typing import Literal

from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    service: str = Field(..., description="Kubernetes service or deployment")
    namespace: str = Field(default="default")
    description: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"


class IncidentAnalysis(BaseModel):
    incident_type: str
    investigation_required: bool
    initial_hypotheses: list[str]
    reasoning: str


class IncidentState(BaseModel):
    incident: IncidentRequest
    analysis: IncidentAnalysis | None = None