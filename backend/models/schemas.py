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


class QuantumJobRequest(BaseModel):
    """Optional parameters for a verification sampling job."""

    particle: Optional[str] = None  # auto | jpsi | z_boson | …
    mode: Optional[str] = "snapshot"  # snapshot | adaptive_snapshot
    target_probability: Optional[float] = None
    mass_bins: Optional[int] = None
    max_iterations: Optional[int] = None
    epsilon: Optional[float] = None
    max_shots: Optional[int] = None
    max_bins: Optional[int] = None
    allow_backend_switch: Optional[bool] = None
    allow_symmetry_toggle: Optional[bool] = None


class QuantumObservableOption(BaseModel):
    id: str
    label: str
    mass_center: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None
    symbol: Optional[str] = None
    decay: Optional[str] = None


class QuantumObservablesResponse(BaseModel):
    observables: List[QuantumObservableOption]


class ClassicalGroundTruthResponse(BaseModel):
    observable: Dict[str, Any]
    exact_classical_probability: float
    binned_classical_probability: float
    discretization_error: float
    discretization_error_abs: float
    bin_count: int
    mass_range: List[float]
    good_bins: List[int]
    event_count: int
