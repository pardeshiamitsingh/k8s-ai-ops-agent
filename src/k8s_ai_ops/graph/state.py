from typing import TypedDict

from k8s_ai_ops.models.incident import (
    IncidentAnalysis,
    IncidentRequest,
)


class AgentState(TypedDict, total=False):
    incident: IncidentRequest
    analysis: IncidentAnalysis