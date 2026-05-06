#!/bin/zsh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$PROJECT_DIR/Tasuke"
APP="$APP_DIR/ui/foundation_unified_app.py"

typeset -a venv_candidates
venv_candidates=(
  "$APP_DIR/.venv"
  "$APP_DIR/venv"
  "$PROJECT_DIR/.venv"
)

VENV=""
for candidate in "${venv_candidates[@]}"; do
  if [ -x "$candidate/bin/streamlit" ]; then
    VENV="$candidate"
    break
  fi
done

if [ -z "$VENV" ]; then
  echo "Streamlit not found. Install it in one of the project virtual environments."
  exit 1
fi

cd "$APP_DIR"
echo "Starting Foundation Unified App..."
exec "$VENV/bin/streamlit" run "$APP" --server.headless false
