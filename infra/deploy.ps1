# ============================================================================
# MyStock Infrastructure Deployment Script (PowerShell)
# ============================================================================
# Description: Deploy Azure infrastructure using Bicep
# Prerequisites:
#   - Azure CLI installed
#   - Logged in to Azure (az login)
#   - Owner/Contributor role on subscription
# ============================================================================

param(
    [string]$SubscriptionId = $env:AZURE_SUBSCRIPTION_ID,
    [string]$Environment = "dev",
    [string]$Location = "koreacentral",
    [string]$AppName = "mystock",
    [string]$GitHubRepo = "HyounsooKim/mystock",
    [string]$GitHubBranch = "AlphaVantage_v1",
    [string]$AlphaVantageApiKey = $env:ALPHA_VANTAGE_API_KEY,
    [string]$JwtSecretKey = $env:JWT_SECRET_KEY
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "MyStock Infrastructure Deployment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check Azure CLI
try {
    az version | Out-Null
} catch {
    Write-Host "Error: Azure CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Login check
try {
    az account show | Out-Null
} catch {
    Write-Host "Not logged in to Azure. Running 'az login'..." -ForegroundColor Yellow
    az login
}

# Select subscription
if ([string]::IsNullOrEmpty($SubscriptionId)) {
    Write-Host "Available subscriptions:" -ForegroundColor Yellow
    az account list --output table
    Write-Host ""
    $SubscriptionId = Read-Host "Enter subscription ID"
}

az account set --subscription $SubscriptionId
$subscriptionName = az account show --query name -o tsv
Write-Host "✓ Using subscription: $subscriptionName" -ForegroundColor Green
Write-Host ""

# Prompt for secrets if not set
if ([string]::IsNullOrEmpty($AlphaVantageApiKey)) {
    $secureApiKey = Read-Host "Enter Alpha Vantage API Key" -AsSecureString
    $BSTR = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureApiKey)
    $AlphaVantageApiKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
}

if ([string]::IsNullOrEmpty($JwtSecretKey)) {
    Write-Host "Generating random JWT secret..." -ForegroundColor Yellow
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $JwtSecretKey = [Convert]::ToBase64String($bytes)
}

# Validate parameters
Write-Host "Deployment Configuration:" -ForegroundColor Yellow
Write-Host "  Environment: $Environment"
Write-Host "  Location: $Location"
Write-Host "  App Name: $AppName"
Write-Host "  GitHub Repo: $GitHubRepo"
Write-Host "  GitHub Branch: $GitHubBranch"
Write-Host ""
$confirmation = Read-Host "Continue with deployment? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Deployment cancelled." -ForegroundColor Red
    exit 1
}

# Deploy infrastructure
Write-Host "Deploying infrastructure..." -ForegroundColor Green

$deploymentName = "mystock-infra-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

az deployment sub create `
  --name $deploymentName `
  --location $Location `
  --template-file ./main.bicep `
  --parameters `
    environmentName=$Environment `
    location=$Location `
    appName=$AppName `
    githubRepoUrl=$GitHubRepo `
    githubBranch=$GitHubBranch `
    alphaVantageApiKey=$AlphaVantageApiKey `
    jwtSecretKey=$JwtSecretKey `
  --output table

# Get deployment outputs
Write-Host ""
Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Retrieving deployment outputs..." -ForegroundColor Yellow

$resourceGroup = az deployment sub show --name $deploymentName --query properties.outputs.resourceGroupName.value -o tsv
$backendUrl = az deployment sub show --name $deploymentName --query properties.outputs.backendUrl.value -o tsv
$frontendUrl = az deployment sub show --name $deploymentName --query properties.outputs.frontendUrl.value -o tsv
$cosmosEndpoint = az deployment sub show --name $deploymentName --query properties.outputs.cosmosDbEndpoint.value -o tsv

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Resource Group: $resourceGroup" -ForegroundColor Yellow
Write-Host "Backend URL: $backendUrl" -ForegroundColor Yellow
Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Yellow
Write-Host "Cosmos DB Endpoint: $cosmosEndpoint" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Set up GitHub Actions secrets for CI/CD"
Write-Host "2. Push code to trigger automatic deployment"
Write-Host "3. Access your app at: $frontendUrl"
Write-Host ""
Write-Host "Done!" -ForegroundColor Green
