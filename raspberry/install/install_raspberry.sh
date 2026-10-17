#!/usr/bin/env bash
set -euo pipefail

REPO_RAW_BASE="${BOTANEO_REPO_RAW_BASE:-https://raw.githubusercontent.com/Botaneo-project/gruterra/main}"
BOTANEO_HOME="${BOTANEO_HOME:-$HOME/botaneo}"
COLLECTOR_DIR="$BOTANEO_HOME/collector"
CONFIG_DIR="$BOTANEO_HOME/config"
DATA_DIR="$BOTANEO_HOME/data"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Commande requise introuvable : $1" >&2
    exit 1
  fi
}

download() {
  local remote="$1"
  local target="$2"
  local tmp
  tmp="$(mktemp)"
  curl -fsSL "$REPO_RAW_BASE/$remote" -o "$tmp"
  install -m 600 "$tmp" "$target"
  rm -f "$tmp"
}

backup_if_exists() {
  local path="$1"
  if [ -e "$path" ]; then
    cp -a "$path" "$path.backup.$(date +%Y%m%d_%H%M%S)"
  fi
}

need_cmd curl
need_cmd python3
need_cmd systemctl

mkdir -p "$COLLECTOR_DIR" "$CONFIG_DIR" "$DATA_DIR" "$SYSTEMD_USER_DIR"

# Deploy the common PC/Pi protocol from its single source.
download "raspberry/collector/pi_web_i18n.py" "$COLLECTOR_DIR/pi_web_i18n.py"
download "_app/light_schedule.py" "$COLLECTOR_DIR/light_schedule.py"
download "_app/weather_protocol.py" "$COLLECTOR_DIR/weather_protocol.py"
chmod 600 "$COLLECTOR_DIR/weather_protocol.py"

for file in weather_backup.py weather_collect.py weather_outbox.py sync_export.py backup_daily.py backup_manifest.py request_collect.py health_status.py; do
  echo "Installation $file"
  backup_if_exists "$COLLECTOR_DIR/$file"
  download "raspberry/$file" "$COLLECTOR_DIR/$file"
  chmod 700 "$COLLECTOR_DIR/$file"
done

for file in passive_ble.py; do
  echo "Installation $file"
  backup_if_exists "$COLLECTOR_DIR/$file"
  download "raspberry/collector/$file" "$COLLECTOR_DIR/$file"
  chmod 700 "$COLLECTOR_DIR/$file"
done

for unit in botaneo-collect.service botaneo-collect.timer botaneo-backup.service botaneo-backup.timer botaneo-passive-test.service; do
  echo "Installation $unit"
  backup_if_exists "$SYSTEMD_USER_DIR/$unit"
  download "raspberry/$unit" "$SYSTEMD_USER_DIR/$unit"
  chmod 600 "$SYSTEMD_USER_DIR/$unit"
done

if [ ! -f "$CONFIG_DIR/collector.json" ]; then
  cat > "$CONFIG_DIR/collector.json.example" <<'JSON'
{
  "device_id": "raspberry-botaneo-01",
  "sensors": [
    "AA:BB:CC:DD:EE:FF"
  ]
}
JSON
  echo "Configuration exemple créée : $CONFIG_DIR/collector.json.example"
  echo "Copiez-la en collector.json puis renseignez vos capteurs avant d'activer la collecte réelle."
fi

if [ ! -f "$DATA_DIR/collect-state.json" ]; then
  printf '{"running": false}\n' > "$DATA_DIR/collect-state.json"
  chmod 600 "$DATA_DIR/collect-state.json"
fi

systemctl --user daemon-reload
systemctl --user enable --now botaneo-collect.timer
systemctl --user enable --now botaneo-backup.timer

echo
systemctl --user list-timers 'botaneo-*' --no-pager || true

echo
echo "Installation Raspberry Botaneo terminée."
echo "Dossier : $BOTANEO_HOME"
echo "Vérifiez la configuration privée : $CONFIG_DIR/collector.json"

# Weather remains disabled until independent OAuth and real transfer are verified.
for unit in gruterra-weather.service gruterra-weather.timer; do
  download "raspberry/$unit" "$SYSTEMD_USER_DIR/$unit"
done
systemctl --user daemon-reload
