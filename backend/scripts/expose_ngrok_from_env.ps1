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
$authtoken = Get-EnvValue $EnvFile "NGROK_AUTHTOKEN" ""
$domain = Get-EnvValue $EnvFile "NGROK_DOMAIN" ""

if ([string]::IsNullOrWhiteSpace($authtoken)) {
  throw "NGROK_AUTHTOKEN is empty in .env"
}
if ([string]::IsNullOrWhiteSpace($domain)) {
  throw "NGROK_DOMAIN is empty in .env (set your reserved ngrok domain)"
}

Write-Host "Configuring ngrok auth token from .env ..."
ngrok config add-authtoken $authtoken | Out-Null

$target = "$apiHost`:$apiPort"
Write-Host "Starting ngrok tunnel to http://$target with domain $domain ..."
ngrok http $target --domain=$domain
