#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-run with sudo: sudo $0" >&2
  exit 1
fi

chmod +x "$APP_DIR/quiet-hours.sh"

install_unit() {
  local src="$1"
  local dst="/etc/systemd/system/$(basename "$src")"
  awk -v app="$APP_DIR" '{ gsub(/\/opt\/rasp\/apps\/quiet-hours/, app) } { print }' "$src" > "$dst"
}

install_unit "$APP_DIR/quiet-hours-start.service"
install_unit "$APP_DIR/quiet-hours-start.timer"
install_unit "$APP_DIR/quiet-hours-end.service"
install_unit "$APP_DIR/quiet-hours-end.timer"
install_unit "$APP_DIR/quiet-hours-boot.service"

systemctl daemon-reload
systemctl enable --now quiet-hours-start.timer quiet-hours-end.timer quiet-hours-boot.service
systemctl start quiet-hours-boot.service

echo
echo "Quiet hours: 01:00–08:00 ($(timedatectl show -p Timezone --value))."
echo "Pi 4 has no RTC, so it stays powered and SSH stays up."
echo "LAN apps stop at 01:00 and start at 08:00."
echo "Timers: systemctl list-timers 'quiet-hours-*'"
