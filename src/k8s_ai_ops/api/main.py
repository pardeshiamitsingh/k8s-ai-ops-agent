from fastapi import FastAPI

from k8s_ai_ops.graph.workflow import build_incident_graph
from k8s_ai_ops.llm.runtime import LLMRuntime
from k8s_ai_ops.llm.settings import AppSettings
from k8s_ai_ops.models.incident import IncidentRequest

from fastapi import HTTPException

from k8s_ai_ops.api.models import (
    ApprovalRequest,
    RejectionRequest,
)
from k8s_ai_ops.remediation.service import (
    RemediationService,
)


remediation_service = RemediationService()


app = FastAPI(
    title="K8s AI Ops Agent",
    version="0.1.0",
)


settings = AppSettings().llm_settings()

llm_runtime = LLMRuntime(settings)

incident_graph = build_incident_graph(
    llm_runtime.get_model()
)


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "k8s-ai-ops-agent",
    }


@app.post("/incidents")
def create_incident(
    incident: IncidentRequest,
):
    result = incident_graph.invoke(
        {
            "incident": incident,
        }
    )

    diagnosis = result["diagnosis"]

    remediation_plan = result[
        "remediation_plan"
    ]

    record = remediation_service.create_record(
        incident
    )

    record = remediation_service.create_plan(
        record=record,
        diagnosis=diagnosis,
    )

    return record.model_dump(
        mode="json"
    )

@app.get("/incidents/{incident_id}")
def get_incident(
    incident_id: str,
):
    try:
        record = remediation_service.get(
            incident_id
        )

        return record.model_dump(
            mode="json"
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@app.post(
    "/incidents/{incident_id}/approve"
)
def approve_incident(
    incident_id: str,
    request: ApprovalRequest,
):
    try:

        record = remediation_service.approve(
            incident_id=incident_id,
            approved_by=request.approved_by,
        )

        return record.model_dump(
            mode="json"
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

@app.post(
    "/incidents/{incident_id}/reject"
)
def reject_incident(
    incident_id: str,
    request: RejectionRequest,
):
    try:

        record = remediation_service.reject(
            incident_id=incident_id,
            rejected_by=request.rejected_by,
        )

        return record.model_dump(
            mode="json"
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

@app.post(
    "/incidents/{incident_id}/execute"
)
def execute_incident(
    incident_id: str,
):
    try:

        record = remediation_service.execute(
            incident_id=incident_id,
        )

        return record.model_dump(
            mode="json"
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )