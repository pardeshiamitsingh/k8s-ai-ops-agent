from pydantic import BaseModel, Field


class Diagnosis(BaseModel):
    """
    Deterministic diagnosis produced from Kubernetes
    investigation evidence.
    """

    root_cause: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    evidence: list[str] = Field(
        default_factory=list,
    )

    recommended_next_steps: list[str] = Field(
        default_factory=list,
    )

    human_intervention_required: bool = False