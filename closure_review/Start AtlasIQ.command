#!/bin/zsh
cd "$(dirname "$0")/.."
PYTHON="/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ ! -x "$PYTHON" ]]; then PYTHON="$(command -v python3)"; fi
open "http://127.0.0.1:8765"
exec "$PYTHON" -m closure_review
