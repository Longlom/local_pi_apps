#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="budget.service"
UNIT_SRC="$APP_DIR/budget.service"
UNIT_DST="/etc/systemd/system/${SERVICE_NAME}"
SERVICE_USER="${SUDO_USER:-$(id -un)}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-run with sudo: sudo $0" >&2
  exit 1
fi

chmod +x "$APP_DIR/run.sh"

if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y
  DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip
fi

if [[ ! -f "$APP_DIR/config.env" ]]; then
  cp "$APP_DIR/config.env.example" "$APP_DIR/config.env"
fi

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

mkdir -p "$APP_DIR/data"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

awk -v user="$SERVICE_USER" -v app="$APP_DIR" '
  { gsub(/\/opt\/rasp\/apps\/budget/, app) }
  /^\[Service\]$/ { print; print "User=" user; print "Group=" user; next }
  { print }
' "$UNIT_SRC" > "$UNIT_DST"

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo
echo "budget is running on port 8090."
echo "Open http://budget.local/ after the gateway is installed."
echo "Logs: journalctl -u ${SERVICE_NAME} -f"
