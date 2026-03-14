param(
    [switch]$SkipInstall = $false
)

$ErrorActionPreference = 'Stop'
$root = 'C:\Users\ibrah\Documents\Codex'
Set-Location $root

$env:TEMP = "$root\.tmp"
$env:TMP = "$root\.tmp"
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m virtualenv .venv --app-data .\.virtualenv --no-periodic-update
}

if (-not $SkipInstall) {
    .\.venv\Scripts\python -m pip install -r requirements.txt
}

.\.venv\Scripts\python backend\scripts\bootstrap_data.py
.\.venv\Scripts\python backend\pipelines\models\train_project_tracker.py
.\.venv\Scripts\python backend\pipelines\models\train_procurement_forecast.py
.\.venv\Scripts\python backend\pipelines\models\train_safety_detector.py
.\.venv\Scripts\python backend\pipelines\models\train_document_analyzer.py
.\.venv\Scripts\python backend\pipelines\models\train_cost_estimator.py
.\.venv\Scripts\python backend\pipelines\models\train_maintenance_predictor.py
.\.venv\Scripts\python backend\pipelines\rag\build_indexes.py
.\.venv\Scripts\python -m pytest -q

Write-Host 'Starting API at http://127.0.0.1:8000 (Ctrl+C to stop)...'
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
