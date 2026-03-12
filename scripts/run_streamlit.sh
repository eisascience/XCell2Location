#!/usr/bin/env bash
# Launch the XCell2Location Streamlit GUI (Linux/macOS)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment if present
VENV="$REPO_ROOT/.venv"
if [ -f "$VENV/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
fi

PORT="${STREAMLIT_SERVER_PORT:-8501}"
echo "Starting XCell2Location GUI on http://localhost:$PORT"

streamlit run \
    "$REPO_ROOT/app/gui/streamlit_app.py" \
    --server.port "$PORT" \
    --server.headless false \
    --browser.gatherUsageStats false
