from unittest.mock import Mock

from k8s_ai_ops.agents.triage import triage_incident
from k8s_ai_ops.models.incident import (
    IncidentAnalysis,
    IncidentRequest,
)


def test_triage_detects_oom():

    incident = IncidentRequest(
        service="payment-service",
        namespace="payments",
        description="Pods are being OOMKilled",
        severity="high",
    )

    mock_llm = Mock()
    mock_structured_llm = Mock()

    mock_analysis = IncidentAnalysis(
        incident_type="kubernetes_incident",
        investigation_required=True,
        initial_hypotheses=[
            "Memory exhaustion or OOMKilled"
        ],
        reasoning=(
            "OOMKilled detected in incident description"
        ),
    )

    mock_structured_llm.invoke.return_value = (
        mock_analysis
    )

    mock_llm.with_structured_output.return_value = (
        mock_structured_llm
    )

    result = triage_incident(
        {
            "incident": incident,
        },
        llm=mock_llm,
    )

    analysis = result["analysis"]

    assert analysis == mock_analysis

    assert analysis.investigation_required is True

    assert "Memory exhaustion or OOMKilled" in (
        analysis.initial_hypotheses
    )

    mock_llm.with_structured_output.assert_called_once_with(
        IncidentAnalysis
    )

    mock_structured_llm.invoke.assert_called_once()