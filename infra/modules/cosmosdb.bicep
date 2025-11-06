// ============================================================================
// Cosmos DB NoSQL Module (Serverless)
// ============================================================================
// Description: Cost-optimized Cosmos DB with serverless billing
// Features:
//   - Serverless mode (pay per request)
//   - NoSQL API
//   - Single region (Korea Central)
//   - Automatic indexing
// ============================================================================

param location string
param appName string
param environmentName string
param tags object

// Variables
var accountName = 'cosmos-${appName}-${environmentName}'
var databaseName = 'mystockdb'
var containerName = 'users'

// Cosmos DB Account (Serverless)
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: accountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: false // Set to true if this is your first Cosmos DB account
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session' // Good balance for MVP
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false // Disable for cost savings
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless' // Serverless mode for cost optimization
      }
    ]
    backupPolicy: {
      type: 'Continuous' // 30-day continuous backup
      continuousModeProperties: {
        tier: 'Continuous7Days' // 7-day point-in-time restore (cheaper)
      }
    }
    publicNetworkAccess: 'Enabled' // For MVP, enable public access
  }
}

// Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

// Container: users (stores all user data, watchlists, portfolios, holdings)
resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: [
          '/email' // Partition by user email
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?' // Exclude system property
          }
        ]
      }
      defaultTtl: -1 // No auto-delete (eternal storage)
    }
  }
}

// Outputs
output endpoint string = cosmosAccount.properties.documentEndpoint
output primaryKey string = cosmosAccount.listKeys().primaryMasterKey
output databaseName string = databaseName
output containerName string = containerName
output accountName string = cosmosAccount.name
output accountId string = cosmosAccount.id
