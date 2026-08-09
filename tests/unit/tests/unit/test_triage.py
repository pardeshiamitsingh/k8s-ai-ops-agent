from k8s_ai_ops.agents.triage import triage_incident
from k8s_ai_ops.models.incident import IncidentRequest


def test_triage_detects_oom():

    incident = IncidentRequest(
        service="payment-service",
        namespace="payments",
        description="Pods are being OOMKilled",
        severity="high",
    )

    result = triage_incident(
        {
            "incident": incident,
        }
    )

    analysis = result["analysis"]

    assert analysis.investigation_required is True

    assert any(
        "OOMKilled" in hypothesis
        for hypothesis in analysis.initial_hypotheses
    )