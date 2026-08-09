from unittest.mock import MagicMock, patch

from k8s_ai_ops.tools.kubernetes import KubernetesTools
from kubernetes.config.config_exception import ConfigException

@patch(
    "k8s_ai_ops.tools.kubernetes.config.load_kube_config"
)
@patch(
    "k8s_ai_ops.tools.kubernetes.config.load_incluster_config"
)
@patch(
    "k8s_ai_ops.tools.kubernetes.client.CoreV1Api"
)
@patch(
    "k8s_ai_ops.tools.kubernetes.client.AppsV1Api"
)
def test_get_pods(
    mock_apps_api,
    mock_core_api,
    mock_incluster,
    mock_kube_config,
):

    mock_incluster.side_effect = ConfigException()

    pod = MagicMock()

    pod.metadata.name = "payment-service-123"
    pod.metadata.namespace = "payments"

    pod.status.phase = "Running"
    pod.status.pod_ip = "10.0.0.10"

    pod.spec.node_name = "node-1"

    container = MagicMock()

    container.name = "payment-service"
    container.restart_count = 3
    container.ready = True

    pod.status.container_statuses = [
        container
    ]

    response = MagicMock()
    response.items = [pod]

    mock_core_api.return_value.list_namespaced_pod.return_value = (
        response
    )

    kubernetes = KubernetesTools()

    result = kubernetes.get_pods(
        namespace="payments"
    )

    assert len(result) == 1

    assert result[0]["name"] == "payment-service-123"
    assert result[0]["namespace"] == "payments"
    assert result[0]["phase"] == "Running"
    assert result[0]["node"] == "node-1"

    assert result[0]["containers"][0]["restart_count"] == 3