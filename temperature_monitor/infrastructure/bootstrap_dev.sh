#!/usr/bin/env bash
# =============================================================
# azure-bootstrap.sh
# One-time setup: creates the Azure service principal, ACR,
# resource groups, and Key Vault secrets needed for CI/CD.
#
# Usage:
#   chmod +x azure-bootstrap.sh
#   ./azure-bootstrap.sh [dev|staging|prod]
# =============================================================
set -euo pipefail

ENV="${1:-dev}"
APP_NAME="tempmonitor"
LOCATION="westeurope"
RG="rg-${APP_NAME}-${ENV}"
ACR_NAME="acr${APP_NAME}${ENV}"          # must be globally unique, lowercase
KV_NAME="kv-${APP_NAME}-${ENV}"
SP_NAME="sp-${APP_NAME}-github-actions"

echo "═══════════════════════════════════════════════"
echo " Temperature Monitor – Azure Bootstrap"
echo " Environment : $ENV"
echo " Region      : $LOCATION"
echo "═══════════════════════════════════════════════"

# ── 1. Login check ──────────────────────────────────────────
if ! az account show &>/dev/null; then
  echo "➜ Logging in to Azure…"
  az login
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "✔ Using subscription: $SUBSCRIPTION_ID"

# ── 2. Resource group ───────────────────────────────────────
echo ""
echo "➜ Creating resource group '$RG'…"
az group create \
  --name "$RG" \
  --location "$LOCATION" \
  --tags application="$APP_NAME" environment="$ENV" managedBy=bicep \
  --output none
echo "✔ Resource group ready."

# ── 3. Azure Container Registry ─────────────────────────────
echo ""
echo "➜ Creating Azure Container Registry '$ACR_NAME'…"
az acr create \
  --resource-group "$RG" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true \
  --output none
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
echo "✔ ACR ready: $ACR_LOGIN_SERVER"

# ── 4. Key Vault ─────────────────────────────────────────────
echo ""
echo "➜ Creating Key Vault '$KV_NAME'…"
az keyvault create \
  --resource-group "$RG" \
  --name "$KV_NAME" \
  --location "$LOCATION" \
  --enable-rbac-authorization false \
  --output none

# Store PostgreSQL password
echo ""
read -rsp "Enter PostgreSQL admin password (will be stored in Key Vault): " PG_PASSWORD
echo ""
az keyvault secret set \
  --vault-name "$KV_NAME" \
  --name "postgres-admin-password" \
  --value "$PG_PASSWORD" \
  --output none
echo "✔ Key Vault ready. Secret 'postgres-admin-password' stored."

# ── 5. Service Principal for GitHub Actions ──────────────────
echo ""
echo "➜ Creating service principal '$SP_NAME'…"

# Contributor on resource group + AcrPush on ACR
SP_JSON=$(az ad sp create-for-rbac \
  --name "$SP_NAME" \
  --role Contributor \
  --scopes "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG}" \
  --sdk-auth)

# Also grant AcrPush
ACR_ID=$(az acr show --name "$ACR_NAME" --query id -o tsv)
SP_APP_ID=$(echo "$SP_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientId'])")
az role assignment create \
  --assignee "$SP_APP_ID" \
  --role AcrPush \
  --scope "$ACR_ID" \
  --output none

echo "✔ Service principal created."

# ── 6. Print GitHub Secrets ──────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════"
echo " Add these secrets to your GitHub repository:"
echo " (Settings → Secrets and variables → Actions)"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Secret name             │ Value"
echo "────────────────────────┼───────────────────────────────"
echo "AZURE_CREDENTIALS       │ (paste the JSON below)"
echo "AZURE_SUBSCRIPTION_ID   │ $SUBSCRIPTION_ID"
echo "ACR_NAME                │ $ACR_NAME"
echo "ACR_LOGIN_SERVER        │ $ACR_LOGIN_SERVER"
echo "POSTGRES_ADMIN_PASSWORD │ (the password you just entered)"
echo ""
echo "── AZURE_CREDENTIALS JSON ────────────────────────────"
echo "$SP_JSON"
echo "──────────────────────────────────────────────────────"

# ── 7. Update parameters files ───────────────────────────────
KV_ID=$(az keyvault show --name "$KV_NAME" --query id -o tsv)

for PARAMS_FILE in infrastructure/parameters.*.json; do
  # Replace placeholder Key Vault ID
  sed -i \
    "s|/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RG_NAME>/providers/Microsoft.KeyVault/vaults/<VAULT_NAME>|${KV_ID}|g" \
    "$PARAMS_FILE" 2>/dev/null || true
done
echo ""
echo "✔ infrastructure/parameters.*.json updated with Key Vault ID."
echo ""
echo "All done! You can now push to dev to trigger a deployment."