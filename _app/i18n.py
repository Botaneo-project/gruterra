"""Gestion simple des langues pour l’interface Gruterra.

Les textes visibles sont stockés dans ``_app/locales/*.json`` pour pouvoir
traduire l’application progressivement sans grossir le code Python principal.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

LANGUES = {"fr", "en"}
LANGUE_DEFAUT = "fr"
DOSSIER_LOCALES = Path(__file__).resolve().parent / "locales"

# Quelques textes vitaux restent ici pour que l’application démarre même si les
# fichiers de langue sont absents ou abîmés après une copie incomplète.
TRADUCTIONS_SECOURS = {
    "app_title": {"fr": "Gruterra", "en": "Gruterra"},
    "system_active": {"fr": "● Système actif", "en": "● System active"},
    "no_sync": {"fr": "Aucune synchronisation effectuée", "en": "No synchronization yet"},
    "settings": {"fr": "⚙ Paramètres", "en": "⚙ Settings"},
    "settings_title": {"fr": "Paramètres Gruterra", "en": "Gruterra settings"},
    "settings_header": {"fr": "⚙ Paramètres", "en": "⚙ Settings"},
    "language": {"fr": "Langue", "en": "Language"},
    "save": {"fr": "Enregistrer", "en": "Save"},
    "cancel": {"fr": "Annuler", "en": "Cancel"},
    "syncing": {"fr": "⏳ Synchronisation...", "en": "⏳ Synchronizing..."},
    "sync_plain": {"fr": "📡 Synchroniser", "en": "📡 Sync"},
    "copy_status": {"fr": "📋 Copier le statut", "en": "📋 Copy status"},
    "copyable_status": {"fr": "Statut copiable", "en": "Copyable status"},
}


def normaliser_langue(langue):
    code = str(langue or "").strip().lower()
    return code if code in LANGUES else LANGUE_DEFAUT


@lru_cache(maxsize=None)
def charger_locale(langue):
    """Charge un fichier de langue Gruterra."""
    code = normaliser_langue(langue)
    fichier = DOSSIER_LOCALES / f"{code}.json"
    try:
        contenu = json.loads(fichier.read_text(encoding="utf-8"))
    except Exception:
        contenu = {}
    return contenu if isinstance(contenu, dict) else {}


def traduire(cle, langue="fr"):
    code = normaliser_langue(langue)
    valeur = charger_locale(code).get(cle)
    if isinstance(valeur, str) and valeur:
        return valeur

    valeur_defaut = charger_locale(LANGUE_DEFAUT).get(cle)
    if isinstance(valeur_defaut, str) and valeur_defaut:
        return valeur_defaut

    secours = TRADUCTIONS_SECOURS.get(cle, {})
    return secours.get(code) or secours.get(LANGUE_DEFAUT) or cle
