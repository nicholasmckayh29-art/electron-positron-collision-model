"""Invariant-mass discretization and classical ground-truth baselines."""

from __future__ import annotations

import numpy as np

from services.quantum.types import MassDistribution, QMCObservable

DEFAULT_BINS = 32


def next_power_of_two(value: int) -> int:
    """Pad histogram bins to $2^n$ for binary qubit state preparation."""

    return 1 << max(1, int(value - 1).bit_length())


def build_mass_distribution(
    data_set: list[dict],
    observable: QMCObservable,
    bins: int = DEFAULT_BINS,
) -> MassDistribution:
    """Discretize invariant mass values and mark bins overlapping the observable."""

    masses = np.array([float(row["M"]) for row in data_set if "M" in row], dtype=float)
    if masses.size == 0:
        raise ValueError("Uploaded data has no invariant mass values.")

    bin_count = next_power_of_two(max(2, bins))
    counts, edges = np.histogram(masses, bins=bin_count)
    probabilities = counts.astype(float) / float(masses.size)
    bin_lows = edges[:-1]
    bin_highs = edges[1:]
    good_bins = np.where((bin_highs >= observable.low) & (bin_lows <= observable.high))[0]
    exact_good = (masses >= observable.low) & (masses <= observable.high)

    return MassDistribution(
        masses=masses,
        counts=counts,
        edges=edges,
        probabilities=probabilities,
        good_bins=good_bins,
        exact_probability=float(np.count_nonzero(exact_good) / masses.size),
        binned_probability=float(np.sum(probabilities[good_bins])),
        bin_count=bin_count,
        encoding_dimension=bin_count,
    )
