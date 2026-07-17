"""IBM Quantum Runtime SamplerV2 execution for verification sampling."""

from __future__ import annotations

import logging

import numpy as np
from qiskit import QuantumCircuit

from services.quantum.ibm_client import (
    StatusCallback,
    create_runtime_service,
    wait_for_runtime_result,
)
from services.quantum.runtime_config import DEFAULT_SHOTS

logger = logging.getLogger(__name__)


def _backend_name(backend) -> str:
    name = getattr(backend, "name", None)
    return name() if callable(name) else str(name)


def _backend_num_qubits(backend) -> int:
    value = getattr(backend, "num_qubits", None)
    if value is not None:
        return int(value)
    configuration = getattr(backend, "configuration", None)
    if callable(configuration):
        return int(configuration().num_qubits)
    return 0


def _backend_pending_jobs(backend) -> int:
    status = getattr(backend, "status", None)
    if not callable(status):
        return 999_999
    try:
        return int(getattr(status(), "pending_jobs", 999_999))
    except Exception:
        return 999_999


def _select_ibm_backend(service, min_qubits: int):
    import os

    requested_backend = os.environ.get("IBM_BACKEND")
    if requested_backend:
        return service.backend(requested_backend)

    from services.quantum.ibm_client import _list_hardware_backends

    candidates = _list_hardware_backends(service, min_qubits)
    if not candidates:
        raise RuntimeError(
            f"No operational IBM hardware backends with >= {min_qubits} qubits. "
            "Set IBM_BACKEND to a system listed in the IBM Quantum Platform, "
            "or configure IBM_QUANTUM_INSTANCE to an instance with hardware access."
        )

    return min(
        candidates,
        key=lambda backend: (_backend_pending_jobs(backend), _backend_num_qubits(backend)),
    )


def _sampler_counts(result) -> dict[str, int]:
    pub_result = result[0]
    data = getattr(pub_result, "data", None)
    if data is not None:
        for register_name in ("meas", "c", "cr", "creg"):
            register = getattr(data, register_name, None)
            if register is not None and hasattr(register, "get_counts"):
                return register.get_counts()
        if hasattr(data, "items"):
            for _, register in data.items():
                if hasattr(register, "get_counts"):
                    return register.get_counts()

    quasi_dists = getattr(result, "quasi_dists", None)
    if quasi_dists:
        return {format(int(k), "b"): int(round(v)) for k, v in quasi_dists[0].items()}

    raise RuntimeError(
        "Could not read measurement counts from IBM Runtime Sampler result."
    )


def _top_histogram_entries(counts: dict[str, int], top_n: int = 12) -> list[dict[str, int]]:
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    payload = []
    for bitstring, count in ranked:
        normalized = str(bitstring).replace(" ", "")
        payload.append(
            {
                "bitstring": normalized,
                "bin_index": int(normalized, 2),
                "counts": int(count),
            }
        )
    return payload


def estimate_observable_on_ibm(
    circuit: QuantumCircuit,
    good_bins: np.ndarray,
    shots: int = DEFAULT_SHOTS,
    status_callback: StatusCallback | None = None,
) -> dict:
    try:
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        from qiskit_ibm_runtime import SamplerV2 as Sampler
    except ImportError as exc:
        raise RuntimeError(
            "qiskit-ibm-runtime is required for USE_REAL_BACKEND=true. "
            "Run pip install -r backend/requirements.txt."
        ) from exc

    if status_callback:
        status_callback("CONNECTING")

    service = create_runtime_service()
    measured_circuit = circuit.measure_all(inplace=False)
    backend = _select_ibm_backend(service, measured_circuit.num_qubits)
    backend_label = _backend_name(backend)

    if status_callback:
        status_callback(f"TRANSPILING:{backend_label}")

    pass_manager = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pass_manager.run(measured_circuit)

    if status_callback:
        status_callback(f"SUBMITTING:{backend_label}")

    sampler = Sampler(mode=backend)
    runtime_job = sampler.run([isa_circuit], shots=shots)
    ibm_job_id = runtime_job.job_id()
    logger.info("Submitted IBM Runtime sampler job %s on %s", ibm_job_id, backend_label)

    if status_callback:
        status_callback(f"QUEUED:{ibm_job_id}")

    result = wait_for_runtime_result(runtime_job, on_status=status_callback)
    counts = _sampler_counts(result)

    good = {int(bin_index) for bin_index in np.asarray(good_bins, dtype=int)}
    good_counts = 0
    total_counts = 0
    for bitstring, count in counts.items():
        normalized = str(bitstring).replace(" ", "")
        bin_index = int(normalized, 2)
        total_counts += int(count)
        if bin_index in good:
            good_counts += int(count)

    if total_counts == 0:
        raise RuntimeError("IBM Runtime Sampler returned zero measurement counts.")

    estimate = good_counts / float(total_counts)
    stderr = float(np.sqrt(max(estimate * (1.0 - estimate), 0.0) / total_counts))

    return {
        "estimate": float(estimate),
        "good_counts": good_counts,
        "shots": total_counts,
        "standard_error": stderr,
        "backend": backend_label,
        "runtime_job_id": ibm_job_id,
        "transpiled_depth": isa_circuit.depth(),
        "transpiled_ops": dict(isa_circuit.count_ops()),
        "top_histogram": _top_histogram_entries(counts, top_n=12),
        "distinct_bins_observed": int(len(counts)),
    }
