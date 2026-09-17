#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

if [[ ! -f "$APP_DIR/config.env" ]]; then
  cp "$APP_DIR/config.env.example" "$APP_DIR/config.env"
fi

set -a
# shellcheck disable=SC1091
source "$APP_DIR/config.env"
set +a

VENV="${APP_DIR}/.venv"
if [[ ! -x "${VENV}/bin/uvicorn" ]]; then
  echo "venv missing. Run install.sh first." >&2
  exit 1
fi

mkdir -p "${DATA_DIR:-data}"
export DATA_DIR BASE_CURRENCY
exec "${VENV}/bin/uvicorn" app:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8090}"
