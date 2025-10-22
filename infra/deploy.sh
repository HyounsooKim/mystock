#!/bin/bash
# ============================================================================
# MyStock Infrastructure Deployment Script
# ============================================================================
# Description: Deploy Azure infrastructure using Bicep
# Prerequisites:
#   - Azure CLI installed
#   - Logged in to Azure (az login)
#   - Owner/Contributor role on subscription
# ============================================================================

set -e # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
LOCATION="${LOCATION:-koreacentral}"
APP_NAME="${APP_NAME:-mystock}"
GITHUB_REPO="${GITHUB_REPO:-HyounsooKim/mystock}"
GITHUB_BRANCH="${GITHUB_BRANCH:-AlphaVantage_v1}"

# Secrets (will be prompted if not set)
ALPHA_VANTAGE_API_KEY="${ALPHA_VANTAGE_API_KEY:-}"
JWT_SECRET_KEY="${JWT_SECRET_KEY:-}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MyStock Infrastructure Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

# Login check
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Azure. Running 'az login'...${NC}"
    az login
fi

# Select subscription
if [ -z "$SUBSCRIPTION_ID" ]; then
    echo -e "${YELLOW}Available subscriptions:${NC}"
    az account list --output table
    echo ""
    read -p "Enter subscription ID: " SUBSCRIPTION_ID
fi

az account set --subscription "$SUBSCRIPTION_ID"
echo -e "${GREEN}✓ Using subscription: $(az account show --query name -o tsv)${NC}"
echo ""

# Prompt for secrets if not set
if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
    read -sp "Enter Alpha Vantage API Key: " ALPHA_VANTAGE_API_KEY
    echo ""
fi

if [ -z "$JWT_SECRET_KEY" ]; then
    echo -e "${YELLOW}Generating random JWT secret...${NC}"
    JWT_SECRET_KEY=$(openssl rand -base64 32)
fi

# Validate parameters
echo -e "${YELLOW}Deployment Configuration:${NC}"
echo "  Environment: $ENVIRONMENT"
echo "  Location: $LOCATION"
echo "  App Name: $APP_NAME"
echo "  GitHub Repo: $GITHUB_REPO"
echo "  GitHub Branch: $GITHUB_BRANCH"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled.${NC}"
    exit 1
fi

# Deploy infrastructure
echo -e "${GREEN}Deploying infrastructure...${NC}"

DEPLOYMENT_NAME="mystock-infra-$(date +%Y%m%d-%H%M%S)"

az deployment sub create \
  --name "$DEPLOYMENT_NAME" \
  --location "$LOCATION" \
  --template-file ./main.bicep \
  --parameters \
    environmentName="$ENVIRONMENT" \
    location="$LOCATION" \
    appName="$APP_NAME" \
    githubRepoUrl="$GITHUB_REPO" \
    githubBranch="$GITHUB_BRANCH" \
    alphaVantageApiKey="$ALPHA_VANTAGE_API_KEY" \
    jwtSecretKey="$JWT_SECRET_KEY" \
  --output table

# Get deployment outputs
echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Retrieving deployment outputs...${NC}"

RESOURCE_GROUP=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query properties.outputs.resourceGroupName.value -o tsv)
BACKEND_URL=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query properties.outputs.backendUrl.value -o tsv)
FRONTEND_URL=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query properties.outputs.frontendUrl.value -o tsv)
COSMOS_ENDPOINT=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query properties.outputs.cosmosDbEndpoint.value -o tsv)

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Resource Group: ${YELLOW}$RESOURCE_GROUP${NC}"
echo -e "Backend URL: ${YELLOW}$BACKEND_URL${NC}"
echo -e "Frontend URL: ${YELLOW}$FRONTEND_URL${NC}"
echo -e "Cosmos DB Endpoint: ${YELLOW}$COSMOS_ENDPOINT${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Set up GitHub Actions secrets for CI/CD"
echo "2. Push code to trigger automatic deployment"
echo "3. Access your app at: $FRONTEND_URL"
echo ""
echo -e "${GREEN}Done!${NC}"
