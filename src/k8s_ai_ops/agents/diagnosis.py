from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from k8s_ai_ops.graph.state import AgentState


def generate_diagnosis(
    state: AgentState,
    llm: BaseChatModel,
) -> dict[str, Any]:

    messages = state.get("messages", [])

    prompt = """
Based on the incident and all Kubernetes evidence collected,
provide a concise incident diagnosis.

Include:

1. Root cause or most likely cause
2. Evidence supporting the conclusion
3. Recommended next investigation step
4. Whether human intervention is required

Do not invent information.
Clearly distinguish observed facts from hypotheses.
"""

    response = llm.invoke(
        messages + [
            HumanMessage(content=prompt)
        ]
    )

    return {
        "diagnosis": response.content
    }