#!/usr/bin/env bash
# Vite dev server (run in a second terminal after the backend is up).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Prefer Homebrew Node so Cursor’s bundled node does not shadow npm’s runtime.
export PATH="/opt/homebrew/bin:${PATH}"

cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm install
fi

echo "→ Vite: http://127.0.0.1:5173  (proxies /api → :8000)"
exec npm run dev
