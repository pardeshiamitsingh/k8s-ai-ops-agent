from typing import Any

from k8s_ai_ops.models.remediation import (
    RemediationAction,
    RemediationPlan,
)
from k8s_ai_ops.tools.kubernetes import KubernetesTools


class RemediationExecutor:
    """
    Executes approved remediation actions.

    Safety rules:
    - Only explicitly supported actions are executable.
    - Mutating actions require explicit human approval.
    - Read-only actions never mutate Kubernetes.
    - Kubernetes mutations are performed only through this class.
    - Unsupported actions are always blocked.
    """

    # Actions that only inspect or validate state.
    READ_ONLY_ACTIONS = {
        "collect_more_evidence",
        "inspect_memory_usage",
        "inspect_previous_logs",
        "inspect_application_logs",
        "verify_image",
        "verify_registry_credentials",
        "inspect_probe_configuration",
    }

    # Actions that can mutate Kubernetes resources.
    MUTATING_ACTIONS = {
        "restart_workload",
        "increase_memory_limit",
        "redeploy_application",
        "adjust_probe_configuration",
    }

    def __init__(
        self,
        kubernetes: KubernetesTools | None = None,
    ):
        self.kubernetes = (
            kubernetes
            if kubernetes is not None
            else KubernetesTools()
        )

    # =========================================================
    # Public API
    # =========================================================

    def execute(
        self,
        plan: RemediationPlan,
        approval: bool = False,
        namespace: str = "default",
        service: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute actions from a remediation plan.

        Parameters
        ----------
        plan:
            Remediation plan produced by RemediationPlanner.

        approval:
            Explicit human approval for mutating actions.

        namespace:
            Kubernetes namespace containing the workload.

        service:
            Kubernetes workload/service name used by actions
            that require a target workload.

        Returns
        -------
        list[dict[str, Any]]
            Execution result for every action in the plan.
        """

        results: list[dict[str, Any]] = []

        for action in plan.actions:
            result = self._execute_action(
                action=action,
                approval=approval,
                namespace=namespace,
                service=service,
            )

            results.append(result)

        return results

    # =========================================================
    # Action dispatcher
    # =========================================================

    def _execute_action(
        self,
        action: RemediationAction,
        approval: bool,
        namespace: str,
        service: str | None,
    ) -> dict[str, Any]:

        action_name = action.action

        # -----------------------------------------------------
        # Unknown actions are ALWAYS blocked.
        # -----------------------------------------------------

        if (
            action_name not in self.READ_ONLY_ACTIONS
            and action_name not in self.MUTATING_ACTIONS
        ):
            return {
                "action": action_name,
                "status": "blocked",
                "reason": (
                    f"Unsupported remediation action: "
                    f"{action_name}"
                ),
            }

        # -----------------------------------------------------
        # Read-only actions
        #
        # These never require approval and never mutate
        # Kubernetes.
        # -----------------------------------------------------

        if action_name in self.READ_ONLY_ACTIONS:
            return self._handle_read_only_action(
                action
            )

        # -----------------------------------------------------
        # Mutating actions
        #
        # Explicit approval is mandatory.
        # -----------------------------------------------------

        if action_name in self.MUTATING_ACTIONS:

            if not approval:
                return {
                    "action": action_name,
                    "status": "blocked",
                    "reason": (
                        "Human approval required "
                        "before executing a mutating action."
                    ),
                }

            return self._execute_mutating_action(
                action=action,
                namespace=namespace,
                service=service,
            )

        # Defensive fallback.
        return {
            "action": action_name,
            "status": "blocked",
            "reason": "Action could not be classified.",
        }

    # =========================================================
    # Read-only actions
    # =========================================================

    def _handle_read_only_action(
        self,
        action: RemediationAction,
    ) -> dict[str, Any]:
        """
        Handle actions that do not modify Kubernetes.
        """

        if action.action == "collect_more_evidence":
            return {
                "action": action.action,
                "status": "skipped",
                "reason": (
                    "Additional evidence collection must "
                    "be performed by the investigation stage."
                ),
            }

        return {
            "action": action.action,
            "status": "skipped",
            "reason": (
                "Read-only remediation action. "
                "No Kubernetes mutation performed."
            ),
        }

    # =========================================================
    # Mutating actions
    # =========================================================

    def _execute_mutating_action(
        self,
        action: RemediationAction,
        namespace: str,
        service: str | None,
    ) -> dict[str, Any]:

        # -----------------------------------------------------
        # All current mutating actions require a workload.
        # -----------------------------------------------------

        if not service:
            return {
                "action": action.action,
                "status": "failed",
                "reason": (
                    "service is required for this "
                    "remediation action."
                ),
            }

        # -----------------------------------------------------
        # Restart workload
        # -----------------------------------------------------

        if action.action == "restart_workload":
            return self._restart_workload(
                action=action,
                namespace=namespace,
                service=service,
            )

        # -----------------------------------------------------
        # Increase memory limit
        # -----------------------------------------------------

        if action.action == "increase_memory_limit":
            return {
                "action": action.action,
                "status": "blocked",
                "reason": (
                    "Automatic memory-limit modification "
                    "is not implemented yet."
                ),
            }

        # -----------------------------------------------------
        # Redeploy application
        # -----------------------------------------------------

        if action.action == "redeploy_application":
            return {
                "action": action.action,
                "status": "blocked",
                "reason": (
                    "Automatic application redeployment "
                    "is not implemented yet."
                ),
            }

        # -----------------------------------------------------
        # Adjust probe configuration
        # -----------------------------------------------------

        if action.action == "adjust_probe_configuration":
            return {
                "action": action.action,
                "status": "blocked",
                "reason": (
                    "Automatic probe configuration changes "
                    "are not implemented yet."
                ),
            }

        # Defensive fallback.
        return {
            "action": action.action,
            "status": "blocked",
            "reason": (
                f"Mutating action is not implemented: "
                f"{action.action}"
            ),
        }

    # =========================================================
    # Restart workload
    # =========================================================

    def _restart_workload(
        self,
        action: RemediationAction,
        namespace: str,
        service: str,
    ) -> dict[str, Any]:
        """
        Restart a Kubernetes workload.

        KubernetesTools owns the actual Kubernetes API call.
        """

        try:
            result = self.kubernetes.restart_workload(
                namespace=namespace,
                service=service,
            )

            return {
                "action": action.action,
                "status": "executed",
                "result": result,
            }

        except Exception as exc:
            return {
                "action": action.action,
                "status": "failed",
                "reason": str(exc),
            }
