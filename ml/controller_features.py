"""Build tabular ML features from quantum hardware databank records.

The source records are append-only JSONL entries written by
``backend/services/quantum/databank.py`` after IBM Runtime jobs complete.
This module intentionally accepts imperfect records so early research data can
still train a baseline model.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_DATABANK = Path("data/quantum_databank/hardware_runs.jsonl")
DEFAULT_OUT = Path("data/quantum_databank/controller_training.csv")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("record_type") == "quantum_hardware_run":
                records.append(record)
    return records


def _ops_features(circuit: dict[str, Any]) -> dict[str, int]:
    ops = circuit.get("ops") or {}
    return {
        "ops_sx": _safe_int(ops.get("sx")),
        "ops_rz": _safe_int(ops.get("rz")),
        "ops_cz": _safe_int(ops.get("cz")),
        "ops_reset": _safe_int(ops.get("reset")),
        "ops_measure": _safe_int(ops.get("measure")),
        "ops_barrier": _safe_int(ops.get("barrier")),
        "ops_total": sum(_safe_int(v) for v in ops.values()),
    }


def _iteration_features(iterations: list[dict[str, Any]]) -> dict[str, float]:
    if not iterations:
        return {
            "first_iteration_error_abs": 0.0,
            "best_iteration_error_abs": 0.0,
            "mean_iteration_error_abs": 0.0,
            "last_iteration_error_abs": 0.0,
            "error_improvement_abs": 0.0,
            "max_iteration_shots": 0.0,
            "total_iteration_shots": 0.0,
        }

    errors = [_safe_float(row.get("error_abs")) for row in iterations]
    shots = [_safe_float(row.get("shots")) for row in iterations]
    first_error = errors[0]
    last_error = errors[-1]
    return {
        "first_iteration_error_abs": first_error,
        "best_iteration_error_abs": min(errors),
        "mean_iteration_error_abs": sum(errors) / len(errors),
        "last_iteration_error_abs": last_error,
        "error_improvement_abs": first_error - last_error,
        "max_iteration_shots": max(shots),
        "total_iteration_shots": sum(shots),
    }


def flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    control = record.get("control_config") or {}
    observable = record.get("observable") or {}
    ground_truth = record.get("ground_truth") or {}
    discretization = ground_truth.get("discretization") or {}
    verification = record.get("verification") or {}
    convergence = record.get("convergence") or {}
    circuit = record.get("circuit") or {}
    encoding = record.get("encoding") or {}
    iterations = record.get("iterations") or []

    row: dict[str, Any] = {
        "saved_at_utc": record.get("saved_at_utc"),
        "mode": record.get("mode", "unknown"),
        "particle": record.get("particle", "unknown"),
        "backend": record.get("backend", "unknown"),
        "observable_name": observable.get("name", "unknown"),
        "encoding_kind": encoding.get("kind", "unknown"),
        "symmetry_protection": encoding.get("symmetry_protection", "none"),
        "allow_backend_switch": bool(control.get("allow_backend_switch")),
        "allow_symmetry_toggle": bool(control.get("allow_symmetry_toggle")),
        "shots": _safe_float(record.get("shots")),
        "estimate": _safe_float(record.get("estimate")),
        "standard_error": _safe_float(record.get("standard_error")),
        "good_counts": _safe_float(record.get("good_counts")),
        "target_probability": _safe_float(
            convergence.get("target_probability"),
            _safe_float(control.get("target_probability")),
        ),
        "epsilon": _safe_float(convergence.get("epsilon"), _safe_float(control.get("epsilon"))),
        "max_iterations": _safe_float(
            convergence.get("max_iterations"),
            _safe_float(control.get("max_iterations")),
        ),
        "mass_bins": _safe_float(control.get("mass_bins"), _safe_float(circuit.get("bins"))),
        "max_shots": _safe_float(control.get("max_shots")),
        "max_bins": _safe_float(control.get("max_bins")),
        "mass_center": _safe_float(observable.get("mass_center")),
        "mass_low": _safe_float(observable.get("low")),
        "mass_high": _safe_float(observable.get("high")),
        "mass_min": _safe_float(discretization.get("mass_min")),
        "mass_max": _safe_float(discretization.get("mass_max")),
        "good_bin_count": len(discretization.get("good_bins") or []),
        "exact_classical_probability": _safe_float(
            ground_truth.get("exact_classical_probability")
        ),
        "binned_classical_probability": _safe_float(
            ground_truth.get("binned_classical_probability")
        ),
        "discretization_error": _safe_float(verification.get("discretization_error")),
        "quantum_vs_exact": _safe_float(verification.get("quantum_vs_exact")),
        "quantum_vs_binned": _safe_float(verification.get("quantum_vs_binned")),
        "quantum_vs_exact_sigma": _safe_float(verification.get("quantum_vs_exact_sigma")),
        "within_2sigma_of_exact": bool(verification.get("within_2sigma_of_exact")),
        "converged": bool(convergence.get("converged")),
        "stopping_reason": convergence.get("stopping_reason", "unknown"),
        "iterations_run": _safe_float(convergence.get("iterations_run"), len(iterations)),
        "final_error": _safe_float(convergence.get("final_error")),
        "final_error_abs": _safe_float(convergence.get("final_error_abs")),
        "final_error_corrected": _safe_float(convergence.get("final_error_corrected")),
        "final_error_abs_corrected": _safe_float(
            convergence.get("final_error_abs_corrected"),
            _safe_float(convergence.get("final_error_abs")),
        ),
        "circuit_qubits": _safe_float(circuit.get("qubits")),
        "circuit_depth": _safe_float(circuit.get("depth")),
        "circuit_bins": _safe_float(circuit.get("bins")),
        "distinct_bins_observed": _safe_float(circuit.get("distinct_bins_observed")),
    }
    row.update(_ops_features(circuit))
    row.update(_iteration_features(iterations))
    return row


def build_controller_frame(path: Path) -> pd.DataFrame:
    """Return one flattened row per databank record."""

    return pd.DataFrame(flatten_record(record) for record in _load_jsonl(path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build controller training CSV")
    parser.add_argument("--databank", default=str(DEFAULT_DATABANK), help="Input JSONL path")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output CSV path")
    args = parser.parse_args()

    databank = Path(args.databank)
    out_path = Path(args.out)
    frame = build_controller_frame(databank)
    if frame.empty:
        raise SystemExit(f"No hardware records found in {databank}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_path, index=False)
    print(f"Wrote {len(frame)} rows x {len(frame.columns)} columns to {out_path}")
    print("Targets available: final_error_abs, final_error_abs_corrected, converged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

