#!/usr/bin/env bash
set -euo pipefail

REPO_RAW_BASE="${BOTANEO_REPO_RAW_BASE:-https://raw.githubusercontent.com/Botaneo-project/botaneo/main}"
BOTANEO_HOME="${BOTANEO_HOME:-$HOME/botaneo}"
COLLECTOR_DIR="$BOTANEO_HOME/collector"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

download() {
  local remote="$1"
  local target="$2"
  local tmp
  tmp="$(mktemp)"
  curl -fsSL "$REPO_RAW_BASE/$remote" -o "$tmp"
  install -m 600 "$tmp" "$target"
  rm -f "$tmp"
}

mkdir -p "$COLLECTOR_DIR" "$SYSTEMD_USER_DIR"

for file in sync_export.py backup_daily.py backup_manifest.py request_collect.py; do
  echo "Mise à jour $file"
  download "raspberry/$file" "$COLLECTOR_DIR/$file"
  chmod 700 "$COLLECTOR_DIR/$file"
done

for file in passive_ble.py; do
  echo "Mise à jour $file"
  download "raspberry/collector/$file" "$COLLECTOR_DIR/$file"
  chmod 700 "$COLLECTOR_DIR/$file"
done

for unit in botaneo-collect.service botaneo-collect.timer botaneo-backup.service botaneo-backup.timer botaneo-passive-test.service; do
  echo "Mise à jour $unit"
  download "raspberry/$unit" "$SYSTEMD_USER_DIR/$unit"
  chmod 600 "$SYSTEMD_USER_DIR/$unit"
done

systemctl --user daemon-reload
systemctl --user restart botaneo-collect.timer botaneo-backup.timer
systemctl --user list-timers 'botaneo-*' --no-pager || true

echo "Mise à jour Raspberry Botaneo terminée."
