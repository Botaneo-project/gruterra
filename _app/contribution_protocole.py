"""Protocole signé Gruterra V2 : octets locaux uniquement, aucun transport."""
import base64
import hashlib
import re
from datetime import datetime, timezone
import contribution_identite as identite

ORIGIN = 'https://api.gruterra.fr'
PATHS = {'contribute': '/v2/contributions', 'withdraw': '/v2/withdrawals'}
UUID4 = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}')


def _fail():
    raise ValueError('Invalid Gruterra V2 request')


def _uuid(value):
    if type(value) is not str or not UUID4.fullmatch(value):
        _fail()


def _decode(text, length):
    try:
        raw = base64.b64decode(text, validate=True) if type(text) is str else b''
        if len(raw) != length or base64.b64encode(raw).decode('ascii') != text:
            _fail()
        return raw
    except (ValueError, TypeError):
        _fail()


def message_signe(operation, public, request_id, challenge_id, nonce, payload):
    """Même ordre que l'API PHP : LF, ASCII, aucune fin de ligne finale.

    payload doit contenir les octets déjà sélectionnés et validés. Cette fonction
    ne valide pas le schéma métier et ne resérialise jamais le contenu.
    """
    if type(operation) is not str or operation not in PATHS or type(payload) is not bytes or not payload or len(payload) > 2097152:
        _fail()
    if type(public) is not dict or set(public) != {'contributor_id', 'public_key'}:
        _fail()
    raw_public = _decode(public['public_key'], 32)
    contributor_id = 'ed25519:' + hashlib.sha256(raw_public).hexdigest()
    if public['contributor_id'] != contributor_id:
        _fail()
    _uuid(request_id)
    _uuid(challenge_id)
    _decode(nonce, 32)
    return '\n'.join(['GRUTERRA-SIGNED-REQUEST-V2', ORIGIN, 'POST', PATHS[operation],
                      contributor_id, request_id, challenge_id, nonce,
                      hashlib.sha256(payload).hexdigest()]).encode('ascii')


def verifier_defi(challenge, now=None):
    required = {'protocol_version', 'challenge_id', 'nonce', 'expires_at'}
    if type(challenge) is not dict or set(challenge) != required or type(challenge['protocol_version']) is not int or challenge['protocol_version'] != 2:
        _fail()
    _uuid(challenge['challenge_id'])
    _decode(challenge['nonce'], 32)
    expires = challenge['expires_at']
    if type(expires) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', expires):
        _fail()
    try:
        deadline = datetime.fromisoformat(expires.replace('Z', '+00:00'))
    except ValueError:
        _fail()
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or deadline <= now:
        _fail()
    return challenge


def enveloppe_signee(operation, payload, request_id, challenge, *, now=None):
    """Prépare un envoi/retrait, sans lire de jeton et sans appeler l'API.

    La consommation unique du défi est une garantie serveur, pas de cette
    fonction. Une reprise conserve request_id et payload mais prend un défi neuf.
    """
    identite._allow()
    verifier_defi(challenge, now)
    public = identite.identite_publique()
    message = message_signe(operation, public, request_id, challenge['challenge_id'], challenge['nonce'], payload)
    return {'protocol_version': 2, **public, 'request_id': request_id,
            'challenge_id': challenge['challenge_id'],
            'payload_b64': base64.b64encode(payload).decode('ascii'),
            'signature': identite.signer(message)}
