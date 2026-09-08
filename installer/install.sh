#!/usr/bin/env bash
set -euo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/edgemlops}"
LICENSE_FILE="${1:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
command -v docker >/dev/null || { echo "Docker is required."; exit 1; }
docker info >/dev/null || { echo "Docker daemon is not running."; exit 1; }
if [[ -z "$LICENSE_FILE" ]]; then echo "Production install requires: sudo ./installer/install.sh /path/to/license.json"; exit 2; fi
sudo mkdir -p "$INSTALL_DIR/license" "$INSTALL_DIR"
sudo cp -a "$ROOT/." "$INSTALL_DIR/"
sudo cp "$LICENSE_FILE" "$INSTALL_DIR/license/license.json"
if [[ ! -f "$INSTALL_DIR/docker/.env" ]]; then
  API_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  printf 'EDGE_API_KEY=%s\nEDGE_PORT=8080\nEDGE_BIND=127.0.0.1\nEDGE_LICENSE_MODE=production\nLOG_LEVEL=INFO\n' "$API_KEY" | sudo tee "$INSTALL_DIR/docker/.env" >/dev/null
fi
cd "$INSTALL_DIR/docker"; sudo docker compose --env-file .env up -d --build
sudo "$INSTALL_DIR/scripts/linux/install-service.sh" "$INSTALL_DIR"
echo "EdgeMLOps Enterprise Edge installed at $INSTALL_DIR"
