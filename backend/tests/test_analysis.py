import numpy as np

from services.analysis import identify_particle
from services.quantum_service import (
    build_mass_distribution,
    build_qmc_circuit,
    estimate_observable_locally,
    infer_mass_window_observable,
)


def test_qmc_mass_window_distribution_and_estimate():
    data = [
        {"M": 3.09},
        {"M": 3.10},
        {"M": 3.20},
        {"M": 9.46},
        {"M": 91.2},
    ]
    observable = infer_mass_window_observable(data)
    distribution = build_mass_distribution(data, observable, bins=4)
    circuit = build_qmc_circuit(distribution["probabilities"])
    result = estimate_observable_locally(circuit, distribution["good_bins"], shots=512)

    assert observable.name == "jpsi_mass_window"
    assert distribution["bin_count"] == 4
    assert np.isclose(float(np.sum(distribution["probabilities"])), 1.0)
    assert circuit.num_qubits == 2
    assert 0.0 <= result["estimate"] <= 1.0
    assert result["shots"] == 512
    assert distribution["exact_probability"] == 3 / 5


def test_identify_z_peak():
    p = identify_particle(91.2)
    assert p["name"] == "z_boson"


def test_identify_unknown():
    p = identify_particle(200.0)
    assert p["name"] == "unknown"


def test_identify_eta():
    p = identify_particle(0.55)
    assert p["name"] == "eta"
