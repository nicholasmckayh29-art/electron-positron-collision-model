from pathlib import Path

import numpy as np
import pytest

from services.collision_data import CollisionDataError, load_collision_csv, load_collision_csv_from_text

DATA_DIR = Path("/Users/nich/Projects/qAI_Projects/data/cern_electrons")

WIDE_SAMPLE = """Run,Event,E1,px1 ,py1,pz1,pt1,eta1,phi1,Q1,E2,px2,py2,pz2,pt2,eta2,phi2,Q2,M
1,1,10.0,1.0,0.0,9.0,1.0,2.0,0.0,1,10.0,-1.0,0.0,-9.0,1.0,2.0,3.14,-1,20.0
"""

ZEE_SAMPLE = """Run,Event,pt1,eta1,phi1,Q1,type1,pt2,eta2,phi2,Q2,type2
1,1,40.0,1.5,0.5,-1,EB,45.0,1.2,-1.0,1,EB
"""

LONG_SAMPLE = """Run,Event,E,px,py,pz,pt,eta,phi,Q,M
1,1,25.0,3.0,4.0,24.0,5.0,2.0,0.9,-1,4.5
1,1,9.0,4.0,3.0,6.0,5.0,0.8,-0.9,1,4.5
"""

HTML_SAMPLE = """<!DOCTYPE html>
<html><head><title>Page not found</title></head><body></body></html>
"""


def test_load_dielectron_csv():
    fmt, records = load_collision_csv(str(DATA_DIR / "dielectron.csv"))
    assert fmt == "wide_full"
    assert len(records) > 90000
    assert records[0]["M"] >= 2.0


def test_load_zee_csv_computes_mass():
    fmt, records = load_collision_csv(str(DATA_DIR / "Zee.csv"))
    assert fmt == "wide_pt_eta_phi"
    assert len(records) == 10000
    masses = [row["M"] for row in records]
    assert min(masses) > 50
    assert max(masses) < 130
    assert np.median(masses) > 85


def test_wide_sample_preserves_mass():
    fmt, records = load_collision_csv_from_text(WIDE_SAMPLE)
    assert fmt == "wide_full"
    assert records[0]["M"] == 20.0
    assert records[0]["E1"] == 10.0


def test_zee_sample_computes_energy_and_mass():
    fmt, records = load_collision_csv_from_text(ZEE_SAMPLE)
    assert fmt == "wide_pt_eta_phi"
    assert records[0]["E1"] > 0
    assert records[0]["E2"] > 0
    assert records[0]["M"] > 0


def test_long_format_pairs_electrons():
    fmt, records = load_collision_csv_from_text(LONG_SAMPLE)
    assert fmt == "long_per_electron"
    assert len(records) == 1
    assert records[0]["E1"] == 25.0
    assert records[0]["E2"] == 9.0
    assert records[0]["M"] == 4.5


def test_html_file_is_rejected():
    with pytest.raises(CollisionDataError, match="HTML error page"):
        load_collision_csv_from_text(HTML_SAMPLE)


def test_local_jpsi_csv_loads():
    path = DATA_DIR / "Jpsi_ElEl_2010.csv"
    if not path.exists():
        pytest.skip("local Jpsi sample missing")
    fmt, records = load_collision_csv(str(path))
    assert fmt == "wide_full"
    assert len(records) == 2000
    assert 2.0 <= min(row["M"] for row in records) <= 5.0