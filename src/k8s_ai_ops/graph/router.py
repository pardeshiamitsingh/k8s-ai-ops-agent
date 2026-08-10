from typing import Literal

from k8s_ai_ops.graph.state import AgentState


def route_investigation(
    state: AgentState,
) -> Literal["tools", "diagnosis"]:

    if state.get("investigation_complete", False):
        return "diagnosis"

    messages = state.get("messages", [])

    if not messages:
        return "diagnosis"

    last_message = messages[-1]

    tool_calls = getattr(
        last_message,
        "tool_calls",
        None,
    )

    if tool_calls:
        return "tools"

    return "diagnosis"