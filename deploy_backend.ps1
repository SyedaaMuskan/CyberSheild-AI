$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$ErrorActionPreference = "Stop"
$acrName = "acrcybershield53659"

Write-Host "Creating Container App Environment..."
az containerapp env create --name env-cybershield --resource-group rg-cybershield --location eastus --output none

Write-Host "Deploying Backend Container App..."
$envVars = Get-Content -Path ".env" | Where-Object { $_ -match '=' -and -not $_.StartsWith('#') } | ForEach-Object { 
    $parts = $_ -split '=', 2
    $key = $parts[0].Trim()
    $value = $parts[1].Trim(' "''')
    "$key=$value"
}
$envStr = $envVars -join ' '

$password = az acr credential show --name $acrName --query "passwords[0].value" -o tsv

$cmd = "az containerapp create --name cybershield-backend --resource-group rg-cybershield --environment env-cybershield --image ${acrName}.azurecr.io/cybershield-backend:latest --target-port 8000 --ingress external --registry-server ${acrName}.azurecr.io --registry-username $acrName --registry-password $password --env-vars $envStr --output none"

Invoke-Expression $cmd

$backendUrl = az containerapp show --name cybershield-backend --resource-group rg-cybershield --query properties.configuration.ingress.fqdn -o tsv
Write-Host "BACKEND_URL=https://$backendUrl"
