from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from k8s_ai_ops.models.incident import (
    IncidentAnalysis,
    IncidentRequest,
)


class AgentState(TypedDict, total=False):
    incident: IncidentRequest

    analysis: IncidentAnalysis

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    investigation_results: list[dict[str, Any]]

    investigation_complete: bool

    diagnosis: str