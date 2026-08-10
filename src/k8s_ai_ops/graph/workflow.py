from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from k8s_ai_ops.agents.diagnosis import (
    generate_diagnosis,
)
from k8s_ai_ops.agents.investigator import (
    investigate_incident,
)
from k8s_ai_ops.agents.triage import (
    triage_incident,
)
from k8s_ai_ops.graph.router import (
    route_investigation,
)
from k8s_ai_ops.graph.state import AgentState
from k8s_ai_ops.graph.tools import tool_node


def build_incident_graph(
    llm: BaseChatModel,
):

    graph = StateGraph(AgentState)

    graph.add_node(
        "triage",
        lambda state: triage_incident(
            state,
            llm,
        ),
    )

    graph.add_node(
        "investigator",
        lambda state: investigate_incident(
            state,
            llm,
        ),
    )

    graph.add_node(
        "tools",
        tool_node,
    )

    graph.add_node(
        "diagnosis",
        lambda state: generate_diagnosis(
            state,
            llm,
        ),
    )

    graph.add_edge(
        START,
        "triage",
    )

    graph.add_edge(
        "triage",
        "investigator",
    )

    graph.add_conditional_edges(
        "investigator",
        route_investigation,
        {
            "tools": "tools",
            "diagnosis": "diagnosis",
        },
    )

    graph.add_edge(
        "tools",
        "investigator",
    )

    graph.add_edge(
        "diagnosis",
        END,
    )

    return graph.compile()