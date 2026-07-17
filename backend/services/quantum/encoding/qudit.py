"""QuDit encoding placeholder for higher spectral resolution.

Not implemented in the sampling-verification phase. See docs/quantum_research.md
and planningCl.md (Binary Binning Validation → QuDit upgrade path).
"""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit

from services.quantum.encoding.base import MassDistributionEncoder


class QuditEncoder(MassDistributionEncoder):
    """Future: native qudit Hilbert spaces for truncated mass spectra."""

    kind = "qudit"

    def required_dimension(self, bin_count: int) -> int:
        raise NotImplementedError(
            "QuDit encoding is planned after binary 2^n baseline validation. "
            "See docs/quantum_research.md (2605.05841v1)."
        )

    def build_preparation_circuit(self, probabilities: np.ndarray) -> QuantumCircuit:
        raise NotImplementedError(
            "QuDit state preparation is not available in the sampling-verification phase."
        )
