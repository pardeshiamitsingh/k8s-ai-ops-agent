from typing import Any

from k8s_ai_ops.models.remediation import (
    RemediationPlan,
)
from k8s_ai_ops.remediation.kubernetes_client import (
    KubernetesClient,
)


class RemediationExecutor:
    """
    Executes approved remediation actions.

    Flow:

        Approval
            ↓
        Execute
            ↓
        Verify
            ↓
        Report

    This class is the only component that translates
    remediation actions into Kubernetes mutations.
    """

    def __init__(
        self,
        kubernetes_client: KubernetesClient | None = None,
    ):
        self.kubernetes_client = (
            kubernetes_client
            if kubernetes_client is not None
            else KubernetesClient()
        )

    def execute(
        self,
        plan: RemediationPlan,
        approved: bool = False,
        namespace: str = "default",
        service: str | None = None,
    ) -> list[dict[str, Any]]:

        results: list[dict[str, Any]] = []

        # =====================================================
        # GLOBAL APPROVAL GATE
        # =====================================================

        if plan.requires_human_approval and not approved:
            return [
                {
                    "status": "rejected",
                    "reason": "Human approval required.",
                }
            ]

        # =====================================================
        # EXECUTE ACTIONS
        # =====================================================

        for action in plan.actions:

            # -------------------------------------------------
            # Per-action approval
            # -------------------------------------------------

            if action.requires_approval and not approved:
                results.append(
                    {
                        "status": "skipped",
                        "action": action.action,
                        "reason": (
                            "Action requires human approval."
                        ),
                    }
                )

                continue

            # -------------------------------------------------
            # Restart workload
            # -------------------------------------------------

            if action.action == "restart_workload":

                result = self._restart_workload(
                    namespace=namespace,
                    service=service,
                )

                results.append(result)

                continue

            # -------------------------------------------------
            # Unsupported action
            # -------------------------------------------------

            results.append(
                {
                    "status": "unsupported",
                    "action": action.action,
                    "reason": (
                        "Remediation action is not implemented."
                    ),
                }
            )

        return results

    # =========================================================
    # RESTART WORKLOAD
    # =========================================================

    def _restart_workload(
        self,
        namespace: str,
        service: str | None,
    ) -> dict[str, Any]:

        if not service:
            return {
                "status": "failed",
                "action": "restart_workload",
                "reason": (
                    "Service/workload name is required."
                ),
            }

        # -----------------------------------------------------
        # Execute
        # -----------------------------------------------------

        try:
            execution_result = (
                self.kubernetes_client
                .restart_deployment(
                    namespace=namespace,
                    deployment=service,
                )
            )

        except Exception as exc:
            return {
                "status": "failed",
                "action": "restart_workload",
                "phase": "execution",
                "error": str(exc),
            }

        # -----------------------------------------------------
        # Verify
        # -----------------------------------------------------

        try:
            verification = (
                self.kubernetes_client
                .get_deployment_status(
                    namespace=namespace,
                    deployment=service,
                )
            )

        except Exception as exc:
            return {
                **execution_result,
                "status": "verification_failed",
                "phase": "verification",
                "error": str(exc),
            }

        # -----------------------------------------------------
        # Final result
        # -----------------------------------------------------

        if verification["rollout_complete"]:

            return {
                **execution_result,
                "status": "verified",
                "phase": "verification",
                "verification": verification,
            }

        return {
            **execution_result,
            "status": "executed_not_verified",
            "phase": "verification",
            "verification": verification,
        }