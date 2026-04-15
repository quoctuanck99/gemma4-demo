#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")" && pwd)"

npm --prefix "$ROOT/frontend" run dev
