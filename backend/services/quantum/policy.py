"""Policy controller for multi-knob adaptive quantum verification.

This module upgrades the adaptive controller from a shot-only thermostat into a
policy engine that can:
1) estimate backend/encoding/circuit bias from historical runs,
2) choose actions across multiple knobs (shots, bins, symmetry, backend),
3) stop based on expected gain vs runtime credit cost.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from services.quantum.databank import load_hardware_records

TRUE_VALUES = {"1", "true", "yes", "on"}


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        if value is None:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


@dataclass
class PolicyAction:
    """Action for one adaptive iteration."""

    shots: int
    bins: int
    use_symmetry: bool
    backend: str | None
    expected_gain: float
    estimated_cost: float
    reason: str


class BiasModel:
    """Simple historical bias model from local hardware databank."""

    def __init__(self):
        self._records = load_hardware_records()

    def predict_bias(self, *, backend: str, encoding: str, qubits: int) -> float:
        """Predict signed bias estimate - exact from similar historical runs."""
        if not self._records:
            return 0.0
        candidates = []
        for rec in self._records:
            rec_backend = rec.get("backend")
            rec_encoding = rec.get("encoding", {}).get("kind")
            if rec_backend != backend:
                continue
            if rec_encoding != encoding:
                continue
            rec_qubits = _safe_float(rec.get("circuit", {}).get("qubits"), fallback=0.0)
            if qubits and rec_qubits and abs(rec_qubits - qubits) > 2:
                continue
            q = _safe_float(rec.get("estimate"))
            exact = _safe_float(rec.get("ground_truth", {}).get("exact_classical_probability"))
            candidates.append(q - exact)
        if not candidates:
            return 0.0
        return float(sum(candidates) / len(candidates))


class RuntimeCostModel:
    """Heuristic runtime credit cost estimator."""

    def __init__(self):
        self.cost_per_shot = float(os.environ.get("QMC_COST_PER_SHOT", "0.00001"))
        self.cost_per_depth = float(os.environ.get("QMC_COST_PER_DEPTH", "0.001"))
        self.cost_per_qubit = float(os.environ.get("QMC_COST_PER_QUBIT", "0.01"))

    def estimate(self, *, shots: int, depth: int, qubits: int) -> float:
        return (
            self.cost_per_shot * max(0, shots)
            + self.cost_per_depth * max(0, depth)
            + self.cost_per_qubit * max(0, qubits)
        )


class AdaptivePolicyController:
    """Policy-based multi-knob controller for adaptive snapshot jobs."""

    def __init__(self):
        self.min_shots = int(os.environ.get("QMC_POLICY_MIN_SHOTS", "1024"))
        self.max_shots = int(os.environ.get("QMC_POLICY_MAX_SHOTS", "65536"))
        self.max_bins = int(os.environ.get("QMC_POLICY_MAX_BINS", "256"))
        self.min_expected_gain = float(os.environ.get("QMC_POLICY_MIN_GAIN", "0.0005"))
        self.max_cost_per_gain = float(os.environ.get("QMC_POLICY_MAX_COST_PER_GAIN", "120.0"))
        self.allow_backend_switch = (
            os.environ.get("QMC_POLICY_ALLOW_BACKEND_SWITCH", "true").lower() in TRUE_VALUES
        )
        self.allow_symmetry_toggle = (
            os.environ.get("QMC_POLICY_ALLOW_SYMMETRY_TOGGLE", "true").lower() in TRUE_VALUES
        )
        self.allow_bin_growth = (
            os.environ.get("QMC_POLICY_ALLOW_BIN_GROWTH", "true").lower() in TRUE_VALUES
        )
        self.bias_model = BiasModel()
        self.cost_model = RuntimeCostModel()

    @staticmethod
    def corrected_estimate(estimate: float, predicted_bias: float) -> float:
        """Apply a bias correction estimate to raw probability."""
        return float(max(0.0, min(1.0, estimate - predicted_bias)))

    def choose_action(
        self,
        *,
        iteration: int,
        max_iterations: int,
        error_abs: float,
        epsilon: float,
        current_shots: int,
        current_bins: int,
        circuit_depth: int,
        circuit_qubits: int,
        current_backend: str | None,
        current_symmetry: bool,
        recent_errors: list[float],
    ) -> PolicyAction:
        """Select the next action across available control knobs."""
        if iteration >= max_iterations:
            return PolicyAction(
                shots=current_shots,
                bins=current_bins,
                use_symmetry=current_symmetry,
                backend=current_backend,
                expected_gain=0.0,
                estimated_cost=0.0,
                reason="max_iterations_reached",
            )

        # Expected gain: recent trend-aware estimate.
        trend_bonus = 0.0
        if len(recent_errors) >= 2:
            trend_bonus = max(0.0, recent_errors[-2] - recent_errors[-1])
        expected_gain = max(0.0, (error_abs - epsilon) * 0.35 + 0.5 * trend_bonus)

        # Multi-knob progression strategy:
        # 1) scale shots early,
        # 2) then add bins,
        # 3) then toggle symmetry,
        # 4) optionally request backend switch.
        next_shots = current_shots
        next_bins = current_bins
        next_symmetry = current_symmetry
        next_backend = current_backend
        reason = "maintain"

        if current_shots < self.max_shots:
            ratio = 2.0 if error_abs > 4 * epsilon else 1.5
            next_shots = min(self.max_shots, max(self.min_shots, int(current_shots * ratio)))
            reason = "increase_shots"
        elif self.allow_bin_growth and current_bins < self.max_bins:
            next_bins = min(self.max_bins, int(current_bins * 2))
            reason = "increase_bins"
        elif self.allow_symmetry_toggle and not current_symmetry:
            next_symmetry = True
            reason = "enable_symmetry"
        elif self.allow_backend_switch and iteration >= max(3, max_iterations // 3):
            # None indicates allow auto-reselection by backend chooser.
            next_backend = None
            reason = "allow_backend_switch"

        estimated_cost = self.cost_model.estimate(
            shots=next_shots,
            depth=circuit_depth,
            qubits=circuit_qubits,
        )
        return PolicyAction(
            shots=next_shots,
            bins=next_bins,
            use_symmetry=next_symmetry,
            backend=next_backend,
            expected_gain=expected_gain,
            estimated_cost=estimated_cost,
            reason=reason,
        )

    def should_stop(
        self,
        *,
        iteration: int,
        max_iterations: int,
        error_abs: float,
        epsilon: float,
        expected_gain: float,
        estimated_cost: float,
    ) -> tuple[bool, str]:
        """Stop based on epsilon or cost-vs-gain economics."""
        if error_abs <= epsilon:
            return True, "epsilon_met"
        if iteration >= max_iterations:
            return True, "max_iterations"
        if expected_gain <= self.min_expected_gain:
            return True, "low_expected_gain"
        cost_per_gain = estimated_cost / max(expected_gain, 1e-9)
        if cost_per_gain > self.max_cost_per_gain:
            return True, "cost_exceeds_expected_gain"
        return False, "continue"

