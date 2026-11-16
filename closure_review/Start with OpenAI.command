#!/bin/zsh
cd "$(dirname "$0")/.."
echo "The AI workspace opens on port 8766. Stop any previous AI workspace before continuing."
echo "Your key stays in this process environment and is not saved to a file."
read -rs 'OPENAI_API_KEY?OpenAI API key (hidden): '
echo
read 'ATLASIQ_AI_MODEL?Model ID enabled in your OpenAI account: '
if [[ -z "$OPENAI_API_KEY" || -z "$ATLASIQ_AI_MODEL" ]]; then
  echo "Both values are required. No server started."
  exit 1
fi
export OPENAI_API_KEY ATLASIQ_AI_MODEL
PYTHON="/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ ! -x "$PYTHON" ]]; then PYTHON="$(command -v python3)"; fi
open "http://127.0.0.1:8766"
exec "$PYTHON" -m closure_review --port 8766
