$ErrorActionPreference = "Stop"

$root = "C:\Users\ibrah\Documents\Codex"
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment not found at .venv\Scripts\python.exe"
}

$apiHost = if ($env:API_HOST) { $env:API_HOST } else { "127.0.0.1" }
$apiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$apiKey = if ($env:API_KEY) { $env:API_KEY } else { "change-me" }
$baseUrl = "http://$apiHost`:$apiPort"

$tokenPayloadPath = "backend\scripts\payloads\integration_token.json"
$predictPayloadPath = "backend\scripts\payloads\project_tracker_predict_delay.json"

if (-not (Test-Path $tokenPayloadPath)) {
    throw "Missing payload file: $tokenPayloadPath"
}
if (-not (Test-Path $predictPayloadPath)) {
    throw "Missing payload file: $predictPayloadPath"
}

$tokenPayload = Get-Content $tokenPayloadPath -Raw
$predictPayload = Get-Content $predictPayloadPath -Raw

Write-Host "Requesting access token from $baseUrl/api/v1/integration/token"
$tokenResp = Invoke-RestMethod -Method POST `
  -Uri "$baseUrl/api/v1/integration/token" `
  -Headers @{ "X-API-Key" = $apiKey } `
  -ContentType "application/json" `
  -Body $tokenPayload

if (-not $tokenResp.access_token) {
    throw "Failed to obtain access token."
}

$accessToken = $tokenResp.access_token
Write-Host "Token acquired. Calling /api/v1/project-tracker/predict-delay"

$resp = Invoke-RestMethod -Method POST `
  -Uri "$baseUrl/api/v1/project-tracker/predict-delay" `
  -Headers @{ "Authorization" = "Bearer $accessToken" } `
  -ContentType "application/json" `
  -Body $predictPayload

$resp | ConvertTo-Json -Depth 10
