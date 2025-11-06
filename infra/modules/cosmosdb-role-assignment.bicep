// ============================================================================
// Cosmos DB Role Assignment Module
// ============================================================================
// Description: Assigns Cosmos DB built-in roles to managed identities
// Usage: Grant Function App managed identity access to Cosmos DB
// ============================================================================

@description('Name of the Cosmos DB account')
param cosmosAccountName string

@description('Role definition ID (use built-in role IDs)')
param roleDefinitionId string

@description('Principal ID of the managed identity')
param principalId string

// Reference to existing Cosmos DB account
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' existing = {
  name: cosmosAccountName
}

// Cosmos DB SQL Role Assignment
resource roleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-04-15' = {
  name: guid(cosmosAccount.id, principalId, roleDefinitionId)
  parent: cosmosAccount
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/${roleDefinitionId}'
    principalId: principalId
    scope: cosmosAccount.id
  }
}

// Outputs
output roleAssignmentId string = roleAssignment.id
