from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from k8s_ai_ops.models.diagnosis import Diagnosis
from k8s_ai_ops.models.incident import (
    IncidentAnalysis,
    IncidentRequest,
)
from k8s_ai_ops.models.remediation import RemediationPlan


class AgentState(TypedDict, total=False):
    """
    Shared state for the complete Kubernetes AIOps workflow.

    Workflow:

        IncidentRequest
             |
             v
          Triage
             |
             v
       Investigation
             |
             v
         Diagnosis
             |
             v
      RemediationPlan
             |
             v
       Human Approval
             |
             v
        Remediation
    """

    # ==================================================
    # INCIDENT
    # ==================================================

    incident: IncidentRequest

    # Optional LLM-generated triage analysis.
    analysis: IncidentAnalysis

    # LangChain conversation/messages if required by
    # future agent nodes.
    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    # ==================================================
    # INVESTIGATION
    # ==================================================

    investigation_results: list[dict[str, Any]]

    investigation_complete: bool

    # ==================================================
    # DIAGNOSIS
    # ==================================================

    diagnosis: Diagnosis

    # ==================================================
    # REMEDIATION PLANNING
    # ==================================================

    remediation_plan: RemediationPlan

    # ==================================================
    # HUMAN APPROVAL
    # ==================================================

    remediation_approved: bool

    remediation_approved_by: str | None

    remediation_approval_reason: str | None

    # ==================================================
    # REMEDIATION EXECUTION
    # ==================================================

    remediation_result: list[dict[str, Any]]

    remediation_complete: bool