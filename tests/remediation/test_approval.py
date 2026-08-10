import pytest

from k8s_ai_ops.models.remediation import (
    RemediationAction,
    RemediationPlan,
)
from k8s_ai_ops.remediation.approval import (
    RemediationApprovalGate,
)


@pytest.fixture
def plan():
    return RemediationPlan(
        root_cause="OOMKilled",
        actions=[
            RemediationAction(
                action="increase_memory_limit",
                description="Increase memory limit.",
                risk="medium",
            )
        ],
        requires_human_approval=True,
    )


def test_approve_plan(plan):
    gate = RemediationApprovalGate()

    approval = gate.approve(
        plan=plan,
        approved_by="amit",
        reason="Reviewed OOM evidence.",
    )

    assert approval.approved is True
    assert approval.approved_by == "amit"
    assert approval.approved_at is not None
    assert approval.reason == "Reviewed OOM evidence."


def test_reject_plan():
    gate = RemediationApprovalGate()

    approval = gate.reject(
        approved_by="amit",
        reason="Need more evidence.",
    )

    assert approval.approved is False
    assert approval.approved_by == "amit"


def test_approval_required_before_execution(plan):
    gate = RemediationApprovalGate()

    approval = gate.reject(
        approved_by="amit",
        reason="Not ready.",
    )

    assert (
        gate.can_execute(
            plan,
            approval,
        )
        is False
    )


def test_approved_plan_can_execute(plan):
    gate = RemediationApprovalGate()

    approval = gate.approve(
        plan=plan,
        approved_by="amit",
    )

    assert (
        gate.can_execute(
            plan,
            approval,
        )
        is True
    )


def test_empty_plan_cannot_be_approved():
    gate = RemediationApprovalGate()

    plan = RemediationPlan(
        root_cause="Unknown",
        actions=[],
    )

    with pytest.raises(ValueError):
        gate.approve(
            plan=plan,
            approved_by="amit",
        )


def test_approval_requires_user():
    gate = RemediationApprovalGate()

    plan = RemediationPlan(
        root_cause="OOMKilled",
        actions=[
            RemediationAction(
                action="increase_memory_limit",
                description="Increase memory.",
                risk="medium",
            )
        ],
    )

    with pytest.raises(ValueError):
        gate.approve(
            plan=plan,
            approved_by="",
        )