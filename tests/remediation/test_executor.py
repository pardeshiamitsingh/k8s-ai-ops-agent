from unittest.mock import MagicMock

from k8s_ai_ops.models.remediation import (
    RemediationAction,
    RemediationPlan,
)
from k8s_ai_ops.remediation.executor import (
    RemediationExecutor,
)


def test_blocks_action_without_approval():

    kubernetes = MagicMock()

    executor = RemediationExecutor(
        kubernetes=kubernetes
    )

    plan = RemediationPlan(
        root_cause="CrashLoopBackOff",
        actions=[
            RemediationAction(
                action="restart_workload",
                description="Restart workload",
                risk="medium",
                requires_approval=True,
            )
        ],
        requires_human_approval=True,
    )

    results = executor.execute(
        plan,
        approval=False,
        namespace="default",
        service="payment-service",
    )

    assert len(results) == 1

    assert results[0]["status"] == "blocked"

    kubernetes.restart_workload.assert_not_called()


def test_executes_restart_after_approval():

    kubernetes = MagicMock()

    kubernetes.restart_workload.return_value = {
        "status": "restarted",
        "service": "payment-service",
    }

    executor = RemediationExecutor(
        kubernetes=kubernetes
    )

    plan = RemediationPlan(
        root_cause="CrashLoopBackOff",
        actions=[
            RemediationAction(
                action="restart_workload",
                description="Restart workload",
                risk="medium",
                requires_approval=True,
            )
        ],
        requires_human_approval=True,
    )

    results = executor.execute(
        plan,
        approval=True,
        namespace="default",
        service="payment-service",
    )

    assert len(results) == 1

    assert results[0]["status"] == "executed"

    kubernetes.restart_workload.assert_called_once_with(
        namespace="default",
        service="payment-service",
    )


def test_read_only_action_does_not_mutate():

    kubernetes = MagicMock()

    executor = RemediationExecutor(
        kubernetes=kubernetes
    )

    plan = RemediationPlan(
        root_cause="OOMKilled",
        actions=[
            RemediationAction(
                action="inspect_memory_usage",
                description="Inspect memory",
                risk="low",
                requires_approval=False,
            )
        ],
        requires_human_approval=True,
    )

    results = executor.execute(
        plan,
        approval=False,
        namespace="default",
        service="payment-service",
    )

    assert results[0]["status"] == "skipped"

    kubernetes.restart_workload.assert_not_called()


def test_unsupported_action_is_blocked():

    kubernetes = MagicMock()

    executor = RemediationExecutor(
        kubernetes=kubernetes
    )

    plan = RemediationPlan(
        root_cause="Unknown",
        actions=[
            RemediationAction(
                action="delete_production_database",
                description="Delete database",
                risk="high",
                requires_approval=True,
            )
        ],
        requires_human_approval=True,
    )

    results = executor.execute(
        plan,
        approval=True,
        namespace="default",
        service="payment-service",
    )

    assert results[0]["status"] == "blocked"

    kubernetes.restart_workload.assert_not_called()