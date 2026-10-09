"""Préparation des alertes e-mail Gruterra, sans envoi automatique.

Ce module prépare le terrain pour un SMTP sécurisé local. Par défaut, il ne
transmet rien : il valide la configuration et construit un aperçu de message.
La vraie transmission devra rester derrière une validation explicite de
l'utilisateur et une configuration locale ignorée par Git.
"""
from __future__ import annotations

from i18n import traduire_courant as _tr

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from botaneo_config import EMAIL_CONFIG, CONFIG_DIR, ecrire_json, lire_json


EMAIL_ALERT_STATE = CONFIG_DIR / "email_alert_state.local.json"


@dataclass(frozen=True)
class EmailSettings:
    enabled: bool
    mode: str
    host: str
    port: int
    starttls: bool
    user: str
    secret_env: str
    sender: str
    recipients: tuple[str, ...]
    subject_prefix: str
    min_delay_hours_same_alert: int
    require_manual_validation: bool


def charger_parametres_email(path=EMAIL_CONFIG) -> EmailSettings:
    """Lit la configuration locale e-mail et retourne une version validée."""

    data = lire_json(path)
    smtp = data.get("smtp", {})
    message = data.get("message", {})
    rules = data.get("rules", {})

    recipients = tuple(str(item).strip() for item in message.get("recipients", []) if str(item).strip())
    settings = EmailSettings(
        enabled=bool(data.get("enabled", False)),
        mode=str(data.get("mode", "preview")).strip() or "preview",
        host=str(smtp.get("host", "")).strip(),
        port=int(smtp.get("port", 587)),
        starttls=bool(smtp.get("starttls", True)),
        user=str(smtp.get("user", "")).strip(),
        secret_env=str(smtp.get("secret_env", "BOTANEO_SMTP_SECRET")).strip(),
        sender=str(message.get("sender", "")).strip(),
        recipients=recipients,
        subject_prefix=str(message.get("subject_prefix", "[Gruterra]")).strip() or "[Gruterra]",
        min_delay_hours_same_alert=int(rules.get("min_delay_hours_same_alert", 24)),
        require_manual_validation=bool(rules.get("require_manual_validation", True)),
    )
    valider_parametres_email(settings)
    return settings


def valider_parametres_email(settings: EmailSettings) -> None:
    if settings.mode not in {"preview", "smtp"}:
        raise RuntimeError(_tr('email_mode_invalid'))
    if settings.port <= 0 or settings.port > 65535:
        raise RuntimeError(_tr('email_port_invalid'))
    if settings.mode == "smtp":
        if not settings.host or not settings.sender or not settings.recipients:
            raise RuntimeError(_tr('botaneo_email_text_73'))
        if not settings.user:
            raise RuntimeError(_tr('botaneo_email_text_75'))
        if not settings.secret_env:
            raise RuntimeError(_tr('botaneo_email_text_77'))
        if not os.environ.get(settings.secret_env):
            raise RuntimeError(_tr('botaneo_email_text_79').format(v0=settings.secret_env))
    if settings.min_delay_hours_same_alert < 1:
        raise RuntimeError(_tr('botaneo_email_text_81'))


def construire_message_alerte(settings: EmailSettings, titre: str, lignes: Iterable[str]) -> EmailMessage:
    """Construit un message prêt à prévisualiser ou envoyer plus tard."""

    sujet = f"{settings.subject_prefix} {titre}".strip()
    corps = "\n".join(str(ligne) for ligne in lignes).strip()
    if not corps:
        corps = _tr('botaneo_email_text_90')

    message = EmailMessage()
    message["Subject"] = sujet
    message["From"] = settings.sender or settings.user or "botaneo-local"
    message["To"] = ", ".join(settings.recipients) if settings.recipients else _tr('botaneo_email_text_95')
    message.set_content(corps)
    return message


def apercu_message_alerte(titre: str, lignes: Iterable[str], settings: EmailSettings | None = None) -> str:
    """Retourne le contenu texte d'un mail sans jamais l'envoyer."""

    settings = settings or charger_parametres_email()
    message = construire_message_alerte(settings, titre, lignes)
    return message.as_string()


def email_actif_pour_envoi(settings: EmailSettings | None = None) -> bool:
    """Indique si la configuration autorise théoriquement un envoi réel.

    Même si cette fonction retourne True, Gruterra doit encore demander une
    validation explicite avant le premier envoi réel.
    """

    settings = settings or charger_parametres_email()
    return settings.enabled and settings.mode == "smtp" and not settings.require_manual_validation


def normaliser_cle_alerte(plante_id=None, type_alerte="generale", titre="") -> str:
    morceaux = [
        str(plante_id) if plante_id not in (None, "") else "global",
        str(type_alerte or "generale").strip().lower() or "generale",
        str(titre or "").strip().lower() or "sans_titre",
    ]
    return "|".join(morceau.replace("|", "/") for morceau in morceaux)


def lire_memoire_alertes(path=EMAIL_ALERT_STATE) -> dict:
    try:
        data = lire_json(path)
    except RuntimeError:
        return {"schema": 1, "alertes": {}}
    if data.get("schema") != 1 or not isinstance(data.get("alertes"), dict):
        return {"schema": 1, "alertes": {}}
    return data


def sauvegarder_memoire_alertes(memoire: dict, path=EMAIL_ALERT_STATE) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema": 1, "alertes": dict(memoire.get("alertes", {}))}
    ecrire_json(path, data)


def derniere_alerte_envoyee(plante_id=None, type_alerte="generale", titre="", path=EMAIL_ALERT_STATE):
    cle = normaliser_cle_alerte(plante_id, type_alerte, titre)
    entree = lire_memoire_alertes(path).get("alertes", {}).get(cle) or {}
    date_texte = entree.get("derniere_alerte")
    if not date_texte:
        return None
    try:
        return datetime.fromisoformat(date_texte)
    except (TypeError, ValueError):
        return None


def alerte_autorisee(plante_id=None, type_alerte="generale", titre="", reference=None, settings: EmailSettings | None = None, path=EMAIL_ALERT_STATE) -> dict:
    settings = settings or charger_parametres_email()
    reference = reference or datetime.now()
    derniere = derniere_alerte_envoyee(plante_id, type_alerte, titre, path)
    if not derniere:
        return {"autorisee": True, "raison": _tr('botaneo_email_text_162'), "prochaine_possible": reference}
    prochaine = derniere + timedelta(hours=settings.min_delay_hours_same_alert)
    if prochaine <= reference:
        return {"autorisee": True, "raison": _tr('botaneo_email_text_165'), "derniere_alerte": derniere, "prochaine_possible": prochaine}
    return {"autorisee": False, "raison": _tr('botaneo_email_text_166'), "derniere_alerte": derniere, "prochaine_possible": prochaine}


def memoriser_alerte_envoyee(plante_id=None, type_alerte="generale", titre="", date_envoi=None, path=EMAIL_ALERT_STATE) -> dict:
    date_envoi = date_envoi or datetime.now()
    cle = normaliser_cle_alerte(plante_id, type_alerte, titre)
    memoire = lire_memoire_alertes(path)
    alertes = memoire.setdefault("alertes", {})
    entree = alertes.get(cle) or {}
    entree["derniere_alerte"] = date_envoi.isoformat(timespec="seconds")
    entree["compteur"] = int(entree.get("compteur", 0)) + 1
    entree["plante_id"] = plante_id
    entree["type_alerte"] = type_alerte
    entree["titre"] = titre
    alertes[cle] = entree
    sauvegarder_memoire_alertes(memoire, path)
    return entree


def resume_memoire_alerte(plante_id=None, type_alerte="generale", titre="", settings: EmailSettings | None = None, reference=None, path=EMAIL_ALERT_STATE) -> str:
    etat = alerte_autorisee(plante_id, type_alerte, titre, reference=reference, settings=settings, path=path)
    if etat["autorisee"]:
        return _tr('botaneo_email_text_188')
    prochaine = etat.get("prochaine_possible")
    prochaine_txt = prochaine.strftime("%d/%m/%Y %H:%M") if prochaine else _tr('botaneo_email_text_192')
    return _tr('botaneo_email_text_191').format(v0=prochaine_txt)
