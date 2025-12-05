#!/usr/bin/env pwsh
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$RootDir = (Resolve-Path "$ScriptDir/.." ).Path
Set-Location $RootDir

$RG = 'tmp'
$Loc = 'japaneast'
$WebApp = 'tmp-rag-chat'
$ZipPath = Join-Path $RootDir 'deploy.zip'
$EnvFile = Join-Path $RootDir '.env'

if (-not (Test-Path $EnvFile)) {
    Write-Error "[エラー] $EnvFile がありません。必要な設定を記入して作成してください。"
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^(?<key>[A-Z0-9_]+)=(?<value>.*)$') {
        $key = $Matches['key']
        $value = $Matches['value']
        Set-Item -Path "env:$key" -Value $value
    }
}

$requiredVars = @('APP_LOGIN_USERNAME','APP_LOGIN_PASSWORD','AZURE_AI_PROJECT_ENDPOINT','AZURE_AI_AGENT_NAME')
foreach ($var in $requiredVars) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($var))) {
        Write-Error "[エラー] $var が $EnvFile に設定されていません。"
    }
}

Write-Host "[情報] $ZipPath にパッケージングします"
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}
Compress-Archive -Path (Get-ChildItem -Recurse | Where-Object {
    $_.FullName -notmatch '\\.git\\' -and \
    $_.FullName -notmatch '\\.venv\\' -and \
    $_.FullName -notmatch '\\__pycache__\\' -and \
    $_.FullName -notmatch '\\.azure\\' -and \
    $_.FullName -notmatch '\\.vscode\\' -and \
    $_.Name -notmatch '\\.env$' -and \
    $_.Name -notmatch 'README\\.md$'
} | Select-Object -ExpandProperty FullName) -DestinationPath $ZipPath -Force

if (-not (az account show *> $null)) {
    Write-Host "[情報] az login を実行します"
    az login | Out-Null
}

Write-Host "[情報] App Service のアプリ設定を更新します"
az webapp config appsettings set \
  --resource-group $RG \
  --name $WebApp \
  --settings \
    APP_LOGIN_USERNAME=$env:APP_LOGIN_USERNAME \
    APP_LOGIN_PASSWORD=$env:APP_LOGIN_PASSWORD \
    AZURE_AI_PROJECT_ENDPOINT=$env:AZURE_AI_PROJECT_ENDPOINT \
    AZURE_AI_AGENT_NAME=$env:AZURE_AI_AGENT_NAME \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    WEBSITES_PORT=8000

$startup = 'bash scripts/startup.sh'
Write-Host "[情報] スタートアップコマンドを $startup に設定します"
az webapp config set --resource-group $RG --name $WebApp --startup-file $startup

Write-Host "[情報] $ZipPath を $WebApp にデプロイします"
az webapp deploy --resource-group $RG --name $WebApp --type zip --src-path $ZipPath

Write-Host "[情報] デプロイ完了"
