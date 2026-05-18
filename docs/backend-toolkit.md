# Backend Toolkit & Architecture Map

## Overview

This backend is a **data analysis engine** for dielectron collision experiments.
It takes raw CMS collision data and transforms it into structured insights:
statistics → outliers → particle matches → spectrum data.

**May 2026:** Session data lives in `services/session_store.py`. Quantum analysis now estimates a QMC-style invariant-mass window observable locally, with IBM Runtime Sampler wiring left as a future backend path. Light meson windows (η, ρ/ω, φ) are present in `PARTICLE_WINDOWS` again for identification completeness.

---

## Architecture Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                               │
│                                                                  │
│  dielectron.csv ──→ POST /api/upload ──→ load_csv_data()        │
│                    Parses & validates, stores in session         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYSIS LAYER (tools)                        │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ summarize_stats()│  │  find_outliers() │  │ identify_    │  │
│  │                  │  │                  │  │ particle()   │  │
│  │ Computes:        │  │ Scans events:    │  │              │  │
│  │ • mean, std      │  │ • z-scores       │  │ Matches M to:│  │
│  │ • min, max       │  │ • threshold flag │  │ • J/ψ (3.097)│  │
│  │                  │  │ • returns events │  │ • ψ(2S)(3.686)│ │
│  │ For features:    │  │                  │  │ • Υ (9.46)   │  │
│  │ • E1, E2, M      │  │                  │  │ • Z⁰ (91.19) │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                     │                    │           │
│           ▼                     ▼                    ▼           │
│     Stats dataclass     OutlierEvent list     Particle dict     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (endpoints)                       │
│                                                                  │
│  GET /api/stats      → { z, min, max }                          │
│  GET /api/outliers   → { outliers: [...], total, has_more }     │
│  GET /api/spectrum   → { edges, counts, particles }             │
│                                                                  │
│  All responses are JSON. Ready for frontend consumption.         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Toolkit: Available Analysis Tools

### Tool 1: `summarize_stats()`

**What it does:**
Computes descriptive statistics for numeric features (E1, E2, M).

**Inputs:**
```python
data_set: list[dict]  # from load_csv_data()
```

**Outputs:**
```python
Stats(
    z = {
        'E1': {'mean': 42.3, 'std': 67.5},
        'E2': {'mean': 41.8, 'std': 65.2},
        'M':  {'mean': 18.7, 'std': 35.4}
    },
    min = {'E1': 0.01, 'E2': 0.02, 'M': 0.15},
    max = {'E1': 262.0, 'E2': 261.8, 'M': 109.9}
)
```

**Use case:**
- Frontend displays summary cards with mean/std ranges
- Used by `find_outliers()` to compute z-scores
- Baseline for understanding data distribution

---

### Tool 2: `find_outliers()`

**What it does:**
Flags events where any feature (E1, E2, M) deviates more than N standard deviations from the mean.

**Inputs:**
```python
data_set: list[dict]       # from load_csv_data()
stats: Stats               # from summarize_stats()
z_threshold: float = 3.0   # how many std devs to flag
```

**Outputs:**
```python
[
    OutlierEvent(
        run=147115,
        event=195828159,
        E1=191.77,
        E2=199.88,
        M=91.82,
        z_scores={'E1': 2.21, 'E2': 2.37, 'M': 2.06},
        particle={
            'name': 'z_boson', 'symbol': 'Z⁰', 'mass': 91.1876,
            'width': 15.0, 'color': '#e9c46a',
            'decay': 'Z⁰ → e⁺ + e⁻', 'quark_content': None
        },
        quantum_score=None
    ),
    ...
]
```

**Use case:**
- Identifies statistically unusual collision events
- Each outlier gets tagged with a particle match
- Frontend displays as sortable table

---

### Tool 3: `identify_particle()`

**What it does:**
Maps an invariant mass value to a known particle using CMS research-backed mass windows.

**Inputs:**
```python
mass_gev: float  # e.g., 91.82
```

**Outputs:**
```python
{
    'name': 'z_boson', 'symbol': 'Z⁰', 'mass': 91.1876, 'width': 15.0,
    'color': '#e9c46a', 'decay': 'Z⁰ → e⁺ + e⁻', 'quark_content': None
}
# OR if no match:
{
    'name': 'unknown', 'symbol': '?', 'mass': 91.82, 'color': '#cccccc',
    'decay': 'Unknown', 'quark_content': None
}
```

**Mass windows (research-backed):**

| Particle | Mass (GeV) | Window (±GeV) | Window Range | Source |
|----------|------------|---------------|--------------|--------|
| J/ψ | 3.097 | 0.15 | 2.947–3.247 | [CERN OD #302](physics/opendata/record-302-Jpsi-ElEl-2010.html); [arXiv:1502.02701](physics/papers/CMS-electron-reconstruction-8TeV-arXiv-1502.02701.pdf) |
| ψ(2S) | 3.686 | 0.15 | 3.536–3.836 | Same resolution regime as J/ψ ([arXiv:1502.02701](physics/papers/CMS-electron-reconstruction-8TeV-arXiv-1502.02701.pdf)) |
| Υ family | 9.460 | 1.50 | 7.96–10.96 | [CERN OD #305](physics/opendata/record-305-Upsilon-ElEl-2010.html); CMS TWiki Υ dielectron note |
| Z⁰ | 91.1876 | 15.0 | 76.19–106.19 | [arXiv:1909.04133](physics/papers/CMS-Z-cross-section-arXiv-1909.04133.pdf) CMS Z cross-section analysis |

> **Note:** η, ρ/ω, and φ are below the data floor of M ≈ 2.04 GeV for this dataset
> and have been removed. See [`physics/particle-id.md`](physics/particle-id.md) for full research basis.
>
> **Note:** Υ window covers Υ(1S), Υ(2S), and Υ(3S) as a single "Υ family" — CMS
> electron resolution cannot resolve the three states separately in dielectron data.
> Display as "Υ family" in the UI, not "Υ(1S)".

**Why these widths:** The CMS detector has electron momentum resolution of 1.7–4.5%
([arXiv:1502.02701](physics/papers/CMS-electron-reconstruction-8TeV-arXiv-1502.02701.pdf)) due to bremsstrahlung energy loss in the tracker. At M = 91 GeV,
4.5% resolution alone is ±4.1 GeV. The ±15 GeV Z⁰ window comes directly from CMS
published analysis ([arXiv:1909.04133](physics/papers/CMS-Z-cross-section-arXiv-1909.04133.pdf)). The ±1.5 GeV Υ window covers all three Υ states
because CMS explicitly states dielectron resolution cannot separate them.

**Use case:**
- Labels each outlier with a particle identity
- Frontend displays colored particle badges
- Unknown events flagged as exotic candidates

**Full research basis:** See [`physics/particle-id.md`](physics/particle-id.md)

---

### Tool 4: `np.histogram()` (via `/api/spectrum`)

**What it does:**
Bins all invariant mass values into a histogram for visualization.

**Inputs:**
```python
session_data: list[dict]  # all ~99k events
bins: int = 200           # number of bins
```

**Outputs:**
```python
{
    "edges": [0.15, 1.2, 2.3, 3.4, ...],      # bin boundaries
    "counts": [42, 1203, 89, 12, ...],         # events per bin
    "particles": [...]                         # reference lines for overlay
}
```

**Use case:**
- Frontend draws histogram chart
- Shows full mass spectrum distribution
- Particle peaks visible as spikes
- Reference lines label known particle positions

---

## Data Flow: End-to-End

```
1. User uploads dielectron.csv
        ↓
2. load_csv_data()
   - Parses CSV
   - Skips rows with NaN/empty values
   - Returns list of dicts
        ↓
3. summarize_stats()  ──→  stored in session_stats
   - Computes mean, std, min, max for E1, E2, M
        ↓
4. find_outliers()  ──→  stored in session_outliers
   - For each event, computes z-scores
   - Flags events with |z| > 3.0
   - Calls identify_particle() on each
        ↓
5. Data ready for API endpoints:
   - GET /api/stats      → returns session_stats
   - GET /api/outliers   → returns session_outliers (paginated)
   - GET /api/spectrum   → bins session_data masses
```

---

## API Quick Reference

| Endpoint | Method | Params | Returns | Purpose |
|----------|--------|--------|---------|---------|
| `/api/health` | GET | none | `{"status": "ok"}` | Check server is running |
| `/api/upload` | POST | CSV file | `{rows, columns, message}` | Ingest and analyze data |
| `/api/stats` | GET | none | `{z, min, max}` | Get computed statistics |
| `/api/outliers` | GET | `limit`, `offset`, `known_only` | `{outliers, total, has_more}` | Get flagged events |
| `/api/spectrum` | GET | `bins` (default 200) | `{edges, counts, particles}` | Get histogram data |

---

## Storage Model

**Current: In-memory globals**
```python
session_data      # list[dict]  → all parsed events (~99k)
session_stats     # Stats       → computed statistics
session_outliers  # list[OutlierEvent] → flagged events (~3.5k)
```

**Lifecycle:**
- Set by `POST /api/upload`
- Read by `GET /api/stats`, `/api/outliers`, `/api/spectrum`
- Cleared on server restart

**Why this works for MVP:**
- Simple, no file I/O overhead
- Fast response times
- Single-user context (dev/testing)

**Future upgrade paths:**
- File-based session storage (write to disk)
- Database persistence (PostgreSQL)
- Multi-session support (user IDs)
- Redis caching layer

---

## Extension Points

These are the "slots" where new tools can be added:

### 1. New Statistics
Add to `summarize_stats()`:
- Median, quartiles, skewness, kurtosis
- Per-feature correlation matrices
- Energy balance (E1 - E2 distribution)

### 2. New Outlier Methods
Replace or augment z-score in `find_outliers()`:
- IQR-based detection (already commented in original code)
- Isolation Forest (scikit-learn)
- DBSCAN clustering
- Mahalanobis distance (multivariate)

### 3. New Particle Matching
Enhance `identify_particle()`:
- Add confidence score based on Gaussian distance to peak center (not just binary in/out window)
- Use actual natural widths (Γ) from PDG in a Breit-Wigner weighting scheme
- Add low-mass particles (φ, ρ/ω, η) if dataset covers M < 2 GeV
- See [`physics/particle-id.md`](physics/particle-id.md) for full research basis before changing any widths

### 4. New API Endpoints
Add to `routers/data.py`:
- `GET /api/particles/{name}` → Get all events matching a particle
- `GET /api/events/{run}/{event}` → Get single event details
- `GET /api/compare` → Compare two datasets

### 5. Quantum Layer (Phase 4)
**Shipped (simulator):** `routers/quantum.py` + `services/quantum_service.py` — infer a resonance mass-window observable, amplitude-encode the binned invariant-mass distribution, locally sample the prepared state, and compare the estimate to exact and binned classical baselines.

**Still open:** IBM Runtime Sampler execution behind the existing `USE_REAL_BACKEND` guardrail.

---

## Decision Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Z-score threshold = 3.0 | Standard statistical outlier cutoff | 2026-04-11 |
| `known_only=True` default | Browser performance, cleaner UX | 2026-04-11 |
| Pagination cap = 500 | Prevents browser hangs on large responses | 2026-04-11 |
| In-memory storage | Simplicity for MVP, fast prototyping | 2026-04-11 |
| J/ψ width ±0.15 GeV | CERN OD record 302 selects 2–5 GeV; ±0.15 conservative relative to broad selection | 2026-04-11 |
| ψ(2S) width ±0.15 GeV | Same dielectron resolution regime as J/ψ | 2026-04-11 |
| Υ width ±1.5 GeV (family) | CERN OD record 305 selects 8–12 GeV; CMS TWiki: can't resolve 1S/2S/3S separately in dielectron | 2026-04-11 |
| Z⁰ width ±15.0 GeV | arXiv:1909.04133: \|m − 91.1876\| < 15 GeV is standard CMS fiducial window | 2026-04-11 |
| Removed η, ρ/ω, φ windows | Below data floor (M_min ≈ 2.04 GeV in dielectron.csv) | 2026-04-11 |
| Υ displayed as "Υ family" | CMS TWiki: electron resolution insufficient to separate Υ(1S/2S/3S) in dielectron channel | 2026-04-11 |
| CORS allow all (dev) | Easy frontend integration during dev | 2026-04-11 |
| QMC mass-window observable | Replaced placeholder ⟨ZZZ⟩ outlier scores with a simulator-first invariant-mass probability estimate and hardware hook | 2026-05-18 |
| η / ρ/ω / φ windows re-added | Align with planning doc & low-mass ID when data supports it | 2026-05-13 |

---

## What the Frontend Gets

When the frontend calls the backend, it receives:

### Stats
```json
{
  "z": {
    "E1": {"mean": 42.3, "std": 67.5},
    "E2": {"mean": 41.8, "std": 65.2},
    "M": {"mean": 18.7, "std": 35.4}
  },
  "min": {"E1": 0.01, "E2": 0.02, "M": 0.15},
  "max": {"E1": 262.0, "E2": 261.8, "M": 109.9}
}
```

### Outliers (page 1)
```json
{
  "outliers": [
    {
      "run": 147115,
      "event": 195828159,
      "E1": 191.77,
      "E2": 199.88,
      "M": 91.82,
      "z_scores": {"E1": 2.21, "E2": 2.37, "M": 2.06},
      "particle": {
        "name": "z_boson",
        "symbol": "Z⁰",
        "mass": 91.1876,
        "color": "#e9c46a",
        "decay": "Z⁰ → e⁺ + e⁻",
        "quark_content": null
      },
      "quantum_score": null
    }
  ],
  "total": 2847,
  "limit": 100,
  "offset": 0,
  "has_more": true
}
```

### Spectrum
```json
{
  "edges": [0.15, 0.70, 1.25, 1.80, ...],
  "counts": [42, 1203, 89, 12, ...],
  "particles": [
    {"name": "jpsi", "symbol": "J/ψ", "mass": 3.097, "color": "#e63946", ...},
    {"name": "psi2s", "symbol": "ψ(2S)", "mass": 3.686, "color": "#f4a261", ...},
    {"name": "upsilon", "symbol": "Υ family", "mass": 9.460, "color": "#2a9d8f", ...},
    {"name": "z_boson", "symbol": "Z⁰", "mass": 91.1876, "color": "#e9c46a", ...}
  ]
}
```

---

## Checklist: Before Building Frontend

- [x] `/api/upload` parses CSV correctly
- [x] `/api/stats` returns computed statistics
- [x] `/api/outliers` returns paginated results
- [x] `/api/outliers?known_only=true` filters unknowns
- [x] `/api/spectrum` returns binned histogram data
- [x] CORS middleware configured
- [x] `requirements.txt` saved
- [x] All endpoints tested with dielectron.csv
- [x] Particle windows updated to CMS research-backed values
- [x] `docs/physics/particle-id.md` added with full research basis
- [x] Frontend initialized (`frontend/`, Vite + React)
- [x] Quantum integration — QMC-style mass-window observable (IBM Runtime optional / future)
