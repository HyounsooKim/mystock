// ============================================================================
// Azure Functions Module - Top Movers Updater
// ============================================================================
// Description: Timer-triggered function to update top movers data hourly
// Components:
//   - Storage Account (Functions runtime requirement)
//   - App Service Plan (Consumption Y1)
//   - Function App (Python 3.11)
// ============================================================================

@description('Primary Azure region')
param location string

@description('Application name prefix')
param appName string

@description('Environment name')
param environmentName string

@description('Resource tags')
param tags object

@description('Log Analytics Workspace ID for monitoring')
param logAnalyticsWorkspaceId string

@description('Application Insights Connection String')
param appInsightsConnectionString string

@description('Cosmos DB endpoint')
param cosmosDbEndpoint string

@description('Cosmos DB primary key')
@secure()
param cosmosDbKey string

@description('Cosmos DB database name')
param cosmosDbDatabaseName string

@description('Alpha Vantage API Key')
@secure()
param alphaVantageApiKey string

// Variables
var storageAccountName = 'st${appName}func${environmentName}'
var functionAppName = 'func-${appName}-topmovers-${environmentName}'
var appServicePlanName = 'asp-${appName}-func-${environmentName}'

// Storage Account (required for Azure Functions)
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        file: {
          keyType: 'Account'
          enabled: true
        }
        blob: {
          keyType: 'Account'
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// App Service Plan (Consumption Y1 - Pay per execution)
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
    size: 'Y1'
    family: 'Y'
    capacity: 0
  }
  properties: {
    reserved: true // Required for Linux
  }
  kind: 'functionapp'
}

// Function App
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(functionAppName)
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        // Application Settings
        {
          name: 'ALPHA_VANTAGE_API_KEY'
          value: alphaVantageApiKey
        }
        {
          name: 'COSMOS_ENDPOINT'
          value: cosmosDbEndpoint
        }
        {
          name: 'COSMOS_KEY'
          value: cosmosDbKey
        }
        {
          name: 'COSMOS_DATABASE_NAME'
          value: cosmosDbDatabaseName
        }
        // Python-specific settings
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
      ]
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
        ]
      }
      use32BitWorkerProcess: false
      alwaysOn: false // Not supported in Consumption plan
    }
    // Security: Disable basic authentication for SCM and FTP
    publicNetworkAccess: 'Enabled'
  }
}

// Disable FTP basic authentication
resource functionAppFtpBasicAuth 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-01-01' = {
  name: 'ftp'
  parent: functionApp
  properties: {
    allow: false
  }
}

// Disable SCM (Kudu) basic authentication
resource functionAppScmBasicAuth 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-01-01' = {
  name: 'scm'
  parent: functionApp
  properties: {
    allow: false
  }
}

// Diagnostic Settings for Function App
resource functionAppDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'functionapp-diagnostics'
  scope: functionApp
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'FunctionAppLogs'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
    ]
  }
}

// Outputs
output functionAppName string = functionApp.name
output functionAppId string = functionApp.id
output functionAppDefaultHostName string = functionApp.properties.defaultHostName
output storageAccountName string = storageAccount.name
output functionAppPrincipalId string = functionApp.identity.principalId
