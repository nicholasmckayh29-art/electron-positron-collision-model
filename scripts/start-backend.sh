#!/usr/bin/env bash
# API for the collision visualizer (run this in one terminal).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q -r requirements.txt

echo "→ FastAPI: http://127.0.0.1:8000  (docs: /docs)"
exec uvicorn main:app --reload --host 127.0.0.1 --port 8000
