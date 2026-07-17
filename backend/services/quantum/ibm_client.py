"""IBM Quantum Runtime connection helpers (instance, probe, job polling)."""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any, Callable

logger = logging.getLogger(__name__)

TRUE_VALUES = {"1", "true", "yes", "on"}
StatusCallback = Callable[[str], None]
DEFAULT_IBM_TIMEOUT = int(os.environ.get("IBM_RUNTIME_TIMEOUT", "900"))
DEFAULT_PROBE_TIMEOUT = int(os.environ.get("IBM_PROBE_TIMEOUT", "45"))


def runtime_service_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "channel": os.environ.get("IBM_QUANTUM_CHANNEL", "ibm_quantum_platform"),
    }
    token = os.environ.get("IBM_QUANTUM_TOKEN") or os.environ.get("IBM_API_KEY")
    instance = (os.environ.get("IBM_QUANTUM_INSTANCE") or "").strip()
    if token:
        kwargs["token"] = token
    if instance:
        kwargs["instance"] = instance
    return kwargs


def create_runtime_service():
    from qiskit_ibm_runtime import QiskitRuntimeService

    if not (os.environ.get("IBM_QUANTUM_TOKEN") or os.environ.get("IBM_API_KEY")):
        raise RuntimeError(
            "IBM_QUANTUM_TOKEN is not set. Add it to .env (see .env.example)."
        )
    return QiskitRuntimeService(**runtime_service_kwargs())


def _active_instance_name(service) -> str | None:
    account = getattr(service, "active_account", None)
    if callable(account):
        value = account()
        if isinstance(value, dict):
            return value.get("instance") or value.get("name")
        return str(value) if value else None
    return None


def _list_hardware_backends(service, min_qubits: int) -> list:
    try:
        return list(
            service.backends(
                simulator=False,
                operational=True,
                min_num_qubits=min_qubits,
            )
        )
    except TypeError:
        picked = []
        for backend in service.backends():
            if getattr(backend, "simulator", False):
                continue
            num_qubits = getattr(backend, "num_qubits", 0) or 0
            if num_qubits >= min_qubits:
                picked.append(backend)
        return picked


def probe_ibm_runtime(timeout_seconds: int = DEFAULT_PROBE_TIMEOUT) -> dict[str, Any]:
    """Test token, instance, and backend visibility without submitting a job."""

    if not (os.environ.get("IBM_QUANTUM_TOKEN") or os.environ.get("IBM_API_KEY")):
        return {
            "ok": False,
            "error": "IBM_QUANTUM_TOKEN is not configured.",
            "hint": "Copy .env.example to .env and set your API token.",
        }

    def _run_probe() -> dict[str, Any]:
        service = create_runtime_service()
        instance = _active_instance_name(service)
        backends = _list_hardware_backends(service, min_qubits=5)
        names = []
        for backend in backends[:12]:
            name = getattr(backend, "name", None)
            names.append(name() if callable(name) else str(name))

        return {
            "ok": True,
            "instance": instance,
            "instance_configured": bool(os.environ.get("IBM_QUANTUM_INSTANCE")),
            "hardware_backend_count": len(backends),
            "hardware_backends_sample": names,
            "channel": os.environ.get("IBM_QUANTUM_CHANNEL", "ibm_quantum_platform"),
        }

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_run_probe)
    try:
        payload = future.result(timeout=timeout_seconds)
        if payload.get("ok") and payload.get("hardware_backend_count", 0) == 0:
            payload["ok"] = False
            payload["error"] = (
                "No operational IBM hardware backends visible for this account/instance."
            )
            payload["hint"] = (
                "Open-plan instances may not expose systems like ibm_marrakesh. "
                "Set IBM_QUANTUM_INSTANCE to your instance CRN from the IBM Quantum "
                "Platform dashboard, or set IBM_BACKEND to an available system."
            )
        return payload
    except FuturesTimeout:
        return {
            "ok": False,
            "error": f"IBM API did not respond within {timeout_seconds}s.",
            "hint": (
                "Check network/VPN, IBM Quantum service status, and that "
                "IBM_QUANTUM_INSTANCE matches your dashboard (CRN string)."
            ),
        }
    except Exception as exc:
        logger.exception("IBM runtime probe failed")
        return {
            "ok": False,
            "error": str(exc),
            "hint": "Verify token, instance CRN, and channel=ibm_quantum_platform.",
        }
    finally:
        executor.shutdown(wait=False)


def wait_for_runtime_result(
    runtime_job,
    timeout_seconds: int = DEFAULT_IBM_TIMEOUT,
    poll_seconds: float = 5.0,
    on_status: StatusCallback | None = None,
):
    """Poll IBM job status instead of blocking silently on result()."""

    deadline = time.time() + timeout_seconds
    last_status: str | None = None

    while time.time() < deadline:
        status = runtime_job.status()
        if status != last_status:
            last_status = status
            logger.info("IBM Runtime job %s status=%s", runtime_job.job_id(), status)
            if on_status:
                on_status(str(status))

        if runtime_job.in_final_state():
            break
        time.sleep(poll_seconds)
    else:
        raise TimeoutError(
            f"IBM Runtime job timed out after {timeout_seconds}s "
            f"(last status: {last_status or 'unknown'})."
        )

    if runtime_job.errored():
        message = getattr(runtime_job, "error_message", None)
        detail = message() if callable(message) else str(message or "IBM job failed")
        raise RuntimeError(f"IBM Runtime job failed: {detail}")

    if runtime_job.cancelled():
        raise RuntimeError("IBM Runtime job was cancelled.")

    return runtime_job.result()
