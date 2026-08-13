from k8s_ai_ops.investigation.diagnosis import (
    DeterministicDiagnosis,
)


def test_oom_killed():
    investigation = {
        "pods": [],
        "relevant_pods": [],
        "pod_events": {
            "payment-service-123": [
                {
                    "type": "Warning",
                    "reason": "OOMKilled",
                    "message": "Container was OOMKilled",
                }
            ]
        },
        "pod_logs": {},
    }

    diagnosis = DeterministicDiagnosis().diagnose(
        investigation
    )

    assert diagnosis.root_cause == "OOMKilled"
    assert diagnosis.confidence == 0.95
    assert diagnosis.human_intervention_required is False


def test_crash_loop_with_application_error():
    investigation = {
        "pods": [],
        "relevant_pods": [],
        "pod_events": {
            "payment-service-123": [
                {
                    "type": "Warning",
                    "reason": "CrashLoopBackOff",
                    "message": "Back-off restarting failed container",
                }
            ]
        },
        "pod_logs": {
            "payment-service-123/payment": (
                "java.lang.OutOfMemoryError: Java heap space"
            )
        },
    }

    diagnosis = DeterministicDiagnosis().diagnose(
        investigation
    )

    assert (
        diagnosis.root_cause
        == "CrashLoopBackOff due to application error"
    )

    assert diagnosis.confidence == 0.95


def test_image_pull_failure():
    investigation = {
        "pods": [],
        "relevant_pods": [],
        "pod_events": {
            "payment-service-123": [
                {
                    "reason": "ImagePullBackOff",
                    "message": "Back-off pulling image",
                }
            ]
        },
        "pod_logs": {},
    }

    diagnosis = DeterministicDiagnosis().diagnose(
        investigation
    )

    assert diagnosis.root_cause == "Container image pull failure"
    assert diagnosis.confidence == 0.95


def test_probe_failure():
    investigation = {
        "pods": [],
        "relevant_pods": [],
        "pod_events": {
            "payment-service-123": [
                {
                    "reason": "Unhealthy",
                    "message": "Liveness probe failed",
                }
            ]
        },
        "pod_logs": {},
    }

    diagnosis = DeterministicDiagnosis().diagnose(
        investigation
    )

    assert (
        diagnosis.root_cause
        == "Kubernetes health probe failure"
    )


def test_pending_pod():
    investigation = {
        "pods": [
            {
                "name": "payment-service-123",
                "phase": "Pending",
                "containers": [],
            }
        ],
        "relevant_pods": [],
        "pod_events": {},
        "pod_logs": {},
    }

    diagnosis = DeterministicDiagnosis().diagnose(
        investigation
    )

    assert diagnosis.root_cause == "Pod scheduling failure"


def test_application_error_in_logs():
    investigation = {
        "pods": [],
        "relevant_pods": [],
        "pod_events": {},
        "pod_logs": {
            "payment-service-123/payment": (
                "panic: runtime error: invalid memory address"
            )
        },
    }

    diagnosis = DeterministicDiagnosis().diagnose(
        investigation
    )

    assert diagnosis.root_cause == "Application error"
    assert diagnosis.confidence == 0.75


def test_unknown_when_evidence_is_insufficient():
    investigation = {
        "pods": [
            {
                "name": "payment-service-123",
                "phase": "Running",
                "containers": [
                    {
                        "name": "nginx",
                        "restart_count": 0,
                        "ready": True,
                        "termination_reason": None,
                        "exit_code": None,
                    }
                ],
            }
        ],
        "relevant_pods": [],
        "pod_events": {
            "payment-service-123": []
        },
        "pod_logs": {
            "payment-service-123/nginx": (
                "nginx started successfully"
            )
        },
    }

    diagnosis = DeterministicDiagnosis().diagnose(
        investigation
    )

    assert diagnosis.root_cause == "Unknown"
    assert diagnosis.confidence == 0.30
    assert diagnosis.human_intervention_required is True