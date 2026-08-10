from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from k8s_ai_ops.graph.state import AgentState


def generate_diagnosis(
    state: AgentState,
    llm: BaseChatModel,
) -> dict[str, Any]:

    incident = state["incident"]

    investigation_results = state.get(
        "investigation_results",
        [],
    )

    prompt = f"""
You are a Kubernetes incident diagnosis agent.

Analyze the incident using ONLY the Kubernetes
investigation evidence provided below.

Incident:

Service: {incident.service}
Namespace: {incident.namespace}
Severity: {incident.severity}
Description: {incident.description}

Investigation evidence:

{investigation_results}

Rules:

1. Use only observed Kubernetes evidence.

2. Do not invent pod names.

3. Do not invent restart counts.

4. Do not invent Kubernetes events.

5. Do not invent log messages.

6. Clearly distinguish:
   - observed evidence
   - hypotheses

7. If the evidence is insufficient,
   the root cause must be "Unknown".

8. Do not claim that additional tools were
   executed unless their results are present
   in the evidence.

Provide:

- root cause or most likely cause
- confidence
- evidence
- recommended next steps
- whether human intervention is required
"""

    response = llm.invoke(
        [
            HumanMessage(
                content=prompt,
            )
        ]
    )

    return {
        "diagnosis": response.content,
    }