$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$ErrorActionPreference = "Stop"
$acrName = "acrcybershield53659"
$backendUrl = "https://cybershield-backend.graytree-5e13f588.eastus.azurecontainerapps.io"

Write-Host "Building Frontend Image..."
docker build --build-arg VITE_API_URL=$backendUrl -t "$acrName.azurecr.io/cybershield-frontend:latest" ./frontend

Write-Host "Pushing Frontend Image..."
docker push "$acrName.azurecr.io/cybershield-frontend:latest"

Write-Host "Deploying Frontend Container App..."
$password = az acr credential show --name $acrName --query "passwords[0].value" -o tsv

$cmd = "az containerapp create --name cybershield-frontend --resource-group rg-cybershield --environment env-cybershield --image $acrName.azurecr.io/cybershield-frontend:latest --target-port 80 --ingress external --registry-server $acrName.azurecr.io --registry-username $acrName --registry-password $password --output none"
Invoke-Expression $cmd

$frontendUrl = az containerapp show --name cybershield-frontend --resource-group rg-cybershield --query properties.configuration.ingress.fqdn -o tsv
Write-Host "FRONTEND_URL=https://$frontendUrl"
