"""In-memory quantum job registry."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class QuantumJobRecord:
    job_id: str
    status: str  # pending | running | completed | failed
    created_at: float
    message: str = ""
    error: Optional[str] = None
    processed: int = 0
    total: int = 0
    scores: dict[str, float] = field(default_factory=dict)  # "run|event" -> score
    result: dict[str, Any] = field(default_factory=dict)


_jobs: dict[str, QuantumJobRecord] = {}


def create_job(total_hint: int = 0) -> QuantumJobRecord:
    jid = str(uuid.uuid4())
    rec = QuantumJobRecord(
        job_id=jid,
        status="pending",
        created_at=time.time(),
        total=total_hint,
    )
    _jobs[jid] = rec
    return rec


def get_job(job_id: str) -> Optional[QuantumJobRecord]:
    return _jobs.get(job_id)


def update_job(job_id: str, **fields: Any) -> None:
    rec = _jobs.get(job_id)
    if not rec:
        return
    for k, v in fields.items():
        if hasattr(rec, k):
            setattr(rec, k, v)


def to_public_dict(rec: QuantumJobRecord) -> dict:
    payload = {
        "job_id": rec.job_id,
        "status": rec.status,
        "message": rec.message,
        "error": rec.error,
        "processed": rec.processed,
        "total": rec.total,
        "scores_applied": False,
        "result_ready": rec.status == "completed" and bool(rec.result),
    }
    if rec.result:
        payload["result"] = rec.result
    return payload
