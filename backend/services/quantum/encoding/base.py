"""Pluggable state encodings for invariant-mass distributions.

Current phase uses binary qubits ($2^n$ bins). Future QuDit encodings should
implement the same interface — see docs/quantum_research.md (arxiv 2605.05841).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from qiskit import QuantumCircuit


class MassDistributionEncoder(ABC):
    """Prepare a quantum state from a normalized bin probability vector."""

    kind: str

    @abstractmethod
    def required_dimension(self, bin_count: int) -> int:
        """Hilbert-space dimension required for ``bin_count`` histogram bins."""

    @abstractmethod
    def build_preparation_circuit(self, probabilities: np.ndarray) -> QuantumCircuit:
        """Return a circuit that prepares amplitudes from ``probabilities``."""
