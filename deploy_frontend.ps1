$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$ErrorActionPreference = "Stop"
$acrName = "acrcybershield53659"
$backendUrl = "https://cybershield-backend.graytree-5e13f588.eastus.azurecontainerapps.io"

$tag = (Get-Date -Format "yyyyMMddHHmmss")

Write-Host "Logging into Azure Container Registry..."
az acr login --name $acrName

Write-Host "Building Frontend Image..."
docker build --build-arg VITE_API_URL=$backendUrl -t "$acrName.azurecr.io/cybershield-frontend:$tag" ./frontend

Write-Host "Pushing Frontend Image..."
docker push "$acrName.azurecr.io/cybershield-frontend:$tag"

Write-Host "Deploying Frontend Container App..."
$cmd = "az containerapp update --name cybershield-frontend --resource-group rg-cybershield --image $acrName.azurecr.io/cybershield-frontend:$tag --output none"
Invoke-Expression $cmd

$frontendUrl = az containerapp show --name cybershield-frontend --resource-group rg-cybershield --query properties.configuration.ingress.fqdn -o tsv
Write-Host "FRONTEND_URL=https://$frontendUrl"
