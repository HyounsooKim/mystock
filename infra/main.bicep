// ============================================================================
// MyStock MVP Infrastructure - Main Bicep Template
// ============================================================================
// Description: Cost-optimized Azure infrastructure for stock portfolio app
// Components:
//   - Cosmos DB (Serverless NoSQL)
//   - Container Apps (Backend API)
//   - Static Web App (Frontend)
//   - Log Analytics (Monitoring)
// ============================================================================

targetScope = 'subscription'

// Parameters
@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environmentName string = 'dev'

@description('Primary Azure region for deployment')
param location string = 'koreacentral'

@description('Application name prefix')
param appName string = 'mystock'

@description('GitHub repository URL (e.g., HyounsooKim/mystock)')
param githubRepoUrl string

@description('GitHub branch to deploy from')
param githubBranch string = 'AlphaVantage_v1'

@description('Alpha Vantage API Key for stock data')
@secure()
param alphaVantageApiKey string

@description('JWT Secret Key for authentication')
@secure()
param jwtSecretKey string

// Variables
var resourceGroupName = 'rg-${appName}-${environmentName}'
var tags = {
  Environment: environmentName
  Application: appName
  ManagedBy: 'Bicep'
  CostCenter: 'MVP'
}

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// Module: Monitoring (Log Analytics + Application Insights)
module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-deployment'
  scope: rg
  params: {
    location: location
    appName: appName
    environmentName: environmentName
    tags: tags
  }
}

// Module: Cosmos DB (NoSQL Serverless)
module cosmosDb 'modules/cosmosdb.bicep' = {
  name: 'cosmosdb-deployment'
  scope: rg
  params: {
    location: location
    appName: appName
    environmentName: environmentName
    tags: tags
  }
}

// Module: Container Apps Environment + Backend App
module containerApps 'modules/containerapps.bicep' = {
  name: 'containerapps-deployment'
  scope: rg
  params: {
    location: location
    appName: appName
    environmentName: environmentName
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    cosmosDbEndpoint: cosmosDb.outputs.endpoint
    cosmosDbKey: cosmosDb.outputs.primaryKey
    cosmosDbDatabaseName: cosmosDb.outputs.databaseName
    cosmosDbContainerName: cosmosDb.outputs.containerName
    alphaVantageApiKey: alphaVantageApiKey
    jwtSecretKey: jwtSecretKey
  }
}

// Module: Static Web App (Frontend)
module staticWebApp 'modules/staticwebapp.bicep' = {
  name: 'staticwebapp-deployment'
  scope: rg
  params: {
    location: location
    appName: appName
    environmentName: environmentName
    tags: tags
    githubRepoUrl: githubRepoUrl
    githubBranch: githubBranch
    backendApiUrl: containerApps.outputs.backendUrl
  }
}

// Module: Azure Functions (Top Movers Updater)
module functions 'modules/functions.bicep' = {
  name: 'functions-deployment'
  scope: rg
  params: {
    location: location
    appName: appName
    environmentName: environmentName
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    cosmosDbEndpoint: cosmosDb.outputs.endpoint
    cosmosDbDatabaseName: cosmosDb.outputs.databaseName
    alphaVantageApiKey: alphaVantageApiKey
  }
}

// Cosmos DB Built-in Data Contributor role definition
// Reference: https://docs.microsoft.com/en-us/azure/cosmos-db/role-based-access-control
var cosmosDbDataContributorRoleDefinitionId = '00000000-0000-0000-0000-000000000002'

// Grant Function App managed identity access to Cosmos DB
module cosmosRoleAssignment 'modules/cosmosdb-role-assignment.bicep' = {
  name: 'cosmosdb-role-assignment'
  scope: rg
  params: {
    cosmosAccountName: cosmosDb.outputs.accountName
    roleDefinitionId: cosmosDbDataContributorRoleDefinitionId
    principalId: functions.outputs.functionAppPrincipalId
  }
}

// Outputs
output resourceGroupName string = rg.name
output cosmosDbEndpoint string = cosmosDb.outputs.endpoint
output cosmosDbDatabaseName string = cosmosDb.outputs.databaseName
output backendUrl string = containerApps.outputs.backendUrl
output frontendUrl string = staticWebApp.outputs.staticWebAppUrl
output functionAppName string = functions.outputs.functionAppName
output functionAppUrl string = 'https://${functions.outputs.functionAppDefaultHostName}'
output logAnalyticsWorkspaceId string = monitoring.outputs.workspaceId
output applicationInsightsConnectionString string = monitoring.outputs.appInsightsConnectionString
