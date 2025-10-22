// ============================================================================
// Container Apps Module (Backend API)
// ============================================================================
// Description: Serverless backend API with auto-scaling
// Features:
//   - Consumption-based pricing
//   - Auto-scale 0-10 replicas
//   - Integrated with Log Analytics
//   - Environment variables for Cosmos DB and Alpha Vantage
// ============================================================================

param location string
param appName string
param environmentName string
param tags object
param logAnalyticsWorkspaceId string
param cosmosDbEndpoint string
@secure()
param cosmosDbKey string
param cosmosDbDatabaseName string
param cosmosDbContainerName string
@secure()
param alphaVantageApiKey string
@secure()
param jwtSecretKey string

// Variables
var containerAppEnvName = 'cae-${appName}-${environmentName}'
var containerAppName = 'ca-${appName}-backend-${environmentName}'
var containerRegistryName = 'cr${appName}${environmentName}' // Max 50 chars, alphanumeric only

// Container Registry (for storing Docker images)
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: {
    name: 'Basic' // Cheapest option
  }
  properties: {
    adminUserEnabled: true // Enable admin user for GitHub Actions
    publicNetworkAccess: 'Enabled'
  }
}

// Container Apps Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2022-10-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2022-10-01').primarySharedKey
      }
    }
  }
}

// Container App (Backend)
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false // Force HTTPS
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
        corsPolicy: {
          allowedOrigins: [
            '*' // For MVP, allow all origins. Restrict in production.
          ]
          allowedMethods: [
            'GET'
            'POST'
            'PUT'
            'DELETE'
            'OPTIONS'
          ]
          allowedHeaders: [
            '*'
          ]
        }
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: [
        {
          name: 'registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
        {
          name: 'cosmos-key'
          value: cosmosDbKey
        }
        {
          name: 'alpha-vantage-key'
          value: alphaVantageApiKey
        }
        {
          name: 'jwt-secret'
          value: jwtSecretKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder, will be replaced by GitHub Actions
          resources: {
            cpu: json('0.25') // 0.25 vCPU (minimum)
            memory: '0.5Gi' // 512 MB (minimum)
          }
          env: [
            {
              name: 'COSMOS_ENDPOINT'
              value: cosmosDbEndpoint
            }
            {
              name: 'COSMOS_KEY'
              secretRef: 'cosmos-key'
            }
            {
              name: 'COSMOS_DATABASE'
              value: cosmosDbDatabaseName
            }
            {
              name: 'COSMOS_CONTAINER'
              value: cosmosDbContainerName
            }
            {
              name: 'ALPHA_VANTAGE_API_KEY'
              secretRef: 'alpha-vantage-key'
            }
            {
              name: 'SECRET_KEY'
              secretRef: 'jwt-secret'
            }
            {
              name: 'ENVIRONMENT'
              value: environmentName
            }
            {
              name: 'CORS_ORIGINS'
              value: '["*"]' // Allow all for MVP
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1 // Always keep 1 replica running (no cold start)
        maxReplicas: 2 // Max 2 replicas for dev environment
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output backendUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output containerAppName string = containerApp.name
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerRegistryName string = containerRegistry.name
