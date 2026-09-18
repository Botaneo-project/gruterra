"""Suivi de disponibilité. Un contact SSH n'est jamais une synchronisation."""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


def now_utc():
    return datetime.now(timezone.utc)


def validate(config):
    if not isinstance(config, dict):
        raise ValueError('Configuration Raspberry invalide.')
    if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', str(config.get('hour', ''))):
        raise ValueError('Heure attendue : HH:MM, entre 00:00 et 23:59.')
    for field in ('enabled', 'away'):
        if type(config.get(field)) is not bool:
            raise ValueError('Options de suivi invalides.')
    for field, low, high in (('retry_minutes', 1, 1440), ('grace_minutes', 0, 1440)):
        if type(config.get(field)) is not int or not low <= config[field] <= high:
            raise ValueError('Délais attendus en minutes, entre 1 et 1440 (tolérance : 0 possible).')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,252}', str(config.get('host', ''))):
        raise ValueError('Adresse Raspberry invalide.')
    if not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}', str(config.get('user', ''))):
        raise ValueError('Utilisateur SSH invalide.')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,63}', str(config.get('hostname', ''))):
        raise ValueError('Nom attendu du Raspberry invalide.')
    if not isinstance(config.get('key'), str) or not config['key']:
        raise ValueError('Chemin de clé SSH absent.')
    return config


def load_config(path):
    return validate(json.loads(Path(path).read_text(encoding='utf-8-sig')))


def save_config(path, config):
    validate(config)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(config, stream, indent=2, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def deadline(config, local_now=None):
    """Dernière échéance locale, y compris si l'application était fermée."""
    local_now = local_now or datetime.now()
    h, m = map(int, config['hour'].split(':'))
    due = local_now.replace(hour=h, minute=m, second=0, microsecond=0)
    if due > local_now:
        due -= timedelta(days=1)
    return due


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, at TEXT NOT NULL, kind TEXT NOT NULL)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def read(self):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM state WHERE id=1').fetchone()
        return json.loads(row[0]) if row else {}

    def reset(self):
        # Ancien appareil ou paramètres modifiés : ne pas attribuer son succès au nouveau.
        with self.connect() as db:
            db.execute('DELETE FROM state')
            db.execute('DELETE FROM events')

    def record(self, ok, reason, due, instant=None):
        instant = instant or now_utc()
        at = instant.isoformat()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT payload FROM state WHERE id=1').fetchone()
            state = json.loads(row[0]) if row else {}
            previous_failure = state.get('failure_since')
            state.update(last_attempt=at, last_error=None if ok else reason)
            if ok:
                state.update(last_contact=at, completed_due=due.isoformat(), failure_since=None)
                if previous_failure:
                    state['recovered_at'] = at
                    db.execute('INSERT INTO events(at,kind) VALUES (?,?)', (at, 'recovered'))
            elif not previous_failure:
                state['failure_since'] = at
                db.execute('INSERT INTO events(at,kind) VALUES (?,?)', (at, 'unreachable'))
            db.execute('INSERT OR REPLACE INTO state(id,payload) VALUES (1,?)', (json.dumps(state),))
            db.execute('DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 200)')
        return state


def is_due(config, state, instant=None, local_now=None):
    if not config['enabled'] or config['away']:
        return False
    due = deadline(config, local_now).isoformat()
    if state.get('completed_due', '') >= due and not state.get('last_error'):
        return False
    last = state.get('last_attempt')
    if last and (instant or now_utc()) - datetime.fromisoformat(last) < timedelta(minutes=config['retry_minutes']):
        return False
    return True


def probe(config, runner=subprocess.run):
    key = Path(config['key']).expanduser()
    if not key.is_file():
        return False, 'Clé SSH introuvable sur ce PC.'
    ssh = shutil.which('ssh')
    if not ssh:
        return False, 'Client SSH Windows introuvable.'
    args = [ssh, '-i', str(key), '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8',
            '-o', 'ConnectionAttempts=1', '-o', 'ServerAliveInterval=5',
            '-o', 'ServerAliveCountMax=1', f"{config['user']}@{config['host']}", 'hostname']
    try:
        result = runner(args, capture_output=True, text=True, timeout=15,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        return False, 'Raspberry injoignable : délai dépassé.'
    except OSError:
        return False, 'Impossible de lancer le contrôle SSH.'
    if result.returncode == 0:
        if result.stdout.strip() != config['hostname']:
            return False, 'Le nom de la machine ne correspond pas au Raspberry attendu.'
        return True, None
    stderr = result.stderr.lower()
    if 'host key verification failed' in stderr or 'remote host identification has changed' in stderr:
        return False, 'Identité SSH à vérifier manuellement.'
    if 'permission denied' in stderr:
        return False, 'Accès SSH refusé : vérifier la clé et ses droits.'
    return False, 'Raspberry injoignable : réseau, alimentation ou service à vérifier.'


def status(config, state, local_now=None):
    local_now = local_now or datetime.now()
    if not config['enabled']:
        return 'Suivi désactivé'
    if config['away']:
        return 'Déplacement : contrôles automatiques suspendus'
    if state.get('last_error'):
        if local_now >= deadline(config, local_now) + timedelta(minutes=config['grace_minutes']):
            return 'Raspberry injoignable — contrôle en retard'
        return 'Échec de contact — nouvel essai prévu'
    if state.get('completed_due', '') >= deadline(config, local_now).isoformat():
        return 'Contact rétabli' if state.get('recovered_at') == state.get('last_contact') else 'Dernier contrôle réussi'
    return 'Contrôle quotidien en attente'


def local_date(value):
    return datetime.fromisoformat(value).astimezone().strftime('%d/%m/%Y %H:%M') if value else 'Jamais'
