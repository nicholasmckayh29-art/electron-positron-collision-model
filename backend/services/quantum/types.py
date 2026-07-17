"""Shared types for the quantum sampling & verification pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class QuantumPhase(str, Enum):
    """Project phase — see docs/planningCl.md."""

    SAMPLING_VERIFICATION = "quantum_sampling_verification"
    SIMULATION = "true_quantum_simulation"


class PipelineMode(str, Enum):
    """Snapshot = fixed distribution (current). Movie = Hamiltonian evolution (future)."""

    SNAPSHOT = "snapshot"
    ADAPTIVE_SNAPSHOT = "adaptive_snapshot"
    POLICY_ADAPTIVE_SNAPSHOT = "policy_adaptive_snapshot"
    EVOLUTION = "evolution"


@dataclass(frozen=True)
class QMCObservable:
    """Mass-window probability observable for a discretized event distribution."""

    name: str
    label: str
    mass_center: float
    low: float
    high: float


@dataclass
class MassDistribution:
    """Classical ground-truth and binned representation of invariant-mass data."""

    masses: np.ndarray
    counts: np.ndarray
    edges: np.ndarray
    probabilities: np.ndarray
    good_bins: np.ndarray
    exact_probability: float
    binned_probability: float
    bin_count: int
    encoding_dimension: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "masses": self.masses,
            "counts": self.counts,
            "edges": self.edges,
            "probabilities": self.probabilities,
            "good_bins": self.good_bins,
            "exact_probability": self.exact_probability,
            "binned_probability": self.binned_probability,
            "bin_count": self.bin_count,
        }


@dataclass
class GroundTruthReport:
    """Classical reference used to verify quantum sampling against peaks."""

    observable: QMCObservable
    exact_probability: float
    binned_probability: float
    bin_count: int
    good_bins: list[int]
    mass_range: tuple[float, float]
    phase: QuantumPhase = QuantumPhase.SAMPLING_VERIFICATION

    def as_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "observable": {
                "name": self.observable.name,
                "label": self.observable.label,
                "mass_center": self.observable.mass_center,
                "low": self.observable.low,
                "high": self.observable.high,
            },
            "exact_classical_probability": self.exact_probability,
            "binned_classical_probability": self.binned_probability,
            "discretization": {
                "mass_bins": self.bin_count,
                "good_bins": self.good_bins,
                "mass_min": self.mass_range[0],
                "mass_max": self.mass_range[1],
            },
        }


@dataclass
class SamplingJobResult:
    """Output of the snapshot verification pipeline (extensible for evolution jobs)."""

    method: str
    pipeline_mode: PipelineMode
    phase: QuantumPhase
    ground_truth: GroundTruthReport
    estimate: float
    standard_error: float
    good_counts: int
    shots: int
    backend: str
    hardware_ready: bool
    runtime_job_id: str | None
    circuit_metadata: dict[str, Any]
    statevector_probability: float | None = None
    symmetry_protection: str = "none"
    encoding_kind: str = "binary_qubits"
    notes: str = ""
    iterations: list[dict[str, Any]] = field(default_factory=list)
    convergence: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def verification_metrics(self) -> dict[str, Any]:
        exact = self.ground_truth.exact_probability
        binned = self.ground_truth.binned_probability
        q = self.estimate
        stderr = self.standard_error
        vs_exact = float(q - exact)
        vs_binned = float(q - binned)
        return {
            "discretization_error": float(binned - exact),
            "quantum_vs_exact": vs_exact,
            "quantum_vs_binned": vs_binned,
            "quantum_vs_exact_sigma": (
                float(abs(vs_exact) / stderr) if stderr > 0 else None
            ),
            "within_2sigma_of_exact": (
                bool(abs(vs_exact) <= 2.0 * stderr) if stderr > 0 else None
            ),
        }

    def to_job_payload(self) -> dict[str, Any]:
        payload = {
            "method": self.method,
            "pipeline_mode": self.pipeline_mode.value,
            "phase": self.phase.value,
            "backend": self.backend,
            "hardware_ready": self.hardware_ready,
            "runtime_job_id": self.runtime_job_id,
            "observable": self.ground_truth.as_dict()["observable"],
            "estimate": self.estimate,
            "standard_error": self.standard_error,
            "good_counts": self.good_counts,
            "shots": self.shots,
            "exact_classical_probability": self.ground_truth.exact_probability,
            "binned_classical_probability": self.ground_truth.binned_probability,
            "statevector_probability": self.statevector_probability,
            "discretization": self.ground_truth.as_dict()["discretization"],
            "verification": self.verification_metrics(),
            "circuit": self.circuit_metadata,
            "encoding": {
                "kind": self.encoding_kind,
                "symmetry_protection": self.symmetry_protection,
            },
            "ground_truth": self.ground_truth.as_dict(),
            "notes": self.notes,
        }
        if self.iterations:
            payload["iterations"] = self.iterations
        if self.convergence:
            payload["convergence"] = self.convergence
        payload.update(self.extra)
        return payload
