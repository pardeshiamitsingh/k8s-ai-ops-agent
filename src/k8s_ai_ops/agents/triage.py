from k8s_ai_ops.graph.state import AgentState
from k8s_ai_ops.models.incident import IncidentAnalysis


def triage_incident(state: AgentState) -> dict:
    incident = state["incident"]

    description = incident.description.lower()

    hypotheses = []

    if "crash" in description or "crashloop" in description:
        hypotheses.append("Application crash or CrashLoopBackOff")

    if "memory" in description or "oom" in description:
        hypotheses.append("Memory exhaustion or OOMKilled")

    if "image" in description:
        hypotheses.append("Container image or ImagePullBackOff")

    if "connection" in description or "timeout" in description:
        hypotheses.append("Dependency or network connectivity failure")

    if not hypotheses:
        hypotheses.append("Unknown application or infrastructure failure")

    analysis = IncidentAnalysis(
        incident_type="kubernetes_incident",
        investigation_required=True,
        initial_hypotheses=hypotheses,
        reasoning=(
            "Initial triage identified potential failure modes from "
            "the incident description. Kubernetes investigation is required "
            "to determine the root cause."
        ),
    )

    return {
        "analysis": analysis,
    }