#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/.run-logs"
if [[ ! -d "$ROOT/backend/.venv" ]]; then
  python -m venv "$ROOT/backend/.venv"
fi
source "$ROOT/backend/.venv/bin/activate"
pip install -q -r "$ROOT/backend/requirements.txt"
(
  cd "$ROOT/backend"
  uvicorn app.main:app --reload --port 8000 > "$ROOT/.run-logs/backend.log" 2>&1
) &
BACK_PID=$!
(
  cd "$ROOT/frontend"
  npm install --silent
  npm run dev -- --host 0.0.0.0 > "$ROOT/.run-logs/frontend.log" 2>&1
) &
FRONT_PID=$!
cleanup() { kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
printf 'Backend log: %s/.run-logs/backend.log\nFrontend log: %s/.run-logs/frontend.log\n' "$ROOT" "$ROOT"
wait
