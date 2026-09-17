#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
GO2RTC_VERSION="${GO2RTC_VERSION:-1.9.9}"
BIN_DIR="$APP_DIR/bin"
SERVICE_NAME="camera-viewer.service"
UNIT_SRC="$APP_DIR/camera-viewer.service"
UNIT_DST="/etc/systemd/system/${SERVICE_NAME}"
SERVICE_USER="${SUDO_USER:-$(id -un)}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-run with sudo: sudo $0" >&2
  exit 1
fi

mkdir -p "$BIN_DIR"
chmod +x "$APP_DIR/run.sh" "$APP_DIR/watch-camera.sh"

if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y
  DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg curl ca-certificates
fi

arch="$(uname -m)"
case "$arch" in
  aarch64 | arm64) asset="go2rtc_linux_arm64" ;;
  armv7l | armv6l | armhf) asset="go2rtc_linux_arm" ;;
  x86_64 | amd64) asset="go2rtc_linux_amd64" ;;
  *)
    echo "Unsupported architecture: $arch" >&2
    exit 1
    ;;
esac

echo "Downloading go2rtc v${GO2RTC_VERSION} (${asset})…"
curl -fsSL "https://github.com/AlexxIT/go2rtc/releases/download/v${GO2RTC_VERSION}/${asset}" \
  -o "$BIN_DIR/go2rtc"
chmod +x "$BIN_DIR/go2rtc"

if [[ ! -f "$APP_DIR/config.env" ]]; then
  cp "$APP_DIR/config.env.example" "$APP_DIR/config.env"
  echo "Wrote $APP_DIR/config.env — edit RTSP_URL / WEBRTC_CANDIDATE if needed."
fi

chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

awk -v user="$SERVICE_USER" -v app="$APP_DIR" '
  { gsub(/\/opt\/rasp\/apps\/camera-viewer/, app) }
  /^\[Service\]$/ { print; print "User=" user; print "Group=" user; next }
  { print }
' "$UNIT_SRC" > "$UNIT_DST"

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo
echo "camera-viewer is running."
echo "On your phone (same Wi-Fi/LAN) open:  http://${ip}:1984/"
echo "Logs: journalctl -u ${SERVICE_NAME} -f"
