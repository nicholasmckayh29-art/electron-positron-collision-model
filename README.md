# Quantum Particle Collision Visualizer

**Version 1.2.0** · July 2026

FastAPI backend plus a React (Vite) UI for dielectron CMS-style CSVs: statistics, invariant-mass spectrum, outlier detection, particle ID by mass windows, and a **Quantum Monte Carlo-style mass-window observable** prototype. The quantum path runs locally by default and can submit the same observable to IBM Quantum Runtime.

## Problem

Particle collision analysis often starts with large dielectron CSV datasets where the important signal is hidden inside invariant-mass distributions. The problem is that the classical analysis, plotting, particle-window matching, and quantum experimentation usually happen in separate tools.

That split makes it hard to answer the research question cleanly: can a quantum sampling observable reproduce or benchmark a resonance signal against a trusted classical baseline?

## Solution

So this project puts the workflow into one reproducible app. A user uploads a dielectron CSV, the backend computes classical statistics, spectra, outliers, and particle-window matches, and then the system runs a Quantum Monte Carlo-style mass-window observable against the same data.

The quantum path runs locally by default, but it can also submit the observable to IBM Quantum hardware. Version 1.1.0 adds adaptive verification, so the backend can re-run a quantum observable, tune shots and policy choices, log hardware runs, and summarize which pathways perform best.

## Benefit

The benefit is a hardware-backed research prototype that compares quantum sampling directly against classical collider baselines. In the current IBM Runtime result, a Z-boson mass-window observable ran on `ibm_marrakesh` with `1024` shots using a `5`-qubit circuit.

That produced a hardware estimate of `0.0693 +/- 0.0079`, compared with an exact classical probability of `0.0936` and a binned classical baseline of `0.1019`. It is not a quantum-advantage claim; it is a concrete NISQ feasibility benchmark and a foundation for future ML-guided quantum control.

This benchmark tests how accurately real quantum hardware can sample an encoded collider invariant-mass distribution and estimate the probability of events falling in a known particle resonance window, compared with the classical baseline.

## Research Claim

**Hardware-backed prototype of a quantum sampling observable for collider invariant-mass resonance analysis, validated against classical baselines on real IBM Quantum hardware.**

## Update 1.1.0: Adaptive Control Loop and Hardware Databank

This release adds thermostat-style quantum verification, automatic logging of real hardware runs, and tooling to compare pathway efficiency for future ML training.

| Feature | Description |
|---------|-------------|
| **Adaptive snapshot mode** | `POST /api/quantum/job` with `"mode": "adaptive_snapshot"` iteratively re-runs the mass-window observable, adjusts shot budget, and stops when error vs target or statistical convergence criteria are met. |
| **Policy adaptive controller** | Multi-knob policy chooses `shots`, `bins`, `symmetry`, and backend switching while applying historical bias correction from hardware databank runs. |
| **Richer single-run telemetry** | Each run now logs top histogram states and distinct observed bins so one run yields more distribution-level data. |
| **Iteration telemetry** | Job results include `iterations[]` (per-round estimate, error, shots) and `convergence` (converged flag, stopping reason, final error). |
| **Local hardware databank** | Every successful IBM Runtime job is appended to `data/quantum_databank/hardware_runs.jsonl` (configurable via `QMC_DATABANK_*`). |
| **Efficiency leaderboard** | `scripts/summarize_quantum_databank.py` ranks pathways by accuracy, uncertainty, shot cost, and adaptive iteration cost. |
| **Runtime config surface** | `GET /api/quantum/runtime` reports databank path/enabled state alongside IBM credentials and backend settings. |

### Research Learnings

- The adaptive loop now runs all `max_iterations` hardware jobs unless `|estimate − target| ≤ epsilon`; it no longer exits early on statistical criteria alone—useful for full pathway traces in `hardware_runs.jsonl`.
- A 20-iteration `z_boson` hardware run (May 2026) exhausted iterations without meeting ε: shot budget reached 16k, final `err_abs` ≈ 0.034, `stopping_reason: max_iterations`.
- Error vs target was **not** monotonic (best ~0.00025 at iteration 7, then large regressions); shot scaling reduces `stderr` but cannot remove NISQ bias on a fixed circuit.
- Next step: ML controller trained on databank features (iteration history, circuit/backend metadata) to predict bias or recommend shots/stop—see [`docs/quantum_research.md`](docs/quantum_research.md#research-findings).

**New / extended API body fields** (`POST /api/quantum/job`):

- `mode`: `snapshot` (default) or `adaptive_snapshot`
- `target_probability`: optional float in `[0, 1]` (defaults to exact classical probability)
- `max_iterations`, `epsilon`: adaptive loop controls
- `max_shots`, `max_bins`: runtime and resolution policy caps
- `allow_backend_switch`, `allow_symmetry_toggle`: enable policy actions beyond shot scaling
- `mass_bins`: per-job initial bin budget (higher bins -> more qubits per run)

**New backend modules:** `backend/services/quantum/pipeline.py` (`AdaptiveSnapshotVerificationPipeline`), `backend/services/quantum/databank.py`, `scripts/summarize_quantum_databank.py`.

**UI (no terminal required):** After upload, the **Quantum verification** panel supports mode selection (adaptive/snapshot), epsilon and iteration controls, policy controls (`max_shots`, `max_bins`, backend/symmetry toggles), iteration/convergence results (including corrected error), databank save confirmation, and a live pathway leaderboard (`GET /api/quantum/databank/summary`).

## Repository layout

| Path | Purpose |
|------|---------|
| [`backend/`](backend/) | FastAPI app, analysis, tests |
| [`frontend/`](frontend/) | React + Vite + Recharts + R3F UI |
| [`backend/README.md`](backend/README.md) | Dev log, run instructions, API checklist |
| [`docs/planningCl.md`](docs/planningCl.md) | Product vision, architecture, milestones |
| [`docs/implementation_directives.md`](docs/implementation_directives.md) | Quantum sampling phase & module conventions |
| [`docs/quantum_research.md`](docs/quantum_research.md) | Research papers (QuDits, symmetry, Hamiltonians) |
| [`docs/daily_plan.md`](docs/daily_plan.md) | Phase checklist / action plan |
| [`docs/backend-status.md`](docs/backend-status.md) | Endpoint status snapshot |
| [`docs/backend-toolkit.md`](docs/backend-toolkit.md) | Backend architecture map |

## Startup Guide

Run the app from the repository root:

```bash
cd /Users/nich/Projects/qAI_Projects/electronCollisions
```

Use two terminals so each dev server stays visible and easy to stop.

Terminal 1, backend API:

```bash
./scripts/start-backend.sh
```

This creates/uses `backend/.venv`, installs `backend/requirements.txt`, and starts FastAPI at `http://127.0.0.1:8000`.
API docs are at `http://127.0.0.1:8000/docs`.

Terminal 2, frontend UI:

```bash
./scripts/start-frontend.sh
```

This installs frontend dependencies if needed and starts Vite at `http://127.0.0.1:5173`.
Open that URL in your browser. The Vite dev server proxies `/api` calls to the backend on port `8000`.

To stop either server, click that terminal and press `Ctrl-C`. The terminal prompt should return and be usable again. If a port is still busy after stopping, close the old dev-server terminal or run:

```bash
lsof -ti :8000 | xargs kill
lsof -ti :5173 | xargs kill
```

### Manual Commands

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

### Quantum verification flow

1. Start both servers.
2. Open `http://127.0.0.1:5173`.
3. Upload a dielectron CSV.
4. In **Quantum sampling verification**, pick a resonance (e.g. J/ψ or Z⁰) and review the classical ground-truth bars (exact vs binned).
5. Click **Run verification job** and compare the quantum sample to those baselines (including discretization and 2σ check).

Adaptive mode (thermostat-style loop) is also available via `POST /api/quantum/job` with `"mode": "adaptive_snapshot"` to iteratively re-run and converge toward a target probability.

Optional calibration sweep:

```bash
cd backend && source .venv/bin/activate
python ../scripts/run_verification_calibration.py --csv /path/to/dielectron.csv --particles jpsi,z_boson
```

Verify connectivity without submitting a job:

```bash
curl "http://127.0.0.1:8000/api/quantum/runtime?probe=true"
```

Or open `GET /api/quantum/runtime?probe=true` in the API docs after starting the backend.

### Local Quantum Databank (hardware runs)

Every successful run that uses real IBM hardware (`USE_REAL_BACKEND=true`) is persisted to a local append-only JSONL databank so you can train downstream ML models and compare pathway efficiency over time.

Default file:

`data/quantum_databank/hardware_runs.jsonl`

Each line is one run record including:
- mode (`snapshot` or `adaptive_snapshot`)
- backend + runtime job id
- observable + classical baselines
- estimate, standard error, verification metrics
- adaptive convergence + iteration trace (when applicable)
- circuit metadata (qubits/depth/ops) and encoding metadata

Optional environment variables:

- `QMC_DATABANK_ENABLED=true|false` (default `true`)
- `QMC_DATABANK_PATH=/absolute/or/relative/path/to/hardware_runs.jsonl`

When a run is saved, `/api/quantum/result/{job_id}` includes:
- `result.databank_recorded = true`
- `result.databank_path = "<resolved local path>"`

### Databank Efficiency Leaderboard

You can summarize saved hardware runs and rank pathways by an efficiency score that balances:
- accuracy vs exact classical baseline
- uncertainty (standard error)
- shot cost
- adaptive iteration cost

Run:

```bash
cd backend && source .venv/bin/activate
python ../scripts/summarize_quantum_databank.py --top 10
```

Optional JSON export:

```bash
cd backend && source .venv/bin/activate
python ../scripts/summarize_quantum_databank.py --json-out ../data/quantum_databank/summary.json
```

Optional custom databank file:

```bash
cd backend && source .venv/bin/activate
python ../scripts/summarize_quantum_databank.py --databank /path/to/hardware_runs.jsonl
```

## Contributing / GitHub

Do not commit virtualenvs, `__pycache__`, or `.env` files. Use `.venv` locally; see `.gitignore`.
