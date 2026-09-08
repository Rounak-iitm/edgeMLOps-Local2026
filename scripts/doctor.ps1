[CmdletBinding()] param([string]$InstallDir="$env:ProgramData\EdgeMLOps")
$ErrorActionPreference='Continue'; Write-Host 'EdgeMLOps Enterprise Edge - System Diagnostics' -ForegroundColor Cyan
Write-Host "Version: $(Get-Content (Join-Path $InstallDir 'VERSION'))"
Get-Command docker -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (Get-Command docker -ErrorAction SilentlyContinue) { docker --version; docker info *> $null; Write-Host "Docker daemon exit: $LASTEXITCODE" }
try { $h=Invoke-RestMethod 'http://127.0.0.1:8080/health' -TimeoutSec 5; $h | ConvertTo-Json } catch { Write-Host "Inference: unavailable" }
