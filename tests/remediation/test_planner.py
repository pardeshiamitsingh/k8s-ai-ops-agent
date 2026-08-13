import pytest

from k8s_ai_ops.models.diagnosis import Diagnosis
from k8s_ai_ops.remediation.planner import RemediationPlanner


@pytest.fixture
def planner():
    return RemediationPlanner()


def make_diagnosis(root_cause: str) -> Diagnosis:
    return Diagnosis(
        root_cause=root_cause,
        confidence=0.95,
        evidence=["Observed Kubernetes evidence"],
        recommended_next_steps=[],
        human_intervention_required=False,
    )


def action_names(plan):
    return [action.action for action in plan.actions]


def test_oom_killed_plan(planner):
    plan = planner.plan(
        make_diagnosis("OOMKilled")
    )

    assert plan.root_cause == "OOMKilled"
    assert action_names(plan) == [
        "increase_memory_limit",
        "inspect_memory_usage",
    ]

    assert plan.requires_human_approval is True

    assert plan.actions[0].requires_approval is True
    assert plan.actions[1].requires_approval is False


def test_crash_loop_backoff_plan(planner):
    plan = planner.plan(
        make_diagnosis("CrashLoopBackOff")
    )

    assert plan.root_cause == "CrashLoopBackOff"

    assert action_names(plan) == [
        "inspect_previous_logs",
        "restart_workload",
    ]

    assert plan.requires_human_approval is True

    assert plan.actions[0].requires_approval is False
    assert plan.actions[1].requires_approval is True


def test_application_error_plan(planner):
    plan = planner.plan(
        make_diagnosis("Application error")
    )

    assert plan.root_cause == "Application error"

    assert action_names(plan) == [
        "inspect_application_logs",
        "redeploy_application",
    ]

    assert plan.requires_human_approval is True

    assert plan.actions[0].risk == "low"
    assert plan.actions[1].risk == "high"


def test_image_pull_failure_plan(planner):
    plan = planner.plan(
        make_diagnosis(
            "Container image pull failure"
        )
    )

    assert plan.root_cause == (
        "Container image pull failure"
    )

    assert action_names(plan) == [
        "verify_image",
        "verify_registry_credentials",
    ]

    assert plan.requires_human_approval is False

    assert all(
        action.requires_approval is False
        for action in plan.actions
    )


def test_probe_failure_plan(planner):
    plan = planner.plan(
        make_diagnosis(
            "Kubernetes health probe failure"
        )
    )

    assert plan.root_cause == (
        "Kubernetes health probe failure"
    )

    assert action_names(plan) == [
        "inspect_probe_configuration",
        "adjust_probe_configuration",
    ]

    assert plan.requires_human_approval is True

    assert plan.actions[0].requires_approval is False
    assert plan.actions[1].requires_approval is True


def test_unknown_plan_requires_human_approval(planner):
    plan = planner.plan(
        make_diagnosis("Unknown")
    )

    assert plan.root_cause == "Unknown"

    assert action_names(plan) == [
        "collect_more_evidence",
    ]

    assert plan.requires_human_approval is True

    assert plan.actions[0].requires_approval is False
    assert plan.actions[0].risk == "low"