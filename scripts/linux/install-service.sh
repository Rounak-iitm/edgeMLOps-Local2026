#!/usr/bin/env bash
set -euo pipefail
INSTALL_DIR="${1:-/opt/edgemlops}"
cat >/etc/systemd/system/edgemlops.service <<UNIT
[Unit]
Description=EdgeMLOps Enterprise Edge
After=docker.service
Requires=docker.service
[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR/docker
ExecStart=/usr/bin/docker compose --env-file $INSTALL_DIR/docker/.env up -d
ExecStop=/usr/bin/docker compose --env-file $INSTALL_DIR/docker/.env down
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now edgemlops.service
