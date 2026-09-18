"""Primitives futures uniquement: aucun serveur, aucun boitier cree a l'import."""
import hashlib
import hmac
import secrets
import uuid


def nouvelle_identite():
    """A appeler uniquement lors du provisionnement d'un vrai boitier.

    Le token brut va dans la configuration privee du boitier; seul son
    SHA-256 va dans le registre central. Ne jamais journaliser le resultat.
    """
    token = secrets.token_urlsafe(32)
    return {"device_id": "BOTANEO-RPI-" + str(uuid.uuid4()),
            "token": token, "token_sha256": hashlib.sha256(token.encode()).hexdigest()}


def verifier_token(token, fiche):
    if fiche.get("revoked", True) or not isinstance(token, str) or not token:
        return False
    expected = fiche.get("token_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        return False
    return hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(), expected)


def nouvelle_mesure_id():
    """Creer une fois a l'acquisition, persister et reutiliser a chaque envoi."""
    return str(uuid.uuid4())
