"""Local append-only databank for real IBM hardware run telemetry."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

_TRUE_VALUES = {"1", "true", "yes", "on"}


def databank_enabled() -> bool:
    """Enable/disable local hardware-run persistence."""

    return os.environ.get("QMC_DATABANK_ENABLED", "true").strip().lower() in _TRUE_VALUES


def databank_path() -> Path:
    """Resolve local databank path (JSONL) for hardware run records."""

    configured = os.environ.get("QMC_DATABANK_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()

    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "data" / "quantum_databank" / "hardware_runs.jsonl"


def append_hardware_run(record: dict[str, Any]) -> str:
    """Append one hardware run record to local JSONL databank."""

    path = databank_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True))
        f.write("\n")
    return str(path)


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        if value is None:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def load_hardware_records(path: Path | None = None) -> list[dict[str, Any]]:
    """Load all hardware run records from JSONL databank."""

    db_path = path or databank_path()
    if not db_path.exists():
        return []

    records: list[dict[str, Any]] = []
    with db_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("record_type") != "quantum_hardware_run":
                continue
            records.append(payload)
    return records


def _pathway_key(record: dict[str, Any]) -> str:
    mode = record.get("mode", "unknown")
    backend = record.get("backend", "unknown_backend")
    observable = record.get("observable", {})
    obs_name = observable.get("name", "unknown_observable")
    encoding = record.get("encoding", {})
    encoding_kind = encoding.get("kind", "unknown_encoding")
    symmetry = encoding.get("symmetry_protection", "none")
    return f"{mode}|{obs_name}|{backend}|{encoding_kind}|{symmetry}"


def _scored_row(record: dict[str, Any]) -> dict[str, Any]:
    verification = record.get("verification", {})
    convergence = record.get("convergence", {})
    estimate = _safe_float(record.get("estimate"))
    stderr = _safe_float(record.get("standard_error"))
    shots = max(1.0, _safe_float(record.get("shots"), fallback=1.0))
    err_abs = abs(_safe_float(verification.get("quantum_vs_exact")))
    sigma = verification.get("quantum_vs_exact_sigma")
    iterations = record.get("iterations", [])
    iterations_run = int(convergence.get("iterations_run", len(iterations) or 1))
    converged = bool(convergence.get("converged"))

    score = (
        err_abs * 0.55
        + stderr * 0.25
        + (shots / 10000.0) * 0.10
        + (iterations_run / 10.0) * 0.10
    )

    return {
        "pathway": _pathway_key(record),
        "mode": record.get("mode"),
        "particle": record.get("particle"),
        "observable": record.get("observable", {}).get("name"),
        "backend": record.get("backend"),
        "estimate": estimate,
        "stderr": stderr,
        "err_abs": err_abs,
        "sigma": sigma,
        "shots": int(shots),
        "iterations_run": iterations_run,
        "converged": converged,
        "efficiency_score": score,
        "runtime_job_id": record.get("runtime_job_id"),
        "saved_at_utc": record.get("saved_at_utc"),
        "job_id": record.get("job_id"),
    }


def _aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["pathway"]].append(row)

    out: list[dict[str, Any]] = []
    for pathway, group in grouped.items():
        n = len(group)
        avg = lambda key: sum(_safe_float(r.get(key)) for r in group) / float(n)
        converged_rate = sum(1 for r in group if r["converged"]) / float(n)
        out.append(
            {
                "pathway": pathway,
                "runs": n,
                "avg_efficiency_score": avg("efficiency_score"),
                "avg_abs_error_vs_exact": avg("err_abs"),
                "avg_standard_error": avg("stderr"),
                "avg_shots": avg("shots"),
                "avg_iterations": avg("iterations_run"),
                "converged_rate": converged_rate,
            }
        )
    out.sort(key=lambda r: (r["avg_efficiency_score"], r["avg_abs_error_vs_exact"]))
    return out


def summarize_hardware_runs(top: int = 10, path: Path | None = None) -> dict[str, Any]:
    """Summarize databank runs and rank pathways (lower score is better)."""

    db_path = path or databank_path()
    records = load_hardware_records(db_path)
    rows = [_scored_row(r) for r in records]
    leaderboard = _aggregate(rows)
    recent = sorted(
        rows,
        key=lambda r: r.get("saved_at_utc") or "",
        reverse=True,
    )[: max(1, top)]

    return {
        "databank_path": str(db_path),
        "databank_exists": db_path.exists(),
        "record_count": len(rows),
        "top_requested": max(1, top),
        "leaderboard": leaderboard[: max(1, top)],
        "recent_runs": recent[: max(1, top)],
        "runs": rows,
    }
