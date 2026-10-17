"""Identité Ed25519 locale. Aucun transport, aucune migration implicite."""
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path

from botaneo_config import CONFIG_DIR, ecrire_json, lire_json
from i18n import traduire_courant as t


def _crypto():
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError:
        raise RuntimeError(t('contribution_crypto_missing')) from None
    return serialization, Ed25519PrivateKey


def _allow():
    if os.environ.get('BOTANEO_DEMO') == '1':
        raise ValueError(t('contribution_demo_blocked'))


def chemin():
    return CONFIG_DIR / 'contribution.identity.local.json'


def _b64(value):
    return base64.b64encode(value).decode('ascii')


def _decode(value, size):
    try:
        if not isinstance(value, str):
            raise ValueError
        decoded = base64.b64decode(value, validate=True)
        if len(decoded) != size or _b64(decoded) != value:
            raise ValueError
        return decoded
    except (ValueError, binascii.Error):
        raise ValueError(t('contribution_invalid_key')) from None


def _identity(key):
    serialization, _ = _crypto()
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    seed = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                             serialization.NoEncryption())
    return {'identity_version': 2, 'algorithm': 'Ed25519',
            'contributor_id': 'ed25519:' + hashlib.sha256(public).hexdigest(),
            'public_key': _b64(public), 'private_seed_b64': _b64(seed)}


def valider_identite(data):
    expected = {'identity_version', 'algorithm', 'contributor_id', 'public_key', 'private_seed_b64'}
    if type(data) is not dict or set(data) != expected or type(data.get('identity_version')) is not int or data['identity_version'] != 2 or data.get('algorithm') != 'Ed25519':
        raise ValueError(t('contribution_invalid_key'))
    _, key_type = _crypto()
    _decode(data['public_key'], 32)
    result = _identity(key_type.from_private_bytes(_decode(data['private_seed_b64'], 32)))
    if result != data:
        raise ValueError(t('contribution_invalid_key'))
    return result


def _read():
    return valider_identite(lire_json(chemin()))


def preparer_identite():
    _allow()
    if chemin().exists():
        return _read()
    legacy = CONFIG_DIR / 'contribution.local.json'
    if legacy.exists():
        state = lire_json(legacy)
        if 'management_key' in state or 'contributor_id' in state:
            raise ValueError(t('contribution_legacy_identity'))
    _, key_type = _crypto()
    identity = _identity(key_type.generate())
    _store(identity)
    return identity


def _store(identity):
    """Verrou exclusif : deux fenêtres ne remplacent pas une identité concurrente."""
    path = chemin()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix('.lock')
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError(t('contribution_identity_busy')) from None
    try:
        os.close(fd)
        if path.exists():
            if _read() != identity:
                raise ValueError(t('contribution_existing_key'))
            return
        ecrire_json(path, identity)
    finally:
        lock.unlink()


def restaurer_identite(identity):
    _allow()
    identity = valider_identite(identity)
    _store(identity)
    return identity


def identite_publique():
    _allow()
    identity = _read()
    return {key: identity[key] for key in ('contributor_id', 'public_key')}


def signer(message):
    """Signe uniquement des octets ; ne crée jamais une clé implicitement."""
    _allow()
    if type(message) is not bytes:
        raise TypeError('bytes required')
    _, key_type = _crypto()
    identity = _read()
    key = key_type.from_private_bytes(_decode(identity['private_seed_b64'], 32))
    return _b64(key.sign(message))


def sauvegarder(destination, passphrase):
    _allow()
    if not isinstance(passphrase, str) or not passphrase:
        raise ValueError(t('contribution_password_required'))
    destination = Path(destination)
    if destination.exists():
        raise ValueError(t('contribution_no_overwrite'))
    identity = preparer_identite()
    serialization, key_type = _crypto()
    key = key_type.from_private_bytes(_decode(identity['private_seed_b64'], 32))
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.BestAvailableEncryption(passphrase.encode('utf-8')))
    backup = {key: identity[key] for key in ('identity_version', 'algorithm', 'contributor_id', 'public_key')}
    backup['encrypted_private_key_pem'] = pem.decode('ascii')
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(backup, stream, ensure_ascii=False, indent=2)


def restaurer_sauvegarde(data, passphrase):
    _allow()
    expected = {'identity_version', 'algorithm', 'contributor_id', 'public_key', 'encrypted_private_key_pem'}
    if type(data) is not dict or set(data) != expected or type(data.get('identity_version')) is not int or data['identity_version'] != 2 or data.get('algorithm') != 'Ed25519':
        raise ValueError(t('contribution_invalid_key'))
    if not isinstance(passphrase, str) or not passphrase:
        raise ValueError(t('contribution_password_required'))
    serialization, key_type = _crypto()
    try:
        pem = data['encrypted_private_key_pem']
        if not isinstance(pem, str) or not pem.startswith('-----BEGIN ENCRYPTED PRIVATE KEY-----'):
            raise ValueError
        key = serialization.load_pem_private_key(pem.encode('ascii'), passphrase.encode('utf-8'))
        if not isinstance(key, key_type):
            raise ValueError
        identity = _identity(key)
        if any(identity[k] != data[k] for k in ('contributor_id', 'public_key')):
            raise ValueError
    except (ValueError, TypeError, UnicodeError):
        raise ValueError(t('contribution_backup_invalid')) from None
    return restaurer_identite(identity)
