// ============================================================
// Temperature Monitor – Azure Infrastructure (Bicep)
// Resources: ACR · Container Apps Environment · Backend App
//            · Frontend App · PostgreSQL Flexible Server
// ============================================================

@description('Short environment name: dev | staging | prod')
@allowed(['dev', 'staging', 'prod'])
param environmentName string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Base name used to derive all resource names')
param appName string = 'temperature_monitor'

@description('PostgreSQL administrator username')
param postgresAdminUser string = 'pgadmin'

@description('PostgreSQL administrator password (use a Key Vault reference in production)')
@secure()
param postgresAdminPassword string

@description('Container image tag to deploy')
param imageTag string = 'latest'

// ── Derived names ──────────────────────────────────────────
var suffix         = '${appName}-${environmentName}'
var acrName        = replace('acr${suffix}', '-', '') // ACR names: alphanumeric only
var logWorkspace   = 'log-${suffix}'
var containerEnv   = 'cae-${suffix}'
var backendApp     = 'ca-backend-${suffix}'
var frontendApp    = 'ca-frontend-${suffix}'
var postgresServer = 'pg-${suffix}'
var postgresDb     = 'appdb'
var vnetName       = 'vnet-${suffix}'
var subnetName     = 'snet-containers'

// ── Tags applied to every resource ────────────────────────
var commonTags = {
  application: appName
  environment: environmentName
  managedBy:   'bicep'
}

// ══════════════════════════════════════════════════════════
// 1. Virtual Network (isolated subnet for Container Apps)
// ══════════════════════════════════════════════════════════
resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name:     vnetName
  location: location
  tags:     commonTags
  properties: {
    addressSpace: { addressPrefixes: ['10.0.0.0/16'] }
    subnets: [
      {
        name: subnetName
        properties: {
          addressPrefix:                     '10.0.0.0/23'
          delegations: [
            {
              name: 'containerAppsDelegation'
              properties: { serviceName: 'Microsoft.App/environments' }
            }
          ]
        }
      }
    ]
  }
}

// ══════════════════════════════════════════════════════════
// 2. Log Analytics Workspace
// ══════════════════════════════════════════════════════════
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name:     logWorkspace
  location: location
  tags:     commonTags
  properties: {
    sku:                  { name: 'PerGB2018' }
    retentionInDays:      30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery:     'Enabled'
  }
}

// ══════════════════════════════════════════════════════════
// 3. Azure Container Registry
// ══════════════════════════════════════════════════════════
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name:     acrName
  location: location
  tags:     commonTags
  sku:      { name: 'Basic' }
  properties: {
    adminUserEnabled: true   // needed for Container Apps pull credentials
  }
}

// ══════════════════════════════════════════════════════════
// 4. Container Apps Environment
// ══════════════════════════════════════════════════════════
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name:     containerEnv
  location: location
  tags:     commonTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey:  logAnalytics.listKeys().primarySharedKey
      }
    }
    vnetConfiguration: {
      infrastructureSubnetId: vnet.properties.subnets[0].id
    }
  }
}

// ══════════════════════════════════════════════════════════
// 5. PostgreSQL Flexible Server
// ══════════════════════════════════════════════════════════
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name:     postgresServer
  location: location
  tags:     commonTags
  sku: {
    name: environmentName == 'prod' ? 'Standard_D2s_v3' : 'Standard_B1ms'
    tier: environmentName == 'prod' ? 'GeneralPurpose' : 'Burstable'
  }
  properties: {
    administratorLogin:         postgresAdminUser
    administratorLoginPassword: postgresAdminPassword
    version:                    '14'
    storage:                    { storageSizeGB: environmentName == 'prod' ? 64 : 32 }
    backup: {
      backupRetentionDays: environmentName == 'prod' ? 7 : 1
      geoRedundantBackup:  environmentName == 'prod' ? 'Enabled' : 'Disabled'
    }
    highAvailability: {
      mode: environmentName == 'prod' ? 'ZoneRedundant' : 'Disabled'
    }
    authConfig: { activeDirectoryAuth: 'Disabled', passwordAuth: 'Enabled' }
  }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: postgres
  name:   postgresDb
  properties: { charset: 'UTF8', collation: 'en_US.utf8' }
}

// Allow Container Apps environment to reach PostgreSQL
resource postgresFirewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = {
  parent: postgres
  name:   'allow-container-apps'
  properties: {
    // Container Apps outbound IPs are dynamic; 0.0.0.0/0 for simplicity –
    // tighten with specific IPs or private endpoint in production.
    startIpAddress: '0.0.0.0'
    endIpAddress:   '255.255.255.255'
  }
}

// ══════════════════════════════════════════════════════════
// 6. Backend Container App (Flask / Gunicorn)
// ══════════════════════════════════════════════════════════
var databaseUrl = 'postgresql://${postgresAdminUser}:${postgresAdminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/${postgresDb}?sslmode=require'

resource backendContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name:     backendApp
  location: location
  tags:     commonTags
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external:   true
        targetPort: 8000
        transport:  'http'
        corsPolicy: {
          allowedOrigins:     ['*']
          allowedMethods:     ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders:     ['*']
          allowCredentials:   false
        }
      }
      registries: [
        {
          server:            acr.properties.loginServer
          username:          acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        { name: 'acr-password',   value: acr.listCredentials().passwords[0].value }
        { name: 'database-url',   value: databaseUrl }
        { name: 'secret-key',     value: uniqueString(resourceGroup().id, appName) }
      ]
    }
    template: {
      containers: [
        {
          name:  'backend'
          image: '${acr.properties.loginServer}/backend:${imageTag}'
          resources: {
            cpu:    environmentName == 'prod' ? '1.0' : '0.5'
            memory: environmentName == 'prod' ? '2Gi' : '1Gi'
          }
          env: [
            { name: 'FLASK_ENV',     value: environmentName == 'prod' ? 'production' : 'development' }
            { name: 'DATABASE_URL',  secretRef: 'database-url' }
            { name: 'SECRET_KEY',    secretRef: 'secret-key' }
            { name: 'PORT',          value: '8000' }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/health', port: 8000 }
              initialDelaySeconds: 15
              periodSeconds:       20
            }
            {
              type: 'Readiness'
              httpGet: { path: '/health', port: 8000 }
              initialDelaySeconds: 5
              periodSeconds:       10
            }
          ]
        }
      ]
      scale: {
        minReplicas: environmentName == 'prod' ? 2 : 1
        maxReplicas: environmentName == 'prod' ? 10 : 3
        rules: [
          {
            name: 'http-scaling'
            http: { metadata: { concurrentRequests: '50' } }
          }
        ]
      }
    }
  }
}

// ══════════════════════════════════════════════════════════
// 7. Frontend Container App (React / Nginx)
// ══════════════════════════════════════════════════════════
resource frontendContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name:     frontendApp
  location: location
  tags:     commonTags
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external:   true
        targetPort: 80
        transport:  'http'
      }
      registries: [
        {
          server:            acr.properties.loginServer
          username:          acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        { name: 'acr-password', value: acr.listCredentials().passwords[0].value }
      ]
    }
    template: {
      containers: [
        {
          name:  'frontend'
          image: '${acr.properties.loginServer}/frontend:${imageTag}'
          resources: {
            cpu:    '0.5'
            memory: '1Gi'
          }
          env: [
            {
              name:  'REACT_APP_API_URL'
              value: 'https://${backendContainerApp.properties.configuration.ingress.fqdn}'
            }
          ]
        }
      ]
      scale: {
        minReplicas: environmentName == 'prod' ? 2 : 1
        maxReplicas: environmentName == 'prod' ? 5 : 2
      }
    }
  }
}

// ══════════════════════════════════════════════════════════
// Outputs
// ══════════════════════════════════════════════════════════
output acrLoginServer    string = acr.properties.loginServer
output backendUrl        string = 'https://${backendContainerApp.properties.configuration.ingress.fqdn}'
output frontendUrl       string = 'https://${frontendContainerApp.properties.configuration.ingress.fqdn}'
output postgresHost      string = postgres.properties.fullyQualifiedDomainName
output containerEnvName  string = containerAppsEnv.name
output resourceGroupName string = resourceGroup().name
