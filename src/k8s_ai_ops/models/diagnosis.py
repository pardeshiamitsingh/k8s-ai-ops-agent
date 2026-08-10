from pydantic import BaseModel, Field
from typing import List


class Diagnosis(BaseModel):
    root_cause: str
    confidence: str
    evidence: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    human_intervention_required: bool = False
