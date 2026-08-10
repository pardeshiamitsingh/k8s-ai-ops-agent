from unittest.mock import MagicMock

from k8s_ai_ops.tools.kubernetes import KubernetesTools


def test_restart_workload():

    kubernetes = KubernetesTools.__new__(
        KubernetesTools
    )

    kubernetes.apps_api = MagicMock()

    deployment = MagicMock()
    deployment.metadata.name = "payment-service"

    kubernetes.apps_api.patch_namespaced_deployment.return_value = (
        deployment
    )

    result = kubernetes.restart_workload(
        namespace="default",
        service="payment-service",
    )

    assert result["status"] == "restarted"

    assert result["deployment"] == "payment-service"

    kubernetes.apps_api.patch_namespaced_deployment.assert_called_once()

    call = (
        kubernetes.apps_api
        .patch_namespaced_deployment
        .call_args
    )

    assert call.kwargs["name"] == "payment-service"
    assert call.kwargs["namespace"] == "default"

    patch = call.kwargs["body"]

    assert (
        "k8s-ai-ops/restartedAt"
        in patch["spec"]["template"]["metadata"]["annotations"]
    )