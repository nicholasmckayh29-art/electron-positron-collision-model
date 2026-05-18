# Project Planning: Quantum Particle Collision Visualizer

## Vision

Upload a dielectron collision dataset → run statistical analysis → identify outlier events
by invariant mass → **match each outlier to a known particle** → render an interactive 3D
model of that particle in the browser. Quantum Runtime (Estimator) provides a second layer
of anomaly scoring on top of the classical z-score pass.

The experience: a physicist (or curious student) uploads their CMS data, sees the mass
spectrum light up with labeled peaks, clicks an outlier event, and watches a 3D particle
model rotate on screen with decay channel annotations.


*** Use QC to generate momentum vectors ?? 
*** Implement hamiltonians to solve schrodingers equations 
*** Sample and solve DEs using monet carlos


---

## Implementation status *(May 2026)*

| Area | Status | Notes |
|------|--------|--------|
| Phase 1 — Script cleanup | **Done** | `analysis.py`, `plots.py`, `Stats` / `OutlierEvent`, `identify_particle()`, docstrings |
| Phase 2 — Backend (FastAPI) | **Done** | Shared `session_store.py`; live routes: `/api/upload`, `/api/stats`, `/api/outliers`, `/api/spectrum` |
| Phase 3 — Frontend | **Done** | Vite + React + Tailwind + Recharts + R3F; components per plan under `frontend/src/` |
| 3D viewer | **Done (MVP)** | Schematic scenes in `ParticleViewer3D.jsx` (not separate `particles/*.jsx` modules) |
| Phase 4 — Quantum | **Partial** | QMC mass-window observable runs locally by default; **IBM Quantum Runtime SamplerV2 wired behind `USE_REAL_BACKEND`** |
| Phase 5 — Polish / deploy | **Partial** | `pytest` + `tests/test_analysis.py`; root + backend README; Docker / prod CORS **TODO** |

**Deviations from this document’s snippets:** ansatz is a fixed **3-parameter RY + CX** circuit (not `RealAmplitudes(3, reps=2)`); API paths use the **`/api`** prefix. There is **no** separate `GET /identify` route (identification runs inside outlier pipeline).

---

## Particle Identification Logic

Invariant mass M (GeV) maps to known particles via mass windows:

| Particle | Mass (GeV) | Decay shown | Notes |
|---|---|---|---|
| η (eta meson) | ~0.548 | η → γγ | Light neutral meson |
| ρ / ω | ~0.775 / ~0.782 | ρ → e⁺e⁻ | Nearly degenerate |
| φ (phi meson) | ~1.019 | φ → e⁺e⁻ | Strange quark content |
| J/ψ | ~3.097 | J/ψ → e⁺e⁻ | Charmonium, very clean peak |
| ψ(2S) | ~3.686 | ψ(2S) → e⁺e⁻ | Excited charmonium |
| Υ (upsilon) | ~9.46 | Υ → e⁺e⁻ | Bottomonium |
| Z boson | ~91.2 | Z → e⁺e⁻ | Electroweak, dominant peak |
| Unknown / exotic | outside windows | — | Flag for quantum review |

### Matching function (backend)

```python
PARTICLE_WINDOWS = [
    {"name": "eta",      "symbol": "η",     "mass": 0.548,  "width": 0.05,  "color": "#a8dadc"},
    {"name": "rho",      "symbol": "ρ/ω",   "mass": 0.778,  "width": 0.05,  "color": "#457b9d"},
    {"name": "phi",      "symbol": "φ",     "mass": 1.019,  "width": 0.02,  "color": "#1d3557"},
    {"name": "jpsi",     "symbol": "J/ψ",   "mass": 3.097,  "width": 0.05,  "color": "#e63946"},
    {"name": "psi2s",    "symbol": "ψ(2S)", "mass": 3.686,  "width": 0.05,  "color": "#f4a261"},
    {"name": "upsilon",  "symbol": "Υ",     "mass": 9.460,  "width": 0.10,  "color": "#2a9d8f"},
    {"name": "z_boson",  "symbol": "Z⁰",    "mass": 91.2,   "width": 3.0,   "color": "#e9c46a"},
]

def identify_particle(mass_gev: float) -> dict:
    for p in PARTICLE_WINDOWS:
        if abs(mass_gev - p["mass"]) <= p["width"]:
            return p
    return {"name": "unknown", "symbol": "?", "mass": mass_gev, "color": "#cccccc"}
```

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   React Frontend                     │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ CSV Upload  │  │ Mass Spectrum│  │  3D Particle │ │
│  │ + Stats     │  │ Histogram    │  │  Viewer      │ │
│  │ Panel       │  │ (Recharts)   │  │  (Three.js)  │ │
│  └─────────────┘  └──────────────┘  └─────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Outlier Table  │  Event Detail  │  Quantum Job │ │
│  │  (identified    │  Card (E1,E2,M │  Panel       │ │
│  │   particles)    │   + particle)  │              │ │
│  └─────────────────────────────────────────────────┘ │
└───────────────────────┬──────────────────────────────┘
                        │ REST / JSON
┌───────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                      │
│  /upload  /stats  /outliers  /identify  /quantum/*   │
└───────────────────────┬──────────────────────────────┘
                        │ Qiskit Runtime SDK
┌───────────────────────▼──────────────────────────────┐
│              IBM Quantum Runtime                     │
│           Estimator primitive (3-qubit)              │
└──────────────────────────────────────────────────────┘
```

---

## Phase 1 — Script Cleanup

**Goal:** Production-ready analysis module, no dead code.  
**Status:** Done *(May 2026)*

### Changes from original

- [x] Remove all commented-out IQR blocks from `test_data_against_stats()`
- [x] Remove redundant inline comments
- [x] Replace 4-tuple return of `summarize_stats()` with `Stats` dataclass
- [x] Extract `FIELDS_TO_CHECK = ['E1', 'E2', 'M']` as constant
- [x] Split plotting into `plots.py`
- [x] Add docstrings to all public functions
- [x] Add `identify_particle()` to `analysis.py`

### Cleaned core types

```python
from dataclasses import dataclass

@dataclass
class Stats:
    z: dict        # {feature: {mean, std}}
    min: dict      # {feature: float}
    max: dict      # {feature: float}

@dataclass
class OutlierEvent:
    run: float
    event: float
    E1: float
    E2: float
    M: float
    z_scores: dict          # {feature: z_value}
    particle: dict          # from identify_particle()
    quantum_score: float    # filled in after quantum job; None until then
```

---

## Phase 2 — Backend (FastAPI)

**Stack:** Python 3.11+, FastAPI, Uvicorn, Pandas, NumPy, Qiskit IBM Runtime  
**Status:** Data + spectrum API **done**; session in `services/session_store.py`; routes mounted under **`/api`**

### Folder structure

```
backend/
├── main.py
├── routers/
│   ├── data.py          # /upload, /stats, /outliers, /identify
│   └── quantum.py       # /quantum/job, /quantum/result/{id}
├── services/
│   ├── analysis.py      # cleaned script + identify_particle()
│   ├── quantum_service.py
│   └── job_store.py     # in-memory job tracker
├── models/
│   └── schemas.py       # Pydantic models for all responses
└── requirements.txt
```

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Parse CSV, cache in session, return shape + columns |
| GET | `/stats` | Return Stats dataclass as JSON |
| GET | `/outliers` | Return list of OutlierEvent with particle identifications |
| GET | `/spectrum` | Return binned M histogram data for all 99k+ events |
| POST | `/quantum/job` | Encode outlier E1/E2/M → submit Estimator job |
| GET | `/quantum/result/{job_id}` | Poll job, return quantum_score per event when ready |

### Spectrum endpoint (used by histogram)

Returns binned counts across full M range so the frontend can render the complete
mass spectrum — not just outliers — and show where peaks fall:

```python
@router.get("/spectrum")
def get_spectrum(bins: int = 200):
    masses = [r["M"] for r in session_data]
    counts, edges = np.histogram(masses, bins=bins)
    return {
        "edges": edges.tolist(),
        "counts": counts.tolist(),
        "particles": PARTICLE_WINDOWS   # overlay reference lines
    }
```

---

## Phase 3 — Frontend (React + Three.js)

**Stack:** React 18, Vite, Recharts, Three.js (via @react-three/fiber + @react-three/drei),
TailwindCSS, Axios  
**Status:** Done *(May 2026)* — `frontend/`; spectrum bin-click zooms mass axis; outlier table does **not** auto-filter by bin (table stays paginated API-driven)

### Folder structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── FileUpload.jsx           # CSV drag-and-drop
│   │   ├── StatsPanel.jsx           # Mean/std summary cards
│   │   ├── MassSpectrum.jsx         # Full histogram with particle peak labels
│   │   ├── OutlierTable.jsx         # Sortable table with particle badge per row
│   │   ├── EventDetailCard.jsx      # E1, E2, M + identified particle info
│   │   ├── ParticleViewer3D.jsx     # Three.js particle model
│   │   └── QuantumJobPanel.jsx      # Submit + poll + score display
│   ├── data/
│   │   └── particleModels.js        # 3D geometry configs per particle type
│   ├── api/
│   │   └── client.js
│   ├── App.jsx
│   └── main.jsx
└── package.json
```

### MassSpectrum component

- Full Recharts BarChart of all ~100k event masses (binned by backend)
- Vertical reference lines at each known particle mass (labeled with symbol)
- Outlier events highlighted as red overlay bars
- Click a bar → filter OutlierTable to that mass range

```jsx
<ReferenceLine x={91.2}  stroke="#e9c46a" label="Z⁰"  />
<ReferenceLine x={3.097} stroke="#e63946" label="J/ψ" />
<ReferenceLine x={9.46}  stroke="#2a9d8f" label="Υ"   />
```

### OutlierTable component

Each row shows: Run, Event, E1, E2, M, z-score flags, **particle badge**, quantum score.
Click a row → open EventDetailCard + load ParticleViewer3D.

### ParticleViewer3D — core feature

Uses `@react-three/fiber` to render a 3D model of the identified particle.
Models are symbolic/schematic (not photo-realistic) — quarks as colored spheres
connected by gluon springs, or lepton pair trajectories for leptonic decays.

```
Particle model configs (particleModels.js):

Z⁰  boson    → large neutral sphere + two electron trajectory arcs (e⁺e⁻ decay)
J/ψ meson    → charm quark (red) + anticharm (blue) orbiting each other
Υ   meson    → bottom quark (green) + antibottom orbiting, larger radius
φ   meson    → strange (purple) + antistrange
ρ/ω meson    → up/down quarks, fast decay shown as pion tracks
unknown      → wireframe sphere with pulsing glow + "Exotic?" label
```

Each model:
- Rotates slowly on Y axis (auto-rotate)
- Shows particle name, symbol, PDG mass, and decay channel as HTML overlay
- Color-coded by quark content
- On hover: shows the specific event's M value vs PDG mass (Δ label)

### UI flow (E2E user journey)

```
1. Land on app → drag-and-drop CSV upload area
2. Upload dielectron.csv
   → StatsPanel appears: mean/std for E1, E2, M
   → MassSpectrum histogram renders with particle peak lines
3. Click "Find Outliers"
   → OutlierTable populates (3547 rows for example data)
   → Each row has colored particle badge (Z⁰, J/ψ, Υ, Unknown, etc.)
4. Click any row (e.g., Run:147115 Event:195828159 M=91.82)
   → EventDetailCard shows: E1=191.77, E2=199.88, M=91.82
   → Identified as: Z⁰ boson (PDG: 91.19 GeV, Δ = +0.63 GeV)
   → ParticleViewer3D loads Z boson model, rotates in panel
   → Decay annotation: Z⁰ → e⁺ + e⁻
5. Click "Run Quantum Analysis"
   → Quantum job submitted for all outlier E1/E2/M vectors
   → Progress bar polls /quantum/result every 5s
   → When complete: OutlierTable gains quantum_score column
   → Events with high quantum scores highlighted in orange
   → These are candidates for truly exotic / unexpected decays
```

---

## Phase 4 — IBM Quantum Integration

**Status:** QMC-style invariant-mass observable path implemented locally by default. The placeholder **Aer Estimator** / `<ZZZ>` outlier scorer has been replaced. IBM Runtime execution is wired through SamplerV2 when `USE_REAL_BACKEND=true`.

**Hardware validation:** IBM Runtime completed a `Z0` mass-window probability job on `ibm_marrakesh` with `1024` shots. The `5`-qubit circuit estimated `0.0693 +/- 0.0079`, compared with an exact classical probability of `0.0936` and a binned classical baseline of `0.1019`.

**Research claim:** Hardware-backed prototype of a quantum sampling observable for collider invariant-mass resonance analysis, validated against classical baselines on real IBM Quantum hardware.

### Encoding strategy

Discretize the uploaded event distribution by invariant mass `M`, then prepare amplitudes proportional to the square root of each bin probability:

```python
probabilities = histogram_counts / total_events
qc.initialize(np.sqrt(probabilities), range(num_qubits))
```

The first observable estimates the probability that an uploaded event lies inside the most populated known resonance mass window. The result is reported with an exact classical baseline, a binned baseline, shot count, uncertainty, circuit width/depth, and backend metadata. This is a hardware-shaped QMC/QAE stepping stone, not a claim of speedup yet.

### Backend quantum service

```python
observable = infer_mass_window_observable(session_data)
distribution = build_mass_distribution(session_data, observable)
circuit = build_qmc_circuit(distribution["probabilities"])
result = estimate_observable_locally(circuit, distribution["good_bins"], shots)
```

### Local dev fallback

Local development uses Qiskit `Statevector` sampling. Setting `USE_REAL_BACKEND=true` submits the measured QMC circuit to IBM Runtime SamplerV2, so keep `QMC_SHOTS` low while testing limited runtime.

---

## Phase 5 — Particle Model Asset Plan

For each particle type, define the 3D scene in `particleModels.js`:

```js
export const PARTICLE_MODELS = {
  z_boson: {
    label: "Z⁰ Boson",
    pdgMass: 91.1876,
    decay: "Z⁰ → e⁺ + e⁻",
    scene: "ZBosonScene",
    color: "#e9c46a",
  },
  jpsi: {
    label: "J/ψ Meson",
    pdgMass: 3.0969,
    decay: "J/ψ → e⁺ + e⁻",
    scene: "CharmoniumScene",
    color: "#e63946",
  },
  upsilon: {
    label: "Υ Meson",
    pdgMass: 9.4603,
    decay: "Υ → e⁺ + e⁻",
    scene: "BottomoniumScene",
    color: "#2a9d8f",
  },
  unknown: {
    label: "Exotic Candidate",
    pdgMass: null,
    decay: "Unknown",
    scene: "ExoticScene",
    color: "#cccccc",
  },
}
```

Each scene component is a self-contained `@react-three/fiber` canvas with:
- Quark spheres (colored by quark type)
- Animated gluon springs between quarks (for mesons/baryons)
- Electron/positron trajectory arcs for leptonic decays
- Particle label as `<Html>` overlay from `@react-three/drei`

---

## Example: Mapping Your Outlier Data

From your actual output (Run 147115):

| Event | E1 | E2 | M | Identified As |
|---|---|---|---|---|
| 195828159 | 191.77 | 199.88 | 91.82 | **Z⁰ boson** (Δ +0.63 GeV) |
| 215225628 | 81.86 | 199.36 | 90.53 | **Z⁰ boson** (Δ -0.67 GeV) |
| 620342956 | 192.57 | 124.19 | 98.22 | **Z⁰ boson** (Δ +7.02 GeV) |
| 283320043 | 40.77 | 74.27 | 109.90 | **Unknown** (above Z window) |
| 489463767 | 5.97 | 262.04 | 78.58 | **Unknown** (below Z window) |
| 482008299 | 178.24 | 18.78 | 16.54 | **Unknown** (low M range) |
| 204726040 | 14.64 | 184.54 | 4.43 | **Unknown** (very low M) |

High-E events with low M (e.g., E1=178 but M=16.54) are strong exotic candidates —
the energies don't match the expected mass reconstruction. These are the events that
will score highest from the quantum Estimator.

---

## Dependencies

### Backend
```
fastapi
uvicorn[standard]
pandas
numpy
qiskit
qiskit-ibm-runtime
qiskit-aer
python-multipart
pydantic
```

### Frontend
```
react
vite
recharts
three
@react-three/fiber
@react-three/drei
tailwindcss
axios
```

---

## Milestones

*Last updated May 2026 — reflects shipped code.*

| # | Milestone | Deliverable | Status |
|---|-----------|-------------|--------|
| 1 | Script cleanup | Clean `analysis.py` + `identify_particle()` | Done |
| 2 | Backend MVP | `/api/upload`, `/api/stats`, `/api/outliers`, `/api/spectrum` | Done |
| 3 | Spectrum UI | Mass histogram with particle peak labels | Done |
| 4 | Outlier table | Particle badges, clickable rows, pagination | Done |
| 5 | 3D viewer (Z boson) | Z⁰ scene on row click | Done |
| 6 | All particle models | 7 resonances + unknown (schematic, one component) | Done (MVP) |
| 7 | Quantum integration (sim) | QMC mass-window observable estimate in panel | Done |
| 8 | Quantum integration (real) | IBM Quantum Runtime Sampler | Done |
| 9 | Full E2E | Upload → spectrum → outlier → 3D → QMC observable | Done (sim + hardware run) |

---

## Open Questions

- [x] **3D model fidelity:** MVP uses **schematic** geometry in `ParticleViewer3D.jsx`; GLTF upgrade remains optional.
- [ ] Unknown/exotic events: auto-flag for quantum review when outside all mass windows?
- [x] **Session storage:** **In-memory** via `session_store` (cleared on server restart); file-backed session still optional.
- [x] **Quantum job batching:** Implemented — `QUANTUM_CHUNK_SIZE` (default **120**) in `quantum_service.py` with aggregation into session outliers.
- [ ] Add a "compare to PDG" panel showing the event M vs the particle's known width (Γ)?
- [ ] Should the 3D viewer animate the decay? (e.g., show the Z⁰ splitting into e⁺e⁻ tracks)
