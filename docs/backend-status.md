# Backend Status Report

## Last Updated: May 13, 2026

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
│  /api/quantum/job → Queue Aer Estimator job │
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
| `/api/quantum/job` | POST | Working | `BackgroundTasks` → `quantum_service.run_quantum_job` |
| `/api/quantum/result/{id}` | GET | Working | Status, `processed`/`total`, `scores_applied` |

**Backend:** `qiskit_aer.primitives.Estimator` (not IBM Runtime). Chunk size: env `QUANTUM_CHUNK_SIZE` (default 120).

### `services/analysis.py`
- `load_csv_data`, `summarize_stats`, `identify_particle`, `find_outliers`
- `PARTICLE_WINDOWS`: η, ρ/ω (`rho_omega`), φ, J/ψ, ψ(2S), Υ, Z⁰
- **Status:** Working

### `services/plots.py`
- `plot_mass_histogram`, `plot_energy_vs_mass` (offline / optional)
- **Status:** Present; not used by API

### `services/quantum_service.py`
- `encode_event`, `run_quantum_job`, Aer Estimator batches, writes `quantum_score` on outliers
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
| IBM Quantum Runtime | Not wired; Aer only |
| `USE_REAL_BACKEND` env | Not implemented |
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

- IBM Runtime + `USE_REAL_BACKEND` toggle  
- Stricter CSV schema validation and upload size limits  
- Integration test suite for `/api/*`  
- Production CORS allowlist  
