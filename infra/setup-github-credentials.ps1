#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup GitHub Actions Azure credentials
.DESCRIPTION
    Creates Azure Service Principal and generates credentials for GitHub Actions
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "  GitHub Actions Azure Setup" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check Azure login
Write-Host "Checking Azure login..." -ForegroundColor Yellow
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in. Logging in..." -ForegroundColor Red
    az login
    $account = az account show | ConvertFrom-Json
}

Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host "✅ Subscription: $($account.name)" -ForegroundColor Green
Write-Host ""

$subscriptionId = $account.id
$resourceGroup = "rg-mystock-dev"

# Create Service Principal
Write-Host "Creating Service Principal for GitHub Actions..." -ForegroundColor Yellow

$spName = "sp-mystock-github-actions"

# Check if SP already exists
$existingSp = az ad sp list --display-name $spName 2>$null | ConvertFrom-Json
if ($existingSp) {
    Write-Host "⚠️  Service Principal already exists. Deleting and recreating..." -ForegroundColor Yellow
    $appId = $existingSp[0].appId
    az ad sp delete --id $appId
}

# Create new SP with Contributor role on resource group
Write-Host "Creating Service Principal with Contributor role..." -ForegroundColor Yellow

$sp = az ad sp create-for-rbac `
    --name $spName `
    --role Contributor `
    --scopes "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup" `
    --sdk-auth `
    --output json | ConvertFrom-Json

Write-Host "✅ Service Principal created!" -ForegroundColor Green
Write-Host ""

# Format credentials for GitHub Secret
$credentials = @{
    clientId = $sp.clientId
    clientSecret = $sp.clientSecret
    subscriptionId = $sp.subscriptionId
    tenantId = $sp.tenantId
} | ConvertTo-Json -Compress

Write-Host "=================================" -ForegroundColor Cyan
Write-Host "  GitHub Secret Configuration" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Go to your GitHub repository:" -ForegroundColor Yellow
Write-Host "   https://github.com/HyounsooKim/mystock/settings/secrets/actions" -ForegroundColor White
Write-Host ""

Write-Host "2. Click 'New repository secret'" -ForegroundColor Yellow
Write-Host ""

Write-Host "3. Add the following secret:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Name: AZURE_CREDENTIALS" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Value:" -ForegroundColor Cyan
Write-Host "   $credentials" -ForegroundColor White
Write-Host ""

# Save to file for reference
$credentials | Out-File -FilePath "azure-credentials.json" -Encoding UTF8
Write-Host "✅ Credentials also saved to: azure-credentials.json" -ForegroundColor Green
Write-Host "⚠️  DO NOT commit this file to Git!" -ForegroundColor Red
Write-Host ""

Write-Host "=================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Copy the JSON credentials above" -ForegroundColor Yellow
Write-Host "2. Add to GitHub Secrets as AZURE_CREDENTIALS" -ForegroundColor Yellow
Write-Host "3. Delete azure-credentials.json file" -ForegroundColor Yellow
Write-Host "4. Push code to trigger GitHub Actions deployment" -ForegroundColor Yellow
Write-Host ""

Write-Host "✅ Setup complete!" -ForegroundColor Green
