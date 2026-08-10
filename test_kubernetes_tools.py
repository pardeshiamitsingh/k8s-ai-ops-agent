from unittest.mock import MagicMock, patch

from kubernetes.config.config_exception import ConfigException

from k8s_ai_ops.tools.kubernetes import KubernetesTools


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

    # Simulate running outside Kubernetes.
    # This should cause fallback to ~/.kube/config.
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

    # Important: explicitly specify that there is
    # no previous container termination.
    container.last_state = None

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

    assert result[0]["containers"][0]["name"] == "payment-service"
    assert result[0]["containers"][0]["restart_count"] == 3
    assert result[0]["containers"][0]["ready"] is True
    assert result[0]["containers"][0]["termination_reason"] is None
    assert result[0]["containers"][0]["exit_code"] is None