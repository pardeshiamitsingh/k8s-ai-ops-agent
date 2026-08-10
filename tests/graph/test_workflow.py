from unittest.mock import Mock

from k8s_ai_ops.graph.workflow import build_incident_graph
from k8s_ai_ops.models.diagnosis import Diagnosis
from k8s_ai_ops.models.incident import IncidentRequest
from k8s_ai_ops.models.remediation import RemediationPlan


def test_workflow_produces_remediation_plan(monkeypatch):

    llm = Mock()

    graph = build_incident_graph(llm)

    incident = IncidentRequest(
        service="payment-service",
        namespace="default",
        description="payment service is restarting",
    )

    # This test focuses on graph structure, so replace
    # the external Kubernetes investigation.
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

    result = graph.invoke(
        {
            "incident": incident,
        }
    )

    assert "diagnosis" in result
    assert "remediation_plan" in result

    assert isinstance(
        result["diagnosis"],
        Diagnosis,
    )

    assert isinstance(
        result["remediation_plan"],
        RemediationPlan,
    )