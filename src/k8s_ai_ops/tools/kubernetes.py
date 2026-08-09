from typing import Any

from kubernetes import client, config
from langchain_core.tools import tool


class KubernetesTools:
    """
    Read-only Kubernetes operations used by the AI Ops agents.
    """

    def __init__(self):
        self._load_config()

        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()

    def _load_config(self) -> None:
        """
        Load Kubernetes configuration.

        Local development:
            ~/.kube/config

        In-cluster deployment:
            ServiceAccount credentials
        """

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

    def get_pods(
        self,
        namespace: str,
    ) -> list[dict[str, Any]]:
        """
        Return pod information for a namespace.
        """

        pods = self.core_api.list_namespaced_pod(
            namespace=namespace
        )

        result = []

        for pod in pods.items:

            containers = []

            for container in (
                pod.status.container_statuses or []
            ):
                termination_reason = None
                exit_code = None

                if (
                    container.last_state
                    and container.last_state.terminated
                ):
                    termination = (
                        container.last_state.terminated
                    )

                    termination_reason = termination.reason
                    exit_code = termination.exit_code

                containers.append(
                    {
                        "name": container.name,
                        "restart_count": (
                            container.restart_count
                        ),
                        "ready": container.ready,
                        "termination_reason": (
                            termination_reason
                        ),
                        "exit_code": exit_code,
                    }
                )

            result.append(
                {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": pod.status.phase,
                    "node": pod.spec.node_name,
                    "pod_ip": pod.status.pod_ip,
                    "containers": containers,
                }
            )

        return result


@tool
def get_pods(
    namespace: str,
) -> list[dict[str, Any]]:
    """
    Get Kubernetes pods in a namespace.

    Use this tool when investigating Kubernetes incidents
    and you need to understand pod health, restart counts,
    container readiness, pod placement, or container
    termination reasons such as OOMKilled.
    """

    kubernetes = KubernetesTools()

    return kubernetes.get_pods(
        namespace=namespace
    )