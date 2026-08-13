from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from k8s_ai_ops.agents.triage import triage_incident
from k8s_ai_ops.graph.state import AgentState
from k8s_ai_ops.investigation.deterministic import (
    DeterministicInvestigator,
)
from k8s_ai_ops.investigation.diagnosis import (
    DeterministicDiagnosis,
)
from k8s_ai_ops.remediation.approval_node import (
    remediation_approval_node,
)
from k8s_ai_ops.remediation.planner import (
    RemediationPlanner,
)
from k8s_ai_ops.remediation.service import (
    RemediationService,
)


def build_incident_graph(
    llm: BaseChatModel,
):
    """
    Build the complete Kubernetes AIOps incident workflow.

    Workflow:

        START
          |
          v
        TRIAGE
          |
          v
      INVESTIGATOR
          |
          v
       DIAGNOSIS
          |
          v
        PLANNER
          |
          v
       APPROVAL
          |
          | interrupt()
          |
          X
      HUMAN APPROVAL
          |
       +--+--+
       |     |
      YES    NO
       |     |
       v     v
    REMEDIATION  END
       |
       v
      END

    Design principles:

    - Triage may use an LLM.
    - Investigation is deterministic.
    - Diagnosis is deterministic.
    - Remediation planning is deterministic.
    - Human approval is handled using LangGraph interrupt().
    - Kubernetes mutation happens only in the remediation node.
    - Rejection terminates the workflow.
    - InMemorySaver provides checkpointing for the POC.
    """

    # ==================================================
    # GRAPH
    # ==================================================

    graph = StateGraph(AgentState)

    # ==================================================
    # COMPONENTS
    # ==================================================

    investigator = DeterministicInvestigator()

    diagnosis_engine = DeterministicDiagnosis()

    planner = RemediationPlanner()

    remediation_service = RemediationService()

    # ==================================================
    # TRIAGE
    # ==================================================

    def triage_node(
        state: AgentState,
    ) -> dict:
        """
        Run LLM-driven incident triage.

        The triage agent analyzes the incident and
        determines whether further investigation is
        required.
        """

        result = triage_incident(
            state,
            llm,
        )

        if result is None:
            return {}

        # Pydantic model
        if hasattr(
            result,
            "model_dump",
        ):
            return result.model_dump()

        # Normal dictionary
        if isinstance(
            result,
            dict,
        ):
            return result

        raise TypeError(
            "triage_incident() must return "
            "a dict or Pydantic model. "
            f"Received: {type(result)!r}"
        )

    graph.add_node(
        "triage",
        triage_node,
    )

    # ==================================================
    # INVESTIGATION
    # ==================================================

    def investigate_node(
        state: AgentState,
    ) -> dict:
        """
        Collect Kubernetes evidence.

        Investigation is deterministic and does not
        use the LLM.
        """

        incident = state["incident"]

        investigation = investigator.investigate(
            incident
        )

        return {
            "investigation_results": investigation,
            "investigation_complete": True,
        }

    graph.add_node(
        "investigator",
        investigate_node,
    )

    # ==================================================
    # DIAGNOSIS
    # ==================================================

    def diagnosis_node(
        state: AgentState,
    ) -> dict:
        """
        Convert Kubernetes investigation evidence
        into a deterministic diagnosis.
        """

        investigation = state.get(
            "investigation_results",
            {},
        )

        diagnosis = diagnosis_engine.diagnose(
            investigation
        )

        return {
            "diagnosis": diagnosis,
        }

    graph.add_node(
        "diagnosis",
        diagnosis_node,
    )

    # ==================================================
    # REMEDIATION PLANNER
    # ==================================================

    def planner_node(
        state: AgentState,
    ) -> dict:
        """
        Generate a remediation plan from the diagnosis.

        IMPORTANT:

        This node only proposes actions.

        It does NOT modify Kubernetes.
        """

        diagnosis = state["diagnosis"]

        plan = planner.plan(
            diagnosis
        )

        return {
            "remediation_plan": plan,
        }

    graph.add_node(
        "planner",
        planner_node,
    )

    # ==================================================
    # HUMAN APPROVAL
    # ==================================================

    graph.add_node(
        "approval",
        remediation_approval_node,
    )

    # ==================================================
    # APPROVAL ROUTING
    # ==================================================

    def route_after_approval(
        state: AgentState,
    ) -> str:
        """
        Decide what happens after human approval.

        approved=True:
            approval -> remediation

        approved=False:
            approval -> END

        Default is DENY.
        """

        approved = state.get(
            "remediation_approved",
            False,
        )

        if approved:
            return "remediation"

        return END

    # ==================================================
    # REMEDIATION
    # ==================================================

    def remediation_node(
        state: AgentState,
    ) -> dict:
        """
        Execute the approved remediation plan.

        This is the ONLY workflow node responsible
        for Kubernetes mutation.

        There are two safety boundaries:

        1. LangGraph approval state.
        2. RemediationService approval check.
        """

        plan = state["remediation_plan"]

        incident = state["incident"]

        approved = state.get(
            "remediation_approved",
            False,
        )

        result = remediation_service.execute(
            plan=plan,
            approved=approved,
            namespace=incident.namespace,
            service=incident.service,
        )

        return {
            "remediation_result": result,
            "remediation_complete": True,
        }

    graph.add_node(
        "remediation",
        remediation_node,
    )

    # ==================================================
    # GRAPH EDGES
    # ==================================================

    # START
    graph.add_edge(
        START,
        "triage",
    )

    # Triage -> Investigation
    graph.add_edge(
        "triage",
        "investigator",
    )

    # Investigation -> Diagnosis
    graph.add_edge(
        "investigator",
        "diagnosis",
    )

    # Diagnosis -> Planner
    graph.add_edge(
        "diagnosis",
        "planner",
    )

    # Planner -> Human Approval
    graph.add_edge(
        "planner",
        "approval",
    )

    # ==================================================
    # APPROVAL -> REMEDIATION / END
    # ==================================================

    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "remediation": "remediation",
            END: END,
        },
    )

    # ==================================================
    # REMEDIATION -> END
    # ==================================================

    graph.add_edge(
        "remediation",
        END,
    )

    # ==================================================
    # CHECKPOINTING
    # ==================================================

    checkpointer = InMemorySaver()

    # ==================================================
    # COMPILE
    # ==================================================

    return graph.compile(
        checkpointer=checkpointer,
    )


# ======================================================
# BACKWARD-COMPATIBLE FACTORY
# ======================================================

def build_workflow(
    llm: BaseChatModel,
):
    """
    Build and return the incident workflow.

    This wrapper exists because IncidentService
    imports build_workflow().
    """

    return build_incident_graph(
        llm
    )