"""IBM Quantum Runtime configuration helpers."""

from __future__ import annotations

import os

from services.quantum.distribution import DEFAULT_BINS

TRUE_VALUES = {"1", "true", "yes", "on"}
DEFAULT_SHOTS = int(os.environ.get("QMC_SHOTS", "4096"))


def real_backend_enabled() -> bool:
    return os.environ.get("USE_REAL_BACKEND", "").lower() in TRUE_VALUES


def get_runtime_status(probe: bool = False) -> dict:
    try:
        import qiskit_ibm_runtime  # noqa: F401

        runtime_installed = True
    except ImportError:
        runtime_installed = False

    status = {
        "phase": "quantum_sampling_verification",
        "real_backend_enabled": real_backend_enabled(),
        "runtime_installed": runtime_installed,
        "token_configured": bool(
            os.environ.get("IBM_QUANTUM_TOKEN") or os.environ.get("IBM_API_KEY")
        ),
        "instance_configured": bool(os.environ.get("IBM_QUANTUM_INSTANCE")),
        "channel": os.environ.get("IBM_QUANTUM_CHANNEL", "ibm_quantum_platform"),
        "requested_backend": os.environ.get("IBM_BACKEND") or None,
        "shots": DEFAULT_SHOTS,
        "mass_bins": int(os.environ.get("QMC_MASS_BINS", str(DEFAULT_BINS))),
        "encoding": os.environ.get("QMC_ENCODING", "binary_qubits"),
        "symmetry_protection": os.environ.get("QMC_SYMMETRY_PROTECTION", "false"),
        "databank_enabled": os.environ.get("QMC_DATABANK_ENABLED", "true"),
        "databank_path": os.environ.get("QMC_DATABANK_PATH") or "data/quantum_databank/hardware_runs.jsonl",
        "policy_max_shots": int(os.environ.get("QMC_POLICY_MAX_SHOTS", "65536")),
        "policy_max_bins": int(os.environ.get("QMC_POLICY_MAX_BINS", "256")),
        "policy_allow_backend_switch": os.environ.get("QMC_POLICY_ALLOW_BACKEND_SWITCH", "true"),
        "policy_allow_symmetry_toggle": os.environ.get("QMC_POLICY_ALLOW_SYMMETRY_TOGGLE", "true"),
        "ibm_timeout_seconds": int(os.environ.get("IBM_RUNTIME_TIMEOUT", "900")),
    }

    if probe and real_backend_enabled() and runtime_installed and status["token_configured"]:
        from services.quantum.ibm_client import probe_ibm_runtime

        status["ibm_probe"] = probe_ibm_runtime()
        status["ibm_ready"] = bool(status["ibm_probe"].get("ok"))
    else:
        status["ibm_ready"] = None
        if real_backend_enabled() and not status["token_configured"]:
            status["ibm_probe"] = {
                "ok": False,
                "error": "Token missing",
                "hint": "Set IBM_QUANTUM_TOKEN in .env",
            }

    if real_backend_enabled() and not status["instance_configured"]:
        status["instance_hint"] = (
            "IBM_QUANTUM_INSTANCE is empty; the SDK will auto-pick an instance (often "
            "open-plan QEC). Set the instance CRN from your IBM Quantum dashboard for "
            "predictable hardware access."
        )

    return status
