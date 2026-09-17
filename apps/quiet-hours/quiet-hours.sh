#!/usr/bin/env bash
# Raspberry Pi 4 has no RTC, so it cannot halt at 01:00 and power itself
# back on at 08:00. Quiet hours stop LAN apps and blank HDMI instead.
# SSH stays up so you can still reach the Pi.
set -euo pipefail

STATE_DIR=/var/lib/quiet-hours
STATE_FILE="${STATE_DIR}/active"
SERVICES=(
  camera-viewer.service
  budget.service
  caddy.service
  mdns-publish.service
)

mkdir -p "$STATE_DIR"

hour=$(date +%H)
minute=$(date +%M)
now=$((10#$hour * 60 + 10#$minute))
quiet_start=$((1 * 60))
quiet_end=$((8 * 60))

in_quiet_window() {
  # 01:00 inclusive … 08:00 exclusive
  [[ "$now" -ge "$quiet_start" && "$now" -lt "$quiet_end" ]]
}

set_display() {
  local mode="$1"
  if command -v vcgencmd >/dev/null 2>&1; then
    vcgencmd display_power "$mode" >/dev/null 2>&1 || true
  fi
}

enter_quiet() {
  echo "Entering quiet hours ($(date))"
  for svc in "${SERVICES[@]}"; do
    if systemctl cat "$svc" >/dev/null 2>&1; then
      systemctl stop "$svc" || true
    fi
  done
  set_display 0
  echo 1 > "$STATE_FILE"
}

leave_quiet() {
  echo "Leaving quiet hours ($(date))"
  set_display 1
  systemctl start avahi-daemon.service 2>/dev/null || true
  for svc in mdns-publish.service camera-viewer.service budget.service caddy.service; do
    if systemctl cat "$svc" >/dev/null 2>&1; then
      systemctl start "$svc" || true
    fi
  done
  rm -f "$STATE_FILE"
}

cmd="${1:-auto}"
case "$cmd" in
  start)
    enter_quiet
    ;;
  end)
    leave_quiet
    ;;
  auto)
    if in_quiet_window; then
      enter_quiet
    else
      leave_quiet
    fi
    ;;
  *)
    echo "Usage: $0 {start|end|auto}" >&2
    exit 1
    ;;
esac
