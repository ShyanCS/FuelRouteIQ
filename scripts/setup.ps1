param([switch]$Demo)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
function Invoke-Python {
    & .\.venv\Scripts\python.exe @args
    if ($LASTEXITCODE -ne 0) { throw "Python command failed: $args" }
}
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
}
Invoke-Python -m pip install -r requirements.lock
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
Invoke-Python manage.py migrate
Invoke-Python manage.py createcachetable
Invoke-Python manage.py import_locations --cities
if ($Demo) { Invoke-Python manage.py import_fuel fixtures/public_demo_prices.csv }
else {
    if (-not (Test-Path -LiteralPath 'data/raw/fuel-prices-for-be-assessment.csv')) {
        New-Item -ItemType Directory -Path 'data/raw' -Force | Out-Null
        if (Test-Path -LiteralPath 'fuel-prices-for-be-assessment.csv') {
            Copy-Item -LiteralPath 'fuel-prices-for-be-assessment.csv' -Destination 'data/raw/fuel-prices-for-be-assessment.csv'
        } else { throw 'Place the supplied CSV in data/raw or use -Demo for clearly labelled illustrative prices' }
    }
    Invoke-Python manage.py import_fuel
}
Invoke-Python manage.py import_locations --verified data/reference/verified_stations.json
Invoke-Python manage.py check
Write-Output 'Ready. Run: .\.venv\Scripts\python.exe manage.py runserver'
