from fastapi import FastAPI

from k8s_ai_ops.api.routes.incidents import (
    router as incidents_router,
)


app = FastAPI(
    title="Kubernetes AI Ops Agent",
    version="0.1.0",
)


app.include_router(
    incidents_router,
    prefix="/api/v1",
)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }