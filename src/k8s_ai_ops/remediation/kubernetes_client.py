from typing import Any
from datetime import datetime, timezone

from kubernetes import client, config


class KubernetesClient:
    """
    Thin wrapper around the Kubernetes Python client.

    Responsible only for Kubernetes API interaction.
    """

    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        self.apps_api = client.AppsV1Api()

    # =========================================================
    # RESTART
    # =========================================================

    def restart_deployment(
        self,
        namespace: str,
        deployment: str,
    ) -> dict[str, Any]:

        restarted_at = datetime.now(
            timezone.utc
        ).isoformat()

        patch = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "k8s-ai-ops/restarted-at": restarted_at
                        }
                    }
                }
            }
        }

        self.apps_api.patch_namespaced_deployment(
            name=deployment,
            namespace=namespace,
            body=patch,
        )

        return {
            "status": "executed",
            "action": "restart_workload",
            "workload": deployment,
            "namespace": namespace,
            "restarted_at": restarted_at,
        }

    # =========================================================
    # VERIFY DEPLOYMENT
    # =========================================================

    def get_deployment_status(
        self,
        namespace: str,
        deployment: str,
    ) -> dict[str, Any]:

        deployment_obj = (
            self.apps_api.read_namespaced_deployment(
                name=deployment,
                namespace=namespace,
            )
        )

        status = deployment_obj.status

        replicas = status.replicas or 0
        ready_replicas = status.ready_replicas or 0
        updated_replicas = status.updated_replicas or 0
        available_replicas = (
            status.available_replicas or 0
        )

        generation = deployment_obj.metadata.generation
        observed_generation = (
            status.observed_generation
        )

        rollout_complete = (
            replicas > 0
            and ready_replicas == replicas
            and updated_replicas == replicas
            and available_replicas == replicas
            and observed_generation == generation
        )

        return {
            "deployment": deployment,
            "namespace": namespace,
            "replicas": replicas,
            "ready_replicas": ready_replicas,
            "updated_replicas": updated_replicas,
            "available_replicas": available_replicas,
            "generation": generation,
            "observed_generation": observed_generation,
            "rollout_complete": rollout_complete,
        }