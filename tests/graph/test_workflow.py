from unittest.mock import patch

from langgraph.types import Command

from k8s_ai_ops.graph.workflow import (
    build_incident_graph,
)
from k8s_ai_ops.models.incident import (
    IncidentRequest,
)


class FakeLLM:
    """
    Minimal serializable fake LLM.

    The workflow test is testing graph orchestration,
    not LLM behavior.
    """

    def with_structured_output(
        self,
        schema,
    ):
        return self

    def invoke(
        self,
        messages,
    ):
        return {
            "summary": "Payment service incident",
            "severity": "medium",
        }


def test_workflow_produces_remediation_plan(
    monkeypatch,
):
    """
    End-to-end graph test.

    Flow:

        triage
          ↓
        investigator
          ↓
        diagnosis
          ↓
        planner
          ↓
        approval
          ↓
        interrupt
          ↓
        human approval
          ↓
        remediation
    """

    # ==================================================
    # GRAPH
    # ==================================================

    graph = build_incident_graph(
        FakeLLM()
    )

    # ==================================================
    # INCIDENT
    # ==================================================

    incident = IncidentRequest(
        service="payment-service",
        namespace="default",
        description=(
            "payment service is restarting"
        ),
    )

    # ==================================================
    # MOCK KUBERNETES INVESTIGATION
    # ==================================================

    from k8s_ai_ops.investigation.deterministic import (
        DeterministicInvestigator,
    )

    monkeypatch.setattr(
        DeterministicInvestigator,
        "investigate",
        lambda self, incident: {
            "incident": incident.model_dump(),
            "pods": [],
            "relevant_pods": [],
            "pod_events": {},
            "pod_logs": {},
        },
    )

    # ==================================================
    # MOCK REMEDIATION
    # ==================================================

    monkeypatch.setattr(
        "k8s_ai_ops.graph.workflow.RemediationService.execute",
        lambda self, plan, approved, namespace, service: [
            {
                "action": "restart_workload",
                "status": "executed",
            }
        ],
    )

    # ==================================================
    # LANGGRAPH THREAD
    # ==================================================

    config = {
        "configurable": {
            "thread_id": (
                "test-workflow-plan"
            ),
        }
    }

    # ==================================================
    # FIRST INVOCATION
    # ==================================================

    first_result = graph.invoke(
        {
            "incident": incident,
        },
        config=config,
    )

    # ==================================================
    # GRAPH SHOULD HAVE PAUSED AT APPROVAL
    # ==================================================

    assert (
        first_result["remediation_plan"]
        is not None
    )

    # It should not have executed remediation yet.

    assert (
        first_result.get(
            "remediation_complete",
            False,
        )
        is False
    )

    # ==================================================
    # RESUME AFTER HUMAN APPROVAL
    # ==================================================

    result = graph.invoke(
        Command(
            resume={
                "approved": True,
                "approved_by": "test-user",
                "reason": (
                    "Approved restart after "
                    "reviewing investigation."
                ),
            }
        ),
        config=config,
    )

    # ==================================================
    # ASSERT APPROVAL
    # ==================================================

    assert (
        result["remediation_approved"]
        is True
    )

    assert (
        result["remediation_approved_by"]
        == "test-user"
    )

    # ==================================================
    # ASSERT REMEDIATION
    # ==================================================

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