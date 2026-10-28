# Deploy galileo-local to Azure Container Apps.
# Prerequisites: az login, Docker running, .env with OPENAI_API_KEY.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$RG = if ($env:GALILEO_AZURE_RG) { $env:GALILEO_AZURE_RG } else { "rg-galileo-local" }
$LOC = if ($env:GALILEO_AZURE_LOC) { $env:GALILEO_AZURE_LOC } else { "westeurope" }
$AcrSuffix = ($env:USERNAME -replace '[^a-zA-Z0-9]', '').ToLower()
if (-not $AcrSuffix) { $AcrSuffix = "user" }
$ACR = if ($env:GALILEO_AZURE_ACR) { $env:GALILEO_AZURE_ACR } else { "acrgalileo$AcrSuffix" }
$ENV = if ($env:GALILEO_AZURE_ENV) { $env:GALILEO_AZURE_ENV } else { "cae-galileo-local" }
$APP = if ($env:GALILEO_AZURE_APP) { $env:GALILEO_AZURE_APP } else { "galileo-local" }
$IMAGE_TAG = "v1"

# Load OPENAI_API_KEY from .env (never echo it)
$OpenAiKey = $env:OPENAI_API_KEY
if (-not $OpenAiKey -and (Test-Path ".env")) {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*OPENAI_API_KEY\s*=\s*(.+)\s*$') {
            $OpenAiKey = $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
}
if (-not $OpenAiKey -or $OpenAiKey.Length -lt 20 -or -not $OpenAiKey.StartsWith("sk-")) {
    throw "Set a usable OPENAI_API_KEY in .env or the environment before deploying."
}

Write-Host "RG=$RG LOC=$LOC ACR=$ACR ENV=$ENV APP=$APP"

az extension add --name containerapp --upgrade --yes 2>$null | Out-Null
az provider register --namespace Microsoft.App --wait 2>$null | Out-Null
az provider register --namespace Microsoft.ContainerRegistry --wait 2>$null | Out-Null
az provider register --namespace Microsoft.OperationalInsights --wait 2>$null | Out-Null

az group create -n $RG -l $LOC | Out-Null

if (-not (az acr show -n $ACR -g $RG 2>$null)) {
    Write-Host "Creating ACR $ACR ..."
    az acr create -n $ACR -g $RG --sku Basic --admin-enabled true | Out-Null
}

if (-not (az containerapp env show -n $ENV -g $RG 2>$null)) {
    Write-Host "Creating Container Apps environment $ENV ..."
    az containerapp env create -n $ENV -g $RG -l $LOC | Out-Null
}

$Image = "$ACR.azurecr.io/galileo-local:$IMAGE_TAG"
Write-Host "Building and pushing $Image ..."
az acr login -n $ACR | Out-Null
docker build -t $Image .
docker push $Image

$AcrUser = az acr credential show -n $ACR --query username -o tsv
$AcrPass = az acr credential show -n $ACR --query "passwords[0].value" -o tsv

$Exists = az containerapp show -n $APP -g $RG 2>$null
if ($Exists) {
    Write-Host "Updating existing Container App $APP ..."
    az containerapp secret set -n $APP -g $RG --secrets "openai-key=$OpenAiKey" | Out-Null
    az containerapp update -n $APP -g $RG `
        --image $Image `
        --set-env-vars `
            "GALILEO_BIND_HOST=0.0.0.0" `
            "GALILEO_BIND_PORT=8080" `
            "OPENAI_API_KEY=secretref:openai-key" | Out-Null
} else {
    Write-Host "Creating Container App $APP ..."
    az containerapp create `
        -n $APP -g $RG `
        --environment $ENV `
        --image $Image `
        --registry-server "$ACR.azurecr.io" `
        --registry-username $AcrUser `
        --registry-password $AcrPass `
        --target-port 8080 `
        --ingress external `
        --cpu 0.5 --memory 1.0Gi `
        --min-replicas 1 --max-replicas 1 `
        --secrets "openai-key=$OpenAiKey" `
        --env-vars `
            "GALILEO_BIND_HOST=0.0.0.0" `
            "GALILEO_BIND_PORT=8080" `
            "OPENAI_API_KEY=secretref:openai-key" | Out-Null
}

$Fqdn = az containerapp show -n $APP -g $RG --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host ""
Write-Host "Deployed."
Write-Host "Chat:    https://$Fqdn/chat"
Write-Host "Console: https://$Fqdn/"
Write-Host "FQDN=$Fqdn"
