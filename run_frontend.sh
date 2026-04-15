#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "Installing dependencies..."
  npm --prefix "$ROOT/frontend" install
fi

npm --prefix "$ROOT/frontend" run dev
