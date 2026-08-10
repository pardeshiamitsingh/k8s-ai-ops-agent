from k8s_ai_ops.models.remediation import (
    RemediationAction,
    RemediationPlan,
)
from k8s_ai_ops.remediation.service import (
    RemediationService,
)


class FakeExecutor:

    def __init__(self):
        self.calls = []

    def execute(
        self,
        plan,
        *,
        approved,
        namespace,
        service,
    ):

        self.calls.append(
            {
                "approved": approved,
                "namespace": namespace,
                "service": service,
            }
        )

        return [
            {
                "status": "executed",
            }
        ]


def test_rejected_remediation_does_not_execute():

    executor = FakeExecutor()

    service = RemediationService(
        executor=executor
    )

    plan = RemediationPlan(
        root_cause="CrashLoopBackOff",
        actions=[
            RemediationAction(
                action="restart_workload",
                description="Restart workload",
                risk="medium",
            )
        ],
    )

    result = service.execute(
        plan,
        approved=False,
        namespace="default",
        service="payment-service",
    )

    assert result[0]["status"] == "rejected"

    assert executor.calls == []


def test_approved_remediation_executes():

    executor = FakeExecutor()

    service = RemediationService(
        executor=executor
    )

    plan = RemediationPlan(
        root_cause="CrashLoopBackOff",
        actions=[
            RemediationAction(
                action="restart_workload",
                description="Restart workload",
                risk="medium",
            )
        ],
    )

    result = service.execute(
        plan,
        approved=True,
        namespace="default",
        service="payment-service",
    )

    assert result[0]["status"] == "executed"

    assert executor.calls == [
        {
            "approved": True,
            "namespace": "default",
            "service": "payment-service",
        }
    ]