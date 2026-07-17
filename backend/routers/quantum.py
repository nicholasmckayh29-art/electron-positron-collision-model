from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Query

from models.schemas import (
    ClassicalGroundTruthResponse,
    QuantumJobRequest,
    QuantumObservablesResponse,
    QuantumObservableOption,
)
from services import job_store, quantum_service, session_store
from services.quantum.databank import summarize_hardware_runs
from services.quantum.observables import list_verification_observables
from services.quantum.pipeline import classical_ground_truth

router = APIRouter()


@router.get("/observables", response_model=QuantumObservablesResponse)
def get_verification_observables():
    """List resonance mass windows available for sampling verification."""
    return QuantumObservablesResponse(
        observables=[QuantumObservableOption(**item) for item in list_verification_observables()]
    )


@router.get("/ground-truth", response_model=ClassicalGroundTruthResponse)
def get_classical_ground_truth(
    particle: Optional[str] = Query(
        None,
        description="Resonance id (auto, jpsi, z_boson, …). Omit or auto for inference.",
    ),
):
    """Classical exact vs binned probability for a mass window (no quantum job)."""
    if not session_store.session_data:
        raise HTTPException(
            status_code=400,
            detail="No session data — upload a CSV first.",
        )
    try:
        payload = classical_ground_truth(session_store.session_data, particle)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ClassicalGroundTruthResponse(**payload)


@router.post("/job")
def submit_quantum_job(
    background_tasks: BackgroundTasks,
    body: QuantumJobRequest = Body(default_factory=QuantumJobRequest),
):
    """Queue snapshot verification sampling for the current uploaded dataset."""
    if not session_store.session_data:
        raise HTTPException(
            status_code=400,
            detail="No session data — upload a CSV and wait for analysis first.",
        )

    particle = body.particle
    mode = (body.mode or "snapshot").strip().lower()
    if mode not in {"snapshot", "adaptive_snapshot"}:
        raise HTTPException(
            status_code=400,
            detail="mode must be one of: snapshot, adaptive_snapshot",
        )

    if body.target_probability is not None and not (0.0 <= body.target_probability <= 1.0):
        raise HTTPException(
            status_code=400,
            detail="target_probability must be between 0 and 1",
        )
    if body.mass_bins is not None and body.mass_bins < 2:
        raise HTTPException(status_code=400, detail="mass_bins must be >= 2")
    if body.max_iterations is not None and body.max_iterations < 1:
        raise HTTPException(status_code=400, detail="max_iterations must be >= 1")
    if body.epsilon is not None and body.epsilon <= 0:
        raise HTTPException(status_code=400, detail="epsilon must be > 0")
    if body.max_shots is not None and body.max_shots < 128:
        raise HTTPException(status_code=400, detail="max_shots must be >= 128")
    if body.max_bins is not None and body.max_bins < 2:
        raise HTTPException(status_code=400, detail="max_bins must be >= 2")

    rec = job_store.create_job()
    background_tasks.add_task(
        quantum_service.run_quantum_job,
        rec.job_id,
        particle,
        mode,
        body.target_probability,
        body.mass_bins,
        body.max_iterations,
        body.epsilon,
        body.max_shots,
        body.max_bins,
        body.allow_backend_switch,
        body.allow_symmetry_toggle,
    )
    label = particle or "auto"
    return {
        "job_id": rec.job_id,
        "status": rec.status,
        "message": (
            f"Verification job queued ({mode}, {label}); "
            "poll GET /api/quantum/result/{job_id}."
        ),
        "total": rec.total,
        "particle": label,
        "mode": mode,
    }


@router.get("/runtime")
def get_quantum_runtime_status(probe: bool = False):
    """Return IBM Runtime configuration; probe=true tests API connectivity."""
    return quantum_service.get_runtime_status(probe=probe)


@router.get("/result/{job_id}")
def get_quantum_result(job_id: str):
    """Poll verification job status and return result metadata when complete."""
    rec = job_store.get_job(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return job_store.to_public_dict(rec)


@router.get("/databank/summary")
def get_databank_summary(top: int = Query(10, ge=1, le=100)):
    """Summarize saved hardware runs and rank efficient pathways."""
    return summarize_hardware_runs(top=top)
