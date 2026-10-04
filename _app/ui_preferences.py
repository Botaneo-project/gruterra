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


def charger_langue_interface():
    try:
        value = lire_json(PREFERENCES).get("langue", "fr")
        return value if value in {"fr", "en"} else "fr"
    except RuntimeError:
        return "fr"


def sauvegarder_langue_interface(langue):
    try:
        code = langue if langue in {"fr", "en"} else "fr"
        preferences = lire_json(PREFERENCES) if PREFERENCES.exists() else {}
        preferences["langue"] = code
        ecrire_json(PREFERENCES, preferences)
        return True
    except (OSError, RuntimeError):
        return False
