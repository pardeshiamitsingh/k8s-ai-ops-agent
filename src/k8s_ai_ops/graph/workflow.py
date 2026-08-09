from langgraph.graph import END, START, StateGraph
from langchain_core.language_models import BaseChatModel

from k8s_ai_ops.agents.triage import triage_incident
from k8s_ai_ops.graph.state import AgentState


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

    graph.add_edge(
        START,
        "triage",
    )

    graph.add_edge(
        "triage",
        END,
    )

    return graph.compile()