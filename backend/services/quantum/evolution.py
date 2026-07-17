"""Hamiltonian evolution pipeline (future — True Quantum Simulation phase).

Snapshot mode prepares a fixed mass distribution. Evolution mode will apply
time dynamics from a collision Hamiltonian to resonance formation — see
docs/quantum_research.md (Hamiltonian formalism, arxiv 2508.03126v2).
"""

from __future__ import annotations

from typing import Any

from services.quantum.types import PipelineMode, QuantumPhase


class EvolutionPipeline:
    """Placeholder for Hamiltonian-based collision simulation."""

    mode = PipelineMode.EVOLUTION
    phase = QuantumPhase.SIMULATION

    def run(self, data_set: list[dict], **kwargs: Any) -> dict:
        raise NotImplementedError(
            "Hamiltonian evolution is part of the True Quantum Simulation phase. "
            "Use SnapshotVerificationPipeline for the current sampling-verification build."
        )
