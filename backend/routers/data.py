from fastapi import APIRouter, UploadFile, File, HTTPException # type: ignore
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analysis import load_csv_data, summarize_stats, find_outliers
from services import session_store
from models.schemas import UploadResponse, StatsResponse, SpectrumResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload a dielectron collision CSV file for analysis."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Save uploaded file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        session_store.session_data = load_csv_data(temp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    if len(session_store.session_data) == 0:
        raise HTTPException(status_code=400, detail="No valid data rows found in CSV")
    
    # Pre-compute stats
    session_store.session_stats = summarize_stats(session_store.session_data)
    session_store.session_outliers = find_outliers(
        session_store.session_data, session_store.session_stats
    )
    
    columns = list(session_store.session_data[0].keys())
    
    return UploadResponse(
        rows=len(session_store.session_data),
        columns=columns,
        message=f"Successfully loaded {len(session_store.session_data)} events"
    )


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """Return statistical summary of uploaded data."""
    if not session_store.session_stats:
        raise HTTPException(status_code=400, detail="No data uploaded yet")
    
    return StatsResponse(
        z=session_store.session_stats.z,
        min=session_store.session_stats.min,
        max=session_store.session_stats.max
    )


@router.get("/outliers", response_model=dict)
def get_outliers(limit: int = 100, offset: int = 0, known_only: bool = True):
    """Return paginated list of outlier events.
    
    Args:
        limit: Number of outliers to return (default 100, max 500)
        offset: Number of outliers to skip (for pagination)
        known_only: If True, only return outliers matched to known particles.
    
    Returns:
        Dict with 'outliers' list, 'total' count, and pagination info.
    """
    if not session_store.session_outliers:
        raise HTTPException(status_code=400, detail="No data uploaded yet")
    
    # Filter out unknown particles if requested
    if known_only:
        filtered = [o for o in session_store.session_outliers if o.particle["name"] != "unknown"]
    else:
        filtered = session_store.session_outliers
    
    total = len(filtered)
    limit = min(limit, 500)  # Cap at 500 to prevent browser hangs
    
    page = filtered[offset:offset + limit]
    
    return {
        "outliers": [
            {
                "run": o.run,
                "event": o.event,
                "E1": o.E1,
                "E2": o.E2,
                "M": o.M,
                "z_scores": o.z_scores,
                "particle": o.particle,
                "quantum_score": o.quantum_score
            }
            for o in page
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.get("/spectrum", response_model=SpectrumResponse)
def get_spectrum(bins: int = 200):
    """Return binned mass spectrum histogram data."""
    import numpy as np
    
    if not session_store.session_data:
        raise HTTPException(status_code=400, detail="No data uploaded yet")
    
    masses = [record['M'] for record in session_store.session_data]
    counts, edges = np.histogram(masses, bins=bins)
    
    from services.analysis import PARTICLE_WINDOWS
    
    return SpectrumResponse(
        edges=edges.tolist(),
        counts=counts.tolist(),
        particles=PARTICLE_WINDOWS
    )
