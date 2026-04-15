#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Setup backend venv ────────────────────────────────────────────────────────
if [ ! -d "$ROOT/backend/.venv" ]; then
  echo "[backend] Creating virtual environment..."
  python3 -m venv "$ROOT/backend/.venv"
fi

echo "[backend] Installing dependencies..."
"$ROOT/backend/.venv/bin/pip" install -q -r "$ROOT/backend/requirements.txt"

# ── Setup frontend ────────────────────────────────────────────────────────────
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "[frontend] Installing dependencies..."
  npm --prefix "$ROOT/frontend" install
fi

# ── Start both services ───────────────────────────────────────────────────────
echo ""
echo "Starting backend on http://localhost:8000"
echo "Starting frontend on http://localhost:5173"
echo "Press Ctrl+C to stop both."
echo ""

cleanup() {
  echo ""
  echo "Stopping..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

"$ROOT/backend/.venv/bin/uvicorn" main:app \
  --app-dir "$ROOT/backend" \
  --host 0.0.0.0 \
  --port 8000 &
BACKEND_PID=$!

npm --prefix "$ROOT/frontend" run dev &
FRONTEND_PID=$!

wait "$BACKEND_PID" "$FRONTEND_PID"
