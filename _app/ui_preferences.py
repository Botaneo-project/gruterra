"""Preferences d'affichage locales, independantes des secrets OAuth."""
from botaneo_config import CONFIG_DIR, lire_json, ecrire_json

PREFERENCES = CONFIG_DIR / "interface.local.json"


def charger_theme_sombre():
    try:
        value = lire_json(PREFERENCES).get("theme_sombre", True)
        return value if isinstance(value, bool) else True
    except RuntimeError:
        return True


def sauvegarder_theme_sombre(actif):
    try:
        preferences = lire_json(PREFERENCES) if PREFERENCES.exists() else {}
        preferences["theme_sombre"] = bool(actif)
        ecrire_json(PREFERENCES, preferences)
        return True
    except (OSError, RuntimeError):
        return False
