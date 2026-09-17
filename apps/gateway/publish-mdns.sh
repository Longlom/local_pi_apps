#!/usr/bin/env bash
set -euo pipefail

NAMES_FILE="$(cd "$(dirname "$0")" && pwd)/mdns-names.txt"
IP="${LAN_IP:-$(hostname -I 2>/dev/null | awk '{print $1}')}"

if [[ -z "$IP" ]]; then
  echo "No LAN IP; cannot publish .local names." >&2
  exit 1
fi

pids=()
cleanup() {
  for pid in "${pids[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

while read -r name; do
  [[ -z "$name" || "$name" =~ ^# ]] && continue
  echo "Publishing ${name} -> ${IP}" >&2
  avahi-publish -a -R "$name" "$IP" &
  pids+=("$!")
done < "$NAMES_FILE"

if [[ ${#pids[@]} -eq 0 ]]; then
  echo "No names in $NAMES_FILE" >&2
  exit 1
fi

wait -n
exit 1
