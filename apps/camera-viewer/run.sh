#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

if [[ ! -f "$APP_DIR/config.env" ]]; then
  cp "$APP_DIR/config.env.example" "$APP_DIR/config.env"
  echo "Created $APP_DIR/config.env from example." >&2
fi

# shellcheck disable=SC1091
set -a
source "$APP_DIR/config.env"
set +a

RTSP_URL="${RTSP_URL:-rtsp://192.168.3.27:554/live/ch00_0}"
RTSP_TRANSPORT="${RTSP_TRANSPORT:-tcp}"
HTTP_LISTEN="${HTTP_LISTEN:-:1984}"
WEBRTC_LISTEN="${WEBRTC_LISTEN:-:8555}"
WEBRTC_CANDIDATE="${WEBRTC_CANDIDATE:-192.168.3.42:8555}"
STREAM_NAME="${STREAM_NAME:-cam}"
RESTART_DELAY="${RESTART_DELAY:-3}"
CAMERA_CHECK_INTERVAL="${CAMERA_CHECK_INTERVAL:-300}"

GO2RTC="$APP_DIR/bin/go2rtc"
if [[ ! -x "$GO2RTC" ]]; then
  echo "go2rtc not found at $GO2RTC. Run install.sh on the Pi first." >&2
  exit 1
fi

# ffmpeg pulls over RTSP TCP (prefer_tcp is go2rtc's default input template) and
# re-packages the camera's AAC, which browsers reject when passed through as-is.
# Video is copied, so this costs almost no CPU.
MAIN_SRC="ffmpeg:${RTSP_URL}#video=copy#audio=aac"
if [[ "$RTSP_TRANSPORT" == "udp" ]]; then
  MAIN_SRC="ffmpeg:${RTSP_URL}#video=copy#audio=aac#input=-rtsp_transport udp -i {input}"
fi

# WebRTC cannot carry AAC, so keep an Opus branch for it.
OPUS_SRC="ffmpeg:${STREAM_NAME}#audio=opus"
# Used only for /api/frame.jpeg snapshots and the MJPEG fallback.
MJPEG_SRC="ffmpeg:${STREAM_NAME}#video=mjpeg"

cat > "$APP_DIR/go2rtc.yaml" <<EOF
api:
  listen: "${HTTP_LISTEN}"
  origin: "*"
  static_dir: "${APP_DIR}/www"

rtsp:
  listen: ":8554"

webrtc:
  listen: "${WEBRTC_LISTEN}"
  candidates:
    - ${WEBRTC_CANDIDATE}

streams:
  ${STREAM_NAME}:
    - "${MAIN_SRC}"
    - "${OPUS_SRC}"
    - "${MJPEG_SRC}"
EOF

echo "Camera viewer listening on http://$(hostname -I 2>/dev/null | awk '{print $1}'):${HTTP_LISTEN#:}/" >&2
echo "Stream: $RTSP_URL (transport=$RTSP_TRANSPORT)" >&2
echo "If the camera is off, checking every ${CAMERA_CHECK_INTERVAL}s" >&2

chmod +x "$APP_DIR/watch-camera.sh" 2>/dev/null || true
"$APP_DIR/watch-camera.sh" &
WATCH_PID=$!

cleanup() {
  kill "$WATCH_PID" 2>/dev/null || true
  if [[ -n "${GO2RTC_PID:-}" ]]; then
    kill "$GO2RTC_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

while true; do
  "$GO2RTC" -c "$APP_DIR/go2rtc.yaml" &
  GO2RTC_PID=$!
  echo "$GO2RTC_PID" > "$APP_DIR/go2rtc.pid"
  wait "$GO2RTC_PID" || true
  echo "go2rtc exited; restarting in ${RESTART_DELAY}s" >&2
  sleep "$RESTART_DELAY"
done
