#!/bin/bash

################################################################################
# MyStock MVP - Azure Infrastructure Provisioning Script
# 
# This script creates all necessary Azure resources for the MVP deployment:
# - Resource Group
# - Azure Database for MySQL Flexible Server
# - Azure App Service (Backend API)
# - Azure Static Web Apps (Frontend)
#
# Prerequisites:
# - Azure CLI installed (az --version)
# - Logged in to Azure (az login)
# - Active Azure subscription
#
# Usage:
#   chmod +x scripts/provision-azure-mvp.sh
#   ./scripts/provision-azure-mvp.sh
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration Variables
PROJECT_NAME="mystock"
ENVIRONMENT="mvp"
LOCATION="koreacentral"
RESOURCE_GROUP="${PROJECT_NAME}-${ENVIRONMENT}-rg"

# MySQL Configuration
MYSQL_SERVER_NAME="${PROJECT_NAME}-${ENVIRONMENT}-mysql"
MYSQL_ADMIN_USER="mystockadmin"
MYSQL_DATABASE_NAME="mystockdb"
MYSQL_SKU="Standard_B1ms"  # 1 vCore, 2GB RAM
MYSQL_STORAGE_SIZE=20       # GB
MYSQL_BACKUP_RETENTION=1    # days
MYSQL_VERSION="8.0.21"

# App Service Configuration
APP_SERVICE_PLAN="${PROJECT_NAME}-${ENVIRONMENT}-plan"
APP_SERVICE_NAME="${PROJECT_NAME}-${ENVIRONMENT}-api"
APP_SERVICE_SKU="B1"        # Basic tier
APP_SERVICE_RUNTIME="PYTHON:3.11"

# Static Web App Configuration
STATIC_WEB_APP_NAME="${PROJECT_NAME}-${ENVIRONMENT}-frontend"
STATIC_WEB_APP_LOCATION="eastasia"  # Static Web Apps는 제한된 region만 지원

# GitHub Configuration (사용자 입력 필요)
GITHUB_REPO_URL=""  # 실행 중 입력받음
GITHUB_BRANCH="main"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        echo "Visit: https://docs.microsoft.com/cli/azure/install-azure-cli"
        exit 1
    fi
    print_success "Azure CLI installed: $(az version --query '\"azure-cli\"' -o tsv)"
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Running 'az login'..."
        az login
    fi
    
    SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    print_success "Logged in to Azure subscription: $SUBSCRIPTION_NAME"
    print_info "Subscription ID: $SUBSCRIPTION_ID"
    
    # Check jq (optional but useful)
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed. Some output formatting may be limited."
        print_info "Install with: brew install jq"
    fi
}

get_user_confirmation() {
    print_header "Configuration Summary"
    
    echo "Project Name:        $PROJECT_NAME"
    echo "Environment:         $ENVIRONMENT"
    echo "Resource Group:      $RESOURCE_GROUP"
    echo "Location:            $LOCATION"
    echo ""
    echo "MySQL Server:        $MYSQL_SERVER_NAME"
    echo "  - SKU:             $MYSQL_SKU (1 vCore, 2GB RAM)"
    echo "  - Storage:         ${MYSQL_STORAGE_SIZE}GB"
    echo "  - Admin User:      $MYSQL_ADMIN_USER"
    echo ""
    echo "App Service:         $APP_SERVICE_NAME"
    echo "  - Plan:            $APP_SERVICE_PLAN"
    echo "  - SKU:             $APP_SERVICE_SKU (Basic, 1.75GB RAM)"
    echo "  - Runtime:         Python 3.11"
    echo ""
    echo "Static Web App:      $STATIC_WEB_APP_NAME"
    echo "  - Location:        $STATIC_WEB_APP_LOCATION"
    echo ""
    
    # Estimate costs
    echo -e "${YELLOW}Estimated Monthly Cost:${NC}"
    echo "  - Static Web Apps:    \$0.00 (Free tier)"
    echo "  - App Service B1:     \$13.14"
    echo "  - MySQL B1ms:         \$12.41"
    echo "  - Total:              ~\$25.55/month"
    echo ""
    
    read -p "Do you want to proceed with this configuration? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        print_warning "Deployment cancelled by user."
        exit 0
    fi
}

generate_secure_password() {
    # Generate a secure random password (32 characters)
    if command -v openssl &> /dev/null; then
        openssl rand -base64 24 | tr -d "=+/" | cut -c1-32
    else
        # Fallback to /dev/urandom
        LC_ALL=C tr -dc 'A-Za-z0-9!@#$%^&*' < /dev/urandom | head -c 32
    fi
}

################################################################################
# Resource Creation Functions
################################################################################

create_resource_group() {
    print_header "Creating Resource Group"
    
    if az group exists --name "$RESOURCE_GROUP" | grep -q "true"; then
        print_warning "Resource group '$RESOURCE_GROUP' already exists. Skipping..."
    else
        az group create \
            --name "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --tags Environment="$ENVIRONMENT" Project="$PROJECT_NAME" \
            --output table
        
        print_success "Resource group created: $RESOURCE_GROUP"
    fi
}

create_mysql_server() {
    print_header "Creating MySQL Flexible Server"
    
    # Generate admin password
    MYSQL_ADMIN_PASSWORD=$(generate_secure_password)
    
    print_info "Creating MySQL server (this may take 5-10 minutes)..."
    
    az mysql flexible-server create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$MYSQL_SERVER_NAME" \
        --location "$LOCATION" \
        --admin-user "$MYSQL_ADMIN_USER" \
        --admin-password "$MYSQL_ADMIN_PASSWORD" \
        --sku-name "$MYSQL_SKU" \
        --tier Burstable \
        --storage-size "$MYSQL_STORAGE_SIZE" \
        --version "$MYSQL_VERSION" \
        --high-availability Disabled \
        --backup-retention "$MYSQL_BACKUP_RETENTION" \
        --storage-auto-grow Disabled \
        --public-access 0.0.0.0 \
        --tags Environment="$ENVIRONMENT" Project="$PROJECT_NAME" \
        --output table
    
    print_success "MySQL server created: $MYSQL_SERVER_NAME"
    
    # Create database
    print_info "Creating database: $MYSQL_DATABASE_NAME..."
    
    az mysql flexible-server db create \
        --resource-group "$RESOURCE_GROUP" \
        --server-name "$MYSQL_SERVER_NAME" \
        --database-name "$MYSQL_DATABASE_NAME" \
        --charset utf8mb4 \
        --collation utf8mb4_unicode_ci \
        --output table
    
    print_success "Database created: $MYSQL_DATABASE_NAME"
    
    # Configure firewall to allow Azure services
    print_info "Configuring firewall rules..."
    
    az mysql flexible-server firewall-rule create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$MYSQL_SERVER_NAME" \
        --rule-name AllowAzureServices \
        --start-ip-address 0.0.0.0 \
        --end-ip-address 0.0.0.0 \
        --output table
    
    print_success "Firewall rule created: AllowAzureServices"
    
    # Save credentials to file
    CREDENTIALS_FILE="./azure-credentials.txt"
    echo "MySQL Admin Password: $MYSQL_ADMIN_PASSWORD" > "$CREDENTIALS_FILE"
    chmod 600 "$CREDENTIALS_FILE"
    
    print_success "MySQL credentials saved to: $CREDENTIALS_FILE"
    print_warning "IMPORTANT: Keep this file secure and don't commit to git!"
}

create_app_service() {
    print_header "Creating App Service"
    
    # Create App Service Plan
    print_info "Creating App Service Plan..."
    
    az appservice plan create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_PLAN" \
        --location "$LOCATION" \
        --is-linux \
        --sku "$APP_SERVICE_SKU" \
        --tags Environment="$ENVIRONMENT" Project="$PROJECT_NAME" \
        --output table
    
    print_success "App Service Plan created: $APP_SERVICE_PLAN"
    
    # Create Web App
    print_info "Creating Web App..."
    
    az webapp create \
        --resource-group "$RESOURCE_GROUP" \
        --plan "$APP_SERVICE_PLAN" \
        --name "$APP_SERVICE_NAME" \
        --runtime "$APP_SERVICE_RUNTIME" \
        --tags Environment="$ENVIRONMENT" Project="$PROJECT_NAME" \
        --output table
    
    print_success "Web App created: $APP_SERVICE_NAME"
    
    # Enable always on (available in B1 tier)
    print_info "Configuring Web App settings..."
    
    az webapp config set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --always-on true \
        --http20-enabled true \
        --min-tls-version 1.2 \
        --output table
    
    print_success "Always On enabled"
    
    # Get MySQL connection string
    MYSQL_HOST="${MYSQL_SERVER_NAME}.mysql.database.azure.com"
    MYSQL_PASSWORD=$(grep "MySQL Admin Password:" ./azure-credentials.txt | cut -d' ' -f4)
    
    DATABASE_URL="mysql+pymysql://${MYSQL_ADMIN_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:3306/${MYSQL_DATABASE_NAME}?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
    
    # Generate JWT secret
    JWT_SECRET=$(generate_secure_password)
    echo "JWT Secret: $JWT_SECRET" >> ./azure-credentials.txt
    
    # Configure application settings
    print_info "Configuring application settings..."
    
    az webapp config appsettings set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --settings \
            DATABASE_URL="$DATABASE_URL" \
            JWT_SECRET="$JWT_SECRET" \
            JWT_ALGORITHM="HS256" \                                                                                                                                                                                                                                         
            ACCESS_TOKEN_EXPIRE_MINUTES="1440" \
            DEBUG="False" \
            ENVIRONMENT="production" \
        --output table
    
    print_success "Application settings configured"
    
    # Get Web App URL
    WEBAPP_URL=$(az webapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --query defaultHostName -o tsv)
    
    print_success "Web App URL: https://$WEBAPP_URL"
}

create_static_web_app() {
    print_header "Creating Static Web App"
    
    # Ask for GitHub repository URL
    if [ -z "$GITHUB_REPO_URL" ]; then
        read -p "Enter your GitHub repository URL (e.g., https://github.com/username/my_stock): " GITHUB_REPO_URL
    fi
    
    if [ -z "$GITHUB_REPO_URL" ]; then
        print_error "GitHub repository URL is required for Static Web Apps"
        return 1
    fi
    
    print_info "Creating Static Web App (requires GitHub authentication)..."
    print_warning "You will be prompted to authorize GitHub access in your browser."
    
    # Create Static Web App
    STATIC_WEB_APP_OUTPUT=$(az staticwebapp create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$STATIC_WEB_APP_NAME" \
        --location "$STATIC_WEB_APP_LOCATION" \
        --source "$GITHUB_REPO_URL" \
        --branch "$GITHUB_BRANCH" \
        --app-location "/frontend" \
        --output-location "dist" \
        --login-with-github \
        --tags Environment="$ENVIRONMENT" Project="$PROJECT_NAME")
    
    print_success "Static Web App created: $STATIC_WEB_APP_NAME"
    
    # Get Static Web App URL
    STATIC_URL=$(az staticwebapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$STATIC_WEB_APP_NAME" \
        --query defaultHostname -o tsv)
    
    print_success "Static Web App URL: https://$STATIC_URL"
    
    # Get deployment token
    STATIC_TOKEN=$(az staticwebapp secrets list \
        --resource-group "$RESOURCE_GROUP" \
        --name "$STATIC_WEB_APP_NAME" \
        --query properties.apiKey -o tsv)
    
    echo "Static Web App Deployment Token: $STATIC_TOKEN" >> ./azure-credentials.txt
    
    # Update App Service CORS settings
    print_info "Updating CORS settings..."
    
    az webapp cors add \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --allowed-origins "https://$STATIC_URL" \
        --output table
    
    print_success "CORS configured for Static Web App"
}

update_app_service_cors() {
    print_header "Updating App Service CORS"
    
    # Get Static Web App URL
    STATIC_URL=$(az staticwebapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$STATIC_WEB_APP_NAME" \
        --query defaultHostname -o tsv 2>/dev/null || echo "")
    
    if [ -n "$STATIC_URL" ]; then
        # Update ALLOWED_ORIGINS setting
        az webapp config appsettings set \
            --resource-group "$RESOURCE_GROUP" \
            --name "$APP_SERVICE_NAME" \
            --settings ALLOWED_ORIGINS="https://$STATIC_URL,http://localhost:5173" \
            --output table
        
        print_success "ALLOWED_ORIGINS updated with Static Web App URL"
    fi
}

display_deployment_info() {
    print_header "Deployment Summary"
    
    echo -e "${GREEN}✓ All resources created successfully!${NC}\n"
    
    # Get URLs
    WEBAPP_URL=$(az webapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --query defaultHostName -o tsv)
    
    STATIC_URL=$(az staticwebapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$STATIC_WEB_APP_NAME" \
        --query defaultHostname -o tsv 2>/dev/null || echo "Not created")
    
    MYSQL_HOST="${MYSQL_SERVER_NAME}.mysql.database.azure.com"
    
    echo "Resource Group:       $RESOURCE_GROUP"
    echo "Location:             $LOCATION"
    echo ""
    echo "Frontend (Static Web App):"
    echo "  URL:                https://$STATIC_URL"
    echo ""
    echo "Backend (App Service):"
    echo "  URL:                https://$WEBAPP_URL"
    echo "  Health Check:       https://$WEBAPP_URL/health"
    echo ""
    echo "Database (MySQL):"
    echo "  Host:               $MYSQL_HOST"
    echo "  Database:           $MYSQL_DATABASE_NAME"
    echo "  Admin User:         $MYSQL_ADMIN_USER"
    echo ""
    echo -e "${YELLOW}Credentials saved in: ./azure-credentials.txt${NC}"
    echo -e "${RED}⚠ Keep this file secure and add it to .gitignore!${NC}\n"
    
    echo "Next Steps:"
    echo "1. Add azure-credentials.txt to .gitignore"
    echo "2. Update frontend/.env.production with API URL"
    echo "3. Configure GitHub Actions secrets for CI/CD"
    echo "4. Deploy your application code"
    echo ""
    
    # Save deployment info
    DEPLOYMENT_INFO_FILE="./azure-deployment-info.md"
    cat > "$DEPLOYMENT_INFO_FILE" << EOF
# MyStock MVP - Azure Deployment Info

**Deployment Date:** $(date)

## Resources

### Frontend (Static Web App)
- **Name:** $STATIC_WEB_APP_NAME
- **URL:** https://$STATIC_URL
- **Resource Group:** $RESOURCE_GROUP

### Backend (App Service)
- **Name:** $APP_SERVICE_NAME
- **URL:** https://$WEBAPP_URL
- **Plan:** $APP_SERVICE_PLAN (B1)
- **Runtime:** Python 3.11

### Database (MySQL Flexible Server)
- **Server:** $MYSQL_SERVER_NAME
- **Host:** $MYSQL_HOST
- **Database:** $MYSQL_DATABASE_NAME
- **Admin User:** $MYSQL_ADMIN_USER
- **SKU:** $MYSQL_SKU (1 vCore, 2GB RAM)
- **Storage:** ${MYSQL_STORAGE_SIZE}GB

## Estimated Costs

- Static Web Apps: \$0.00/month (Free tier)
- App Service B1: \$13.14/month
- MySQL B1ms: \$12.41/month
- **Total:** ~\$25.55/month

## Management Commands

### View Resources
\`\`\`bash
az resource list --resource-group $RESOURCE_GROUP --output table
\`\`\`

### View App Service Logs
\`\`\`bash
az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_SERVICE_NAME
\`\`\`

### Connect to MySQL
\`\`\`bash
mysql -h $MYSQL_HOST -u $MYSQL_ADMIN_USER -p $MYSQL_DATABASE_NAME
\`\`\`

### Delete All Resources
\`\`\`bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
\`\`\`

## Environment Variables

Add these to your GitHub Actions secrets:

- \`AZURE_WEBAPP_NAME\`: $APP_SERVICE_NAME
- \`AZURE_STATIC_WEB_APP_TOKEN\`: (see azure-credentials.txt)
- \`DATABASE_URL\`: (configured in App Service)

## Next Steps

1. ✅ Infrastructure provisioned
2. ⏳ Configure GitHub Actions CI/CD
3. ⏳ Deploy application code
4. ⏳ Run database migrations
5. ⏳ Test end-to-end functionality
EOF
    
    print_success "Deployment info saved to: $DEPLOYMENT_INFO_FILE"
}

cleanup_on_error() {
    print_error "An error occurred during provisioning."
    print_warning "You may want to clean up partially created resources:"
    echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "MyStock MVP - Azure Infrastructure Provisioning"
    
    # Set error trap
    trap cleanup_on_error ERR
    
    # Run provisioning steps
    check_prerequisites
    get_user_confirmation
    
    create_resource_group
    create_mysql_server
    create_app_service
    
    # Ask if user wants to create Static Web App now
    read -p "Do you want to create Static Web App now? (requires GitHub repo) (yes/no): " -r
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        create_static_web_app
        update_app_service_cors
    else
        print_warning "Skipping Static Web App creation. You can create it later with:"
        echo "  az staticwebapp create --resource-group $RESOURCE_GROUP --name $STATIC_WEB_APP_NAME ..."
    fi
    
    display_deployment_info
    
    print_success "Provisioning complete! 🎉"
}

# Run main function
main "$@"
