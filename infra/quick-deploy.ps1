#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick deploy MyStock infrastructure to Azure
.DESCRIPTION
    Uses existing API keys from .env file for faster deployment
#>

param(
    [Parameter()]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$EnvironmentName = 'dev',
    
    [Parameter()]
    [string]$Location = 'koreacentral'
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠️  $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "❌ $args" -ForegroundColor Red }

Write-Host ""
Write-Host "=================================" -ForegroundColor Magenta
Write-Host "  MyStock Azure Quick Deploy" -ForegroundColor Magenta
Write-Host "=================================" -ForegroundColor Magenta
Write-Host ""

# Check Azure login
Write-Info "Checking Azure login..."
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Warning "Not logged in. Logging in..."
    az login
    $account = az account show | ConvertFrom-Json
}
Write-Success "Logged in: $($account.user.name)"
Write-Success "Subscription: $($account.name)"
Write-Host ""

# Configuration
$appName = "mystock"
$githubRepoUrl = "HyounsooKim/mystock"
$githubBranch = "main"

# Read API key from .env
$envFile = "..\backend\.env"
$alphaVantageApiKey = "N6Z9MFQ7VUBY9XLT"  # From your .env
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
    $apiKeyLine = $envContent | Where-Object { $_ -match "^ALPHA_VANTAGE_API_KEY=" }
    if ($apiKeyLine) {
        $alphaVantageApiKey = ($apiKeyLine -split "=", 2)[1].Trim()
        Write-Success "Found Alpha Vantage API Key from .env"
    }
}

# Generate JWT secret
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$jwtSecretKey = [Convert]::ToBase64String($bytes)
Write-Success "Generated JWT secret key"

Write-Host ""
Write-Host "Deployment Configuration:" -ForegroundColor Yellow
Write-Host "  Environment:     $EnvironmentName"
Write-Host "  Location:        $Location"
Write-Host "  App Name:        $appName"
Write-Host "  GitHub Repo:     $githubRepoUrl"
Write-Host "  Branch:          $githubBranch"
Write-Host "  Alpha Vantage:   $($alphaVantageApiKey.Substring(0, 4))..." -NoNewline
Write-Host " (from .env)" -ForegroundColor Green
Write-Host ""

Write-Warning "This will create Azure resources:"
Write-Host "  • Resource Group: rg-$appName-$EnvironmentName"
Write-Host "  • Cosmos DB (Serverless)"
Write-Host "  • Container Apps (Backend)"
Write-Host "  • Static Web App (Frontend)"
Write-Host "  • Azure Functions (Top Movers)"
Write-Host "  • Log Analytics + App Insights"
Write-Host ""

$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne 'y') {
    Write-Warning "Deployment cancelled"
    exit 0
}

# Validate Bicep
Write-Info "Validating Bicep template..."
try {
    az bicep build --file main.bicep --stdout | Out-Null
    Write-Success "Bicep template valid"
} catch {
    Write-Error "Bicep validation failed: $_"
    exit 1
}

# Deploy
$deploymentName = "mystock-$EnvironmentName-$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Info "Starting deployment: $deploymentName"
Write-Host ""
Write-Warning "This may take 10-15 minutes. Please wait..."
Write-Host ""

try {
    $result = az deployment sub create `
        --name $deploymentName `
        --location $Location `
        --template-file main.bicep `
        --parameters environmentName=$EnvironmentName `
                    location=$Location `
                    appName=$appName `
                    githubRepoUrl=$githubRepoUrl `
                    githubBranch=$githubBranch `
                    alphaVantageApiKey=$alphaVantageApiKey `
                    jwtSecretKey=$jwtSecretKey `
        --output json 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Deployment failed!"
        Write-Host $result
        exit 1
    }

    $deployment = $result | ConvertFrom-Json
    $outputs = $deployment.properties.outputs

    Write-Host ""
    Write-Success "Deployment completed! 🎉"
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host "  Deployment Summary" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host ""

    Write-Host "📦 Resources Created:" -ForegroundColor Cyan
    Write-Host "  Resource Group:  $($outputs.resourceGroupName.value)"
    Write-Host ""

    Write-Host "🗄️  Cosmos DB:" -ForegroundColor Cyan
    Write-Host "  Endpoint:        $($outputs.cosmosDbEndpoint.value)"
    Write-Host "  Database:        $($outputs.cosmosDbDatabaseName.value)"
    Write-Host ""

    Write-Host "🚀 Backend API:" -ForegroundColor Cyan
    Write-Host "  URL:             $($outputs.backendUrl.value)"
    Write-Host ""

    Write-Host "🌐 Frontend:" -ForegroundColor Cyan
    Write-Host "  URL:             $($outputs.frontendUrl.value)"
    Write-Host ""

    Write-Host "⚡ Azure Functions:" -ForegroundColor Cyan
    Write-Host "  App Name:        $($outputs.functionAppName.value)"
    Write-Host "  URL:             $($outputs.functionAppUrl.value)"
    Write-Host ""

    Write-Host "📊 Monitoring:" -ForegroundColor Cyan
    Write-Host "  Log Analytics:   $($outputs.logAnalyticsWorkspaceId.value)"
    Write-Host ""

    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host ""

    Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Deploy Functions Code:" -ForegroundColor White
    Write-Host "   .\deploy-functions.ps1 -EnvironmentName $EnvironmentName"
    Write-Host ""
    Write-Host "2. Get Function App Publish Profile for GitHub Actions:" -ForegroundColor White
    Write-Host "   az functionapp deployment list-publishing-profiles \"
    Write-Host "     --name $($outputs.functionAppName.value) \"
    Write-Host "     --resource-group $($outputs.resourceGroupName.value) \"
    Write-Host "     --xml"
    Write-Host ""
    Write-Host "3. Backend & Frontend will auto-deploy via GitHub Actions" -ForegroundColor White
    Write-Host ""
    Write-Host "4. View in Azure Portal:" -ForegroundColor White
    Write-Host "   https://portal.azure.com/#@/resource$($outputs.resourceGroupName.value)"
    Write-Host ""

    Write-Success "All done! 🚀"

} catch {
    Write-Error "Deployment failed: $_"
    exit 1
}
