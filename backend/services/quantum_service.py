"""Quantum Monte Carlo-style observable estimation for collision datasets.

The implementation prepares a small amplitude-encoded distribution over
invariant-mass bins and estimates the probability of a selected resonance
window. It runs locally by default and can submit the same measured circuit to
IBM Quantum Runtime when ``USE_REAL_BACKEND=true`` is configured.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from services import job_store, session_store
from services.analysis import PARTICLE_WINDOWS

logger = logging.getLogger(__name__)

DEFAULT_SHOTS = int(os.environ.get("QMC_SHOTS", "4096"))
DEFAULT_BINS = int(os.environ.get("QMC_MASS_BINS", "32"))
RNG_SEED = int(os.environ.get("QMC_RNG_SEED", "2026"))
TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class QMCObservable:
    """Mass-window probability observable for a discretized event distribution."""

    name: str
    label: str
    mass_center: float
    low: float
    high: float


def _next_power_of_two(value: int) -> int:
    return 1 << max(1, int(value - 1).bit_length())


def infer_mass_window_observable(data_set: list[dict]) -> QMCObservable:
    """Choose the resonance window with the most matching uploaded events."""

    masses = np.array([float(row["M"]) for row in data_set if "M" in row], dtype=float)
    if masses.size == 0:
        raise ValueError("Uploaded data has no invariant mass column M.")

    best_particle = None
    best_count = -1
    for particle in PARTICLE_WINDOWS:
        low = float(particle["mass"]) - float(particle["width"])
        high = float(particle["mass"]) + float(particle["width"])
        count = int(np.count_nonzero((masses >= low) & (masses <= high)))
        if count > best_count:
            best_particle = particle
            best_count = count

    if best_particle and best_count > 0:
        mass = float(best_particle["mass"])
        width = float(best_particle["width"])
        return QMCObservable(
            name=f"{best_particle['name']}_mass_window",
            label=f"{best_particle['symbol']} mass-window probability",
            mass_center=mass,
            low=mass - width,
            high=mass + width,
        )

    mean = float(np.mean(masses))
    std = float(np.std(masses))
    half_width = std if std > 0 else max(abs(mean) * 0.05, 1.0)
    return QMCObservable(
        name="central_mass_window",
        label="Central mass-window probability",
        mass_center=mean,
        low=mean - half_width,
        high=mean + half_width,
    )


def build_mass_distribution(
    data_set: list[dict], observable: QMCObservable, bins: int = DEFAULT_BINS
) -> dict:
    """Discretize invariant mass values and mark bins overlapping the observable."""

    masses = np.array([float(row["M"]) for row in data_set if "M" in row], dtype=float)
    if masses.size == 0:
        raise ValueError("Uploaded data has no invariant mass values.")

    bin_count = _next_power_of_two(max(2, bins))
    counts, edges = np.histogram(masses, bins=bin_count)
    probabilities = counts.astype(float) / float(masses.size)
    bin_lows = edges[:-1]
    bin_highs = edges[1:]
    good_bins = np.where((bin_highs >= observable.low) & (bin_lows <= observable.high))[0]
    exact_good = (masses >= observable.low) & (masses <= observable.high)

    return {
        "masses": masses,
        "counts": counts,
        "edges": edges,
        "probabilities": probabilities,
        "good_bins": good_bins,
        "exact_probability": float(np.count_nonzero(exact_good) / masses.size),
        "binned_probability": float(np.sum(probabilities[good_bins])),
        "bin_count": bin_count,
    }


def build_qmc_circuit(probabilities: np.ndarray) -> QuantumCircuit:
    """Prepare sqrt(probability) amplitudes over mass bins."""

    probabilities = np.asarray(probabilities, dtype=float)
    if probabilities.ndim != 1 or probabilities.size == 0:
        raise ValueError("probabilities must be a non-empty 1D array.")
    if not np.isclose(float(np.sum(probabilities)), 1.0):
        raise ValueError("probabilities must sum to one.")

    num_qubits = int(np.log2(probabilities.size))
    if 2**num_qubits != probabilities.size:
        raise ValueError("probability vector length must be a power of two.")

    qc = QuantumCircuit(num_qubits, name="qmc_mass_distribution")
    qc.initialize(np.sqrt(probabilities), range(num_qubits))
    return qc


def estimate_observable_locally(
    circuit: QuantumCircuit, good_bins: np.ndarray, shots: int = DEFAULT_SHOTS
) -> dict:
    """Sample a prepared quantum distribution with a deterministic local simulator."""

    state = Statevector.from_instruction(circuit)
    probabilities = np.asarray(state.probabilities(), dtype=float)
    good = np.asarray(good_bins, dtype=int)
    if good.size == 0:
        good_probability = 0.0
    else:
        good_probability = float(np.sum(probabilities[good]))

    rng = np.random.default_rng(RNG_SEED)
    sampled_good = int(rng.binomial(shots, good_probability))
    estimate = sampled_good / float(shots)
    stderr = float(np.sqrt(max(estimate * (1.0 - estimate), 0.0) / shots))

    return {
        "estimate": float(estimate),
        "good_counts": sampled_good,
        "shots": shots,
        "standard_error": stderr,
        "statevector_probability": good_probability,
    }


def real_backend_enabled() -> bool:
    """Return whether quantum jobs should submit to IBM Runtime."""

    return os.environ.get("USE_REAL_BACKEND", "").lower() in TRUE_VALUES


def get_runtime_status() -> dict:
    """Report local IBM Runtime configuration without submitting any jobs."""

    try:
        import qiskit_ibm_runtime  # noqa: F401

        runtime_installed = True
    except ImportError:
        runtime_installed = False

    return {
        "real_backend_enabled": real_backend_enabled(),
        "runtime_installed": runtime_installed,
        "token_configured": bool(
            os.environ.get("IBM_QUANTUM_TOKEN") or os.environ.get("IBM_API_KEY")
        ),
        "instance_configured": bool(os.environ.get("IBM_QUANTUM_INSTANCE")),
        "channel": os.environ.get("IBM_QUANTUM_CHANNEL", "ibm_quantum_platform"),
        "requested_backend": os.environ.get("IBM_BACKEND") or None,
        "shots": DEFAULT_SHOTS,
        "mass_bins": DEFAULT_BINS,
    }


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
    requested_backend = os.environ.get("IBM_BACKEND")
    if requested_backend:
        return service.backend(requested_backend)

    try:
        candidates = service.backends(
            simulator=False,
            operational=True,
            min_num_qubits=min_qubits,
        )
    except TypeError:
        candidates = []
        for backend in service.backends():
            if getattr(backend, "simulator", False):
                continue
            if _backend_num_qubits(backend) >= min_qubits:
                candidates.append(backend)

    if not candidates:
        raise RuntimeError(f"No operational IBM backends with >= {min_qubits} qubits.")

    return min(
        candidates,
        key=lambda backend: (_backend_pending_jobs(backend), _backend_num_qubits(backend)),
    )


def _sampler_counts(result) -> dict[str, int]:
    """Extract counts from Runtime SamplerV2 results across minor API variants."""

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


def estimate_observable_on_ibm(
    circuit: QuantumCircuit, good_bins: np.ndarray, shots: int = DEFAULT_SHOTS
) -> dict:
    """Submit the measured QMC circuit to IBM Runtime SamplerV2."""

    try:
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
    except ImportError as exc:
        raise RuntimeError(
            "qiskit-ibm-runtime is required for USE_REAL_BACKEND=true. "
            "Run pip install -r backend/requirements.txt."
        ) from exc

    service_kwargs = {
        "channel": os.environ.get("IBM_QUANTUM_CHANNEL", "ibm_quantum_platform"),
    }
    token = os.environ.get("IBM_QUANTUM_TOKEN") or os.environ.get("IBM_API_KEY")
    instance = os.environ.get("IBM_QUANTUM_INSTANCE")
    if token:
        service_kwargs["token"] = token
    if instance:
        service_kwargs["instance"] = instance

    service = QiskitRuntimeService(**service_kwargs)
    measured_circuit = circuit.measure_all(inplace=False)
    backend = _select_ibm_backend(service, measured_circuit.num_qubits)
    pass_manager = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pass_manager.run(measured_circuit)

    sampler = Sampler(mode=backend)
    runtime_job = sampler.run([isa_circuit], shots=shots)
    counts = _sampler_counts(runtime_job.result())

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
        "backend": _backend_name(backend),
        "runtime_job_id": runtime_job.job_id(),
        "transpiled_depth": isa_circuit.depth(),
        "transpiled_ops": dict(isa_circuit.count_ops()),
    }


def run_quantum_job(job_id: str) -> None:
    """Background worker: estimate a QMC mass-window observable."""

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

    try:
        job_store.update_job(
            job_id,
            status="running",
            message="Preparing QMC mass-window observable.",
            total=shots,
        )

        observable = infer_mass_window_observable(data_set)
        distribution = build_mass_distribution(data_set, observable, DEFAULT_BINS)
        circuit = build_qmc_circuit(distribution["probabilities"])

        if real_backend_enabled():
            job_store.update_job(
                job_id,
                status="running",
                message="Submitting QMC circuit to IBM Quantum Runtime.",
                total=shots,
            )
            estimate = estimate_observable_on_ibm(circuit, distribution["good_bins"], shots)
            backend_name = estimate["backend"]
            hardware_ready = True
            runtime_job_id = estimate["runtime_job_id"]
        else:
            estimate = estimate_observable_locally(circuit, distribution["good_bins"], shots)
            backend_name = "local_statevector_sampler"
            hardware_ready = False
            runtime_job_id = None
        processed = shots

        decomposed = circuit.decompose(reps=5)
        result = {
            "method": "qmc_mass_window_probability",
            "backend": backend_name,
            "hardware_ready": hardware_ready,
            "runtime_job_id": runtime_job_id,
            "observable": {
                "name": observable.name,
                "label": observable.label,
                "mass_center": observable.mass_center,
                "low": observable.low,
                "high": observable.high,
            },
            "estimate": estimate["estimate"],
            "standard_error": estimate["standard_error"],
            "good_counts": estimate["good_counts"],
            "shots": estimate["shots"],
            "exact_classical_probability": distribution["exact_probability"],
            "binned_classical_probability": distribution["binned_probability"],
            "statevector_probability": estimate.get("statevector_probability"),
            "discretization": {
                "mass_bins": distribution["bin_count"],
                "good_bins": distribution["good_bins"].astype(int).tolist(),
                "mass_min": float(distribution["edges"][0]),
                "mass_max": float(distribution["edges"][-1]),
            },
            "circuit": {
                "qubits": circuit.num_qubits,
                "depth": estimate.get("transpiled_depth", decomposed.depth()),
                "ops": estimate.get("transpiled_ops", dict(decomposed.count_ops())),
            },
            "notes": (
                "Prototype QMC/QAE-style observable estimation. This sampling job "
                "does not yet claim quadratic speedup or Hamiltonian replay."
            ),
        }

        job_store.update_job(
            job_id,
            status="completed",
            message="QMC observable estimation complete.",
            processed=processed,
            total=shots,
            result=result,
        )
    except Exception as exc:  # pragma: no cover - hardware / qiskit failures
        logger.exception("QMC quantum job failed")
        job_store.update_job(
            job_id,
            status="failed",
            error=str(exc),
            processed=processed,
            total=shots,
        )
