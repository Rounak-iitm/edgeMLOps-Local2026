[CmdletBinding()]
param([string]$InstallDir = "$env:ProgramData\EdgeMLOps", [switch]$KeepModels)
$ErrorActionPreference = 'Stop'
if (Get-Command docker -ErrorAction SilentlyContinue) {
  $compose = Join-Path $InstallDir 'docker'
  if (Test-Path $compose) { Push-Location $compose; try { docker compose down } finally { Pop-Location } }
}
if ($KeepModels) {
  $backup = "$InstallDir-models-backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
  Copy-Item (Join-Path $InstallDir 'model_store') $backup -Recurse -Force
  Write-Host "Models backed up to $backup"
}
if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
Write-Host 'EdgeMLOps Local removed.'
