#!/usr/bin/env bash
# Quick start: creates the venv if needed, installs deps, runs on port 8100.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

exec python -m uvicorn app.main:app --port 8100 "$@"
