from fastapi import APIRouter, BackgroundTasks, HTTPException

from services import job_store, quantum_service, session_store

router = APIRouter()


@router.post("/job")
def submit_quantum_job(background_tasks: BackgroundTasks):
    """Queue Aer Estimator scoring for all outliers in the current session."""
    if not session_store.session_outliers:
        raise HTTPException(
            status_code=400,
            detail="No outlier data — upload a CSV and wait for analysis first.",
        )
    if not session_store.session_stats:
        raise HTTPException(status_code=400, detail="No session statistics available.")

    rec = job_store.create_job(total_hint=len(session_store.session_outliers))
    background_tasks.add_task(quantum_service.run_quantum_job, rec.job_id)
    return {
        "job_id": rec.job_id,
        "status": rec.status,
        "message": "Job queued; poll GET /api/quantum/result/{job_id}.",
        "total": len(session_store.session_outliers),
    }


@router.get("/result/{job_id}")
def get_quantum_result(job_id: str):
    """Poll quantum job status; when completed, `scores` maps run|event keys to ⟨ZZZ⟩ values."""
    rec = job_store.get_job(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return job_store.to_public_dict(rec)
