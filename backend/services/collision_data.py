"""Load and normalize CMS-style dielectron collision CSV formats."""

from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from typing import Any

import numpy as np

ELECTRON_MASS_GEV = 0.000511

CANONICAL_KEYS = ("Run", "Event", "E1", "E2", "M")

_HTML_MARKERS = ("<!doctype html", "<html", "<head>", "page not found")


class CollisionDataError(ValueError):
    """Raised when uploaded content is not a supported collision dataset."""


def _normalize_column_name(name: str | None) -> str:
    if name is None:
        return ""
    return name.strip()


def _looks_like_html(text: str) -> bool:
    sample = text.lstrip()[:4096].lower()
    return any(marker in sample for marker in _HTML_MARKERS)


def _parse_raw_rows(text: str) -> tuple[list[str], list[dict[str, Any]]]:
    if not text or not text.strip():
        raise CollisionDataError("CSV file is empty.")

    if _looks_like_html(text):
        raise CollisionDataError(
            "File looks like an HTML error page, not collision data. "
            "Re-download the CSV from CERN Open Data (opendata.cern.ch), e.g. "
            "record 302 (J/ψ), 305 (Υ), or the bundled Zee.csv from record 545."
        )

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = [_normalize_column_name(name) for name in (reader.fieldnames or [])]
    fieldnames = [name for name in fieldnames if name]
    if not fieldnames:
        raise CollisionDataError("CSV header row is missing or unreadable.")

    rows: list[dict[str, Any]] = []
    for raw_row in reader:
        if not raw_row:
            continue
        row: dict[str, Any] = {}
        skip_row = False
        for raw_key, raw_value in raw_row.items():
            key = _normalize_column_name(raw_key)
            if not key:
                continue
            value = "" if raw_value is None else str(raw_value).strip()
            if value == "":
                skip_row = True
                break
            try:
                float_val = float(value)
                if np.isnan(float_val):
                    skip_row = True
                    break
                row[key] = float_val
            except ValueError:
                row[key] = value
        if not skip_row and row:
            rows.append(row)

    return fieldnames, rows


def _four_momentum_from_pt_eta_phi(pt: float, eta: float, phi: float) -> tuple[float, float, float, float]:
    px = pt * math.cos(phi)
    py = pt * math.sin(phi)
    pz = pt * math.sinh(eta)
    momentum = math.sqrt(px * px + py * py + pz * pz)
    energy = math.sqrt(momentum * momentum + ELECTRON_MASS_GEV * ELECTRON_MASS_GEV)
    return energy, px, py, pz


def _four_momentum_from_px_py_pz(px: float, py: float, pz: float) -> tuple[float, float, float, float]:
    momentum = math.sqrt(px * px + py * py + pz * pz)
    energy = math.sqrt(momentum * momentum + ELECTRON_MASS_GEV * ELECTRON_MASS_GEV)
    return energy, px, py, pz


def _invariant_mass(
    e1: tuple[float, float, float, float],
    e2: tuple[float, float, float, float],
) -> float:
    energy = e1[0] + e2[0]
    px = e1[1] + e2[1]
    py = e1[2] + e2[2]
    pz = e1[3] + e2[3]
    mass_squared = energy * energy - px * px - py * py - pz * pz
    return math.sqrt(max(mass_squared, 0.0))


def _detect_format(columns: set[str]) -> str:
    if {"E1", "E2"}.issubset(columns) or {"E1", "M"}.issubset(columns):
        if "M" in columns:
            return "wide_full"
        if {"px1", "py1", "pz1", "px2", "py2", "pz2"}.issubset(columns):
            return "wide_kinematics"
        if {"pt1", "eta1", "phi1", "pt2", "eta2", "phi2"}.issubset(columns):
            return "wide_pt_eta_phi"

    if {"pt1", "eta1", "phi1", "pt2", "eta2", "phi2"}.issubset(columns):
        return "wide_pt_eta_phi"

    if {"px1", "py1", "pz1", "px2", "py2", "pz2"}.issubset(columns):
        return "wide_kinematics"

    long_columns = {"E", "px", "py", "pz", "pt", "eta", "phi", "Q", "M"}
    if long_columns.issubset(columns) and "E1" not in columns:
        return "long_per_electron"

    raise CollisionDataError(
        "Unsupported CSV layout. Expected CMS dielectron columns such as "
        "Run, Event, E1, E2, M (wide format), pt1/eta1/phi1 + pt2/eta2/phi2 "
        "(Zee-style), or E/px/py/pz/pt/eta/phi/Q/M per electron (long format)."
    )


def _electron_four_vector(row: dict[str, Any], prefix: str) -> tuple[float, float, float, float]:
    px_key = f"px{prefix}"
    py_key = f"py{prefix}"
    pz_key = f"pz{prefix}"
    if {px_key, py_key, pz_key}.issubset(row):
        return _four_momentum_from_px_py_pz(row[px_key], row[py_key], row[pz_key])

    pt_key = f"pt{prefix}"
    eta_key = f"eta{prefix}"
    phi_key = f"phi{prefix}"
    if {pt_key, eta_key, phi_key}.issubset(row):
        return _four_momentum_from_pt_eta_phi(row[pt_key], row[eta_key], row[phi_key])

    energy_key = f"E{prefix}"
    if energy_key in row:
        raise CollisionDataError(
            f"Row is missing momentum components for electron {prefix.strip('1').strip('2') or prefix}."
        )
    raise CollisionDataError("Unable to reconstruct electron four-momentum from available columns.")


def _normalize_wide_row(row: dict[str, Any], fmt: str) -> dict[str, Any]:
    record = dict(row)
    record.setdefault("Run", row.get("Run", 0))
    record.setdefault("Event", row.get("Event", 0))

    if fmt == "wide_full":
        if "E1" not in record or "E2" not in record:
            vec1 = _electron_four_vector(row, "1")
            vec2 = _electron_four_vector(row, "2")
            record.setdefault("E1", vec1[0])
            record.setdefault("E2", vec2[0])
        if "M" not in record:
            vec1 = _electron_four_vector(row, "1")
            vec2 = _electron_four_vector(row, "2")
            record["M"] = _invariant_mass(vec1, vec2)
        return record

    vec1 = _electron_four_vector(row, "1")
    vec2 = _electron_four_vector(row, "2")
    record["E1"] = vec1[0]
    record["E2"] = vec2[0]
    record["M"] = _invariant_mass(vec1, vec2)

    record.setdefault("px1", vec1[1])
    record.setdefault("py1", vec1[2])
    record.setdefault("pz1", vec1[3])
    record.setdefault("px2", vec2[1])
    record.setdefault("py2", vec2[2])
    record.setdefault("pz2", vec2[3])
    return record


def _normalize_long_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if "Run" not in row or "Event" not in row:
            continue
        grouped[(row["Run"], row["Event"])].append(row)

    events: list[dict[str, Any]] = []
    for (run, event), electrons in grouped.items():
        if len(electrons) != 2:
            continue
        electrons = sorted(
            electrons,
            key=lambda item: float(item.get("pt", item.get("E", 0.0))),
            reverse=True,
        )
        e1_row, e2_row = electrons[0], electrons[1]

        vec1 = _four_momentum_from_px_py_pz(e1_row["px"], e1_row["py"], e1_row["pz"])
        vec2 = _four_momentum_from_px_py_pz(e2_row["px"], e2_row["py"], e2_row["pz"])
        mass = e1_row.get("M", e2_row.get("M"))
        if mass is None:
            mass = _invariant_mass(vec1, vec2)

        record: dict[str, Any] = {
            "Run": run,
            "Event": event,
            "E1": e1_row.get("E", vec1[0]),
            "E2": e2_row.get("E", vec2[0]),
            "px1": e1_row["px"],
            "py1": e1_row["py"],
            "pz1": e1_row["pz"],
            "pt1": e1_row.get("pt"),
            "eta1": e1_row.get("eta"),
            "phi1": e1_row.get("phi"),
            "Q1": e1_row.get("Q"),
            "px2": e2_row["px"],
            "py2": e2_row["py"],
            "pz2": e2_row["pz"],
            "pt2": e2_row.get("pt"),
            "eta2": e2_row.get("eta"),
            "phi2": e2_row.get("phi"),
            "Q2": e2_row.get("Q"),
            "M": float(mass),
        }
        events.append(record)

    return events


def normalize_collision_rows(rows: list[dict[str, Any]], columns: list[str]) -> tuple[str, list[dict[str, Any]]]:
    """Normalize parsed CSV rows into the canonical dielectron event schema."""
    if not rows:
        raise CollisionDataError("No valid data rows found in CSV.")

    column_set = set(columns) | {key for row in rows for key in row}
    fmt = _detect_format(column_set)

    if fmt == "long_per_electron":
        normalized = _normalize_long_rows(rows)
    else:
        normalized = [_normalize_wide_row(row, fmt) for row in rows]

    normalized = [
        record
        for record in normalized
        if all(key in record for key in CANONICAL_KEYS)
    ]
    if not normalized:
        raise CollisionDataError(
            "No complete dielectron events found. Long-format files need exactly "
            "two electron rows per Run/Event pair."
        )

    return fmt, normalized


def describe_dataset_format(fmt: str) -> str:
    descriptions = {
        "wide_full": "CMS wide dielectron table (Run, Event, E1, E2, M, …)",
        "wide_kinematics": "Wide kinematics table (px/py/pz or pt/eta/phi; M computed)",
        "wide_pt_eta_phi": "Zee-style electron table (pt/eta/phi; E and M computed)",
        "long_per_electron": "Long per-electron table (paired by Run/Event)",
    }
    return descriptions.get(fmt, fmt)


def load_collision_csv_from_text(text: str) -> tuple[str, list[dict[str, Any]]]:
    columns, rows = _parse_raw_rows(text)
    return normalize_collision_rows(rows, columns)


def load_collision_csv(filepath: str) -> tuple[str, list[dict[str, Any]]]:
    with open(filepath, encoding="utf-8", newline="") as handle:
        return load_collision_csv_from_text(handle.read())
