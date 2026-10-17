#!/usr/bin/env bash
set -euo pipefail

REPO_RAW_BASE="${BOTANEO_REPO_RAW_BASE:-https://raw.githubusercontent.com/Botaneo-project/gruterra/main}"
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

# Deploy the common PC/Pi protocol from its single source.
download "raspberry/collector/pi_web_i18n.py" "$COLLECTOR_DIR/pi_web_i18n.py"
download "_app/light_schedule.py" "$COLLECTOR_DIR/light_schedule.py"
download "_app/weather_protocol.py" "$COLLECTOR_DIR/weather_protocol.py"
chmod 600 "$COLLECTOR_DIR/weather_protocol.py"

for file in weather_backup.py weather_collect.py weather_outbox.py sync_export.py backup_daily.py backup_manifest.py request_collect.py health_status.py; do
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

# Weather remains disabled until independent OAuth and real transfer are verified.
for unit in gruterra-weather.service gruterra-weather.timer; do
  download "raspberry/$unit" "$SYSTEMD_USER_DIR/$unit"
done
systemctl --user daemon-reload
