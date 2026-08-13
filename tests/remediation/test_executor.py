from unittest.mock import Mock

from k8s_ai_ops.models.remediation import (
    RemediationAction,
    RemediationPlan,
)
from k8s_ai_ops.remediation.executor import (
    RemediationExecutor,
)


def test_restart_workload_and_verify():

    kubernetes_client = Mock()

    kubernetes_client.restart_deployment.return_value = {
        "status": "executed",
        "action": "restart_workload",
        "workload": "payment-service",
        "namespace": "default",
    }

    kubernetes_client.get_deployment_status.return_value = {
        "deployment": "payment-service",
        "namespace": "default",
        "replicas": 3,
        "ready_replicas": 3,
        "updated_replicas": 3,
        "available_replicas": 3,
        "generation": 10,
        "observed_generation": 10,
        "rollout_complete": True,
    }

    executor = RemediationExecutor(
        kubernetes_client=kubernetes_client
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

    result = executor.execute(
        plan=plan,
        approved=True,
        namespace="default",
        service="payment-service",
    )

    assert len(result) == 1

    assert result[0]["status"] == "verified"

    assert result[0]["phase"] == "verification"

    assert (
        result[0]["verification"]["rollout_complete"]
        is True
    )

    kubernetes_client.restart_deployment.assert_called_once_with(
        namespace="default",
        deployment="payment-service",
    )

    kubernetes_client.get_deployment_status.assert_called_once_with(
        namespace="default",
        deployment="payment-service",
    )