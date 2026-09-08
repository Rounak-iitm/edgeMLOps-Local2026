[CmdletBinding()] param([string]$InstallDir="$env:ProgramData\EdgeMLOps")
$ErrorActionPreference='Stop'; & docker compose --env-file (Join-Path $InstallDir 'docker\.env') -f (Join-Path $InstallDir 'docker\docker-compose.yml') up -d
