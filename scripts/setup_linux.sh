#!/usr/bin/env bash
# Setup script for Linux
set -euo pipefail

PYTHON_VERSION="3.10"
VENV_DIR=".venv"

echo "=== XCell2Location Linux Setup ==="

# ── System dependencies (apt) ──────────────────────────────────────────────────
if command -v apt-get &>/dev/null; then
    echo "Installing system dependencies..."
    sudo apt-get update -q
    sudo apt-get install -y -q \
        python3-dev python3-pip \
        libhdf5-dev libssl-dev curl git \
        build-essential
fi

# ── Install uv if missing ──────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "uv: $(uv --version)"

# ── Create virtual environment ─────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python $PYTHON_VERSION virtual environment..."
    uv venv "$VENV_DIR" --python "$PYTHON_VERSION"
fi

source "$VENV_DIR/bin/activate"

# ── Install dependencies ───────────────────────────────────────────────────────
echo "Installing production dependencies..."
uv pip install -r requirements-uv.txt

echo "Installing package in editable mode..."
uv pip install -e .

# ── R (optional) ──────────────────────────────────────────────────────────────
if ! command -v Rscript &>/dev/null; then
    echo ""
    echo "R is not installed. For Seurat .rds import, install R:"
    echo "  sudo apt-get install r-base r-base-dev"
    echo "Then in R:"
    echo "  install.packages('Seurat')"
    echo "  remotes::install_github('mojaveazure/seurat-disk')"
fi

echo ""
echo "✓ Setup complete!"
echo ""
echo "Activate environment:  source $VENV_DIR/bin/activate"
echo "Launch GUI:            make run-gui"
echo "Show CLI help:         spx --help"
