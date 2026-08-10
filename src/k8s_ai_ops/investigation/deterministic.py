from typing import Any

from k8s_ai_ops.models.incident import IncidentRequest
from k8s_ai_ops.tools.kubernetes import (
    get_pods,
    get_pod_events,
    get_pod_logs,
)


class DeterministicInvestigator:
    """
    Deterministic Kubernetes incident investigator.

    Responsibilities:
    1. Collect pod information.
    2. Identify relevant pods using deterministic rules.
    3. Collect Kubernetes events for relevant pods.
    4. Collect container logs for relevant pods.
    5. Return observed evidence.

    The investigator does NOT use an LLM.
    """

    def investigate(
        self,
        incident: IncidentRequest,
    ) -> dict[str, Any]:

        # --------------------------------------------------
        # 1. Get pods
        # --------------------------------------------------

        pods = get_pods.invoke(
            {
                "namespace": incident.namespace,
            }
        )

        # --------------------------------------------------
        # 2. Identify relevant pods
        # --------------------------------------------------

        relevant_pods = self._find_relevant_pods(
            incident=incident,
            pods=pods,
        )

        pod_events: dict[str, Any] = {}
        pod_logs: dict[str, Any] = {}

        # --------------------------------------------------
        # 3. Get events for relevant pods
        # --------------------------------------------------

        for pod in relevant_pods:

            pod_name = pod["name"]

            events = get_pod_events.invoke(
                {
                    "namespace": incident.namespace,
                    "pod_name": pod_name,
                }
            )

            pod_events[pod_name] = events

        # --------------------------------------------------
        # 4. Get logs for relevant pod containers
        # --------------------------------------------------

        for pod in relevant_pods:

            pod_name = pod["name"]

            for container in pod.get(
                "containers",
                [],
            ):

                container_name = container["name"]

                key = (
                    f"{pod_name}/{container_name}"
                )

                try:

                    logs = get_pod_logs.invoke(
                        {
                            "namespace": incident.namespace,
                            "pod_name": pod_name,
                            "container": container_name,
                            "tail_lines": 100,
                        }
                    )

                    pod_logs[key] = logs

                except Exception as exc:

                    # A log failure should not stop
                    # investigation of the other pods.
                    pod_logs[key] = {
                        "error": str(exc)
                    }

        # --------------------------------------------------
        # 5. Return collected evidence
        # --------------------------------------------------

        return {
            "incident": incident.model_dump(),
            "pods": pods,
            "relevant_pods": relevant_pods,
            "pod_events": pod_events,
            "pod_logs": pod_logs,
        }

    # ======================================================
    # Relevant Pod Detection
    # ======================================================

    def _find_relevant_pods(
        self,
        incident: IncidentRequest,
        pods: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        description = (
            incident.description.lower()
        )

        # --------------------------------------------------
        # Determine whether the incident itself indicates
        # that restart/crash investigation is required.
        # --------------------------------------------------

        restart_incident = any(
            keyword in description
            for keyword in (
                "restart",
                "restarting",
                "restarted",
                "crash",
                "crashing",
                "crashed",
                "crashloop",
                "crashloopbackoff",
                "oom",
                "oomkilled",
                "backoff",
            )
        )

        relevant_pods: list[
            dict[str, Any]
        ] = []

        # --------------------------------------------------
        # Inspect every pod
        # --------------------------------------------------

        for pod in pods:

            pod_name = pod.get(
                "name",
                "",
            )

            # --------------------------------------------------
            # Only inspect pods belonging to the service.
            #
            # Example:
            #
            # service = payment-service
            #
            # payment-service-abc
            # payment-service-xyz
            #
            # are relevant.
            # --------------------------------------------------

            if not pod_name.startswith(
                incident.service
            ):
                continue

            unhealthy = False

            # --------------------------------------------------
            # Pod phase
            # --------------------------------------------------

            if pod.get("phase") != "Running":
                unhealthy = True

            # --------------------------------------------------
            # Container health
            # --------------------------------------------------

            for container in pod.get(
                "containers",
                [],
            ):

                restart_count = container.get(
                    "restart_count",
                    0,
                )

                ready = container.get(
                    "ready",
                    False,
                )

                termination_reason = (
                    container.get(
                        "termination_reason"
                    )
                )

                exit_code = container.get(
                    "exit_code"
                )

                # Container has restarted.
                if restart_count > 0:
                    unhealthy = True

                # Container isn't ready.
                if not ready:
                    unhealthy = True

                # Container has termination information.
                if termination_reason is not None:
                    unhealthy = True

                # Container exited with a code.
                if exit_code is not None:
                    unhealthy = True

            # --------------------------------------------------
            # A pod is relevant when:
            #
            # 1. Kubernetes currently reports it unhealthy
            #
            # OR
            #
            # 2. The incident description explicitly indicates
            #    a restart/crash/OOM investigation.
            # --------------------------------------------------

            if unhealthy or restart_incident:
                relevant_pods.append(pod)

        return relevant_pods