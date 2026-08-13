from unittest.mock import patch

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langgraph.types import Command

from k8s_ai_ops.graph.workflow import (
    build_incident_graph,
)
from k8s_ai_ops.models.diagnosis import Diagnosis
from k8s_ai_ops.models.incident import IncidentRequest
from k8s_ai_ops.models.remediation import (
    RemediationAction,
    RemediationPlan,
)


class FakeLLM(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(
        self,
        messages,
        stop=None,
        run_manager=None,
        **kwargs,
    ):
        from langchain_core.outputs import (
            ChatGeneration,
            ChatResult,
        )

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content="triage complete"
                    )
                )
            ]
        )


def test_graph_pauses_for_approval():

    incident = IncidentRequest(
        service="payment-service",
        namespace="default",
        description=(
            "Payment pod keeps crashing."
        ),
        severity="medium",
    )

    diagnosis = Diagnosis(
        root_cause="CrashLoopBackOff",
        confidence=0.95,
        evidence=[
            "Container repeatedly crashes",
        ],
    )

    plan = RemediationPlan(
        root_cause="CrashLoopBackOff",
        actions=[
            RemediationAction(
                action="restart_workload",
                description="Restart workload.",
                risk="medium",
                requires_approval=True,
            )
        ],
        requires_human_approval=True,
    )

    graph = build_incident_graph(
        FakeLLM()
    )

    config = {
        "configurable": {
            "thread_id": "test-approval-pause"
        }
    }

    with patch(
        "k8s_ai_ops.graph.workflow.triage_incident",
        return_value={},
    ), patch(
        "k8s_ai_ops.graph.workflow.DeterministicInvestigator.investigate",
        return_value=[],
    ), patch(
        "k8s_ai_ops.graph.workflow.DeterministicDiagnosis.diagnose",
        return_value=diagnosis,
    ), patch(
        "k8s_ai_ops.graph.workflow.RemediationPlanner.plan",
        return_value=plan,
    ):

        result = graph.invoke(
            {
                "incident": incident,
            },
            config=config,
        )

    # Graph must pause before remediation.
    assert result.get("remediation_result") is None

    # Verify an interrupt exists.
    state = graph.get_state(config)

    assert state.next == (
        "approval",
    )


def test_graph_resumes_after_approval():

    incident = IncidentRequest(
        service="payment-service",
        namespace="default",
        description=(
            "Payment pod keeps crashing."
        ),
        severity="medium",
    )

    diagnosis = Diagnosis(
        root_cause="CrashLoopBackOff",
        confidence=0.95,
        evidence=[
            "Container repeatedly crashes",
        ],
    )

    plan = RemediationPlan(
        root_cause="CrashLoopBackOff",
        actions=[
            RemediationAction(
                action="restart_workload",
                description="Restart workload.",
                risk="medium",
                requires_approval=True,
            )
        ],
        requires_human_approval=True,
    )

    graph = build_incident_graph(
        FakeLLM()
    )

    config = {
        "configurable": {
            "thread_id": "test-approval-resume"
        }
    }

    with patch(
        "k8s_ai_ops.graph.workflow.triage_incident",
        return_value={},
    ), patch(
        "k8s_ai_ops.graph.workflow.DeterministicInvestigator.investigate",
        return_value=[],
    ), patch(
        "k8s_ai_ops.graph.workflow.DeterministicDiagnosis.diagnose",
        return_value=diagnosis,
    ), patch(
        "k8s_ai_ops.graph.workflow.RemediationPlanner.plan",
        return_value=plan,
    ), patch(
        "k8s_ai_ops.graph.workflow.RemediationService.execute",
        return_value=[
            {
                "action": "restart_workload",
                "status": "executed",
            }
        ],
    ) as execute_mock:

        # ----------------------------------------------
        # First invocation.
        # ----------------------------------------------

        graph.invoke(
            {
                "incident": incident,
            },
            config=config,
        )

        # ----------------------------------------------
        # Resume with approval.
        # ----------------------------------------------

        result = graph.invoke(
            Command(
                resume={
                    "approved": True,
                    "approved_by": "amit",
                    "reason": (
                        "Reviewed evidence and "
                        "approved restart."
                    ),
                }
            ),
            config=config,
        )

    # ----------------------------------------------
    # Approval state
    # ----------------------------------------------

    assert (
        result["remediation_approved"]
        is True
    )

    assert (
        result["remediation_approved_by"]
        == "amit"
    )

    assert (
        result["remediation_approval_reason"]
        == (
            "Reviewed evidence and "
            "approved restart."
        )
    )

    # ----------------------------------------------
    # Remediation state
    # ----------------------------------------------

    assert (
        result["remediation_complete"]
        is True
    )

    assert (
        result["remediation_result"]
        == [
            {
                "action": "restart_workload",
                "status": "executed",
            }
        ]
    )

    # ----------------------------------------------
    # Executor must have been called exactly once.
    # ----------------------------------------------

    execute_mock.assert_called_once_with(
        plan,
        approved=True,
        namespace="default",
        service="payment-service",
    )