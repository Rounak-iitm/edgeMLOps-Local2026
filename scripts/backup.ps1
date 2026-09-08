[CmdletBinding()]
param([string]$InstallDir="$env:ProgramData\EdgeMLOps", [string]$Destination="$env:ProgramData\EdgeMLOps-Backups")
$ErrorActionPreference='Stop'; New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'; $out=Join-Path $Destination "backup-$stamp.zip"
Compress-Archive -Path (Join-Path $InstallDir 'model_store'),(Join-Path $InstallDir 'config'),(Join-Path $InstallDir 'docker\.env') -DestinationPath $out -Force
Write-Host "Backup: $out"
