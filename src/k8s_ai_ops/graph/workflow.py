from langgraph.graph import END, START, StateGraph

from k8s_ai_ops.agents.triage import triage_incident
from k8s_ai_ops.graph.state import AgentState


def build_incident_graph():
    graph = StateGraph(AgentState)

    graph.add_node(
        "triage",
        triage_incident,
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