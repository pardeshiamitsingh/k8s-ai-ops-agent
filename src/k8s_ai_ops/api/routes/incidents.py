import uuid

from fastapi import APIRouter, Depends

from k8s_ai_ops.api.dependencies import get_incident_service
from k8s_ai_ops.models.incident import IncidentRequest
from k8s_ai_ops.services.incident_service import IncidentService


router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
)


# =========================================================
# CREATE INCIDENT
# =========================================================

@router.post("")
def create_incident(
    incident: IncidentRequest,
    service: IncidentService = Depends(
        get_incident_service
    ),
):
    """
    Create an incident and execute the investigation/
    diagnosis/remediation workflow.

    The workflow may pause at the human approval node.
    """

    thread_id = str(uuid.uuid4())

    result = service.create_incident(
        incident=incident,
        thread_id=thread_id,
    )

    return {
        "thread_id": thread_id,
        "status": (
            "approval_required"
            if result.get("approval_required", True)
            else "completed"
        ),
        "result": result,
    }


# =========================================================
# APPROVE / REJECT
# =========================================================

@router.post("/{thread_id}/approval")
def approve_incident(
    thread_id: str,
    approval: dict,
    service: IncidentService = Depends(
        get_incident_service
    ),
):
    """
    Resume a paused LangGraph workflow.

    Example:

    {
        "approved": true,
        "approved_by": "amit",
        "reason": "Reviewed evidence and approved remediation."
    }
    """

    result = service.approve_incident(
        thread_id=thread_id,
        approved=bool(
            approval.get(
                "approved",
                False,
            )
        ),
        approved_by=approval.get(
            "approved_by",
            "unknown",
        ),
        reason=approval.get(
            "reason"
        ),
    )

    return {
        "thread_id": thread_id,
        "status": (
            "completed"
            if result.get("remediation_complete")
            else "rejected"
        ),
        "result": result,
    }
