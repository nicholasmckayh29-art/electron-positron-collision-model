"""Quantum sampling & verification package.

Phase: establish ground truth for resonance peaks (J/ψ, Z⁰, …) via hardware
calibration before True Quantum Simulation. See docs/planningCl.md and
docs/quantum_research.md.
"""

from services.quantum.distribution import build_mass_distribution, next_power_of_two
from services.quantum.encoding import BinaryQubitEncoder, MassDistributionEncoder
from services.quantum.estimation import estimate_observable_locally, estimate_observable_on_ibm
from services.quantum.observables import infer_mass_window_observable, observable_from_particle
from services.quantum.pipeline import (
    AdaptiveSnapshotVerificationPipeline,
    SnapshotVerificationPipeline,
    get_encoder,
)
from services.quantum.runtime_config import DEFAULT_SHOTS, get_runtime_status, real_backend_enabled
from services.quantum.types import QMCObservable, QuantumPhase

__all__ = [
    "BinaryQubitEncoder",
    "DEFAULT_SHOTS",
    "AdaptiveSnapshotVerificationPipeline",
    "MassDistributionEncoder",
    "QMCObservable",
    "QuantumPhase",
    "SnapshotVerificationPipeline",
    "build_mass_distribution",
    "estimate_observable_locally",
    "estimate_observable_on_ibm",
    "get_encoder",
    "get_runtime_status",
    "infer_mass_window_observable",
    "next_power_of_two",
    "observable_from_particle",
    "real_backend_enabled",
]
