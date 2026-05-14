import numpy as np

from models.types import Stats
from services.analysis import identify_particle
from services.quantum_service import encode_event


def test_encode_event_scaled_to_pi():
    stats = Stats(
        z={"E1": {"mean": 0, "std": 1}, "E2": {"mean": 0, "std": 1}, "M": {"mean": 0, "std": 1}},
        min={"E1": 0.0, "E2": 0.0, "M": 0.0},
        max={"E1": 200.0, "E2": 200.0, "M": 100.0},
    )
    v = encode_event({"E1": 100.0, "E2": 50.0, "M": 25.0}, stats)
    assert len(v) == 3
    assert all(0 <= x <= np.pi + 1e-9 for x in v)
    assert abs(v[0] - np.pi / 2) < 1e-9
    assert abs(v[1] - np.pi / 4) < 1e-9
    assert abs(v[2] - np.pi / 4) < 1e-9


def test_identify_z_peak():
    p = identify_particle(91.2)
    assert p["name"] == "z_boson"


def test_identify_unknown():
    p = identify_particle(200.0)
    assert p["name"] == "unknown"


def test_identify_eta():
    p = identify_particle(0.55)
    assert p["name"] == "eta"
