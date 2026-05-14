import numpy as np
import csv

from models.types import Stats, OutlierEvent

FIELDS_TO_CHECK = ['E1', 'E2', 'M']

PARTICLE_WINDOWS = [
    {
        "name": "eta",
        "symbol": "η",
        "mass": 0.548,
        "width": 0.06,
        "color": "#a8dadc",
        "decay": "η → γγ",
        "quark_content": "uū+dd̄+ss̄",
    },
    {
        "name": "rho_omega",
        "symbol": "ρ/ω",
        "mass": 0.778,
        "width": 0.06,
        "color": "#457b9d",
        "decay": "ρ/ω → e⁺ + e⁻",
        "quark_content": "uū+dd̄",
    },
    {
        "name": "phi",
        "symbol": "φ",
        "mass": 1.019,
        "width": 0.03,
        "color": "#1d3557",
        "decay": "φ → e⁺ + e⁻",
        "quark_content": "ss̄",
    },
    {
        "name": "jpsi",
        "symbol": "J/ψ",
        "mass": 3.097,
        "width": 0.15,
        "color": "#e63946",
        "decay": "J/ψ → e⁺ + e⁻",
        "quark_content": "cc̄",
    },
    {
        "name": "psi2s",
        "symbol": "ψ(2S)",
        "mass": 3.686,
        "width": 0.15,
        "color": "#f4a261",
        "decay": "ψ(2S) → e⁺ + e⁻",
        "quark_content": "cc̄",
    },
    {
        "name": "upsilon",
        "symbol": "Υ family",
        "mass": 9.460,
        "width": 1.5,
        "color": "#2a9d8f",
        "decay": "Υ → e⁺ + e⁻",
        "quark_content": "bb̄",
    },
    {
        "name": "z_boson",
        "symbol": "Z⁰",
        "mass": 91.1876,
        "width": 15.0,
        "color": "#e9c46a",
        "decay": "Z⁰ → e⁺ + e⁻",
        "quark_content": None,
    },
]


def load_csv_data(filepath: str) -> list[dict]:
    """Load dielectron collision data from CSV file.
    
    Args:
        filepath: Path to CSV file with columns: Run, Event, E1, E2, M
        
    Returns:
        List of records with numeric values converted to float.
        Rows with missing/invalid values are skipped.
    """
    data_set = []
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            record = {}
            skip_row = False
            
            for key, value in row.items():
                clean_key = key.strip()
                try:
                    float_val = float(value)
                    if np.isnan(float_val):
                        skip_row = True
                        break
                    record[clean_key] = float_val
                except ValueError:
                    if value.strip() == '':
                        skip_row = True
                        break
                    record[clean_key] = value
            
            if not skip_row:
                data_set.append(record)
    
    return data_set


def summarize_stats(data_set: list[dict]) -> Stats:
    """Calculate statistical summaries for numeric features.
    
    Args:
        data_set: List of records from load_csv_data()
        
    Returns:
        Stats dataclass with z-score parameters, min, and max for each feature.
    """
    exclude_keys = {'Run', 'Event'}
    keys = [k for k in data_set[0].keys() 
            if isinstance(data_set[0][k], (int, float)) and k not in exclude_keys]
    
    z_dict = {}
    min_dict = {}
    max_dict = {}
    
    for key in keys:
        values = [record[key] for record in data_set]
        
        mean = np.mean(values)
        std = np.std(values)
        min_val = np.min(values)
        max_val = np.max(values)
        
        z_dict[key] = {'mean': float(mean), 'std': float(std)}
        min_dict[key] = float(min_val)
        max_dict[key] = float(max_val)
    
    return Stats(z=z_dict, min=min_dict, max=max_dict)


def identify_particle(mass_gev: float) -> dict:
    """Match an invariant mass to a known particle.

    Mass windows are research-backed from CMS electron reconstruction
    papers. See docs/physics/particle-id.md for sources.

    Args:
        mass_gev: Invariant mass value in GeV

    Returns:
        Particle dict with name, symbol, mass, width, color, decay, quark_content.
        Returns unknown particle if mass falls outside all windows.
    """
    for p in PARTICLE_WINDOWS:
        if abs(mass_gev - p["mass"]) <= p["width"]:
            return p
    return {
        "name": "unknown",
        "symbol": "?",
        "mass": mass_gev,
        "color": "#cccccc",
        "decay": "Unknown",
        "quark_content": None,
    }


def find_outliers(data_set: list[dict], stats: Stats, z_threshold: float = 3.0) -> list[OutlierEvent]:
    """Identify outlier events using z-score threshold.
    
    Args:
        data_set: List of records from load_csv_data()
        stats: Stats dataclass from summarize_stats()
        z_threshold: Number of standard deviations to flag as outlier
        
    Returns:
        List of OutlierEvent objects for events exceeding z_threshold in any feature.
    """
    outliers = []
    
    for record in data_set:
        outlier_reasons = []
        z_scores = {}
        
        for key in FIELDS_TO_CHECK:
            value = record[key]
            
            if stats.z[key]['std'] == 0:
                continue
            
            z_score = (value - stats.z[key]['mean']) / stats.z[key]['std']
            z_scores[key] = float(z_score)
            
            if abs(z_score) > z_threshold:
                outlier_reasons.append(f"{key}: z={z_score:.2f}")
        
        if outlier_reasons:
            particle = identify_particle(record['M'])
            outlier = OutlierEvent(
                run=record.get('Run', 0),
                event=record.get('Event', 0),
                E1=record['E1'],
                E2=record['E2'],
                M=record['M'],
                z_scores=z_scores,
                particle=particle,
            )
            outliers.append(outlier)
    
    return outliers
