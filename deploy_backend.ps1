$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$ErrorActionPreference = "Stop"
$acrName = "acrcybershield53659"

Write-Host "Creating Container App Environment..."
az containerapp env create --name env-cybershield --resource-group rg-cybershield --location eastus --output none

$tag = (Get-Date -Format "yyyyMMddHHmmss")

Write-Host "Logging into Azure Container Registry..."
az acr login --name $acrName

Write-Host "Building Backend Image..."
docker build -t "$acrName.azurecr.io/cybershield-backend:$tag" .

Write-Host "Pushing Backend Image..."
docker push "$acrName.azurecr.io/cybershield-backend:$tag"

Write-Host "Deploying Backend Container App..."
$envVars = Get-Content -Path ".env" | Where-Object { $_ -match '=' -and -not $_.StartsWith('#') } | ForEach-Object { 
    $parts = $_ -split '=', 2
    $key = $parts[0].Trim()
    $value = $parts[1].Trim(' "''')
    "$key=$value"
}
$envStr = $envVars -join ' '

$cmd = "az containerapp update --name cybershield-backend --resource-group rg-cybershield --image ${acrName}.azurecr.io/cybershield-backend:$tag --set-env-vars $envStr --output none"
Invoke-Expression $cmd

$backendUrl = az containerapp show --name cybershield-backend --resource-group rg-cybershield --query properties.configuration.ingress.fqdn -o tsv
Write-Host "BACKEND_URL=https://$backendUrl"
