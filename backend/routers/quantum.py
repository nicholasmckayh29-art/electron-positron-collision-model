from fastapi import APIRouter, BackgroundTasks, HTTPException

from services import job_store, quantum_service, session_store

router = APIRouter()


@router.post("/job")
def submit_quantum_job(background_tasks: BackgroundTasks):
    """Queue QMC-style observable estimation for the current uploaded dataset."""
    if not session_store.session_data:
        raise HTTPException(
            status_code=400,
            detail="No session data — upload a CSV and wait for analysis first.",
        )

    rec = job_store.create_job()
    background_tasks.add_task(quantum_service.run_quantum_job, rec.job_id)
    return {
        "job_id": rec.job_id,
        "status": rec.status,
        "message": "QMC observable job queued; poll GET /api/quantum/result/{job_id}.",
        "total": rec.total,
    }


@router.get("/runtime")
def get_quantum_runtime_status():
    """Return IBM Runtime configuration without spending quantum runtime."""
    return quantum_service.get_runtime_status()


@router.get("/result/{job_id}")
def get_quantum_result(job_id: str):
    """Poll QMC observable job status and return result metadata when complete."""
    rec = job_store.get_job(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return job_store.to_public_dict(rec)
