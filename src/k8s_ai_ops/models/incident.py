
from typing import Literal

from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    service: str = Field(
        ...,
        description="Kubernetes service or deployment",
    )
    namespace: str = Field(
        default="default",
    )
    description: str
    severity: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ] = "medium"


class IncidentAnalysis(BaseModel):
    """
    Initial triage analysis.
    """

    incident_type: str

    investigation_required: bool

    initial_hypotheses: list[str]

    reasoning: str


class IncidentDiagnosis(BaseModel):
    """
    Final diagnosis based on observed
    Kubernetes investigation evidence.
    """

    root_cause: str = Field(
        description=(
            "Root cause or most likely cause "
            "based only on collected evidence."
        )
    )

    confidence: Literal[
        "low",
        "medium",
        "high",
    ] = Field(
        description="Confidence in the diagnosis.",
    )

    evidence: list[str] = Field(
        description=(
            "Observed facts from Kubernetes tools "
            "that support the diagnosis."
        ),
    )

    recommended_next_steps: list[str] = Field(
        description=(
            "Recommended next investigation or "
            "operational steps."
        ),
    )

    human_intervention_required: bool = Field(
        description=(
            "Whether human intervention is required "
            "before taking further action."
        ),
    )


class IncidentState(BaseModel):
    incident: IncidentRequest

    analysis: IncidentAnalysis | None = None

    diagnosis: IncidentDiagnosis | None = None

