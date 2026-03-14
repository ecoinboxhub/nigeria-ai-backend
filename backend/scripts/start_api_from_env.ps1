param(
  [string]$EnvFile = ".env"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

function Get-EnvValue([string]$Path, [string]$Key, [string]$Default="") {
  if (!(Test-Path $Path)) { return $Default }
  $lines = Get-Content $Path
  $value = $Default
  foreach ($line in $lines) {
    $trim = $line.Trim()
    if ($trim.StartsWith("#") -or $trim -eq "") { continue }
    if ($trim -match "^$Key=(.*)$") { $value = $matches[1].Trim() }
  }
  return $value
}

$apiHost = Get-EnvValue $EnvFile "API_HOST" "127.0.0.1"
$apiPort = Get-EnvValue $EnvFile "API_PORT" "8000"

if (!(Test-Path ".venv\Scripts\python.exe")) {
  throw "Virtual environment not found at .venv."
}

Write-Host "Starting API on http://$apiHost`:$apiPort ..."
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host $apiHost --port $apiPort
