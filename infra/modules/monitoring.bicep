// ============================================================================
// Monitoring Module (Log Analytics + Application Insights)
// ============================================================================
// Description: Cost-effective logging and monitoring
// Features:
//   - Log Analytics Workspace (31-day retention)
//   - Application Insights (basic monitoring)
//   - Pay-per-GB ingestion model
// ============================================================================

param location string
param appName string
param environmentName string
param tags object

// Variables
var workspaceName = 'law-${appName}-${environmentName}'
var appInsightsName = 'appi-${appName}-${environmentName}'

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018' // Pay-per-GB model (cheapest)
    }
    retentionInDays: 31 // Minimum retention (31 days for Basic tier)
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    IngestionMode: 'LogAnalytics' // Use Log Analytics for storage
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Outputs
output workspaceId string = logAnalyticsWorkspace.id
output workspaceName string = logAnalyticsWorkspace.name
output appInsightsName string = applicationInsights.name
output appInsightsConnectionString string = applicationInsights.properties.ConnectionString
output appInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey
