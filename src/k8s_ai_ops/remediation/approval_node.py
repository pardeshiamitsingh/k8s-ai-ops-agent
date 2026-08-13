from langgraph.types import interrupt

from k8s_ai_ops.graph.state import AgentState


def remediation_approval_node(
    state: AgentState,
) -> dict:
    """
    Pause the LangGraph workflow and request explicit
    human approval before executing remediation.

    The graph is resumed using:

        Command(
            resume={
                "approved": True,
                "approved_by": "amit",
                "reason": "Reviewed evidence and approved restart.",
            }
        )

    The value returned by interrupt() becomes `decision`
    after the graph is resumed.
    """

    plan = state["remediation_plan"]

    # ==================================================
    # HUMAN APPROVAL INTERRUPT
    # ==================================================

    decision = interrupt(
        {
            "type": "remediation_approval",
            "message": (
                "Human approval required before "
                "Kubernetes remediation."
            ),
            "root_cause": plan.root_cause,
            "actions": [
                {
                    "action": action.action,
                    "description": action.description,
                    "risk": action.risk,
                    "requires_approval": (
                        action.requires_approval
                    ),
                }
                for action in plan.actions
            ],
        }
    )

    # ==================================================
    # NORMALIZE DECISION
    # ==================================================

    approved = False
    approved_by = None
    reason = None

    if isinstance(decision, bool):
        approved = decision

    elif isinstance(decision, dict):
        approved = bool(
            decision.get(
                "approved",
                False,
            )
        )

        approved_by = decision.get(
            "approved_by"
        )

        reason = decision.get(
            "reason"
        )

    else:
        raise ValueError(
            "Invalid remediation approval decision: "
            f"{type(decision)!r}"
        )

    # ==================================================
    # RETURN STATE UPDATE
    # ==================================================

    return {
        "remediation_approved": approved,
        "remediation_approved_by": approved_by,
        "remediation_approval_reason": reason,
    }