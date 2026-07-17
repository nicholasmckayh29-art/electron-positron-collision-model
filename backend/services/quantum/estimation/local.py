"""Local statevector sampling — classical verification of the prepared distribution."""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

import os

from services.quantum.runtime_config import DEFAULT_SHOTS

RNG_SEED = int(os.environ.get("QMC_RNG_SEED", "2026"))


def estimate_observable_locally(
    circuit: QuantumCircuit, good_bins: np.ndarray, shots: int = DEFAULT_SHOTS
) -> dict:
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
    sampled_states = rng.choice(
        np.arange(probabilities.size), size=shots, p=probabilities, replace=True
    )
    unique_bins, counts = np.unique(sampled_states, return_counts=True)
    pairs = sorted(zip(unique_bins.tolist(), counts.tolist()), key=lambda kv: kv[1], reverse=True)
    top_hist = [
        {"bitstring": format(int(idx), f"0{circuit.num_qubits}b"), "bin_index": int(idx), "counts": int(ct)}
        for idx, ct in pairs[:12]
    ]

    return {
        "estimate": float(estimate),
        "good_counts": sampled_good,
        "shots": shots,
        "standard_error": stderr,
        "statevector_probability": good_probability,
        "top_histogram": top_hist,
        "distinct_bins_observed": int(unique_bins.size),
    }
