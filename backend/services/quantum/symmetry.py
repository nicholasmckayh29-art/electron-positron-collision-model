"""Symmetry-protected error mitigation hooks for IBM Runtime sampling.

Passive symmetry protection (Floquet / emergent hierarchical symmetries) is a
research target — see docs/quantum_research.md (arxiv 2604.11085v1).

The sampling-verification phase applies an identity hook so Runtime integration
stays stable while a real protection layer can be swapped in later.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qiskit import QuantumCircuit

TRUE_VALUES = {"1", "true", "yes", "on"}


def symmetry_protection_enabled() -> bool:
    return os.environ.get("QMC_SYMMETRY_PROTECTION", "").lower() in TRUE_VALUES


def apply_symmetry_protection(
    circuit: QuantumCircuit, force_enabled: bool | None = None
) -> tuple[QuantumCircuit, str]:
    """Optional pre-measurement circuit transform for noise resilience.

    Returns:
        (possibly modified circuit, protection label for job metadata)
    """
    enabled = symmetry_protection_enabled() if force_enabled is None else bool(force_enabled)
    if not enabled:
        return circuit, "none"

    # Placeholder: future Floquet / symmetry-enforcing layers before measurement.
    return circuit, "symmetry_protected_stub"
