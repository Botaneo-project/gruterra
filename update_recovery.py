"""Standalone update recovery: stdlib only, usable from a frozen backup copy."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import uuid
import zipfile

MARKER = 'update-pending.json'
RUNNER = 'update-recovery.py'
PRIVATE_DIRS = {'_config', '_security_backups', '_user_backups', '.venv', '_historique', '.git'}
PRIVATE_FILES = {'plantes.db', 'netatmo_config.json', 'discord_bot/.env'}


class RecoveryBlocked(RuntimeError):
    """Stable error code only; never render raw filesystem exceptions to users."""


def preserved(relative):
    name = Path(relative).as_posix().replace('\\', '/').casefold()
    return (name in PRIVATE_FILES or any(name == p or name.startswith(p + '/') for p in PRIVATE_DIRS)
            or name == '_app/data' or name.startswith('_app/data/')
            or name.endswith(('.db', '.sqlite', '.sqlite3', '.db-wal', '.db-shm', '.db-journal',
                '.sqlite-wal', '.sqlite-shm', '.sqlite-journal', '.sqlite3-wal', '.sqlite3-shm',
                '.sqlite3-journal', '.local.json')))


def safe_target(root, value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise RecoveryBlocked('invalid_path')
    relative = PurePosixPath(value)
    if relative.is_absolute() or relative.as_posix() != value or any(p in ('.', '..') or p.endswith((' ', '.')) for p in relative.parts) or preserved(value):
        raise RecoveryBlocked('invalid_path')
    root = Path(root).resolve()
    target = root.joinpath(*relative.parts)
    if target.resolve() != target or not target.resolve().is_relative_to(root):
        raise RecoveryBlocked('linked_path')
    return target


def control_folder(root, name):
    folder = Path(root).resolve() / name
    if folder.resolve() != folder:
        raise RecoveryBlocked('linked_control_folder')
    return folder


def checksum(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def sync_file(path):
    with Path(path).open('r+b') as stream:
        stream.flush(); os.fsync(stream.fileno())


def sync_directory(path):
    # Windows does not expose POSIX directory fsync; do not pretend to test a
    # physical power cut. File flushes and atomic renames are used on both OSes.
    if os.name != 'nt':
        descriptor = os.open(path, os.O_RDONLY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)


def atomic_json(path, data):
    path = Path(path)
    descriptor, name = tempfile.mkstemp(prefix='update-state-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, sort_keys=True)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path); sync_directory(path.parent)
    finally:
        Path(name).unlink(missing_ok=True)


@contextmanager
def update_lock(root):
    folder = control_folder(root, '_config')
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'gruterra-update.lock').open('a+b') as stream:
        if stream.seek(0, 2) == 0: stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RecoveryBlocked('update_busy') from None
        try: yield
        finally:
            stream.seek(0)
            if os.name == 'nt': msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else: fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _load(root):
    folder = control_folder(root, '_security_backups')
    try:
        data = json.loads((folder / MARKER).read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('schema') != 1 or data.get('state') not in ('applying', 'committed'):
            raise RecoveryBlocked('invalid_journal')
        backup_name = data['backup']
        if not re.fullmatch(r'gruterra-pre-update-[A-Za-z0-9_.-]+[.]zip', backup_name):
            raise RecoveryBlocked('invalid_backup')
        backup = folder / backup_name
        if backup.resolve() != backup or not re.fullmatch('[0-9a-f]{64}', data['backup_sha256']) or checksum(backup) != data['backup_sha256']:
            raise RecoveryBlocked('invalid_backup')
        entries = data['files']; attempted = data['attempted']
        if not isinstance(entries, list) or not isinstance(attempted, list) or len(entries) > 20000:
            raise RecoveryBlocked('invalid_journal')
        seen = set()
        for item in entries:
            safe_target(root, item['path'])
            if item['path'].casefold() in seen or type(item['existed']) is not bool:
                raise RecoveryBlocked('invalid_journal')
            seen.add(item['path'].casefold())
            for digest in (item['new_sha256'], item['old_sha256'] if item['existed'] else '0' * 64):
                if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest): raise RecoveryBlocked('invalid_journal')
            staged = item['stage']
            safe_target(root, staged)
            if PurePosixPath(staged).parent != PurePosixPath(item['path']).parent or not re.fullmatch(r'[.]gruterra-update-[0-9a-f]{32}', PurePosixPath(staged).name):
                raise RecoveryBlocked('invalid_stage')
        paths = [item['path'] for item in entries]
        if any(not isinstance(p, str) or p not in paths for p in attempted) or len(attempted) != len(set(attempted)):
            raise RecoveryBlocked('invalid_journal')
        return data, backup
    except (OSError, ValueError, TypeError, KeyError):
        raise RecoveryBlocked('unreadable_journal_or_backup') from None


def begin(root, source, files, backup):
    root = Path(root).resolve(); folder = control_folder(root, '_security_backups')
    if (folder / MARKER).exists(): raise RecoveryBlocked('recovery_required')
    backup = Path(backup).resolve()
    if backup.parent != folder: raise RecoveryBlocked('invalid_backup')
    sync_file(backup)
    entries = []
    with zipfile.ZipFile(backup) as archive:
        if archive.testzip() is not None: raise RecoveryBlocked('invalid_backup')
        for relative in files:
            name = Path(relative).as_posix(); target = safe_target(root, name)
            existed = target.exists()
            if existed and not target.is_file(): raise RecoveryBlocked('invalid_target')
            old = checksum(target) if existed else None
            if existed and hashlib.sha256(archive.read(name)).hexdigest() != old:
                raise RecoveryBlocked('backup_mismatch')
            stage = str(PurePosixPath(name).with_name('.gruterra-update-' + uuid.uuid4().hex))
            entries.append({'path': name, 'existed': existed, 'old_sha256': old,
                            'new_sha256': checksum(Path(source) / relative), 'stage': stage})
    # Keep a standalone runner outside the program files about to be replaced.
    runner = folder / RUNNER; temporary = runner.with_suffix('.tmp')
    shutil.copyfile(Path(__file__), temporary); sync_file(temporary)
    os.replace(temporary, runner); sync_directory(folder)
    data = {'schema': 1, 'state': 'applying', 'backup': backup.name,
            'backup_sha256': checksum(backup), 'files': entries, 'attempted': []}
    atomic_json(folder / MARKER, data)
    return data


def checkpoint(root, data, item):
    data['attempted'].append(item['path'])
    atomic_json(Path(root) / '_security_backups' / MARKER, data)


def commit(root, data):
    data['state'] = 'committed'
    atomic_json(Path(root) / '_security_backups' / MARKER, data)
    clear(root)


def clear(root):
    folder = control_folder(root, '_security_backups')
    (folder / MARKER).unlink(missing_ok=True); sync_directory(folder)


def recover_pending(root, *, locked=False):
    root = Path(root).resolve()
    if not locked:
        with update_lock(root): return recover_pending(root, locked=True)
    folder = control_folder(root, '_security_backups')
    if not (folder / MARKER).exists(): return {'status': 'none'}
    data, backup = _load(root)
    if data['state'] == 'committed' and all(safe_target(root, item['path']).is_file() and checksum(safe_target(root, item['path'])) == item['new_sha256'] for item in data['files']):
        clear(root); return {'status': 'committed'}
    attempted = [item for item in data['files'] if item['path'] in data['attempted']]
    try:
        with zipfile.ZipFile(backup) as archive:
            # Check the entire rollback set before touching any installed file.
            for item in attempted:
                if item['existed'] and hashlib.sha256(archive.read(item['path'])).hexdigest() != item['old_sha256']:
                    raise RecoveryBlocked('backup_mismatch')
            for item in reversed(attempted):
                target = safe_target(root, item['path']); stage = safe_target(root, item['stage'])
                stage.unlink(missing_ok=True)
                if item['existed']:
                    if target.is_file() and checksum(target) == item['old_sha256']: continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with stage.open('xb') as stream:
                        stream.write(archive.read(item['path'])); stream.flush(); os.fsync(stream.fileno())
                    os.replace(stage, target); sync_directory(target.parent)
                elif target.exists():
                    # A newly created unrelated file is never removed by recovery.
                    if not target.is_file() or checksum(target) != item['new_sha256']:
                        raise RecoveryBlocked('unexpected_new_file')
                    target.unlink(); sync_directory(target.parent)
        clear(root)
        return {'status': 'restored', 'backup': str(backup)}
    except (OSError, KeyError, zipfile.BadZipFile):
        raise RecoveryBlocked('restore_failed') from None


if __name__ == '__main__':
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else Path(__file__).resolve().parent
    if len(sys.argv) == 1 and root.name == '_security_backups': root = root.parent
    try:
        result = recover_pending(root)
        print('Gruterra recovery: ' + result['status'])
    except (RecoveryBlocked, OSError, ValueError):
        print('Gruterra: recovery blocked. Keep the backup; do not start the application.')
        raise SystemExit(3)
