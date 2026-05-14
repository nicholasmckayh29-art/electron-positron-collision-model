from dataclasses import dataclass
from typing import Optional


@dataclass
class Stats:
    """Statistical summary for each feature."""
    z: dict        # {feature: {mean, std}}
    min: dict      # {feature: float}
    max: dict      # {feature: float}


@dataclass
class OutlierEvent:
    """A single outlier event with z-scores and particle identification."""
    run: float
    event: float
    E1: float
    E2: float
    M: float
    z_scores: dict          # {feature: z_value}
    particle: dict          # from identify_particle()
    quantum_score: Optional[float] = None  # filled in after quantum job
