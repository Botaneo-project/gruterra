"""Préparation des alertes e-mail Botaneo, sans envoi automatique.

Ce module prépare le terrain pour un SMTP sécurisé local. Par défaut, il ne
transmet rien : il valide la configuration et construit un aperçu de message.
La vraie transmission devra rester derrière une validation explicite de
l'utilisateur et une configuration locale ignorée par Git.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable

from botaneo_config import EMAIL_CONFIG, lire_json


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
        subject_prefix=str(message.get("subject_prefix", "[Botaneo]")).strip() or "[Botaneo]",
        min_delay_hours_same_alert=int(rules.get("min_delay_hours_same_alert", 24)),
        require_manual_validation=bool(rules.get("require_manual_validation", True)),
    )
    valider_parametres_email(settings)
    return settings


def valider_parametres_email(settings: EmailSettings) -> None:
    if settings.mode not in {"preview", "smtp"}:
        raise RuntimeError("Configuration e-mail invalide : mode attendu preview ou smtp.")
    if settings.port <= 0 or settings.port > 65535:
        raise RuntimeError("Configuration e-mail invalide : port SMTP incorrect.")
    if settings.mode == "smtp":
        if not settings.host or not settings.sender or not settings.recipients:
            raise RuntimeError("Configuration e-mail SMTP incomplète : serveur, expéditeur ou destinataire manquant.")
        if not settings.user:
            raise RuntimeError("Configuration e-mail SMTP incomplète : utilisateur manquant.")
        if not settings.secret_env:
            raise RuntimeError("Configuration e-mail SMTP incomplète : variable locale du secret absente.")
        if not os.environ.get(settings.secret_env):
            raise RuntimeError(f"Secret SMTP absent : définir la variable d'environnement {settings.secret_env}.")
    if settings.min_delay_hours_same_alert < 1:
        raise RuntimeError("Configuration e-mail invalide : délai minimal trop court.")


def construire_message_alerte(settings: EmailSettings, titre: str, lignes: Iterable[str]) -> EmailMessage:
    """Construit un message prêt à prévisualiser ou envoyer plus tard."""

    sujet = f"{settings.subject_prefix} {titre}".strip()
    corps = "\n".join(str(ligne) for ligne in lignes).strip()
    if not corps:
        corps = "Aucun détail fourni."

    message = EmailMessage()
    message["Subject"] = sujet
    message["From"] = settings.sender or settings.user or "botaneo-local"
    message["To"] = ", ".join(settings.recipients) if settings.recipients else "destinataire non configuré"
    message.set_content(corps)
    return message


def apercu_message_alerte(titre: str, lignes: Iterable[str], settings: EmailSettings | None = None) -> str:
    """Retourne le contenu texte d'un mail sans jamais l'envoyer."""

    settings = settings or charger_parametres_email()
    message = construire_message_alerte(settings, titre, lignes)
    return message.as_string()


def email_actif_pour_envoi(settings: EmailSettings | None = None) -> bool:
    """Indique si la configuration autorise théoriquement un envoi réel.

    Même si cette fonction retourne True, Botaneo doit encore demander une
    validation explicite avant le premier envoi réel.
    """

    settings = settings or charger_parametres_email()
    return settings.enabled and settings.mode == "smtp" and not settings.require_manual_validation

