"""Orchestration for quantum sampling & verification (snapshot + adaptive loop)."""

from __future__ import annotations

import os

from services.quantum.distribution import DEFAULT_BINS, build_mass_distribution
from services.quantum.encoding import BinaryQubitEncoder, MassDistributionEncoder, QuditEncoder
from services.quantum.estimation import estimate_observable_locally, estimate_observable_on_ibm
from services.quantum.ibm_client import StatusCallback
from services.quantum.observables import infer_mass_window_observable, observable_from_particle
from services.quantum.policy import AdaptivePolicyController
from services.quantum.runtime_config import DEFAULT_SHOTS, real_backend_enabled
from services.quantum.symmetry import apply_symmetry_protection
from services.quantum.types import (
    GroundTruthReport,
    PipelineMode,
    QuantumPhase,
    SamplingJobResult,
)


DEFAULT_ADAPTIVE_MAX_ITERATIONS = int(os.environ.get("QMC_ADAPTIVE_MAX_ITERATIONS", "20"))
DEFAULT_ADAPTIVE_EPSILON = float(os.environ.get("QMC_ADAPTIVE_EPSILON", "0.00001"))
DEFAULT_ADAPTIVE_MIN_SHOTS = int(os.environ.get("QMC_ADAPTIVE_MIN_SHOTS", "1024"))
DEFAULT_ADAPTIVE_MAX_SHOTS = int(os.environ.get("QMC_ADAPTIVE_MAX_SHOTS", "16384"))


def get_encoder() -> MassDistributionEncoder:
    kind = os.environ.get("QMC_ENCODING", "binary_qubits").lower()
    if kind == "qudit":
        return QuditEncoder()
    return BinaryQubitEncoder()


def resolve_observable(data_set: list[dict], particle_name: str | None = None):
    """Pick resonance window from request, env override, or data-driven inference."""

    chosen = (particle_name or "").strip() or os.environ.get(
        "QMC_OBSERVABLE_PARTICLE", ""
    ).strip()
    if chosen and chosen.lower() != "auto":
        return observable_from_particle(chosen)
    return infer_mass_window_observable(data_set)


def classical_ground_truth(
    data_set: list[dict],
    particle_name: str | None = None,
    bins: int | None = None,
) -> dict:
    """Classical exact vs binned baselines without running a quantum job."""

    mass_bins = int(os.environ.get("QMC_MASS_BINS", str(bins or DEFAULT_BINS)))
    observable = resolve_observable(data_set, particle_name)
    distribution = build_mass_distribution(data_set, observable, mass_bins)
    exact = distribution.exact_probability
    binned = distribution.binned_probability
    return {
        "observable": {
            "name": observable.name,
            "label": observable.label,
            "mass_center": observable.mass_center,
            "low": observable.low,
            "high": observable.high,
        },
        "exact_classical_probability": exact,
        "binned_classical_probability": binned,
        "discretization_error": float(binned - exact),
        "discretization_error_abs": float(abs(binned - exact)),
        "bin_count": distribution.bin_count,
        "mass_range": [
            float(distribution.edges[0]),
            float(distribution.edges[-1]),
        ],
        "good_bins": distribution.good_bins.astype(int).tolist(),
        "event_count": int(distribution.masses.size),
    }


class SnapshotVerificationPipeline:
    """Snapshot: amplitude-encoded mass distribution → sample window probability."""

    mode = PipelineMode.SNAPSHOT
    phase = QuantumPhase.SAMPLING_VERIFICATION

    def run(
        self,
        data_set: list[dict],
        shots: int = DEFAULT_SHOTS,
        bins: int | None = None,
        particle_name: str | None = None,
        status_callback: StatusCallback | None = None,
    ) -> SamplingJobResult:
        mass_bins = int(os.environ.get("QMC_MASS_BINS", str(bins or DEFAULT_BINS)))
        observable = resolve_observable(data_set, particle_name)
        distribution = build_mass_distribution(data_set, observable, mass_bins)

        encoder = get_encoder()
        circuit = encoder.build_preparation_circuit(distribution.probabilities)
        circuit, symmetry_label = apply_symmetry_protection(circuit)

        if real_backend_enabled():
            estimate = estimate_observable_on_ibm(
                circuit,
                distribution.good_bins,
                shots,
                status_callback=status_callback,
            )
            backend_name = estimate["backend"]
            hardware_ready = True
            runtime_job_id = estimate["runtime_job_id"]
        else:
            estimate = estimate_observable_locally(circuit, distribution.good_bins, shots)
            backend_name = "local_statevector_sampler"
            hardware_ready = False
            runtime_job_id = None

        decomposed = circuit.decompose(reps=5)
        ground_truth = GroundTruthReport(
            observable=observable,
            exact_probability=distribution.exact_probability,
            binned_probability=distribution.binned_probability,
            bin_count=distribution.bin_count,
            good_bins=distribution.good_bins.astype(int).tolist(),
            mass_range=(
                float(distribution.edges[0]),
                float(distribution.edges[-1]),
            ),
            phase=self.phase,
        )

        return SamplingJobResult(
            method="qmc_mass_window_probability",
            pipeline_mode=self.mode,
            phase=self.phase,
            ground_truth=ground_truth,
            estimate=estimate["estimate"],
            standard_error=estimate["standard_error"],
            good_counts=estimate["good_counts"],
            shots=estimate["shots"],
            backend=backend_name,
            hardware_ready=hardware_ready,
            runtime_job_id=runtime_job_id,
            statevector_probability=estimate.get("statevector_probability"),
            symmetry_protection=symmetry_label,
            encoding_kind=encoder.kind,
            circuit_metadata={
                "qubits": circuit.num_qubits,
                "depth": estimate.get("transpiled_depth", decomposed.depth()),
                "ops": estimate.get("transpiled_ops", dict(decomposed.count_ops())),
            },
            notes=(
                "Quantum sampling & verification: statistical sampler checks a resonance "
                "mass-window against exact and binned classical ground truth. "
                "Hamiltonian evolution (movie) is deferred to the simulation phase."
            ),
        )


class AdaptiveSnapshotVerificationPipeline:
    """Policy-driven multi-knob adaptive loop over verification jobs."""

    mode = PipelineMode.POLICY_ADAPTIVE_SNAPSHOT
    phase = QuantumPhase.SAMPLING_VERIFICATION

    def _resolve_target_probability(
        self, distribution, target_probability: float | None
    ) -> float:
        if target_probability is None:
            return float(distribution.exact_probability)
        return float(max(0.0, min(1.0, target_probability)))

    def run(
        self,
        data_set: list[dict],
        shots: int = DEFAULT_SHOTS,
        bins: int | None = None,
        particle_name: str | None = None,
        target_probability: float | None = None,
        max_iterations: int = DEFAULT_ADAPTIVE_MAX_ITERATIONS,
        epsilon: float = DEFAULT_ADAPTIVE_EPSILON,
        min_shots: int = DEFAULT_ADAPTIVE_MIN_SHOTS,
        max_shots: int = DEFAULT_ADAPTIVE_MAX_SHOTS,
        status_callback: StatusCallback | None = None,
    ) -> SamplingJobResult:
        observable = resolve_observable(data_set, particle_name)
        mass_bins = int(os.environ.get("QMC_MASS_BINS", str(bins or DEFAULT_BINS)))
        controller = AdaptivePolicyController()
        target: float | None = None

        encoder = get_encoder()
        use_real_backend = real_backend_enabled()

        if max_iterations < 1:
            max_iterations = 1
        epsilon = max(1e-6, float(epsilon))
        min_shots = max(32, int(min_shots))
        max_shots = max(min_shots, int(max_shots))
        current_shots = max(min_shots, min(max_shots, int(shots)))
        current_bins = mass_bins
        current_symmetry = bool(os.environ.get("QMC_SYMMETRY_PROTECTION", "").lower() == "true")
        current_backend = os.environ.get("IBM_BACKEND") or None

        iterations: list[dict] = []
        final_estimate: dict | None = None
        backend_name = "local_statevector_sampler"
        hardware_ready = False
        runtime_job_id: str | None = None
        stopping_reason = "max_iterations"
        converged = False
        recent_errors: list[float] = []
        final_distribution = None
        final_observable = observable
        final_encoding_kind = encoder.kind
        final_symmetry_label = "none"
        final_circuit = None

        for i in range(1, max_iterations + 1):
            if status_callback:
                status_callback(f"ADAPTIVE_ITERATION:{i}/{max_iterations}")

            if current_backend:
                os.environ["IBM_BACKEND"] = current_backend
            else:
                os.environ.pop("IBM_BACKEND", None)

            distribution = build_mass_distribution(data_set, observable, current_bins)
            if target is None:
                target = self._resolve_target_probability(distribution, target_probability)
            circuit = encoder.build_preparation_circuit(distribution.probabilities)
            circuit, symmetry_label = apply_symmetry_protection(
                circuit, force_enabled=current_symmetry
            )
            final_distribution = distribution
            final_circuit = circuit
            final_symmetry_label = symmetry_label

            if use_real_backend:
                estimate = estimate_observable_on_ibm(
                    circuit,
                    distribution.good_bins,
                    current_shots,
                    status_callback=status_callback,
                )
                backend_name = estimate["backend"]
                hardware_ready = True
                runtime_job_id = estimate["runtime_job_id"]
            else:
                estimate = estimate_observable_locally(
                    circuit, distribution.good_bins, current_shots
                )
                backend_name = "local_statevector_sampler"
                hardware_ready = False
                runtime_job_id = None

            err = float(estimate["estimate"] - target)
            err_abs = float(abs(err))
            recent_errors.append(err_abs)
            sigma = (
                float(err_abs / estimate["standard_error"])
                if estimate["standard_error"] > 0
                else None
            )
            predicted_bias = controller.bias_model.predict_bias(
                backend=backend_name,
                encoding=encoder.kind,
                qubits=int(circuit.num_qubits),
            )
            corrected = controller.corrected_estimate(
                float(estimate["estimate"]), predicted_bias
            )
            corrected_err = float(corrected - target)
            corrected_err_abs = float(abs(corrected_err))

            action = controller.choose_action(
                iteration=i,
                max_iterations=max_iterations,
                error_abs=corrected_err_abs,
                epsilon=epsilon,
                current_shots=current_shots,
                current_bins=current_bins,
                circuit_depth=estimate.get("transpiled_depth", circuit.depth()),
                circuit_qubits=circuit.num_qubits,
                current_backend=backend_name,
                current_symmetry=current_symmetry,
                recent_errors=recent_errors,
            )
            should_stop, reason = controller.should_stop(
                iteration=i,
                max_iterations=max_iterations,
                error_abs=corrected_err_abs,
                epsilon=epsilon,
                expected_gain=action.expected_gain,
                estimated_cost=action.estimated_cost,
            )

            iteration_payload = {
                "iteration": i,
                "shots": int(estimate["shots"]),
                "bins": int(current_bins),
                "estimate": float(estimate["estimate"]),
                "standard_error": float(estimate["standard_error"]),
                "good_counts": int(estimate["good_counts"]),
                "target_probability": target,
                "error_to_target": err,
                "error_abs": err_abs,
                "error_sigma": sigma,
                "bias_prediction": predicted_bias,
                "estimate_corrected": corrected,
                "error_to_target_corrected": corrected_err,
                "error_abs_corrected": corrected_err_abs,
                "policy_action": {
                    "shots_next": action.shots,
                    "bins_next": action.bins,
                    "use_symmetry_next": action.use_symmetry,
                    "backend_next": action.backend,
                    "expected_gain": action.expected_gain,
                    "estimated_cost": action.estimated_cost,
                    "reason": action.reason,
                },
                "top_histogram": estimate.get("top_histogram", []),
                "distinct_bins_observed": estimate.get("distinct_bins_observed"),
            }
            iterations.append(iteration_payload)
            final_estimate = estimate

            if should_stop:
                converged = reason == "epsilon_met"
                stopping_reason = reason
                break

            current_shots = max(min_shots, min(max_shots, int(action.shots)))
            current_bins = max(2, int(action.bins))
            current_symmetry = bool(action.use_symmetry)
            current_backend = action.backend

        if final_estimate is None:
            raise RuntimeError("Adaptive snapshot pipeline produced no estimates.")
        if final_distribution is None or final_circuit is None:
            raise RuntimeError("Adaptive snapshot pipeline missing final distribution/circuit.")

        decomposed = final_circuit.decompose(reps=5)
        ground_truth = GroundTruthReport(
            observable=final_observable,
            exact_probability=final_distribution.exact_probability,
            binned_probability=final_distribution.binned_probability,
            bin_count=final_distribution.bin_count,
            good_bins=final_distribution.good_bins.astype(int).tolist(),
            mass_range=(
                float(final_distribution.edges[0]),
                float(final_distribution.edges[-1]),
            ),
            phase=self.phase,
        )
        final_bias = controller.bias_model.predict_bias(
            backend=backend_name,
            encoding=encoder.kind,
            qubits=int(final_circuit.num_qubits),
        )
        final_corrected = controller.corrected_estimate(
            float(final_estimate["estimate"]), final_bias
        )
        final_error = float(final_estimate["estimate"] - target)
        final_error_corrected = float(final_corrected - target)
        convergence = {
            "converged": converged,
            "stopping_reason": stopping_reason,
            "iterations_run": len(iterations),
            "max_iterations": int(max_iterations),
            "target_probability": target,
            "epsilon": epsilon,
            "final_error": final_error,
            "final_error_abs": float(abs(final_error)),
            "final_bias_prediction": final_bias,
            "final_estimate_corrected": final_corrected,
            "final_error_corrected": final_error_corrected,
            "final_error_abs_corrected": float(abs(final_error_corrected)),
        }

        return SamplingJobResult(
            method="qmc_mass_window_probability_adaptive",
            pipeline_mode=self.mode,
            phase=self.phase,
            ground_truth=ground_truth,
            estimate=final_estimate["estimate"],
            standard_error=final_estimate["standard_error"],
            good_counts=final_estimate["good_counts"],
            shots=final_estimate["shots"],
            backend=backend_name,
            hardware_ready=hardware_ready,
            runtime_job_id=runtime_job_id,
            statevector_probability=final_estimate.get("statevector_probability"),
            symmetry_protection=final_symmetry_label,
            encoding_kind=final_encoding_kind,
            iterations=iterations,
            convergence=convergence,
            circuit_metadata={
                "qubits": final_circuit.num_qubits,
                "depth": final_estimate.get("transpiled_depth", decomposed.depth()),
                "ops": final_estimate.get("transpiled_ops", dict(decomposed.count_ops())),
                "bins": int(final_distribution.bin_count),
                "distinct_bins_observed": final_estimate.get("distinct_bins_observed"),
                "top_histogram": final_estimate.get("top_histogram", []),
            },
            notes=(
                "Policy-adaptive verification: learns historical bias and chooses multi-knob "
                "actions (shots, bins, symmetry, backend) each iteration. Stops based on "
                "epsilon and cost-vs-expected-gain economics."
            ),
        )
