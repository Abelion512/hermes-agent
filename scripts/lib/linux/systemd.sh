#!/bin/bash
# Systemd service management for Hermes CLI on Linux

set -e

HERMES_SERVICE_NAME="hermes-gateway"
SYSTEMD_DIR="/etc/systemd/system"

create_systemd_service() {
    local hermes_path="$1"
    local user="${2:-$USER}"
    local port="${3:-8080}"
    
    cat > "${SYSTEMD_DIR}/${HERMES_SERVICE_NAME}.service" << EOF
[Unit]
Description=Hermes AI Gateway Service
After=network.target

[Service]
Type=simple
User=${user}
WorkingDirectory=${hermes_path}
ExecStart=${hermes_path}/venv/bin/hermes gateway --port ${port}
Restart=on-failure
RestartSec=5
Environment=PATH=${hermes_path}/venv/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    echo "Systemd service created: ${HERMES_SERVICE_NAME}"
}

start_service() {
    systemctl start "${HERMES_SERVICE_NAME}"
    echo "Service started"
}

stop_service() {
    systemctl stop "${HERMES_SERVICE_NAME}"
    echo "Service stopped"
}

restart_service() {
    systemctl restart "${HERMES_SERVICE_NAME}"
    echo "Service restarted"
}

enable_service() {
    systemctl enable "${HERMES_SERVICE_NAME}"
    echo "Service enabled on boot"
}

disable_service() {
    systemctl disable "${HERMES_SERVICE_NAME}"
    echo "Service disabled on boot"
}

check_status() {
    systemctl status "${HERMES_SERVICE_NAME}" --no-pager
}

case "${1:-status}" in
    create)
        create_systemd_service "${2:-/opt/hermes}" "${3:-}" "${4:-8080}"
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    enable)
        enable_service
        ;;
    disable)
        disable_service
        ;;
    status)
        check_status
        ;;
    *)
        echo "Usage: $0 {create|start|stop|restart|enable|disable|status} [path] [user] [port]"
        exit 1
        ;;
esac
