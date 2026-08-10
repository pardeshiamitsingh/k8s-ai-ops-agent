from langgraph.prebuilt import ToolNode

from k8s_ai_ops.tools.kubernetes import (
    get_pods,
    get_pod_logs,
    get_pod_events,
)


kubernetes_tools = [
    get_pods,
    get_pod_logs,
    get_pod_events,
]


tool_node = ToolNode(
    kubernetes_tools
)