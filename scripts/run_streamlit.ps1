# Launch the XCell2Location Streamlit GUI (Windows PowerShell)
[CmdletBinding()]
param(
    [int]$Port = 8501
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvActivate = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"

if (Test-Path $VenvActivate) {
    & $VenvActivate
}

$AppPath = Join-Path $RepoRoot "app\gui\streamlit_app.py"
Write-Host "Starting XCell2Location GUI on http://localhost:$Port" -ForegroundColor Cyan

streamlit run $AppPath `
    --server.port $Port `
    --server.headless $false `
    --browser.gatherUsageStats $false
