
from typing import Any

from k8s_ai_ops.models.remediation import RemediationPlan
from k8s_ai_ops.remediation.executor import RemediationExecutor


class RemediationService:
    """
    Coordinates remediation approval and execution.

    The service is responsible for enforcing the approval boundary.
    Kubernetes mutations are performed by RemediationExecutor.
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
        """
        Execute a remediation plan only when approval is granted.
        """

        # --------------------------------------------------
        # Approval gate
        # --------------------------------------------------

        if plan.requires_human_approval and not approved:
            return [
                {
                    "status": "rejected",
                    "reason": "Human approval required.",
                }
            ]

        # --------------------------------------------------
        # Execute approved remediation
        # --------------------------------------------------

        return self.executor.execute(
            plan=plan,
            approved=approved,
            namespace=namespace,
            service=service,
        )
