from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from k8s_ai_ops.models.remediation import RemediationPlan
from k8s_ai_ops.models.diagnosis import Diagnosis
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

    # Raw deterministic investigation evidence.
    #
    # Example:
    #
    # {
    #     "incident": {...},
    #     "pods": [...],
    #     "relevant_pods": [...],
    #     "pod_events": {...},
    #     "pod_logs": {...},
    # }
    investigation_results: list[dict[str, Any]]

    investigation_complete: bool

    # Final deterministic diagnosis.
    diagnosis: Diagnosis

    remediation_plan: RemediationPlan

    remediation_approved: bool

    remediation_result: list[dict[str, Any]]