"""Quantum anomaly scoring using a small parameterized circuit (Aer Estimator)."""

from __future__ import annotations

import logging
import os
from typing import Iterable

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer.primitives import Estimator

from models.types import OutlierEvent, Stats
from services import job_store, session_store

logger = logging.getLogger(__name__)

CHUNK_SIZE = int(os.environ.get("QUANTUM_CHUNK_SIZE", "120"))

_OBSERVABLE = SparsePauliOp("ZZZ")


def _ansatz() -> QuantumCircuit:
    pv = ParameterVector("p", 3)
    qc = QuantumCircuit(3)
    qc.ry(pv[0], 0)
    qc.ry(pv[1], 1)
    qc.ry(pv[2], 2)
    qc.cx(0, 1)
    qc.cx(1, 2)
    return qc


_ANSATZ = _ansatz()


def event_key(run: float, event: float) -> str:
    return f"{run:.0f}|{event:.0f}"


def encode_event(event: dict, stats: Stats) -> list[float]:
    """Map E1, E2, M to [0, π] using dataset maxima (plan: angle encoding)."""

    def angle(val: float, key: str) -> float:
        mx = stats.max.get(key, 0.0)
        if mx == 0:
            return 0.0
        x = min(max(float(val) / mx, 0.0), 1.0)
        return float(x * np.pi)

    return [
        angle(float(event["E1"]), "E1"),
        angle(float(event["E2"]), "E2"),
        angle(float(event["M"]), "M"),
    ]


def _compute_scores_chunk(encoded: list[list[float]]) -> list[float]:
    if not encoded:
        return []
    n = len(encoded)
    estimator = Estimator()
    job = estimator.run([_ANSATZ] * n, [_OBSERVABLE] * n, encoded)
    vals = job.result().values
    return [float(v) for v in vals]


def _chunks(items: list[list[float]], size: int) -> Iterable[tuple[int, list[list[float]]]]:
    for i in range(0, len(items), size):
        yield i, items[i : i + size]


def run_quantum_job(job_id: str) -> None:
    """Background worker: score all current outliers and write scores into session + job record."""
    rec = job_store.get_job(job_id)
    if not rec:
        return

    stats = session_store.session_stats
    outliers = session_store.session_outliers
    if not stats or not outliers:
        job_store.update_job(
            job_id,
            status="failed",
            error="No session stats or outliers; upload a CSV first.",
        )
        return

    job_store.update_job(job_id, status="running", message="Running Aer Estimator batches…")

    encoded: list[list[float]] = []
    keys: list[str] = []
    for o in outliers:
        ev = {"E1": o.E1, "E2": o.E2, "M": o.M}
        encoded.append(encode_event(ev, stats))
        keys.append(event_key(o.run, o.event))

    scores_out: dict[str, float] = {}
    processed = 0
    total = len(encoded)

    try:
        for offset, batch in _chunks(encoded, CHUNK_SIZE):
            batch_scores = _compute_scores_chunk(batch)
            for i, sc in enumerate(batch_scores):
                scores_out[keys[offset + i]] = sc
            processed = min(offset + len(batch), total)
            job_store.update_job(job_id, processed=processed, total=total)

        for o in session_store.session_outliers:
            k = event_key(o.run, o.event)
            if k in scores_out:
                o.quantum_score = scores_out[k]

        job_store.update_job(
            job_id,
            status="completed",
            message="Quantum scoring complete.",
            scores=scores_out,
            processed=total,
            total=total,
        )
    except Exception as exc:  # pragma: no cover - hardware / qiskit failures
        logger.exception("Quantum job failed")
        job_store.update_job(
            job_id,
            status="failed",
            error=str(exc),
            processed=processed,
            total=total,
        )
