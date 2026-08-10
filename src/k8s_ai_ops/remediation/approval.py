from datetime import datetime, timezone

from k8s_ai_ops.models.remediation import (
    RemediationApproval,
    RemediationPlan,
)


class RemediationApprovalGate:
    """
    Controls whether a remediation plan is approved for execution.

    Approval is explicit and must identify the approving user.
    """

    def approve(
        self,
        plan: RemediationPlan,
        approved_by: str,
        reason: str | None = None,
    ) -> RemediationApproval:

        if not approved_by or not approved_by.strip():
            raise ValueError(
                "approved_by is required."
            )

        if not plan.actions:
            raise ValueError(
                "Cannot approve an empty remediation plan."
            )

        return RemediationApproval(
            approved=True,
            approved_by=approved_by,
            reason=reason,
            approved_at=datetime.now(timezone.utc),
        )

    def reject(
        self,
        approved_by: str,
        reason: str | None = None,
    ) -> RemediationApproval:

        if not approved_by or not approved_by.strip():
            raise ValueError(
                "approved_by is required."
            )

        return RemediationApproval(
            approved=False,
            approved_by=approved_by,
            reason=reason,
            approved_at=datetime.now(timezone.utc),
        )

    def can_execute(
        self,
        plan: RemediationPlan,
        approval: RemediationApproval,
    ) -> bool:
        """
        Determine whether a remediation plan may execute.

        A plan can execute only when:
        1. The plan contains actions.
        2. The plan requires approval and approval is granted.
        3. The approval identifies an approver.

        Read-only plans that do not require human approval
        can execute without an approval record.
        """

        if not plan.actions:
            return False

        if not plan.requires_human_approval:
            return True

        if approval is None:
            return False

        if not approval.approved:
            return False

        if not approval.approved_by.strip():
            return False

        return True
