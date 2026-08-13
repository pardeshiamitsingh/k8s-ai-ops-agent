from typing import Any

from k8s_ai_ops.models.diagnosis import Diagnosis


class DeterministicDiagnosis:
    """
    Produces a deterministic diagnosis from Kubernetes
    investigation evidence.

    Confidence:

        0.95 -> high confidence
        0.75 -> medium confidence
        0.30 -> low confidence
    """

    HIGH_CONFIDENCE = 0.95
    MEDIUM_CONFIDENCE = 0.75
    LOW_CONFIDENCE = 0.30

    RESTART_THRESHOLD = 3

    def diagnose(
        self,
        investigation: dict[str, Any],
    ) -> Diagnosis:

        evidence: list[str] = []

        pods = investigation.get("pods", [])
        relevant_pods = investigation.get("relevant_pods", [])
        pod_events = investigation.get("pod_events", {})
        pod_logs = investigation.get("pod_logs", {})

        # =========================================================
        # 1. OOMKilled
        # =========================================================

        for pod_name, events in pod_events.items():
            for event in events:
                message = self._event_text(event)

                if "OOMKilled" in message:
                    evidence.append(
                        f"Pod {pod_name} reported OOMKilled."
                    )

                    return Diagnosis(
                        root_cause="OOMKilled",
                        confidence=self.HIGH_CONFIDENCE,
                        evidence=evidence,
                        recommended_next_steps=[
                            "Increase the memory limit for the affected container.",
                            "Check application memory usage and heap configuration.",
                            "Inspect the application for memory leaks.",
                        ],
                        human_intervention_required=False,
                    )

        # =========================================================
        # 2. CrashLoopBackOff
        # =========================================================

        for pod_name, events in pod_events.items():
            for event in events:
                message = self._event_text(event)

                if "CrashLoopBackOff" in message:
                    evidence.append(
                        f"Pod {pod_name} reported CrashLoopBackOff."
                    )

                    log_match = self._find_log_failure(
                        pod_name,
                        pod_logs,
                    )

                    if log_match:
                        evidence.append(log_match)

                    return Diagnosis(
                        root_cause="CrashLoopBackOff",
                        confidence=self.HIGH_CONFIDENCE,
                        evidence=evidence,
                        recommended_next_steps=[
                            "Inspect the previous container logs.",
                            "Identify the application or startup failure.",
                            "Restart the affected workload after human approval.",
                        ],
                        human_intervention_required=True,
                    )

        # =========================================================
        # 3. Repeated container crashes / BackOff
        #
        # Kubernetes may report:
        #
        #   BackOff restarting failed container
        #
        # instead of explicitly reporting CrashLoopBackOff.
        #
        # =========================================================

        for pod_name, events in pod_events.items():

            has_backoff = False
            backoff_message = None
            backoff_count = None

            for event in events:
                message = self._event_text(event)

                if "BackOff" in message:
                    has_backoff = True
                    backoff_message = message

                    if isinstance(event, dict):
                        backoff_count = event.get("count")

            if not has_backoff:
                continue

            pod = self._find_pod(
                pod_name,
                relevant_pods or pods,
            )

            if not pod:
                continue

            containers = pod.get("containers", [])

            for container in containers:

                restart_count = container.get(
                    "restart_count",
                    0,
                )

                ready = container.get(
                    "ready",
                    True,
                )

                termination_reason = container.get(
                    "termination_reason"
                )

                exit_code = container.get(
                    "exit_code"
                )

                if (
                    restart_count >= self.RESTART_THRESHOLD
                    and not ready
                    and termination_reason == "Error"
                ):
                    container_name = container.get(
                        "name",
                        "unknown",
                    )

                    evidence.append(
                        f"Pod {pod_name} has container "
                        f"{container_name} repeatedly failing."
                    )

                    evidence.append(
                        f"Container {container_name}: "
                        f"restart_count={restart_count}, "
                        f"ready={ready}, "
                        f"termination_reason="
                        f"{termination_reason}, "
                        f"exit_code={exit_code}."
                    )

                    if backoff_message:
                        evidence.append(
                            f"Kubernetes event: "
                            f"{backoff_message}"
                        )

                    if backoff_count is not None:
                        evidence.append(
                            f"BackOff event count="
                            f"{backoff_count}."
                        )

                    log_match = self._find_log_failure(
                        pod_name,
                        pod_logs,
                    )

                    if log_match:
                        evidence.append(log_match)

                    return Diagnosis(
                        root_cause="Container repeatedly crashing",
                        confidence=self.HIGH_CONFIDENCE,
                        evidence=evidence,
                        recommended_next_steps=[
                            "Inspect the failing container logs.",
                            "Verify the container startup command and configuration.",
                            "Restart the affected workload after human approval.",
                        ],
                        human_intervention_required=True,
                    )

        # =========================================================
        # 4. ImagePullBackOff / ErrImagePull
        # =========================================================

        for pod_name, events in pod_events.items():
            for event in events:
                message = self._event_text(event)

                if (
                    "ImagePullBackOff" in message
                    or "ErrImagePull" in message
                ):
                    evidence.append(
                        f"Pod {pod_name} reported image pull failure: "
                        f"{message}"
                    )

                    return Diagnosis(
                        root_cause="Container image pull failure",
                        confidence=self.HIGH_CONFIDENCE,
                        evidence=evidence,
                        recommended_next_steps=[
                            "Verify the container image name and tag.",
                            "Verify registry credentials.",
                            "Verify that the image exists in the configured registry.",
                        ],
                        human_intervention_required=False,
                    )

        # =========================================================
        # 5. Probe failures
        # =========================================================

        for pod_name, events in pod_events.items():
            for event in events:
                message = self._event_text(event).lower()

                if (
                    "liveness probe failed" in message
                    or "readiness probe failed" in message
                    or "startup probe failed" in message
                ):
                    evidence.append(
                        f"Pod {pod_name} reported a probe failure: "
                        f"{self._event_text(event)}"
                    )

                    return Diagnosis(
                        root_cause="Kubernetes health probe failure",
                        confidence=self.HIGH_CONFIDENCE,
                        evidence=evidence,
                        recommended_next_steps=[
                            "Inspect the failing probe configuration.",
                            "Verify the application health endpoint.",
                            "Check application startup time and probe thresholds.",
                        ],
                        human_intervention_required=False,
                    )

        # =========================================================
        # 6. Scheduling failures / Pending pods
        # =========================================================

        for pod in pods:
            if pod.get("phase") == "Pending":

                pod_name = pod.get(
                    "name",
                    "unknown",
                )

                evidence.append(
                    f"Pod {pod_name} is Pending."
                )

                return Diagnosis(
                    root_cause="Pod scheduling failure",
                    confidence=self.MEDIUM_CONFIDENCE,
                    evidence=evidence,
                    recommended_next_steps=[
                        "Inspect Kubernetes scheduling events.",
                        "Check node capacity and resource requests.",
                        "Check node selectors, taints, and tolerations.",
                    ],
                    human_intervention_required=False,
                )

        # =========================================================
        # 7. Application errors in logs
        # =========================================================

        for key, logs in pod_logs.items():

            failure = self._detect_application_failure(
                logs
            )

            if failure:
                evidence.append(
                    f"Application failure detected in "
                    f"{key}: {failure}"
                )

                return Diagnosis(
                    root_cause="Application error",
                    confidence=self.MEDIUM_CONFIDENCE,
                    evidence=evidence,
                    recommended_next_steps=[
                        "Inspect the application stack trace.",
                        "Fix the application error and redeploy.",
                    ],
                    human_intervention_required=False,
                )

        # =========================================================
        # 8. Insufficient evidence
        # =========================================================

        if pods:

            for pod in relevant_pods or pods:

                pod_name = pod.get(
                    "name",
                    "unknown",
                )

                phase = pod.get("phase")

                evidence.append(
                    f"Pod {pod_name} is currently "
                    f"in phase {phase}."
                )

                for container in pod.get(
                    "containers",
                    [],
                ):
                    evidence.append(
                        f"Container "
                        f"{container.get('name')} "
                        f"in pod {pod_name}: "
                        f"restart_count="
                        f"{container.get('restart_count')}, "
                        f"ready="
                        f"{container.get('ready')}, "
                        f"termination_reason="
                        f"{container.get('termination_reason')}, "
                        f"exit_code="
                        f"{container.get('exit_code')}."
                    )

        evidence.append(
            "Collected evidence does not identify "
            "a definitive failure."
        )

        return Diagnosis(
            root_cause="Unknown",
            confidence=self.LOW_CONFIDENCE,
            evidence=evidence,
            recommended_next_steps=[
                "Verify whether the reported restart condition is still occurring.",
                "Check historical pod restart counts.",
                "Inspect Kubernetes events over a longer time window.",
                "Collect application and container metrics.",
            ],
            human_intervention_required=True,
        )

    # =============================================================
    # Helpers
    # =============================================================

    @staticmethod
    def _find_pod(
        pod_name: str,
        pods: list[dict[str, Any]],
    ) -> dict[str, Any] | None:

        for pod in pods:
            if pod.get("name") == pod_name:
                return pod

        return None

    @staticmethod
    def _event_text(
        event: Any,
    ) -> str:

        if isinstance(event, str):
            return event

        if isinstance(event, dict):

            parts: list[str] = []

            for key in (
                "type",
                "reason",
                "message",
            ):
                value = event.get(key)

                if value:
                    parts.append(
                        str(value)
                    )

            return " ".join(parts)

        return str(event)

    @staticmethod
    def _find_log_failure(
        pod_name: str,
        pod_logs: dict[str, Any],
    ) -> str | None:

        for key, logs in pod_logs.items():

            if not key.startswith(
                f"{pod_name}/"
            ):
                continue

            failure = (
                DeterministicDiagnosis
                ._detect_application_failure(
                    logs
                )
            )

            if failure:
                return (
                    f"Application failure detected "
                    f"in {key}: {failure}"
                )

            # Simple generic crash indication.
            if logs is not None:

                if isinstance(logs, bytes):
                    text = logs.decode(
                        "utf-8",
                        errors="replace",
                    )
                else:
                    text = str(logs)

                if "crashing" in text.lower():
                    return (
                        f"Container logs for {key} "
                        f"contain a crash indication."
                    )

        return None

    @staticmethod
    def _detect_application_failure(
        logs: Any,
    ) -> str | None:

        if logs is None:
            return None

        if isinstance(logs, bytes):
            logs = logs.decode(
                "utf-8",
                errors="replace",
            )

        logs = str(logs)

        indicators = [
            "OutOfMemoryError",
            "OOMKilled",
            "panic:",
            "Traceback",
            "Exception",
            "FATAL",
            "fatal error",
            "segmentation fault",
            "Segmentation fault",
            "connection refused",
            "database connection failed",
        ]

        for indicator in indicators:

            if indicator.lower() in logs.lower():
                return indicator

        return None