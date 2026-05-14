from pydantic import BaseModel
from typing import List, Dict, Optional, Any


class UploadResponse(BaseModel):
    """Response after uploading and parsing a CSV file."""
    rows: int
    columns: List[str]
    message: str


class StatsResponse(BaseModel):
    """Statistical summary for each feature."""
    z: Dict[str, Dict[str, float]]  # {feature: {mean, std}}
    min: Dict[str, float]
    max: Dict[str, float]


class ParticleInfo(BaseModel):
    """Identified particle information."""
    name: str
    symbol: str
    mass: Optional[float] = None
    color: str
    decay: Optional[str] = None
    quark_content: Optional[str] = None


class OutlierEventResponse(BaseModel):
    """A single outlier event with z-scores and particle identification."""
    run: float
    event: float
    E1: float
    E2: float
    M: float
    z_scores: Dict[str, float]
    particle: ParticleInfo
    quantum_score: Optional[float] = None


class SpectrumResponse(BaseModel):
    """Binned mass spectrum histogram data."""
    edges: List[float]
    counts: List[int]
    particles: List[Dict[str, Any]]
