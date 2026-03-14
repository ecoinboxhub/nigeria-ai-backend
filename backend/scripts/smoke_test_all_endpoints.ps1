$ErrorActionPreference = "Stop"

$root = "C:\Users\ibrah\Documents\Codex"
Set-Location $root

$apiHost = if ($env:API_HOST) { $env:API_HOST } else { "127.0.0.1" }
$apiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$apiKey = if ($env:API_KEY) { $env:API_KEY } else { "change-me" }
$baseUrl = "http://$apiHost`:$apiPort"

$payloadDir = Join-Path $root "backend\scripts\payloads"
if (-not (Test-Path $payloadDir)) {
    throw "Payload directory not found: $payloadDir"
}

function Load-JsonPayload {
    param([Parameter(Mandatory = $true)][string]$FileName)
    $path = Join-Path $payloadDir $FileName
    if (-not (Test-Path $path)) {
        throw "Missing payload file: $path"
    }
    return Get-Content $path -Raw
}

function Invoke-SmokeCall {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Path,
        [hashtable]$Headers,
        [string]$Body
    )

    $uri = "$baseUrl$Path"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $status = $null
    $ok = $false
    $errorText = ""

    try {
        if ($Body) {
            $resp = Invoke-WebRequest -UseBasicParsing -Method $Method -Uri $uri -Headers $Headers -ContentType "application/json" -Body $Body
        } else {
            $resp = Invoke-WebRequest -UseBasicParsing -Method $Method -Uri $uri -Headers $Headers
        }
        $status = [int]$resp.StatusCode
        $ok = ($status -ge 200 -and $status -lt 300)
    }
    catch {
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $status = [int]$_.Exception.Response.StatusCode
        }
        $errorText = $_.Exception.Message
        $ok = $false
    }
    finally {
        $sw.Stop()
    }

    [PSCustomObject]@{
        Name      = $Name
        Method    = $Method
        Path      = $Path
        Status    = if ($status -ne $null) { $status } else { "-" }
        Ok        = $ok
        DurationMs = [math]::Round($sw.Elapsed.TotalMilliseconds, 1)
        Error     = $errorText
    }
}

$results = New-Object System.Collections.Generic.List[object]

# 1) Health
$results.Add((Invoke-SmokeCall -Name "health" -Method "GET" -Path "/api/v1/health"))

# 2) Token
$tokenBody = Load-JsonPayload -FileName "integration_token.json"
$tokenResult = Invoke-SmokeCall -Name "integration_token" -Method "POST" -Path "/api/v1/integration/token" -Headers @{ "X-API-Key" = $apiKey } -Body $tokenBody
$results.Add($tokenResult)

$accessToken = $null
$refreshToken = $null
if ($tokenResult.Ok) {
    try {
        $tokenRespObj = Invoke-RestMethod -Method POST -Uri "$baseUrl/api/v1/integration/token" -Headers @{ "X-API-Key" = $apiKey } -ContentType "application/json" -Body $tokenBody
        $accessToken = $tokenRespObj.access_token
        $refreshToken = $tokenRespObj.refresh_token
    }
    catch {
        # Keep flow alive; auth checks below will fail explicitly if token missing.
    }
}

$authHeaders = @{}
if ($accessToken) {
    $authHeaders["Authorization"] = "Bearer $accessToken"
}

# 3) Integration refresh
$refreshPayloadObj = (Load-JsonPayload -FileName "integration_refresh.json" | ConvertFrom-Json)
if ($refreshToken) {
    $refreshPayloadObj.refresh_token = $refreshToken
}
$refreshBody = $refreshPayloadObj | ConvertTo-Json -Depth 6
$results.Add((Invoke-SmokeCall -Name "integration_refresh" -Method "POST" -Path "/api/v1/integration/refresh" -Body $refreshBody))

# 4) Protected integration endpoints
$results.Add((Invoke-SmokeCall -Name "integration_module_status" -Method "GET" -Path "/api/v1/integration/module-status" -Headers $authHeaders))
$results.Add((Invoke-SmokeCall -Name "integration_endpoints" -Method "GET" -Path "/api/v1/integration/endpoints" -Headers $authHeaders))

# 5) Domain endpoints
$results.Add((Invoke-SmokeCall -Name "project_tracker_predict_delay" -Method "POST" -Path "/api/v1/project-tracker/predict-delay" -Headers $authHeaders -Body (Load-JsonPayload "project_tracker_predict_delay.json")))
$results.Add((Invoke-SmokeCall -Name "procurement_supplier_intelligence" -Method "POST" -Path "/api/v1/procurement/supplier-intelligence" -Headers $authHeaders -Body (Load-JsonPayload "procurement_supplier_intelligence.json")))
$results.Add((Invoke-SmokeCall -Name "safety_analyze_log" -Method "POST" -Path "/api/v1/safety/analyze-log" -Headers $authHeaders -Body (Load-JsonPayload "safety_analyze_log.json")))
$results.Add((Invoke-SmokeCall -Name "document_analyzer_review" -Method "POST" -Path "/api/v1/document-analyzer/review" -Headers $authHeaders -Body (Load-JsonPayload "document_analyzer_review.json")))
$results.Add((Invoke-SmokeCall -Name "cost_estimator_estimate" -Method "POST" -Path "/api/v1/cost-estimator/estimate" -Headers $authHeaders -Body (Load-JsonPayload "cost_estimator_estimate.json")))
$results.Add((Invoke-SmokeCall -Name "workforce_optimize" -Method "POST" -Path "/api/v1/workforce/optimize" -Headers $authHeaders -Body (Load-JsonPayload "workforce_optimize.json")))
$results.Add((Invoke-SmokeCall -Name "maintenance_predict" -Method "POST" -Path "/api/v1/maintenance/predict" -Headers $authHeaders -Body (Load-JsonPayload "maintenance_predict.json")))
$results.Add((Invoke-SmokeCall -Name "progress_visualizer_analyze" -Method "POST" -Path "/api/v1/progress-visualizer/analyze" -Headers $authHeaders -Body (Load-JsonPayload "progress_visualizer_analyze.json")))
$results.Add((Invoke-SmokeCall -Name "tender_analyzer_analyze" -Method "POST" -Path "/api/v1/tender-analyzer/analyze" -Headers $authHeaders -Body (Load-JsonPayload "tender_analyzer_analyze.json")))

$table = $results | Select-Object Name, Method, Path, Status, Ok, DurationMs
$table | Format-Table -AutoSize

$passed = ($results | Where-Object { $_.Ok }).Count
$failed = $results.Count - $passed
Write-Host ""
Write-Host "Summary: total=$($results.Count), passed=$passed, failed=$failed"

if ($failed -gt 0) {
    Write-Host ""
    Write-Host "Failed endpoints (with errors):"
    $results | Where-Object { -not $_.Ok } | Select-Object Name, Status, Error | Format-Table -AutoSize
    exit 1
}

exit 0
