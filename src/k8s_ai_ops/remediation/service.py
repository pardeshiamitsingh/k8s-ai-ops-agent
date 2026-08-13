from typing import Any

from k8s_ai_ops.models.remediation import RemediationPlan
from k8s_ai_ops.remediation.executor import RemediationExecutor


class RemediationService:
    """
    Coordinates remediation approval and execution.

    Responsibilities:

    1. Enforce the human approval boundary.
    2. Delegate execution to RemediationExecutor.
    3. Never directly modify Kubernetes resources.
    """

    def __init__(
        self,
        executor: RemediationExecutor | None = None,
    ):
        self.executor = (
            executor
            if executor is not None
            else RemediationExecutor()
        )

    def execute(
        self,
        plan: RemediationPlan,
        approved: bool = False,
        namespace: str = "default",
        service: str | None = None,
    ) -> list[dict[str, Any]]:

        # ==================================================
        # GLOBAL APPROVAL GATE
        # ==================================================

        if plan.requires_human_approval and not approved:
            return [
                {
                    "status": "rejected",
                    "reason": "Human approval required.",
                }
            ]

        # ==================================================
        # EXECUTION
        # ==================================================

        return self.executor.execute(
            plan=plan,
            approved=approved,
            namespace=namespace,
            service=service,
        )