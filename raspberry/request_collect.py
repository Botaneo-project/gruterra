"""Queue a Botaneo Raspberry collection request without opening Bluetooth directly.

This script is intended for systemd timers. It uses the same request file as
PC-triggered collect_now, so the existing collector remains the only process
that talks to Bluetooth.
"""
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    base = Path.home() / 'botaneo'
    data = base / 'data'
    data.mkdir(parents=True, exist_ok=True)
    state_path = data / 'collect-state.json'
    request_path = data / 'collect.request'

    try:
        state = json.loads(state_path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        state = {'running': False}

    if state.get('running'):
        print('Collecte déjà en cours ; aucune nouvelle demande créée.')
        return

    payload = {
        'source': 'timer',
        'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'reason': 'scheduled_4_per_day'
    }

    try:
        with request_path.open('x', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False)
    except FileExistsError:
        print('Demande de collecte déjà en attente.')
        return

    print('Demande de collecte planifiée créée.')


if __name__ == '__main__':
    main()
