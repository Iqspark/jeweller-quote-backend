#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy-azure.sh  —  Provision all Azure resources for json-to-email
# Run once to set up infrastructure. CI/CD handles subsequent deploys.
# Usage: bash deploy-azure.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

# ── Config — edit these ───────────────────────────────────────────────────────
SUBSCRIPTION_ID="<YOUR_SUBSCRIPTION_ID>"
LOCATION="eastus"
RG="rg-json-to-email"
ACR="acrjsontoemail"                        # must be globally unique, no hyphens
COSMOSDB_ACCOUNT="cosmos-json-to-email"     # must be globally unique
COSMOSDB_DB="json_submissions"
COSMOSDB_COLLECTION="submissions"
ACS_RESOURCE="acs-json-to-email"
CONTAINER_ENV="env-json-to-email"
CONTAINER_APP="ca-json-to-email"
IMAGE="$ACR.azurecr.io/json-to-email:latest"

echo "🔑 Setting subscription..."
az account set --subscription "$SUBSCRIPTION_ID"

# ── 1. Resource Group ─────────────────────────────────────────────────────────
echo "📦 Creating resource group..."
az group create --name "$RG" --location "$LOCATION"

# ── 2. Azure Container Registry ──────────────────────────────────────────────
echo "🐳 Creating Container Registry..."
az acr create --resource-group "$RG" --name "$ACR" --sku Basic --admin-enabled true

# ── 3. CosmosDB for MongoDB ───────────────────────────────────────────────────
echo "🍃 Creating CosmosDB (MongoDB API)..."
az cosmosdb create \
  --name "$COSMOSDB_ACCOUNT" \
  --resource-group "$RG" \
  --kind MongoDB \
  --server-version 4.2 \
  --default-consistency-level Session

az cosmosdb mongodb database create \
  --account-name "$COSMOSDB_ACCOUNT" \
  --resource-group "$RG" \
  --name "$COSMOSDB_DB"

az cosmosdb mongodb collection create \
  --account-name "$COSMOSDB_ACCOUNT" \
  --resource-group "$RG" \
  --database-name "$COSMOSDB_DB" \
  --name "$COSMOSDB_COLLECTION" \
  --shard "_id"

COSMOS_CONN=$(az cosmosdb keys list \
  --name "$COSMOSDB_ACCOUNT" \
  --resource-group "$RG" \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" -o tsv)
echo "✅ CosmosDB connection string captured."

# ── 4. Azure Communication Services ──────────────────────────────────────────
echo "📧 Creating Azure Communication Services..."
az communication create \
  --name "$ACS_RESOURCE" \
  --resource-group "$RG" \
  --location "global" \
  --data-location "United States"

ACS_CONN=$(az communication list-key \
  --name "$ACS_RESOURCE" \
  --resource-group "$RG" \
  --query primaryConnectionString -o tsv)
echo "✅ ACS connection string captured."

# ── 5. Build & Push Docker Image ─────────────────────────────────────────────
echo "🔨 Building and pushing Docker image..."
az acr login --name "$ACR"
docker build -t "$IMAGE" .
docker push "$IMAGE"

# ── 6. Container Apps Environment ────────────────────────────────────────────
echo "🌐 Creating Container Apps environment..."
az extension add --name containerapp --upgrade -y
az containerapp env create \
  --name "$CONTAINER_ENV" \
  --resource-group "$RG" \
  --location "$LOCATION"

# ── 7. Deploy Container App ───────────────────────────────────────────────────
echo "🚀 Deploying Container App..."
ACR_USER=$(az acr credential show --name "$ACR" --query username -o tsv)
ACR_PASS=$(az acr credential show --name "$ACR" --query passwords[0].value -o tsv)

az containerapp create \
  --name "$CONTAINER_APP" \
  --resource-group "$RG" \
  --environment "$CONTAINER_ENV" \
  --image "$IMAGE" \
  --registry-server "$ACR.azurecr.io" \
  --registry-username "$ACR_USER" \
  --registry-password "$ACR_PASS" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 5 \
  --env-vars \
      MONGO_URI="$COSMOS_CONN" \
      MONGO_DATABASE="$COSMOSDB_DB" \
      MONGO_COLLECTION="$COSMOSDB_COLLECTION" \
      EMAIL_PROVIDER="acs" \
      ACS_CONNECTION_STRING="$ACS_CONN" \
      ACS_SENDER_ADDRESS="DoNotReply@yourdomain.azurecomm.net"

# ── 8. Print URL ──────────────────────────────────────────────────────────────
APP_URL=$(az containerapp show \
  --name "$CONTAINER_APP" \
  --resource-group "$RG" \
  --query properties.configuration.ingress.fqdn -o tsv)

echo ""
echo "═══════════════════════════════════════════════════"
echo "✅  Deployment complete!"
echo "🌍  API URL:     https://$APP_URL"
echo "📖  Swagger UI:  https://$APP_URL/docs"
echo "═══════════════════════════════════════════════════"
