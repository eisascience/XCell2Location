# Setup script for Windows (PowerShell)
# Run from the repository root: .\scripts\setup_windows.ps1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PythonVersion = "3.10"
$VenvDir = ".venv"

Write-Host "=== XCell2Location Windows Setup ===" -ForegroundColor Cyan

# ── Install uv ────────────────────────────────────────────────────────────────
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..." -ForegroundColor Yellow
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
}

Write-Host "uv: $(uv --version)"

# ── Create virtual environment ─────────────────────────────────────────────────
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating Python $PythonVersion virtual environment..."
    uv venv $VenvDir --python $PythonVersion
}

& "$VenvDir\Scripts\Activate.ps1"

# ── Install dependencies ───────────────────────────────────────────────────────
Write-Host "Installing production dependencies (rpy2 excluded on Windows)..." -ForegroundColor Yellow

# On Windows we exclude rpy2 (not well supported)
uv pip install -r requirements-uv.txt

Write-Host "Installing package in editable mode..."
uv pip install -e .

Write-Host ""
Write-Host "✓ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Activate environment : $VenvDir\Scripts\Activate.ps1"
Write-Host "Launch GUI           : streamlit run app\gui\streamlit_app.py"
Write-Host "Show CLI help        : spx --help"
Write-Host ""
Write-Host "Note: R integration (Seurat .rds import) is not supported on Windows." -ForegroundColor Yellow
Write-Host "Use .h5ad files directly or perform conversion on Linux/macOS." -ForegroundColor Yellow
