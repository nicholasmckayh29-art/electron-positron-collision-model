from services.quantum.observables import list_verification_observables, observable_from_particle
from services.quantum.pipeline import SnapshotVerificationPipeline, classical_ground_truth

SAMPLE = [
    {"M": 3.09},
    {"M": 3.10},
    {"M": 3.20},
    {"M": 91.2},
    {"M": 91.5},
]


def test_list_verification_observables_includes_auto_and_jpsi():
    items = list_verification_observables()
    ids = {item["id"] for item in items}
    assert "auto" in ids
    assert "jpsi" in ids
    assert "z_boson" in ids


def test_classical_ground_truth_jpsi_window():
    gt = classical_ground_truth(SAMPLE, particle_name="jpsi")
    assert gt["observable"]["name"] == "jpsi_mass_window"
    assert 0.0 <= gt["exact_classical_probability"] <= 1.0
    assert "discretization_error" in gt


def test_pipeline_z_boson_verification_metrics():
    pipeline = SnapshotVerificationPipeline()
    result = pipeline.run(SAMPLE, shots=256, particle_name="z_boson", bins=4)
    payload = result.to_job_payload()
    assert payload["observable"]["name"] == "z_boson_mass_window"
    assert "verification" in payload
    assert "quantum_vs_exact" in payload["verification"]
    assert payload["phase"] == "quantum_sampling_verification"


def test_observable_from_particle_matches_analysis_windows():
    obs = observable_from_particle("z_boson")
    assert obs.mass_center == 91.1876
