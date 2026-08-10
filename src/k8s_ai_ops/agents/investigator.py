import json
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from k8s_ai_ops.graph.state import AgentState
from k8s_ai_ops.tools.kubernetes import (
    get_pod_events,
    get_pod_logs,
    get_pods,
)


def investigate_incident(
    state: AgentState,
    llm: BaseChatModel,
) -> dict[str, Any]:

    incident = state["incident"]

    namespace = incident.namespace
    service = incident.service

    # ---------------------------------------------------------
    # 1. Get pods
    # ---------------------------------------------------------

    pods = get_pods.invoke(
        {
            "namespace": namespace,
        }
    )

    # ---------------------------------------------------------
    # 2. Select pods relevant to the incident
    #
    # We don't ask the LLM to select them.
    # We use the service name directly.
    # ---------------------------------------------------------

    relevant_pods = [
        pod
        for pod in pods
        if service in pod.get("name", "")
    ]

    # If no pod name contains the service name,
    # investigate all pods in the namespace.
    if not relevant_pods:
        relevant_pods = pods

    # ---------------------------------------------------------
    # 3. Get events and logs for relevant pods
    # ---------------------------------------------------------

    pod_events: dict[str, Any] = {}
    pod_logs: dict[str, Any] = {}

    for pod in relevant_pods:

        pod_name = pod["name"]

        # ---------------------------------------------
        # Events
        # ---------------------------------------------

        events = get_pod_events.invoke(
            {
                "namespace": namespace,
                "pod_name": pod_name,
            }
        )

        pod_events[pod_name] = events

        # ---------------------------------------------
        # Logs
        # ---------------------------------------------

        containers = pod.get("containers", [])

        for container in containers:

            container_name = container.get("name")

            if not container_name:
                continue

            logs = get_pod_logs.invoke(
                {
                    "namespace": namespace,
                    "pod_name": pod_name,
                    "container": container_name,
                    "tail_lines": 100,
                }
            )

            pod_logs[
                f"{pod_name}/{container_name}"
            ] = logs

    # ---------------------------------------------------------
    # 4. Build grounded evidence
    # ---------------------------------------------------------

    evidence = {
        "incident": {
            "service": service,
            "namespace": namespace,
            "severity": incident.severity,
            "description": incident.description,
        },
        "pods": pods,
        "relevant_pods": relevant_pods,
        "pod_events": pod_events,
        "pod_logs": pod_logs,
    }

    # ---------------------------------------------------------
    # 5. Give ONLY observed evidence to the diagnosis agent
    # ---------------------------------------------------------

    evidence_message = HumanMessage(
        content=(
            "Kubernetes investigation results.\n\n"
            "IMPORTANT:\n"
            "The following data was collected directly from "
            "Kubernetes tools.\n"
            "Treat this as observed evidence.\n"
            "Do not invent or modify Kubernetes observations.\n\n"
            f"{json.dumps(evidence, indent=2, default=str)}"
        )
    )

    return {
        "investigation_results": [
            evidence
        ],
        "messages": [
            evidence_message
        ],
        "investigation_complete": True,
    }