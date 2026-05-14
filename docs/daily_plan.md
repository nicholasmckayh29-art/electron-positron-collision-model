# Electron Collision Visualizer - Phase-Based Action Plan

> **May 2026 update:** Core work through **Phase 4 (simulator quantum)** is implemented. Items still open are left as `[ ]` below (e.g. column sort, IBM Runtime, Docker, orange row highlights).

## Phase 1: Core Backend & Analysis Cleanup
**Goal:** Production-ready analysis module with FastAPI endpoints

### 1.1 Project Setup & Script Cleanup
- [X] Create `backend/` directory structure (includes `services/session_store.py`):
  ```
  backend/
  ├── main.py
  ├── routers/
  │   ├── data.py
  │   └── quantum.py
  ├── services/
  │   ├── session_store.py
  │   ├── analysis.py
  │   ├── quantum_service.py
  │   ├── job_store.py
  │   └── plots.py
  ├── models/
  │   ├── types.py
  │   └── schemas.py
  └── requirements.txt
  ```
- [X] Create virtual environment and install base dependencies:
  ```powershell
  cd backend
  python -m venv .venv
  .\.venv\Scripts\Activate
  pip install -r requirements.txt
  ```
- [X] Review existing analysis script and remove all commented-out IQR blocks
- [X] Remove redundant inline comments
- [X] Extract `FIELDS_TO_CHECK = ['E1', 'E2', 'M']` as module-level constant
- [X] Test that cleaned script runs without errors

### 1.2 Data Types & Refactoring
- [X] Create `backend/models/types.py` and implement dataclasses:
  ```python
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
- [X] Refactor `summarize_stats()` to return `Stats` dataclass instead of 4-tuple
- [X] Update all callers to use new return type
- [X] Add docstrings to all public functions
- [X] Write basic unit tests for Stats/OutlierEvent creation (`tests/test_analysis.py`)
- [X] Run existing analysis to verify no regressions

### 1.3 Particle Identification Module
- [X] Create `backend/services/analysis.py`
- [X] Define `PARTICLE_WINDOWS` constant (η, ρ/ω as `rho_omega`, φ, J/ψ, ψ(2S), Υ, Z⁰ — widths tuned in code)
- [X] Implement `identify_particle(mass_gev: float) -> dict` function
- [X] Add unit tests for particle window boundary and edge cases (`tests/test_analysis.py`)
- [X] Integrate `identify_particle()` into outlier detection pipeline
- [X] Verify OutlierEvent objects include particle identification

### 1.4 Plotting Module Extraction
- [X] Create `backend/services/plots.py`
- [X] Move matplotlib helpers into `plots.py` (`plot_mass_histogram`, `plot_energy_vs_mass`)
- [X] Plotting helpers are independent from API path and from core analysis logic (optional / offline use)
- [ ] Test that plots generate correctly with sample data *(manual)*
- [X] Clean up imports and dependencies

### 1.5 FastAPI Backend Skeleton
- [X] Create `backend/main.py` with FastAPI app initialization and CORS middleware
- [X] Create `backend/models/schemas.py` with Pydantic response models:
  - `UploadResponse` (shape, columns)
  - `StatsResponse` (mean, std, min, max per feature)
  - `OutlierEventResponse` (full event data with particle + quantum_score)
  - `SpectrumResponse` (edges, counts, particles)
- [X] Test that server starts and health check endpoint responds:
  ```powershell
  uvicorn main:app --reload
  ```

### 1.6 Upload & Stats Endpoints
- [X] Implement `POST /api/upload` in `routers/data.py`:
  - Accept CSV file upload (python-multipart)
  - Parse CSV (stdlib `csv` + numpy)
  - Validate required columns (E1, E2, M, Run, Event)
  - Cache data in `session_store`
  - Return shape and columns info
- [X] Implement `GET /api/stats` endpoint:
  - Call `summarize_stats()` on cached data
  - Return JSON matching StatsResponse schema
- [X] Add error handling for missing data, invalid CSV, etc.
- [X] Test with sample dielectron.csv

### 1.7 Outliers & Spectrum Endpoints
- [X] Implement `GET /api/outliers` endpoint:
  - Run z-score outlier detection on cached data
  - Call `identify_particle()` for each outlier
  - Return list of OutlierEvent with particle identifications (paginated)
- [X] Implement `GET /api/spectrum` endpoint:
  - Accept optional `bins` parameter (default 200)
  - Compute histogram using numpy
  - Return edges, counts, and PARTICLE_WINDOWS for overlay
- [X] Test with large dataset (99k+ events)
- [X] Verify performance and response times

**Phase 1 Deliverable:** Backend API serving stats, spectrum, and outliers with particle IDs

---

## Phase 2: React Frontend & Data Visualization
**Goal:** Complete UI for upload, spectrum viewing, and outlier exploration

### 2.1 Frontend Project Setup
- [X] Initialize React frontend (`frontend/`, Vite + React)
- [X] Install dependencies (recharts, axios, three, R3F, drei, tailwind, etc. — see `package.json`)
- [X] Configure Tailwind in `tailwind.config.js` and add directives to `index.css`
- [X] Set up folder structure (`components/`, `api/`, `data/`)
- [X] Verify app runs: `npm run dev`

### 2.2 File Upload Component
- [X] Create `src/components/FileUpload.jsx`
- [X] Implement drag-and-drop zone with visual feedback
- [X] Add file input fallback for manual selection
- [X] Wire up to `POST /api/upload` (Vite proxy to backend)
- [X] Display upload result or error message
- [X] Test with sample CSV file

### 2.3 Stats Panel Component
- [X] Create `src/components/StatsPanel.jsx`
- [X] Fetch data from `GET /api/stats`
- [X] Create summary cards for each feature (E1, E2, M) showing mean, std, min, max
- [X] Add loading and error states (upload-level)
- [X] Integrate into App.jsx after successful upload

### 2.4 Mass Spectrum Histogram
- [X] Create `src/components/MassSpectrum.jsx`
- [X] Fetch data from `GET /api/spectrum`
- [X] Implement Recharts BarChart with binned data
- [X] Add vertical ReferenceLines for each known particle mass
- [X] Label each reference line with particle symbol
- [X] Add tooltip showing bin center, count, outliers-in-bin
- [X] Bin click zooms X-axis mass range

### 2.5 Outlier Table Component
- [X] Create `src/components/OutlierTable.jsx`
- [X] Fetch data from `GET /api/outliers` (via `App` state)
- [ ] Implement sortable table columns *(not implemented — pagination only)*
- [X] Add particle badge column with colored labels
- [ ] Implement column sorting and search/filter functionality
- [X] Add pagination for large outlier sets
- [X] Make rows clickable → trigger EventDetailCard + 3D viewer
- [X] Test with outlier data from backend

### 2.6 Event Detail Card
- [X] Create `src/components/EventDetailCard.jsx`
- [X] Accept event data as prop from OutlierTable click
- [X] Display: Run, Event, E1, E2, M values
- [X] Show identified particle info (symbol, PDG mass, delta, decay channel)
- [X] Visual distinction for unknown via badge + 3D exotic scene
- [X] Test with sample outlier event data

### 2.7 Integration & Polish
- [X] Update `src/App.jsx` to orchestrate all components
- [X] Implement complete user flow: Upload → Stats + Spectrum → Outliers → Detail + 3D
- [ ] Add React error boundaries *(not implemented)*
- [X] Test complete E2E flow with sample data
- [X] Basic responsive / dark styling (full polish in Phase 5)

**Phase 2 Deliverable:** Full UI working - upload CSV, view spectrum, explore outliers with particle IDs

---

## Phase 3: 3D Particle Viewer
**Goal:** Interactive 3D visualization of identified particles

### 3.1 Three.js Setup & Particle Model Data
- [X] Install 3D dependencies (`three`, `@react-three/fiber`, `@react-three/drei`)
- [X] Create `src/data/particleModels.js` with PARTICLE_MODELS for all types:
  - z_boson, jpsi, psi2s, upsilon, phi, rho_omega, eta, unknown
- [ ] Document quark color conventions *(informal in code only)*

### 3.2 Base 3D Viewer Component
- [X] Create `src/components/ParticleViewer3D.jsx`
- [X] Set up `@react-three/fiber` Canvas with OrbitControls
- [X] Add lighting and camera positioning
- [X] Scene primitives per particle type (not single placeholder only)
- [X] Add HTML overlay showing particle name / PDG
- [X] Test basic 3D scene renders and rotates

### 3.3 Z Boson 3D Scene
- [X] Z scene implemented **inside** `ParticleViewer3D.jsx` (no separate `ZBosonScene.jsx`)
- [X] Large icosahedron + two e⁺/e⁻ spheres (schematic)
- [ ] Animated decay arcs *(static geometry)*
- [X] HTML overlay: label, mass
- [ ] Hover interaction for Δ mass *(not implemented)*
- [X] Scene loads when Z⁰ outlier is selected

### 3.4 Meson Scenes (J/ψ, Υ, φ)
- [X] J/ψ & ψ(2S): shared charmonium-style scene in `ParticleViewer3D.jsx`
- [X] Υ: bottomonium-style scene (two green spheres)
- [X] φ: uses generic **light meson** octahedron (not dedicated strange pair scene file)
- [X] Test scenes render and animate (auto-rotate)

### 3.5 Light Meson & Unknown Scenes
- [X] η / ρ/ω / φ fall through to `LightMesonScene` in `ParticleViewer3D.jsx` *(no separate RhoOmega/Eta files)*
- [X] Unknown: `ExoticScene` wireframe
- [ ] Dedicated η → γγ or ρ pion-track visuals *(not implemented)*
- [X] Unknown particle displays for out-of-window events

### 3.6 Integration & Polish
- [X] Wire 3D viewer beside EventDetailCard in `App.jsx`
- [X] Pass event M to overlay; PDG delta in detail card
- [ ] Smooth scene transitions / camera reset button
- [ ] Loading spinner for GL *(minimal — local scenes)*
- [X] Verify all particle `name` keys resolve to a scene

**Phase 3 Deliverable:** Click any outlier → see identified particle rotating in 3D with annotations

---

## Phase 4: IBM Quantum Integration
**Goal:** Quantum anomaly scoring for outlier events

### 4.1 Quantum Service Setup
- [X] Add quantum dependencies (`qiskit`, `qiskit-aer` in `requirements.txt`; IBM runtime optional / not required for sim)
- [X] Create `backend/services/quantum_service.py`
- [X] Implement `encode_event()` (normalize E1, E2, M to [0, π] using dataset maxima)
- [X] Define `SparsePauliOp("ZZZ")` observable; ansatz is **3× RY + CX** (not `RealAmplitudes`)
- [ ] Add environment variable `USE_REAL_BACKEND` and IBM path *(not implemented)*
- [ ] Implement backend selection logic (real IBM vs Aer) *(Aer only today)*
- [X] Test circuit execution via Estimator batches

### 4.2 Quantum Job Management
- [X] Create `backend/services/job_store.py` with in-memory job tracker
- [X] Implement background worker `run_quantum_job()` (encode all outliers, Estimator batches, map scores)
- [X] Store `job_id`, status, progress (`processed` / `total`)
- [X] Map ⟨ZZZ⟩ results back to `session_outliers` by run/event key
- [X] Test job submission with **qiskit-aer** Estimator

### 4.3 Quantum API Endpoints
- [X] Implement `POST /api/quantum/job` in `routers/quantum.py` (queues `BackgroundTasks`)
- [X] Implement `GET /api/quantum/result/{job_id}` (status + progress; scores applied on session rows)
- [X] Add error handling for failed jobs
- [X] Test quantum job flow via API + UI

### 4.4 Quantum Batching Strategy
- [X] Implement batching (`QUANTUM_CHUNK_SIZE`, default 120)
- [X] Single logical job with internal chunk loop *(not multiple job_ids)*
- [X] Aggregate scores into one pass over outliers
- [X] Test with large outlier counts

### 4.5 Frontend Quantum Panel & Score Integration
- [X] Create `src/components/QuantumJobPanel.jsx` (submit + poll ~2s)
- [X] OutlierTable includes `quantum_score` column (⟨ZZZ⟩)
- [ ] Color-code high quantum scores (orange row highlight)
- [ ] Sorting by `quantum_score`
- [ ] EventDetailCard shows quantum score inline *(only in table column today)*
- [X] End-to-end: submit → poll → refresh outliers

**Phase 4 Deliverable:** Run quantum analysis on outliers → get anomaly scores in UI

---

## Phase 5: Testing, Polish & Deployment
**Goal:** Production-ready application with full documentation

### 5.1 Error Handling & Edge Cases
- [ ] Add validation for CSV format (required columns, data types)
- [ ] Handle missing/null values gracefully
- [ ] Add retry logic for failed quantum jobs
- [ ] Implement graceful degradation if quantum backend unavailable
- [ ] Test with corrupted/malformed CSV, small datasets, no-outlier datasets
- [ ] Add user-friendly error messages throughout

### 5.2 Performance Optimization
- [ ] Profile backend response times for large datasets
- [ ] Optimize pandas operations (vectorize where possible)
- [ ] Add caching for repeated API calls
- [ ] Implement lazy loading/virtual scrolling in OutlierTable
- [ ] Optimize Recharts and 3D scene performance
- [ ] Test with 100k+ event dataset

### 5.3 UI/UX Polish
- [ ] Add application header/title and consistent styling
- [ ] Implement responsive layout for different screen sizes
- [ ] Add tooltips/help text for quantum scores, particle IDs
- [ ] Add loading animations/skeleton screens
- [ ] Create "About" or "Help" modal explaining the app
- [ ] Test complete UX flow with non-technical user

### 5.4 Testing Suite
- [X] Create `backend/tests/` directory
- [X] Write unit tests for: `identify_particle()`, `encode_event()` (`tests/test_analysis.py`)
- [ ] Write unit tests for `summarize_stats()` *(optional)*
- [ ] Write integration tests for all API endpoints
- [X] Run test suite — `pytest` passes
- [ ] Add test coverage reporting

### 5.5 Documentation
- [X] Write backend README.md (setup, API docs)
- [ ] Write frontend README.md (setup, scripts) *(covered in root README quick start)*
- [X] Create root project README.md (quick start, layout)
- [ ] Add inline code comments for complex logic *(partial)*
- [ ] Document particle model conventions and quantum encoding strategy *(see planning docs)*

### 5.6 Deployment Prep
- [ ] Create `backend/Dockerfile` and `frontend/Dockerfile`
- [ ] Create `docker-compose.yml` for local deployment
- [ ] Add `.env.example` files with required variables
- [ ] Test Dockerized deployment locally
- [ ] Add deployment documentation
- [ ] Document IBM Quantum authentication setup

### 5.7 Final Review & Demo
- [ ] Run complete E2E test with fresh dataset
- [ ] Record demo video/GIF of full user journey
- [ ] Review all open questions from planning.md and document decisions
- [ ] Create presentation/demo script

**Phase 5 Deliverable:** Production-ready, documented, and deployable application

---

## Phase Dependencies & Order

```
Phase 1 (Backend) → Phase 2 (Frontend) → Phase 3 (3D Viewer)
       ↓                                       ↓
Phase 4 (Quantum) ←────────────────────────────┘
       ↓
Phase 5 (Polish & Deploy)
```

**Minimum Viable Flow:** Phases 1–2 ✅  
**Full Experience (simulator quantum + 3D):** Phases 1–4 ✅ on **Aer**; Phase 4 **IBM hardware** + Phase 5 production hardening still open.

---

## Success Criteria

### Phase 1 ✅
- [X] All 4 backend data endpoints working (`/api/upload`, `/api/stats`, `/api/outliers`, `/api/spectrum`)
- [X] Particle identification for 7 known windows + unknown
- [X] Outlier detection with z-scores functioning

### Phase 2 ✅
- [X] Upload CSV → Stats + Spectrum display
- [X] Outlier table with particle badges, clickable rows
- [X] Event detail card showing particle info

### Phase 3 ✅
- [X] All particle `name` keys map to a 3D schematic (single `ParticleViewer3D.jsx`)
- [X] Click outlier → 3D model loads with annotations
- [X] Rotation / OrbitControls

### Phase 4 ✅ (simulator)
- [X] Quantum job submission and polling working
- [X] Anomaly scores appear in outlier table
- [ ] High-score events highlighted in UI

### Phase 5 ✅
- [ ] Complete E2E automated test
- [X] Core unit tests pass (`pytest`)
- [X] Documentation sufficient for local dev (README)
- [ ] Deployable via Docker

---

## Key Decisions

1. **3D Model Fidelity:** Schematic (colored spheres + animations) for MVP, GLTF upgrade later — **shipped in `ParticleViewer3D.jsx`**
2. **Unknown/Exotic Flag:** Auto-flag events outside all mass windows — **not auto-queued for quantum** (manual “Run quantum job”)
3. **Session Storage:** In-memory `session_store` for MVP
4. **Quantum Batching:** Chunked Estimator runs via `QUANTUM_CHUNK_SIZE` (default 120)
5. **Decay Animation:** Stretch goal — not in current UI
6. **Backend:** **qiskit-aer `Estimator` only**; IBM Quantum Runtime deferred

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| IBM Quantum job failures | AerSimulator fallback + retry logic |
| Large dataset performance | Pagination + optimized pandas ops |
| 3D rendering performance | Reduce polygon count + lazy load scenes |
| Quantum API quota/costs | Start with simulator + monitor usage |
| Data format inconsistencies | Robust validation + document expected format |
