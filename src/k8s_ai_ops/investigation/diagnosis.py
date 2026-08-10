from typing import Any

from k8s_ai_ops.models.diagnosis import Diagnosis


class DeterministicDiagnosis:

    def diagnose(
        self,
        investigation: dict[str, Any],
    ) -> Diagnosis:

        evidence: list[str] = []
        next_steps: list[str] = []

        pods = investigation.get("pods", [])
        relevant_pods = investigation.get("relevant_pods", [])
        pod_events = investigation.get("pod_events", {})
        pod_logs = investigation.get("pod_logs", {})

        # ---------------------------------------------------------
        # 1. OOMKilled
        # ---------------------------------------------------------
        for pod_name, events in pod_events.items():
            for event in events:
                message = self._event_text(event)

                if "OOMKilled" in message:
                    evidence.append(
                        f"Pod {pod_name} reported OOMKilled."
                    )

                    return Diagnosis(
                        root_cause="OOMKilled",
                        confidence="high",
                        evidence=evidence,
                        recommended_next_steps=[
                            "Increase the memory limit for the affected container.",
                            "Check application memory usage and heap configuration.",
                            "Inspect the application for memory leaks.",
                        ],
                        human_intervention_required=False,
                    )

        # ---------------------------------------------------------
        # 2. CrashLoopBackOff
        # ---------------------------------------------------------
        for pod_name, events in pod_events.items():
            for event in events:
                message = self._event_text(event)

                if "CrashLoopBackOff" in message:
                    evidence.append(
                        f"Pod {pod_name} reported CrashLoopBackOff."
                    )

                    # Look for application evidence in logs.
                    log_match = self._find_log_failure(
                        pod_name,
                        pod_logs,
                    )

                    if log_match:
                        evidence.append(log_match)

                        return Diagnosis(
                            root_cause="CrashLoopBackOff due to application error",
                            confidence="high",
                            evidence=evidence,
                            recommended_next_steps=[
                                "Inspect the application error causing the container to exit.",
                                "Fix the application failure and redeploy.",
                            ],
                            human_intervention_required=False,
                        )

                    return Diagnosis(
                        root_cause="CrashLoopBackOff",
                        confidence="medium",
                        evidence=evidence,
                        recommended_next_steps=[
                            "Inspect container logs for the crash reason.",
                            "Inspect the previous container instance logs.",
                            "Review the pod configuration and startup command.",
                        ],
                        human_intervention_required=False,
                    )

        # ---------------------------------------------------------
        # 3. ImagePullBackOff / ErrImagePull
        # ---------------------------------------------------------
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
                        confidence="high",
                        evidence=evidence,
                        recommended_next_steps=[
                            "Verify the container image name and tag.",
                            "Verify registry credentials.",
                            "Verify that the image exists in the configured registry.",
                        ],
                        human_intervention_required=False,
                    )

        # ---------------------------------------------------------
        # 4. Probe failures
        # ---------------------------------------------------------
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
                        confidence="high",
                        evidence=evidence,
                        recommended_next_steps=[
                            "Inspect the failing probe configuration.",
                            "Verify the application health endpoint.",
                            "Check application startup time and probe thresholds.",
                        ],
                        human_intervention_required=False,
                    )

        # ---------------------------------------------------------
        # 5. Scheduling failures / Pending pods
        # ---------------------------------------------------------
        for pod in pods:
            if pod.get("phase") == "Pending":
                pod_name = pod.get("name", "unknown")

                evidence.append(
                    f"Pod {pod_name} is Pending."
                )

                return Diagnosis(
                    root_cause="Pod scheduling failure",
                    confidence="medium",
                    evidence=evidence,
                    recommended_next_steps=[
                        "Inspect Kubernetes scheduling events.",
                        "Check node capacity and resource requests.",
                        "Check node selectors, taints, and tolerations.",
                    ],
                    human_intervention_required=False,
                )

        # ---------------------------------------------------------
        # 6. Application errors in logs
        # ---------------------------------------------------------
        for key, logs in pod_logs.items():
            failure = self._detect_application_failure(logs)

            if failure:
                evidence.append(
                    f"Application failure detected in {key}: {failure}"
                )

                return Diagnosis(
                    root_cause="Application error",
                    confidence="medium",
                    evidence=evidence,
                    recommended_next_steps=[
                        "Inspect the application stack trace.",
                        "Fix the application error and redeploy.",
                    ],
                    human_intervention_required=False,
                )

        # ---------------------------------------------------------
        # 7. Healthy pods / insufficient evidence
        # ---------------------------------------------------------
        if pods:
            for pod in relevant_pods or pods:
                pod_name = pod.get("name", "unknown")
                phase = pod.get("phase")

                evidence.append(
                    f"Pod {pod_name} is currently in phase {phase}."
                )

                for container in pod.get("containers", []):
                    evidence.append(
                        f"Container {container.get('name')} in pod "
                        f"{pod_name}: "
                        f"restart_count={container.get('restart_count')}, "
                        f"ready={container.get('ready')}, "
                        f"termination_reason="
                        f"{container.get('termination_reason')}, "
                        f"exit_code={container.get('exit_code')}."
                    )

        evidence.append(
            "Collected evidence does not identify a definitive failure."
        )

        next_steps.extend([
            "Verify whether the reported restart condition is still occurring.",
            "Check historical pod restart counts.",
            "Inspect Kubernetes events over a longer time window.",
            "Collect application and container metrics.",
        ])

        return Diagnosis(
            root_cause="Unknown",
            confidence="low",
            evidence=evidence,
            recommended_next_steps=next_steps,
            human_intervention_required=True,
        )

    # =============================================================
    # Helpers
    # =============================================================

    @staticmethod
    def _event_text(event: Any) -> str:
        """
        Normalize different event representations.
        """

        if isinstance(event, str):
            return event

        if isinstance(event, dict):
            parts = []

            for key in (
                "type",
                "reason",
                "message",
            ):
                value = event.get(key)

                if value:
                    parts.append(str(value))

            return " ".join(parts)

        return str(event)

    @staticmethod
    def _find_log_failure(
        pod_name: str,
        pod_logs: dict[str, Any],
    ) -> str | None:

        for key, logs in pod_logs.items():

            if not key.startswith(f"{pod_name}/"):
                continue

            failure = DeterministicDiagnosis._detect_application_failure(
                logs
            )

            if failure:
                return (
                    f"Application failure detected in {key}: "
                    f"{failure}"
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