$ErrorActionPreference = 'Stop'
$root = 'C:\Users\ibrah\Documents\Codex'
Set-Location $root

$env:TEMP = "$root\.tmp"
$env:TMP = "$root\.tmp"
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    throw 'Virtual environment not found. Run backend\scripts\run_all.ps1 first.'
}

$env:USE_EXISTING_API = "true"
$env:API_TEST_PORT = "8000"
.\.venv\Scripts\python backend\scripts\validate_all_endpoints.py
