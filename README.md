# Quantum Particle Collision Visualizer

FastAPI backend plus a React (Vite) UI for dielectron CMS-style CSVs: statistics, invariant-mass spectrum, outlier detection, particle ID by mass windows, and a **Quantum Monte Carlo-style mass-window observable** prototype. The quantum path runs locally by default and can submit the same observable to IBM Quantum Runtime.

## Research Claim

**Hardware-backed prototype of a quantum sampling observable for collider invariant-mass resonance analysis, validated against classical baselines on real IBM Quantum hardware.**

Current IBM Runtime result: a Z-boson mass-window observable was executed on `ibm_marrakesh` with `1024` shots using a `5`-qubit circuit. The hardware estimate was `0.0693 +/- 0.0079`, compared with an exact classical probability of `0.0936` and a binned classical baseline of `0.1019`. This is a NISQ feasibility result and hardware benchmark, not a quantum-advantage claim.

This benchmark tests how accurately real quantum hardware can sample an encoded collider invariant-mass distribution and estimate the probability of events falling in a known particle resonance window, compared with the classical baseline.

## Repository layout

| Path | Purpose |
|------|---------|
| [`backend/`](backend/) | FastAPI app, analysis, tests |
| [`frontend/`](frontend/) | React + Vite + Recharts + R3F UI |
| [`backend/README.md`](backend/README.md) | Dev log, run instructions, API checklist |
| [`docs/planningCl.md`](docs/planningCl.md) | Product vision, architecture, milestones |
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

### Quantum Test Flow

1. Start both servers.
2. Open `http://127.0.0.1:5173`.
3. Upload a dielectron CSV.
4. Click **Run quantum job** in the Quantum analysis panel.
5. The result should show the QMC observable, local backend, shot count, quantum estimate, classical baseline, and circuit metadata.

### IBM Quantum Runtime

Local simulation is still the default. To spend real IBM Quantum runtime, copy `.env.example` to `.env`, set `IBM_QUANTUM_TOKEN`, optionally set `IBM_QUANTUM_INSTANCE` / `IBM_BACKEND`, then set `USE_REAL_BACKEND=true`. Keep `QMC_SHOTS` low while testing with limited runtime, for example `1024`.

Check configuration without submitting a quantum job at `GET /api/quantum/runtime`.

## Contributing / GitHub

Do not commit virtualenvs, `__pycache__`, or `.env` files. Use `.venv` locally; see `.gitignore`.
