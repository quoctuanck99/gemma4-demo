#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$ROOT/backend/.venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$ROOT/backend/.venv"
fi

"$ROOT/backend/.venv/bin/pip" install -q -r "$ROOT/backend/requirements.txt"

"$ROOT/backend/.venv/bin/uvicorn" main:app \
  --app-dir "$ROOT/backend" \
  --host 0.0.0.0 \
  --port 8000
