from fastapi import FastAPI

from k8s_ai_ops.graph.workflow import build_incident_graph
from k8s_ai_ops.models.incident import IncidentRequest

app = FastAPI(
    title="K8s AI Ops Agent",
    version="0.1.0",
)

incident_graph = build_incident_graph()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "k8s-ai-ops-agent",
    }


@app.post("/incidents")
async def create_incident(
    incident: IncidentRequest,
):
    result = incident_graph.invoke(
        {
            "incident": incident,
        }
    )

    return result