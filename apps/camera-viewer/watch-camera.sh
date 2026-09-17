#!/usr/bin/env bash
# Probe whether the IP camera is powered on (RTSP port open).
# A second ffmpeg/RTSP client can kick cheap cameras, so this is TCP-only.
set -u

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

if [[ -f "$APP_DIR/config.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "$APP_DIR/config.env"
  set +a
fi

RTSP_URL="${RTSP_URL:-rtsp://192.168.3.27:554/live/ch00_0}"
HTTP_LISTEN="${HTTP_LISTEN:-:1984}"
CAMERA_CHECK_INTERVAL="${CAMERA_CHECK_INTERVAL:-300}"
STATUS_FILE="${APP_DIR}/www/status.json"
PID_FILE="${APP_DIR}/go2rtc.pid"

listen="${HTTP_LISTEN#:}"
API="http://127.0.0.1:${listen}"

write_status() {
  local ok="$1"
  local err="${2:-}"
  local now
  now="$(date --iso-8601=seconds 2>/dev/null || date -Iseconds 2>/dev/null || date)"
  python3 - "$STATUS_FILE" "$ok" "$err" "$now" "$CAMERA_CHECK_INTERVAL" <<'PY' || true
import json, sys
path, ok, err, now, interval = sys.argv[1:6]
payload = {
    "ok": ok == "true",
    "checked_at": now,
    "interval_sec": int(interval),
    "error": err or None,
}
tmp = path + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(payload, f)
    f.write("\n")
import os
os.replace(tmp, path)
PY
}

wait_for_api() {
  local i
  for i in $(seq 1 30); do
    if curl -sf --max-time 2 "${API}/api/streams" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

rtsp_host_port() {
  local u="${RTSP_URL#rtsp://}"
  u="${u#*@}"
  u="${u%%/*}"
  local host="${u%%:*}"
  local port="${u##*:}"
  if [[ "$host" == "$port" ]]; then
    port=554
  fi
  echo "$host" "$port"
}

camera_ok() {
  local host port
  read -r host port < <(rtsp_host_port)
  timeout 3 bash -c "echo >/dev/tcp/${host}/${port}" 2>/dev/null
}

restart_go2rtc() {
  local pid=""
  if [[ -f "$PID_FILE" ]]; then
    pid="$(tr -d ' \n' < "$PID_FILE" || true)"
  fi
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "Camera is back; restarting go2rtc (pid $pid)" >&2
    kill "$pid" 2>/dev/null || true
  fi
}

was_ok="unknown"
wait_for_api || echo "go2rtc API not ready yet; will keep checking" >&2

while true; do
  err=""
  if camera_ok; then
    write_status true ""
    if [[ "$was_ok" == "false" ]]; then
      restart_go2rtc
    fi
    was_ok="true"
    echo "Camera check: up" >&2
  else
    err="rtsp port closed"
    write_status false "$err"
    was_ok="false"
    echo "Camera check: down (next in ${CAMERA_CHECK_INTERVAL}s)" >&2
  fi
  sleep "$CAMERA_CHECK_INTERVAL"
done
