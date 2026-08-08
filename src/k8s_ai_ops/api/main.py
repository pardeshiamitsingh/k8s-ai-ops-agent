from fastapi import FastAPI

app = FastAPI(
    title="K8s AI Ops Agent",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "k8s-ai-ops-agent",
    }