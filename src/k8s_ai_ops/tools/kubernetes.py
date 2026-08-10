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

    def get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        container: str | None = None,
        tail_lines: int = 100,
        previous: bool = False,
    ) -> str:
        
        logs = self.core_api.read_namespaced_pod_log(
        name=pod_name,
        namespace=namespace,
        container=container,
        tail_lines=tail_lines,
        previous=previous,
    )
        if isinstance(logs, bytes):
         return logs.decode("utf-8", errors="replace")

        return str(logs)

    def get_pod_events(
        self,
        namespace: str,
        pod_name: str,
    ) -> list[dict[str, Any]]:

        events = self.core_api.list_namespaced_event(
            namespace=namespace,
            field_selector=f"involvedObject.name={pod_name}",
        )

        result = []

        for event in events.items:
            result.append(
                {
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "count": event.count,
                    "first_timestamp": (
                        event.first_timestamp.isoformat()
                        if event.first_timestamp
                        else None
                    ),
                    "last_timestamp": (
                        event.last_timestamp.isoformat()
                        if event.last_timestamp
                        else None
                    ),
                    "source": (
                        event.source.component
                        if event.source
                        else None
                    ),
                }
            )

        return result


    def restart_workload(
        self,
        namespace: str,
        service: str,
    ) -> dict[str, Any]:
        """
        Restart a Kubernetes Deployment.

        The restart is performed by changing the pod-template
        annotation, which causes Kubernetes to create a new
        ReplicaSet and perform a rolling restart.

        This method mutates Kubernetes state and therefore should
        only be called after the remediation approval gate.
        """

        from datetime import datetime, timezone

        restart_timestamp = (
            datetime.now(timezone.utc)
            .isoformat()
        )

        patch = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "k8s-ai-ops/restartedAt": (
                                restart_timestamp
                            )
                        }
                    }
                }
            }
        }

        deployment = (
            self.apps_api.patch_namespaced_deployment(
                name=service,
                namespace=namespace,
                body=patch,
            )
        )

        return {
            "status": "restarted",
            "deployment": deployment.metadata.name,
            "namespace": namespace,
            "restarted_at": restart_timestamp,
        }
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


@tool
def get_pod_events(
    namespace: str,
    pod_name: str,
) -> list[dict[str, Any]]:
    """
    Get Kubernetes events associated with a pod.

    Use this tool when investigating pod failures,
    restarts, CrashLoopBackOff, OOMKilled events,
    scheduling failures, image pull failures,
    probe failures, or other Kubernetes lifecycle issues.
    """

    kubernetes = KubernetesTools()

    return kubernetes.get_pod_events(
        namespace=namespace,
        pod_name=pod_name,
    )

@tool
def get_pod_logs(
    namespace: str,
    pod_name: str,
    container: str | None = None,
    tail_lines: int = 100,
    previous: bool = False,
) -> str:
    """Get logs from a Kubernetes pod.

    Use previous=True to retrieve logs from the
    previous terminated container instance.
    """

    kubernetes = KubernetesTools()

    return kubernetes.get_pod_logs(
        namespace=namespace,
        pod_name=pod_name,
        container=container,
        tail_lines=tail_lines,
        previous=previous,
    )