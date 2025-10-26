# Azure Functions 배포 스크립트
# Usage: .\deploy-functions.ps1 -EnvironmentName dev

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$EnvironmentName = 'dev'
)

$ErrorActionPreference = 'Stop'

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Azure Functions Deployment Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Variables
$appName = "mystock"
$functionAppName = "func-$appName-topmovers-$EnvironmentName"
$resourceGroup = "rg-$appName-$EnvironmentName"
$functionPath = "$PSScriptRoot\..\backend\functions"

Write-Host "Environment: $EnvironmentName" -ForegroundColor Yellow
Write-Host "Function App: $functionAppName" -ForegroundColor Yellow
Write-Host "Resource Group: $resourceGroup" -ForegroundColor Yellow
Write-Host ""

# Check if logged in to Azure
Write-Host "[1/5] Checking Azure login..." -ForegroundColor Green
$account = az account show 2>$null
if (-not $account) {
    Write-Host "Not logged in to Azure. Running 'az login'..." -ForegroundColor Yellow
    az login
}
Write-Host "✓ Logged in to Azure" -ForegroundColor Green
Write-Host ""

# Check if Function App exists
Write-Host "[2/5] Checking if Function App exists..." -ForegroundColor Green
$functionExists = az functionapp show --name $functionAppName --resource-group $resourceGroup 2>$null
if (-not $functionExists) {
    Write-Host "✗ Function App '$functionAppName' not found!" -ForegroundColor Red
    Write-Host "Please deploy infrastructure first using: .\infra\deploy.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Function App exists" -ForegroundColor Green
Write-Host ""

# Build the function package
Write-Host "[3/5] Building function package..." -ForegroundColor Green
Push-Location $functionPath

# Create virtual environment if not exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment and install dependencies
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt --quiet

Write-Host "✓ Dependencies installed" -ForegroundColor Green
Pop-Location
Write-Host ""

# Deploy to Azure Functions
Write-Host "[4/5] Deploying to Azure Functions..." -ForegroundColor Green
func azure functionapp publish $functionAppName --python

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Deployment failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Deployment successful" -ForegroundColor Green
Write-Host ""

# Get Function App URL
Write-Host "[5/5] Retrieving Function App information..." -ForegroundColor Green
$functionUrl = az functionapp show --name $functionAppName --resource-group $resourceGroup --query "defaultHostName" -o tsv
Write-Host "✓ Function App URL: https://$functionUrl" -ForegroundColor Green
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Function App: $functionAppName" -ForegroundColor White
Write-Host "URL: https://$functionUrl" -ForegroundColor White
Write-Host "Schedule: Every hour (0 0 * * * *)" -ForegroundColor White
Write-Host ""
Write-Host "Monitor logs:" -ForegroundColor Yellow
Write-Host "  Azure Portal: https://portal.azure.com/#@/resource/subscriptions/.../resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$functionAppName/appServices" -ForegroundColor Cyan
Write-Host "  CLI: func azure functionapp logstream $functionAppName" -ForegroundColor Cyan
