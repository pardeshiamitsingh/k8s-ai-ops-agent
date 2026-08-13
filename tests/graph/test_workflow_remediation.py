from k8s_ai_ops.models.diagnosis import Diagnosis
from k8s_ai_ops.remediation.planner import RemediationPlanner


def test_remediation_planner_creates_plan():

    diagnosis = Diagnosis(
        root_cause="OOMKilled",
        confidence=0.95,
        evidence=[
            "Pod payment-service was OOMKilled."
        ],
        recommended_next_steps=[
            "Increase memory limit."
        ],
        human_intervention_required=False,
    )

    planner = RemediationPlanner()

    plan = planner.plan(diagnosis)

    assert plan is not None

    assert plan.root_cause == "OOMKilled"

    assert len(plan.actions) > 0

    assert plan.requires_human_approval is True