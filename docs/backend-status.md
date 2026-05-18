# Backend Status Report

## Last Updated: May 18, 2026

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              FastAPI Application             │
│                                              │
│  /api/upload    → Parse CSV, session_store  │
│  /api/stats     → Return computed stats     │
│  /api/outliers  → Paginated outlier list    │
│  /api/spectrum  → Binned histogram data     │
│  /api/quantum/job → Queue QMC observable job │
│  /api/quantum/result/{id} → Poll status     │
└─────────────────────────────────────────────┘
```

---

## File Inventory & Status

### `main.py` — App Entry Point
- FastAPI app, CORS, routers `/api` (data) and `/api/quantum`
- Health: `GET /`, `GET /api/health`
- **Status:** Working

### `routers/data.py` — Data Endpoints

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/upload` | POST | Working | Parses CSV, fills `session_store`, pre-computes stats + outliers |
| `/api/stats` | GET | Working | mean/std/min/max |
| `/api/outliers` | GET | Working | Paginated (`limit` max 500), `known_only` filter |
| `/api/spectrum` | GET | Working | Binned histogram + `PARTICLE_WINDOWS` |

**Storage:** `services/session_store.py` (in-memory; cleared on restart).

### `routers/quantum.py` — Quantum Endpoints

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/quantum/job` | POST | Working | `BackgroundTasks` → QMC mass-window observable estimation |
| `/api/quantum/result/{id}` | GET | Working | Status, `processed`/`total`, `result` when complete |
| `/api/quantum/runtime` | GET | Working | Runtime configuration check; does not submit a job |

**Backend:** local Qiskit statevector sampling over a discretized invariant-mass distribution by default. Set `USE_REAL_BACKEND=true` with IBM Quantum credentials to submit the measured QMC circuit through Runtime SamplerV2.

**Hardware result:** IBM Runtime completed a `Z0` mass-window probability job on `ibm_marrakesh`: `1024` shots, `5` qubits, depth `191`, estimate `0.0693 +/- 0.0079`, exact classical probability `0.0936`, binned classical probability `0.1019`.

**Research claim:** Hardware-backed prototype of a quantum sampling observable for collider invariant-mass resonance analysis, validated against classical baselines on real IBM Quantum hardware.

### `services/analysis.py`
- `load_csv_data`, `summarize_stats`, `identify_particle`, `find_outliers`
- `PARTICLE_WINDOWS`: η, ρ/ω (`rho_omega`), φ, J/ψ, ψ(2S), Υ, Z⁰
- **Status:** Working

### `services/plots.py`
- `plot_mass_histogram`, `plot_energy_vs_mass` (offline / optional)
- **Status:** Present; not used by API

### `services/quantum_service.py`
- QMC-style observable contract, invariant-mass distribution encoding, local sampling estimate, IBM Runtime SamplerV2 execution, classical baseline comparison
- **Status:** Working

### `services/job_store.py`
- In-memory job records
- **Status:** Working

### `services/session_store.py`
- `session_data`, `session_stats`, `session_outliers`
- **Status:** Working

### `models/types.py`, `models/schemas.py`
- **Status:** Working

### `requirements.txt`
- FastAPI stack + `qiskit`, `qiskit-aer`, `pytest` (flexible pins for Python 3.9+)
- **Status:** Maintained — use UTF-8 when editing (avoid UTF-16)

---

## Known Gaps (vs aspirational docs)

| Item | Notes |
|------|--------|
| IBM Quantum Runtime | Runtime SamplerV2 wired behind `USE_REAL_BACKEND=true` |
| `USE_REAL_BACKEND` env | Local by default; real hardware mode when enabled |
| CSV column validation | Minimal — invalid rows skipped |
| Integration tests | Not yet added |

---

## Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  

---

## Next (optional)

- Repeat IBM Runtime runs across backends / shot counts for noise and scaling comparisons  
- Stricter CSV schema validation and upload size limits  
- Integration test suite for `/api/*`  
- Production CORS allowlist  
