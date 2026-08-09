from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from k8s_ai_ops import llm
from k8s_ai_ops.graph.state import AgentState
from k8s_ai_ops.models.incident import IncidentAnalysis


SYSTEM_PROMPT = """
You are a Kubernetes incident triage agent.

Your job is to perform the initial classification
of a Kubernetes incident.

Determine:

1. The type of incident.
2. Whether further investigation is required.
3. Initial technical hypotheses.
4. Concise reasoning.

Important rules:

- Do not invent Kubernetes observations.
- Do not claim that you inspected pods, logs,
  events, metrics, or deployments.
- Do not recommend remediation yet.
- If information is insufficient, indicate that
  investigation is required.
- Return the result using the required structured
  output schema.
"""


def triage_incident(
    state: AgentState,
    llm: BaseChatModel,
) -> dict:

    incident = state["incident"]
    print("========== TRIAGE DEBUG ==========")
    print("LLM TYPE:", type(llm))
    print("LLM MODULE:", type(llm).__module__)
    print("LLM CLASS:", type(llm).__name__)
    print("LLM MRO:", type(llm).mro())
    print("HAS STRUCTURED:", hasattr(llm, "with_structured_output"))
    print("===================================")
    structured_llm = llm.with_structured_output(
        IncidentAnalysis
    )

    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT,
        ),
        HumanMessage(
            content=f"""
Service: {incident.service}

Namespace: {incident.namespace}

Severity: {incident.severity}

Incident description:
{incident.description}
""",
        ),
    ]

    analysis = structured_llm.invoke(
        messages,
    )

    return {
        "analysis": analysis,
    }