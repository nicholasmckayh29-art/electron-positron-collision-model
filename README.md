# Quantum Particle Collision Visualizer

FastAPI backend plus a React (Vite) UI for dielectron CMS-style CSVs: statistics, invariant-mass spectrum, outlier detection, particle ID by mass windows, and **Aer Estimator** ⟨ZZZ⟩ scoring per outlier (IBM Runtime can be wired later via `USE_REAL_BACKEND`).

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

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API: http://127.0.0.1:8000 — docs: http://127.0.0.1:8000/docs

### Frontend (needs Node 18+)

Install Node if needed: `brew install node` (use `/opt/homebrew/bin` first on your `PATH` so Cursor’s helper `node` does not shadow Homebrew).

**Two terminals:**

```bash
# Terminal 1 — API
./scripts/start-backend.sh

# Terminal 2 — UI
./scripts/start-frontend.sh
```

Or manually:

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — the dev server proxies `/api` to the backend on port 8000, so run **both** `uvicorn` and `npm run dev`, or set `vite.config.js` `server.proxy` target to match your API host.

## Contributing / GitHub

Do not commit virtualenvs, `__pycache__`, or `.env` files. Use `.venv` locally; see `.gitignore`.
