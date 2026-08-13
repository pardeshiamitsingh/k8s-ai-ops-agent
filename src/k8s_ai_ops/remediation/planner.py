from k8s_ai_ops.models.diagnosis import Diagnosis
from k8s_ai_ops.models.remediation import (
    RemediationAction,
    RemediationPlan,
)


class RemediationPlanner:
    """
    Deterministic remediation planner.

    Converts a diagnosis into a proposed remediation plan.

    IMPORTANT:
    This class NEVER modifies Kubernetes resources.
    """

    def plan(
        self,
        diagnosis: Diagnosis,
    ) -> RemediationPlan:

        root_cause = diagnosis.root_cause

        # --------------------------------------------------
        # OOMKilled
        # --------------------------------------------------

        if root_cause == "OOMKilled":

            return RemediationPlan(
                root_cause=root_cause,
                actions=[
                    RemediationAction(
                        action="increase_memory_limit",
                        description=(
                            "Increase the memory limit for "
                            "the affected container."
                        ),
                        risk="medium",
                    ),
                    RemediationAction(
                        action="inspect_memory_usage",
                        description=(
                            "Inspect application memory usage "
                            "and identify possible memory leaks."
                        ),
                        risk="low",
                        requires_approval=False,
                    ),
                ],
                requires_human_approval=True,
            )

        # --------------------------------------------------
        # CrashLoopBackOff
        # --------------------------------------------------

        if root_cause == "CrashLoopBackOff":

            return RemediationPlan(
                root_cause=root_cause,
                actions=[
                    RemediationAction(
                        action="inspect_previous_logs",
                        description=(
                            "Inspect logs from the previous "
                            "container instance."
                        ),
                        risk="low",
                        requires_approval=False,
                    ),
                    RemediationAction(
                        action="restart_workload",
                        description=(
                            "Restart the affected workload "
                            "after confirming the failure."
                        ),
                        risk="medium",
                    ),
                ],
                requires_human_approval=True,
            )

        # --------------------------------------------------
        # Application error
        # --------------------------------------------------

        if root_cause == "Application error":

            return RemediationPlan(
                root_cause=root_cause,
                actions=[
                    RemediationAction(
                        action="inspect_application_logs",
                        description=(
                            "Inspect the application stack "
                            "trace and identify the failure."
                        ),
                        risk="low",
                        requires_approval=False,
                    ),
                    RemediationAction(
                        action="redeploy_application",
                        description=(
                            "Deploy a corrected application "
                            "version after fixing the error."
                        ),
                        risk="high",
                    ),
                ],
                requires_human_approval=True,
            )

        # --------------------------------------------------
        # Image pull failure
        # --------------------------------------------------

        if root_cause == "Container image pull failure":

            return RemediationPlan(
                root_cause=root_cause,
                actions=[
                    RemediationAction(
                        action="verify_image",
                        description=(
                            "Verify the configured container "
                            "image name and tag."
                        ),
                        risk="low",
                        requires_approval=False,
                    ),
                    RemediationAction(
                        action="verify_registry_credentials",
                        description=(
                            "Verify credentials and permissions "
                            "for the container registry."
                        ),
                        risk="low",
                        requires_approval=False,
                    ),
                ],
                requires_human_approval=False,
            )

        # --------------------------------------------------
        # Probe failure
        # --------------------------------------------------

        if root_cause == "Kubernetes health probe failure":

            return RemediationPlan(
                root_cause=root_cause,
                actions=[
                    RemediationAction(
                        action="inspect_probe_configuration",
                        description=(
                            "Inspect liveness, readiness, or "
                            "startup probe configuration."
                        ),
                        risk="low",
                        requires_approval=False,
                    ),
                    RemediationAction(
                        action="adjust_probe_configuration",
                        description=(
                            "Adjust probe thresholds or timing "
                            "after validating application behavior."
                        ),
                        risk="medium",
                    ),
                ],
                requires_human_approval=True,
            )

        # --------------------------------------------------
        # Unknown diagnosis
        # --------------------------------------------------

        return RemediationPlan(
            root_cause=root_cause,
            actions=[
                RemediationAction(
                    action="collect_more_evidence",
                    description=(
                        "Collect additional Kubernetes events, "
                        "logs, and metrics before taking action."
                    ),
                    risk="low",
                    requires_approval=False,
                )
            ],
            requires_human_approval=True,
        )