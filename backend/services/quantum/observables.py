"""Resonance mass-window observables for ground-truth verification."""

from __future__ import annotations

import numpy as np

from services.analysis import PARTICLE_WINDOWS
from services.quantum.types import QMCObservable


def list_verification_observables() -> list[dict]:
    """Resonance windows available for ground-truth verification jobs."""

    items = [
        {
            "id": "auto",
            "label": "Auto (most populated peak)",
            "mass_center": None,
            "low": None,
            "high": None,
        }
    ]
    for particle in PARTICLE_WINDOWS:
        mass = float(particle["mass"])
        width = float(particle["width"])
        items.append(
            {
                "id": particle["name"],
                "label": f"{particle['symbol']} ({mass:.4g} GeV)",
                "symbol": particle["symbol"],
                "mass_center": mass,
                "low": mass - width,
                "high": mass + width,
                "decay": particle.get("decay"),
            }
        )
    return items


def observable_from_particle(particle_name: str) -> QMCObservable:
    """Build a mass-window observable for a known resonance (e.g. jpsi, z_boson)."""

    for particle in PARTICLE_WINDOWS:
        if particle["name"] == particle_name:
            mass = float(particle["mass"])
            width = float(particle["width"])
            return QMCObservable(
                name=f"{particle['name']}_mass_window",
                label=f"{particle['symbol']} mass-window probability",
                mass_center=mass,
                low=mass - width,
                high=mass + width,
            )
    raise ValueError(f"Unknown particle window: {particle_name}")


def infer_mass_window_observable(data_set: list[dict]) -> QMCObservable:
    """Choose the resonance window with the most matching uploaded events."""

    masses = np.array([float(row["M"]) for row in data_set if "M" in row], dtype=float)
    if masses.size == 0:
        raise ValueError("Uploaded data has no invariant mass column M.")

    best_particle = None
    best_count = -1
    for particle in PARTICLE_WINDOWS:
        low = float(particle["mass"]) - float(particle["width"])
        high = float(particle["mass"]) + float(particle["width"])
        count = int(np.count_nonzero((masses >= low) & (masses <= high)))
        if count > best_count:
            best_particle = particle
            best_count = count

    if best_particle and best_count > 0:
        return observable_from_particle(best_particle["name"])

    mean = float(np.mean(masses))
    std = float(np.std(masses))
    half_width = std if std > 0 else max(abs(mean) * 0.05, 1.0)
    return QMCObservable(
        name="central_mass_window",
        label="Central mass-window probability",
        mass_center=mean,
        low=mean - half_width,
        high=mean + half_width,
    )
