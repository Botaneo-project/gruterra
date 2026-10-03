"""Configuration locale commune, sans dependance et sans ouverture reseau."""
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

APP_DIR = Path(__file__).resolve().parent
CONFIG_DIR = Path(os.environ.get("BOTANEO_CONFIG_DIR", str(APP_DIR.parent / "_config")))
NETATMO_CONFIG = CONFIG_DIR / "netatmo_config.json"
LOCAL_CONFIG = CONFIG_DIR / "botaneo.local.json"
EMAIL_CONFIG = CONFIG_DIR / "email.local.json"


def normaliser_station_favorite(valeur):
    """Accepte un identifiant Netatmo ou un lien weathermap complet."""

    texte = str(valeur or "").strip()

    if not texte:
        return ""

    if "stationid=" in texte or texte.startswith("http://") or texte.startswith("https://"):
        try:
            requete = parse_qs(urlparse(texte).query)
            station_id = requete.get("stationid", [""])[0]
            if station_id:
                return station_id.strip()
        except Exception:
            pass

    return texte


def lire_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise RuntimeError("Configuration locale absente, inaccessible ou JSON invalide.") from None
    if not isinstance(data, dict):
        raise RuntimeError("La configuration locale doit etre un objet JSON.")
    return data


def ecrire_json(path, data):
    """Remplacement atomique; un echec laisse le fichier precedent intact."""
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError:
        raise RuntimeError("Ecriture de la configuration locale impossible.") from None
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def diagnostiquer_config_netatmo():
    """Controle local de la configuration Netatmo, sans connexion reseau.

    Ne retourne jamais les valeurs sensibles.
    """

    champs_requis = (
        "client" + "_" + "id",
        "client" + "_" + "secret",
        "access" + "_" + "token",
        "refresh" + "_" + "token",
    )

    if not NETATMO_CONFIG.exists():
        return {
            "ok": False,
            "niveau": "absente",
            "message": "Configuration Netatmo absente.",
            "details": "Créer _config/netatmo_config.json à partir de netatmo_config.example.json.",
            "manquants": list(champs_requis),
        }

    try:
        data = lire_json(NETATMO_CONFIG)
    except RuntimeError as erreur:
        return {
            "ok": False,
            "niveau": "illisible",
            "message": "Configuration Netatmo illisible.",
            "details": str(erreur),
            "manquants": list(champs_requis),
        }

    manquants = []
    exemples = []
    for champ in champs_requis:
        valeur = str(data.get(champ, "") or "").strip()
        if not valeur:
            manquants.append(champ)
        elif valeur.startswith("votre_"):
            exemples.append(champ)

    problemes = manquants + exemples
    if problemes:
        return {
            "ok": False,
            "niveau": "incomplete",
            "message": "Configuration Netatmo incomplète.",
            "details": "Champs à renseigner : " + ", ".join(problemes) + ".",
            "manquants": problemes,
        }

    return {
        "ok": True,
        "niveau": "prete",
        "message": "Configuration Netatmo présente.",
        "details": "Les champs nécessaires existent. Utilisez Actualiser Netatmo pour tester la connexion réelle.",
        "manquants": [],
    }


def parametres_netatmo():
    data = lire_json(LOCAL_CONFIG).get("netatmo_public", {})
    try:
        lat, lon = float(data["latitude"]), float(data["longitude"])
        radius = int(data["rayon_metres"])
        search = int(data["rayon_favoris_metres"])
        favorites = data["stations_favorites"]
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and radius > 0 and search > 0):
            raise ValueError()
        if not isinstance(favorites, list) or not all(isinstance(x, str) for x in favorites):
            raise ValueError()
        favorites = [normaliser_station_favorite(x) for x in favorites]
        favorites = [x for x in favorites if x]
    except (KeyError, TypeError, ValueError, OverflowError):
        raise RuntimeError("Parametres locaux Netatmo invalides.") from None
    return lat, lon, radius, search, set(favorites)
