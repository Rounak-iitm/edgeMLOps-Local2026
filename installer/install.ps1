[CmdletBinding()]
param(
  [string]$InstallDir = "$env:ProgramData\EdgeMLOps",
  [string]$LicenseFile = "",
  [switch]$Demo,
  [switch]$SkipTraining
)
$ErrorActionPreference = 'Stop'
Write-Host "EdgeMLOps Local Enterprise Edge 2.0.0" -ForegroundColor Cyan
Write-Host "Install directory: $InstallDir"
function Require-Command($name,$hint){ if(-not(Get-Command $name -ErrorAction SilentlyContinue)){throw "$name is required. $hint"} }
Require-Command docker "Install Docker Desktop with WSL2, then rerun."
docker info *> $null; if($LASTEXITCODE -ne 0){throw "Docker is installed but not running."}
if(-not $Demo -and [string]::IsNullOrWhiteSpace($LicenseFile)){throw "Production installation requires -LicenseFile. Use -Demo only for evaluation."}
if(-not (Test-Path $InstallDir)){New-Item -ItemType Directory -Path $InstallDir -Force|Out-Null}
$source=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Copy-Item "$source\*" $InstallDir -Recurse -Force -Exclude '.venv','.git','__pycache__','*.pyc'
New-Item -ItemType Directory -Path (Join-Path $InstallDir 'license') -Force|Out-Null
$envFile=Join-Path $InstallDir 'docker\.env'
if($Demo){$mode='demo'}else{$mode='production'; Copy-Item (Resolve-Path $LicenseFile) (Join-Path $InstallDir 'license\license.json') -Force}
if(-not(Test-Path $envFile)){
  $bytes=New-Object byte[] 32; [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
  $apiKey=[Convert]::ToBase64String($bytes)
  "EDGE_API_KEY=$apiKey`nEDGE_PORT=8080`nEDGE_BIND=127.0.0.1`nEDGE_LICENSE_MODE=$mode`nLOG_LEVEL=INFO" | Set-Content $envFile -Encoding UTF8
}else{
  (Get-Content $envFile) -replace '^EDGE_LICENSE_MODE=.*$',"EDGE_LICENSE_MODE=$mode" | Set-Content $envFile -Encoding UTF8
}
if(-not $SkipTraining){
  Require-Command py "Python 3.12 is required only for the local training/bootstrap environment."
  $venv=Join-Path $InstallDir '.venv'
  if(-not(Test-Path (Join-Path $venv 'Scripts\python.exe'))){py -3.12 -m venv $venv}
  & (Join-Path $venv 'Scripts\python.exe') -m pip install --upgrade pip
  & (Join-Path $venv 'Scripts\python.exe') -m pip install -r (Join-Path $InstallDir 'requirements.txt')
  Push-Location $InstallDir; try {
    if(-not(Test-Path '.zen\config.yaml')){& (Join-Path $venv 'Scripts\zenml.exe') init}
    if($Demo){& (Join-Path $venv 'Scripts\python.exe') run_pipeline.py --simulate-drift}
  } finally {Pop-Location}
}
Push-Location (Join-Path $InstallDir 'docker'); try {docker compose --env-file .env up -d --build; if($LASTEXITCODE -ne 0){throw 'Docker Compose failed.'}} finally {Pop-Location}
Write-Host "Installation complete." -ForegroundColor Green
Write-Host "Health: http://127.0.0.1:8080/health"; Write-Host "Docs: http://127.0.0.1:8080/docs"; Write-Host "Install root: $InstallDir"
