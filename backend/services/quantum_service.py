"""Facade for quantum sampling & verification (backward-compatible imports).

Implementation lives under ``services.quantum`` — modular encoders, symmetry hooks,
and snapshot vs evolution pipelines. See docs/implementation_directives.md.
"""

from __future__ import annotations

import datetime as dt
import logging
import os

import numpy as np
from qiskit import QuantumCircuit

from services import job_store, session_store
from services.quantum.distribution import DEFAULT_BINS
from services.quantum.encoding import BinaryQubitEncoder
from services.quantum.estimation import estimate_observable_locally, estimate_observable_on_ibm
from services.quantum.databank import append_hardware_run, databank_enabled
from services.quantum.observables import infer_mass_window_observable
from services.quantum.pipeline import (
    AdaptiveSnapshotVerificationPipeline,
    SnapshotVerificationPipeline,
)
from services.quantum.runtime_config import DEFAULT_SHOTS, get_runtime_status, real_backend_enabled
from services.quantum.types import QMCObservable

logger = logging.getLogger(__name__)

_default_encoder = BinaryQubitEncoder()


def _next_power_of_two(value: int) -> int:
    from services.quantum.distribution import next_power_of_two

    return next_power_of_two(value)


def build_mass_distribution(data_set, observable, bins=DEFAULT_BINS):
    from services.quantum.distribution import build_mass_distribution as _build

    dist = _build(data_set, observable, bins)
    return dist.as_dict()


def build_qmc_circuit(probabilities: np.ndarray) -> QuantumCircuit:
    return _default_encoder.build_preparation_circuit(probabilities)


def _build_hardware_run_record(
    *,
    job_id: str,
    mode: str,
    particle_name: str | None,
    target_probability: float | None,
    mass_bins: int | None,
    max_iterations: int | None,
    epsilon: float | None,
    max_shots: int | None,
    max_bins: int | None,
    allow_backend_switch: bool | None,
    allow_symmetry_toggle: bool | None,
    result_payload: dict,
) -> dict:
    observable = result_payload.get("observable", {})
    verification = result_payload.get("verification", {})
    circuit = result_payload.get("circuit", {})
    encoding = result_payload.get("encoding", {})
    convergence = result_payload.get("convergence", {})
    return {
        "record_type": "quantum_hardware_run",
        "record_version": 1,
        "saved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "job_id": job_id,
        "mode": mode,
        "particle": particle_name or "auto",
        "control_config": {
            "target_probability": target_probability,
            "mass_bins": mass_bins,
            "max_iterations": max_iterations,
            "epsilon": epsilon,
            "max_shots": max_shots,
            "max_bins": max_bins,
            "allow_backend_switch": allow_backend_switch,
            "allow_symmetry_toggle": allow_symmetry_toggle,
        },
        "backend": result_payload.get("backend"),
        "runtime_job_id": result_payload.get("runtime_job_id"),
        "shots": result_payload.get("shots"),
        "estimate": result_payload.get("estimate"),
        "standard_error": result_payload.get("standard_error"),
        "good_counts": result_payload.get("good_counts"),
        "observable": observable,
        "ground_truth": {
            "exact_classical_probability": result_payload.get("exact_classical_probability"),
            "binned_classical_probability": result_payload.get("binned_classical_probability"),
            "discretization": result_payload.get("discretization"),
        },
        "verification": verification,
        "convergence": convergence,
        "iterations": result_payload.get("iterations", []),
        "circuit": {
            "qubits": circuit.get("qubits"),
            "depth": circuit.get("depth"),
            "ops": circuit.get("ops"),
            "bins": circuit.get("bins"),
            "distinct_bins_observed": circuit.get("distinct_bins_observed"),
            "top_histogram": circuit.get("top_histogram", []),
        },
        "encoding": encoding,
        "notes": result_payload.get("notes"),
    }


def run_quantum_job(
    job_id: str,
    particle_name: str | None = None,
    mode: str = "snapshot",
    target_probability: float | None = None,
    mass_bins: int | None = None,
    max_iterations: int | None = None,
    epsilon: float | None = None,
    max_shots: int | None = None,
    max_bins: int | None = None,
    allow_backend_switch: bool | None = None,
    allow_symmetry_toggle: bool | None = None,
) -> None:
    """Background worker: snapshot verification sampling job."""

    rec = job_store.get_job(job_id)
    if not rec:
        return

    data_set = session_store.session_data
    if not data_set:
        job_store.update_job(
            job_id,
            status="failed",
            error="No session data; upload a CSV first.",
        )
        return

    shots = DEFAULT_SHOTS
    processed = 0
    particle_label = particle_name or "auto"
    mode_label = (mode or "snapshot").strip().lower()

    try:
        job_store.update_job(
            job_id,
            status="running",
            message=(
                f"Preparing {mode_label} verification for resonance '{particle_label}'."
            ),
            total=shots,
        )

        if mode_label == "adaptive_snapshot":
            pipeline = AdaptiveSnapshotVerificationPipeline()
        else:
            pipeline = SnapshotVerificationPipeline()

        def ibm_status(status: str) -> None:
            job_store.update_job(
                job_id,
                status="running",
                message=f"IBM Runtime: {status}",
                total=shots,
            )

        if real_backend_enabled():
            from services.quantum.ibm_client import probe_ibm_runtime

            probe = probe_ibm_runtime()
            if not probe.get("ok"):
                hint = probe.get("hint", "")
                raise RuntimeError(
                    f"IBM Runtime not ready: {probe.get('error', 'unknown')}. {hint}".strip()
                )
            job_store.update_job(
                job_id,
                status="running",
                message="Connecting to IBM Quantum Runtime…",
                total=shots,
            )

        if mode_label == "adaptive_snapshot":
            policy_env = {}
            if max_shots is not None:
                policy_env["QMC_POLICY_MAX_SHOTS"] = str(int(max_shots))
            if max_bins is not None:
                policy_env["QMC_POLICY_MAX_BINS"] = str(int(max_bins))
            if allow_backend_switch is not None:
                policy_env["QMC_POLICY_ALLOW_BACKEND_SWITCH"] = (
                    "true" if allow_backend_switch else "false"
                )
            if allow_symmetry_toggle is not None:
                policy_env["QMC_POLICY_ALLOW_SYMMETRY_TOGGLE"] = (
                    "true" if allow_symmetry_toggle else "false"
                )
            previous = {k: os.environ.get(k) for k in policy_env}
            os.environ.update(policy_env)
            result = pipeline.run(
                data_set,
                shots=shots,
                bins=mass_bins,
                particle_name=particle_name,
                target_probability=target_probability,
                max_iterations=max_iterations or 20,
                epsilon=epsilon if epsilon is not None else 0.00001,
                status_callback=ibm_status if real_backend_enabled() else None,
            )
            for k, old in previous.items():
                if old is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old
            processed = int(sum(step.get("shots", 0) for step in result.iterations))
        else:
            result = pipeline.run(
                data_set,
                shots=shots,
                bins=mass_bins,
                particle_name=particle_name,
                status_callback=ibm_status if real_backend_enabled() else None,
            )
            processed = shots

        job_store.update_job(
            job_id,
            status="completed",
            message=f"Quantum {mode_label} verification complete.",
            processed=processed,
            total=max(shots, processed),
            result=result.to_job_payload(),
        )
        rec = job_store.get_job(job_id)
        result_payload = rec.result if rec else result.to_job_payload()
        if (
            result_payload.get("hardware_ready")
            and result_payload.get("runtime_job_id")
            and databank_enabled()
        ):
            record = _build_hardware_run_record(
                job_id=job_id,
                mode=mode_label,
                particle_name=particle_name,
                target_probability=target_probability,
                mass_bins=mass_bins,
                max_iterations=max_iterations,
                epsilon=epsilon,
                max_shots=max_shots,
                max_bins=max_bins,
                allow_backend_switch=allow_backend_switch,
                allow_symmetry_toggle=allow_symmetry_toggle,
                result_payload=result_payload,
            )
            db_path = append_hardware_run(record)
            result_payload["databank_recorded"] = True
            result_payload["databank_path"] = db_path
            job_store.update_job(job_id, result=result_payload)
    except Exception as exc:  # pragma: no cover
        logger.exception("Quantum sampling verification job failed")
        job_store.update_job(
            job_id,
            status="failed",
            error=str(exc),
            processed=processed,
            total=shots,
        )


__all__ = [
    "DEFAULT_BINS",
    "DEFAULT_SHOTS",
    "QMCObservable",
    "build_mass_distribution",
    "build_qmc_circuit",
    "estimate_observable_locally",
    "estimate_observable_on_ibm",
    "get_runtime_status",
    "infer_mass_window_observable",
    "real_backend_enabled",
    "run_quantum_job",
]
