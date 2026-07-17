"""Binary qubit amplitude encoding — baseline for quantum sampling verification."""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit

from services.quantum.encoding.base import MassDistributionEncoder


class BinaryQubitEncoder(MassDistributionEncoder):
    """Map $p_i$ to amplitudes $\\sqrt{p_i}$ on $\\lceil \\log_2 N \\rceil$ qubits."""

    kind = "binary_qubits"

    def required_dimension(self, bin_count: int) -> int:
        if bin_count < 1:
            raise ValueError("bin_count must be positive.")
        size = 1 << max(1, int(bin_count - 1).bit_length())
        return size

    def build_preparation_circuit(self, probabilities: np.ndarray) -> QuantumCircuit:
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
