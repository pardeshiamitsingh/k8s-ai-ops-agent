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
    Build the complete Kubernetes incident workflow.

    Architecture:

        START
          |
          v
        triage
          |
          v
      investigator
          |
          v
       diagnosis
          |
          v
        planner
          |
          v
        approval
          |
          | interrupt()
          |
          X
       HUMAN
          |
          | Command(resume=...)
          |
          +----------------------+
          |                      |
      approved                rejected
          |                      |
          v                      v
      remediation               END
          |
          v
         END

    Important:

    - Triage may use an LLM.
    - Investigation is deterministic.
    - Diagnosis is deterministic.
    - Planning is deterministic.
    - Approval is a LangGraph interrupt.
    - Remediation executes only after approval.
    - Rejection terminates the workflow.
    - InMemorySaver allows pause/resume using thread_id.
    """

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
        Run LLM-driven triage.

        triage_incident() must return a normal
        serializable dictionary/Pydantic model.
        """

        result = triage_incident(
            state,
            llm,
        )

        if result is None:
            return {}

        if isinstance(result, dict):
            return result

        if hasattr(
            result,
            "model_dump",
        ):
            return result.model_dump()

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
        Collect deterministic Kubernetes evidence.
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
        Convert raw investigation evidence into
        deterministic diagnosis.
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
        Generate deterministic remediation plan.
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
        Route the workflow based on human approval.

        approved=True:
            approval -> remediation

        approved=False:
            approval -> END

        Default behavior is deny.
        """

        if state.get(
            "remediation_approved",
            False,
        ):
            return "remediation"

        return END

    # ==================================================
    # REMEDIATION
    # ==================================================

    def remediation_node(
        state: AgentState,
    ) -> dict:
        """
        Execute remediation.

        This is the ONLY node that performs
        Kubernetes mutation.

        The approved flag is passed to the
        remediation service as a second
        safety boundary.
        """

        plan = state["remediation_plan"]
        incident = state["incident"]

        approved = state.get(
            "remediation_approved",
            False,
        )

        result = remediation_service.execute(
            plan,
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
    # EDGES
    # ==================================================

    graph.add_edge(
        START,
        "triage",
    )

    graph.add_edge(
        "triage",
        "investigator",
    )

    graph.add_edge(
        "investigator",
        "diagnosis",
    )

    graph.add_edge(
        "diagnosis",
        "planner",
    )

    graph.add_edge(
        "planner",
        "approval",
    )

    # IMPORTANT:
    #
    # Do NOT use:
    #
    # graph.add_edge("approval", "remediation")
    #
    # because that would execute remediation even
    # after human rejection.

    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "remediation": "remediation",
            END: END,
        },
    )

    graph.add_edge(
        "remediation",
        END,
    )

    # ==================================================
    # CHECKPOINTER
    # ==================================================

    checkpointer = InMemorySaver()

    return graph.compile(
        checkpointer=checkpointer,
    )