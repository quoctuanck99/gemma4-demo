#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")" && pwd)"

"$ROOT/backend/.venv/bin/uvicorn" main:app \
  --app-dir "$ROOT/backend" \
  --host 0.0.0.0 \
  --port 8000
