# Backend - Quantum Particle Collision Visualizer

Planning and architecture notes live in the repo root under [`../docs/`](../docs/) (vision, daily plan, backend status/toolkit).

## Development Log

### April 11, 2026 - Project Setup & Environment


**Suggestion** 
Netlify/render/railway/vercel

**Task:** Created backend directory structure and Python virtual environment

**What was done:**
- Created folder structure: `routers/`, `services/`, `models/`, `tests/`
- Created all empty source files (`main.py`, `data.py`, `quantum.py`, `analysis.py`, etc.)
- Initialized Python virtual environment for isolated dependencies

**Commands run:**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate
pip install fastapi uvicorn[standard] pandas numpy pydantic python-multipart
```

**Issue encountered:** PowerShell execution policy blocked activation script
**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Result:** All dependencies installed and verified working

---

### April 11, 2026 - Analysis Script Cleanup & Refactoring

**Task:** Converted legacy analysis script into clean backend modules

**What was done:**
- Removed all commented-out IQR blocks from `test_data_against_stats()`
- Removed redundant inline comments
- Extracted `FIELDS_TO_CHECK = ['E1', 'E2', 'M']` as module constant
- Split plotting logic into separate `services/plots.py` module
- Replaced 4-tuple return of `summarize_stats()` with `Stats` dataclass
- Created `OutlierEvent` dataclass with particle identification field
- Added `identify_particle()` function matching invariant mass to known particles
- Added docstrings to all public functions

**Files created/modified:**
- `models/types.py` — Stats and OutlierEvent dataclasses
- `services/analysis.py` — Core analysis logic (load, stats, outliers, particle ID)
- `services/plots.py` — Matplotlib visualization functions

---

### Phase 1 — Pending Tasks

#### Script Cleanup & Refactoring
- [X] Review existing analysis script, remove commented IQR blocks
- [X] Remove redundant inline comments
- [X] Extract `FIELDS_TO_CHECK = ['E1', 'E2', 'M']` as constant
- [X] Test cleaned script runs without errors

#### Data Types
- [X] Create `backend/models/types.py` with `Stats` and `OutlierEvent` dataclasses
- [X] Refactor `summarize_stats()` to return `Stats` instead of 4-tuple
- [X] Add docstrings to all public functions

#### Particle Identification
- [X] Create `backend/services/analysis.py`
- [X] Define `PARTICLE_WINDOWS` constant (eta, rho, phi, J/ψ, ψ(2S), Υ, Z⁰)
- [X] Implement `identify_particle(mass_gev)` function
- [X] Write unit tests for particle window boundaries

#### FastAPI Endpoints
- [X] `POST /upload` — Parse CSV, cache data, return shape + columns
- [X] `GET /stats` — Return mean/std/min/max for E1, E2, M
- [X] `GET /outliers` — Return outlier events with particle IDs
- [X] `GET /spectrum` — Return binned mass histogram data

#### Quantum Endpoints
- [X] `POST /quantum/job` — Submit Estimator job for outlier events
- [X] `GET /quantum/result/{job_id}` — Poll and return quantum scores

---

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies (pinned versions)
├── README.md               # This file (dev log + runbook)
├── routers/
│   ├── data.py             # /upload, /stats, /outliers, /spectrum
│   └── quantum.py          # /quantum/* endpoints
├── services/
│   ├── analysis.py         # Core analysis logic + particle ID
│   ├── quantum_service.py  # Qiskit quantum integration
│   └── job_store.py        # Quantum job tracking
├── models/
│   ├── types.py            # Python dataclasses (Stats, OutlierEvent)
│   └── schemas.py          # Pydantic response models
└── tests/
    └── test_*.py           # Unit and integration tests
```

## Environment Setup Reference

**To recreate the environment:**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

**Run the server:**
```powershell
uvicorn main:app --reload
```

Server runs at: http://localhost:8000  
API docs at: http://localhost:8000/docs

## Troubleshooting Reference

| Problem | Solution |
|---------|----------|
| `python` not recognized | Add Python to PATH, or use `py` instead |
| Activation policy error | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `pip` not found | Use `python -m pip install ...` instead |
| Import errors | Ensure `.venv` is activated (prompt shows `(.venv)`) |
| Port 8000 in use | Use `--port 8001` or kill existing process |
