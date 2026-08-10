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

    messages = state.get("messages", [])

    if not messages:

        prompt = f"""
You are a Kubernetes incident investigation agent.

Your job is to investigate the incident using
available Kubernetes tools.

Incident:

Service: {incident.service}
Namespace: {incident.namespace}
Severity: {incident.severity}
Description: {incident.description}

Available tools:

1. get_pods(namespace)

Use this to inspect:
- pod phase
- readiness
- restart counts
- container termination reasons
- exit codes

2. get_pod_events(namespace, pod_name)

Use this to inspect:
- OOMKilled
- BackOff
- CrashLoopBackOff
- scheduling failures
- image pull failures
- probe failures
- Kubernetes lifecycle events

3. get_pod_logs(
       namespace,
       pod_name,
       container,
       tail_lines
   )

Use this to inspect:
- application errors
- exceptions
- crashes
- runtime failures

Investigation rules:

1. Start by inspecting the pods.

2. If a pod appears unhealthy, restarting,
   or has a termination reason, inspect its events.

3. Inspect logs when they can provide additional
   evidence about the failure.

4. Do not assume Kubernetes observations.

5. Do not claim that a tool was used unless
   the tool was actually called.

6. Distinguish observed evidence from hypotheses.

7. Continue investigating when additional
   evidence is necessary.

8. Stop investigating only when sufficient
   evidence has been collected to produce
   a diagnosis.

9. If the available evidence is insufficient,
   explicitly state that the root cause is unknown.
"""

        messages = [
            HumanMessage(
                content=prompt,
            )
        ]

    llm_with_tools = llm.bind_tools(
        [
            get_pods,
            get_pod_events,
            get_pod_logs,
        ]
    )

    response = llm_with_tools.invoke(
        messages
    )

    return {
        "messages": [
            response,
        ]
    }