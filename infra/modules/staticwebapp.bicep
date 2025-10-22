// ============================================================================
// Static Web App Module (Frontend)
// ============================================================================
// Description: Free-tier Static Web App with GitHub integration
// Features:
//   - Free SKU (100 GB bandwidth/month)
//   - Automatic CI/CD from GitHub
//   - Custom domain support
//   - Built-in authentication (optional)
// ============================================================================

param location string
param appName string
param environmentName string
param tags object
param githubRepoUrl string
param githubBranch string
param backendApiUrl string

// Variables
var staticWebAppName = 'swa-${appName}-${environmentName}'
// Static Web Apps는 Korea Central을 지원하지 않으므로 East Asia 사용
var staticWebAppLocation = location == 'koreacentral' ? 'eastasia' : location

// Static Web App
resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: staticWebAppName
  location: staticWebAppLocation
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    repositoryUrl: 'https://github.com/${githubRepoUrl}'
    branch: githubBranch
    buildProperties: {
      appLocation: '/frontend' // Frontend code location in repo
      apiLocation: '' // No API (using Container Apps)
      outputLocation: 'dist' // Vite build output
      appBuildCommand: 'npm run build'
    }
    stagingEnvironmentPolicy: 'Enabled' // Enable staging environments for PRs
    allowConfigFileUpdates: true
    provider: 'GitHub'
  }
}

// App Settings (Environment Variables for Frontend)
resource staticWebAppSettings 'Microsoft.Web/staticSites/config@2022-09-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    VITE_API_BASE_URL: backendApiUrl
  }
}

// Outputs
output staticWebAppUrl string = 'https://${staticWebApp.properties.defaultHostname}'
output staticWebAppName string = staticWebApp.name
output staticWebAppId string = staticWebApp.id
