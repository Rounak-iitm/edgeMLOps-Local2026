[CmdletBinding()]
param([string]$InstallDir="$env:ProgramData\EdgeMLOps", [Parameter(Mandatory=$true)][string]$ModelFile)
$ErrorActionPreference='Stop'
$store=Join-Path $InstallDir 'model_store'; $target=Join-Path $store $ModelFile
if (-not (Test-Path $target)) { throw "Model not found: $ModelFile" }
if ([IO.Path]::GetExtension($ModelFile) -ne '.onnx') { throw 'Only .onnx models can be selected.' }
$tmp=Join-Path $store 'LATEST.tmp'; Set-Content -Path $tmp -Value $ModelFile -NoNewline; Move-Item $tmp (Join-Path $store 'LATEST') -Force
docker compose --env-file (Join-Path $InstallDir 'docker\.env') -f (Join-Path $InstallDir 'docker\docker-compose.yml') restart edge-inference
Write-Host "Rolled back to $ModelFile" -ForegroundColor Green
