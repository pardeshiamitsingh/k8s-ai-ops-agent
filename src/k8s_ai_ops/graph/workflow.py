from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from k8s_ai_ops.agents.triage import triage_incident
from k8s_ai_ops.graph.state import AgentState
from k8s_ai_ops.investigation.deterministic import (
    DeterministicInvestigator,
)
from k8s_ai_ops.investigation.diagnosis import (
    DeterministicDiagnosis,
)
from k8s_ai_ops.remediation.planner import (
    RemediationPlanner,
)


def build_incident_graph(
    llm: BaseChatModel,
):
    """
    Build the Kubernetes incident investigation graph.

    Architecture:

        START
          |
          v
        triage              <- LLM
          |
          v
        investigator        <- deterministic
          |
          v
        diagnosis           <- deterministic
          |
          v
        planner             <- deterministic
          |
          v
         END

    Responsibilities:

    1. Triage
       Understand and classify the incoming incident using the LLM.

    2. Investigation
       Collect Kubernetes evidence using deterministic logic.

    3. Diagnosis
       Determine the most likely root cause from observed evidence.

    4. Remediation planning
       Convert the diagnosis into a proposed remediation plan.

    IMPORTANT:
    This graph does NOT execute remediation.

    Kubernetes mutations must happen separately through
    RemediationExecutor after explicit human approval.
    """

    graph = StateGraph(AgentState)

    # ==========================================================
    # COMPONENTS
    # ==========================================================

    investigator = DeterministicInvestigator()
    diagnosis_engine = DeterministicDiagnosis()
    remediation_planner = RemediationPlanner()

    # ==========================================================
    # TRIAGE
    # ==========================================================
    #
    # LLM understands the incoming incident and produces the
    # normalized incident information used by the rest of the
    # workflow.
    #
    # ==========================================================

    def triage_node(
        state: AgentState,
    ) -> dict:

        return triage_incident(
            state,
            llm,
        )

    graph.add_node(
        "triage",
        triage_node,
    )

    # ==========================================================
    # INVESTIGATION
    # ==========================================================
    #
    # Deterministic Kubernetes investigation.
    #
    # No LLM is involved here.
    #
    # The investigator collects:
    #
    #   - pods
    #   - relevant pods
    #   - Kubernetes events
    #   - container logs
    #
    # ==========================================================

    def investigate_node(
        state: AgentState,
    ) -> dict:

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

    # ==========================================================
    # DIAGNOSIS
    # ==========================================================
    #
    # Determine root cause using only observed evidence.
    #
    # Example:
    #
    #   OOMKilled
    #   CrashLoopBackOff
    #   ImagePullBackOff
    #   Probe failure
    #   Application error
    #   Unknown
    #
    # ==========================================================

    def diagnosis_node(
        state: AgentState,
    ) -> dict:

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

    # ==========================================================
    # REMEDIATION PLANNER
    # ==========================================================
    #
    # Converts the diagnosis into proposed remediation actions.
    #
    # IMPORTANT:
    #
    # The planner ONLY proposes actions.
    #
    # It does NOT:
    #
    #   - patch Kubernetes
    #   - restart pods
    #   - scale deployments
    #   - modify resources
    #
    # Those operations belong to RemediationExecutor and require
    # explicit approval.
    #
    # ==========================================================

    def planner_node(
        state: AgentState,
    ) -> dict:

        diagnosis = state["diagnosis"]

        plan = remediation_planner.plan(
            diagnosis
        )

        return {
            "remediation_plan": plan,
        }

    graph.add_node(
        "planner",
        planner_node,
    )

    # ==========================================================
    # GRAPH EDGES
    # ==========================================================

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
        END,
    )

    # ==========================================================
    # COMPILE
    # ==========================================================

    return graph.compile()
