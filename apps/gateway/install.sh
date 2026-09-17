#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
WWW_DST="/var/www/rasp-gateway"
CADDY_DST="/etc/caddy/Caddyfile"
UNIT_DST="/etc/systemd/system/mdns-publish.service"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-run with sudo: sudo $0" >&2
  exit 1
fi

if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y
  DEBIAN_FRONTEND=noninteractive apt-get install -y caddy avahi-daemon avahi-utils rsync
fi

install -d -m 0755 "$WWW_DST"
rsync -a --delete "$APP_DIR/www/" "$WWW_DST/"
chown -R caddy:caddy "$WWW_DST"

install -m 0644 "$APP_DIR/Caddyfile" "$CADDY_DST"
chmod +x "$APP_DIR/publish-mdns.sh"

awk -v app="$APP_DIR" '{ gsub(/\/home\/longlom\/rasp\/apps\/gateway/, app) } { print }' \
  "$APP_DIR/mdns-publish.service" > "$UNIT_DST"

systemctl enable --now avahi-daemon
systemctl daemon-reload
systemctl enable --now mdns-publish.service
systemctl restart mdns-publish.service
systemctl enable --now caddy
systemctl reload caddy || systemctl restart caddy

ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo
echo "LAN gateway is running."
echo "  Hub:    http://pi.local/     (also http://${ip}/ )"
echo "  Camera: http://camera.local/"
echo "  Budget: http://budget.local/"
echo "Logs: journalctl -u caddy -f ; journalctl -u mdns-publish -f"
