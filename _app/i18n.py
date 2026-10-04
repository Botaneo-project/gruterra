"""Traductions simples pour l’interface Gruterra.

Ce module ne traduit pas encore toute l’application. Il fournit une base stable
pour brancher progressivement les textes visibles sur une préférence locale.
"""

LANGUES = {"fr", "en"}
LANGUE_DEFAUT = "fr"

TRADUCTIONS = {
    "app_title": {"fr": "Gruterra", "en": "Gruterra"},
    "system_active": {"fr": "● Système actif", "en": "● System active"},
    "no_sync": {"fr": "Aucune synchronisation effectuée", "en": "No synchronization yet"},
    "refresh": {"fr": "⟳ Actualiser", "en": "⟳ Refresh"},
    "sync": {"fr": "🔄 Synchroniser", "en": "🔄 Sync"},
    "add_plant": {"fr": "＋ Ajouter une plante", "en": "＋ Add plant"},
    "add_sensor": {"fr": "＋ Ajouter un capteur", "en": "＋ Add sensor"},
    "plants": {"fr": "🌱 Plantes", "en": "🌱 Plants"},
    "settings": {"fr": "⚙ Paramètres", "en": "⚙ Settings"},
    "about": {"fr": "ℹ À propos", "en": "ℹ About"},
    "health": {"fr": "🩺 État Gruterra", "en": "🩺 Gruterra status"},
    "maintenance": {"fr": "🧰 Base & synthèses", "en": "🧰 Database & summaries"},
    "light_mode": {"fr": "☀️ Mode clair", "en": "☀️ Light mode"},
    "dark_mode": {"fr": "🌙 Mode sombre", "en": "🌙 Dark mode"},
    "settings_title": {"fr": "Paramètres Gruterra", "en": "Gruterra settings"},
    "settings_header": {"fr": "⚙ Paramètres", "en": "⚙ Settings"},
    "display": {"fr": "Affichage", "en": "Display"},
    "language": {"fr": "Langue", "en": "Language"},
    "language_note": {"fr": "Traduction progressive : certains écrans restent en français.", "en": "Progressive translation: some screens are still in French."},
    "save": {"fr": "Enregistrer", "en": "Save"},
    "cancel": {"fr": "Annuler", "en": "Cancel"},
    "settings_saved": {"fr": "Paramètres enregistrés.", "en": "Settings saved."},
}


def normaliser_langue(langue):
    code = str(langue or "").strip().lower()
    return code if code in LANGUES else LANGUE_DEFAUT


def traduire(cle, langue="fr"):
    code = normaliser_langue(langue)
    entree = TRADUCTIONS.get(cle, {})
    return entree.get(code) or entree.get(LANGUE_DEFAUT) or cle
