
# ============================================================
# BOTANEO - NETATMO
# Récupération des données Netatmo
#
# Gestion OAuth automatique :
# - utilise l'access_token actuel
# - détecte automatiquement un token expiré
# - utilise le refresh_token
# - récupère un nouvel access_token
# - sauvegarde automatiquement les nouveaux tokens
# - réessaie l'appel API
#
# Le reste du module :
# - détecte automatiquement les stations
# - détecte automatiquement les modules
# - récupère leurs mesures
# - retourne une structure utilisable par Botaneo
#
# Aucun nom de station ou de module n'est codé en dur.
# ============================================================

import json
import os
import math
import time
import requests
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

# Compatibilite avec python capteurs/netatmo.py et les imports de l'application.
if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from botaneo_config import NETATMO_CONFIG, lire_json, ecrire_json, parametres_netatmo
from botaneo_journal import evenement

CONFIG = str(NETATMO_CONFIG)


def _requete(method, *args, **kwargs):
    try:
        response = getattr(requests, method)(*args, **kwargs)
    except requests.RequestException:
        evenement("netatmo_network_error")
        raise RuntimeError("Connexion Netatmo impossible (erreur reseau).") from None
    if not response.ok:
        evenement("netatmo_http_error", response.status_code)
    return response


URL_STATIONS = "https://api.netatmo.com/api/getstationsdata"
URL_PUBLIC = "https://api.netatmo.com/api/getpublicdata"
URL_WEATHERMAP_TOKEN = "https://auth.netatmo.com/weathermap/token"
URL_PUBLIC_MEASURE = "https://app.netatmo.net/api/getpublicmeasure"
URL_TOKEN = "https://api.netatmo.com/oauth2/token"

(LATITUDE_APPROX, LONGITUDE_APPROX, RAYON_PUBLIC_METRES,
 RAYON_RECHERCHE_FAVORIS_METRES, STATIONS_PUBLIQUES_FAVORITES) = parametres_netatmo()


# ============================================================
# CONFIGURATION JSON
# ============================================================

def charger_configuration():
    return lire_json(CONFIG)


def sauvegarder_configuration(config):
    # Conserve le chemin et la rotation OAuth; aucune copie supplementaire de tokens.
    ecrire_json(CONFIG, config)


# ============================================================
# OAUTH NETATMO
# ============================================================

def rafraichir_token(config):
    """
    Utilise le refresh_token pour obtenir un nouveau access_token.

    Si Netatmo fournit également un nouveau refresh_token,
    celui-ci remplace automatiquement l'ancien.
    """

    if not config.get("client_id"):
        raise RuntimeError(
            "Le fichier netatmo_config.json ne contient pas "
            "de client_id."
        )

    if not config.get("client_secret"):
        raise RuntimeError(
            "Le fichier netatmo_config.json ne contient pas "
            "de client_secret."
        )

    if not config.get("refresh_token"):
        raise RuntimeError(
            "Aucun refresh_token n'est présent dans "
            "netatmo_config.json."
        )

    print("🔄 Access token expiré.")
    print("🔐 Renouvellement automatique du token Netatmo...")

    donnees = {
        "grant_type": "refresh_token",
        "refresh_token": config["refresh_token"],
        "client_id": config["client_id"],
        "client_secret": config["client_secret"]
    }

    try:
        reponse = _requete("post", 
            URL_TOKEN,
            data=donnees,
            timeout=15
        )

    except requests.RequestException as erreur:
        raise RuntimeError(
            f"Impossible de contacter le serveur OAuth Netatmo : {erreur}"
        )

    if not reponse.ok:
        raise RuntimeError(
            f"Erreur OAuth Netatmo {reponse.status_code} : "
            "Reponse serveur masquee."
        )

    try:
        resultat = reponse.json()

    except ValueError:
        raise RuntimeError(
            "Netatmo a retourné une réponse OAuth invalide."
        )

    nouvel_access_token = resultat.get("access_token")

    if not nouvel_access_token:
        raise RuntimeError(
            "Netatmo n'a pas retourné de nouvel access_token."
        )

    # --------------------------------------------------------
    # Nouveau access token
    # --------------------------------------------------------

    config["access_token"] = nouvel_access_token

    # --------------------------------------------------------
    # Nouveau refresh token éventuel
    # --------------------------------------------------------

    nouveau_refresh_token = resultat.get("refresh_token")

    if nouveau_refresh_token:
        config["refresh_token"] = nouveau_refresh_token

    # --------------------------------------------------------
    # Sauvegarde immédiate
    # --------------------------------------------------------

    sauvegarder_configuration(config)
    evenement("netatmo_refresh_ok")

    print("✅ Token Netatmo renouvelé automatiquement.")
    print("💾 Nouveau token sauvegardé.")

    return config["access_token"]


# ============================================================
# API NETATMO
# ============================================================

def recuperer_donnees(access_token):
    """
    Récupère les données de toutes les stations Netatmo.

    Retourne :
        (donnees, token_valide)

    Un token est considéré comme expiré si Netatmo renvoie :
        - HTTP 401
        - HTTP 403 avec le message "Access token expired"
    """

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    reponse = None

    for tentative in range(1, 4):

        try:
            reponse = _requete("get", 
                URL_STATIONS,
                headers=headers,
                timeout=15
            )

        except requests.RequestException as erreur:
            raise RuntimeError(
                f"Impossible de contacter l'API Netatmo : {erreur}"
            )

        if reponse.status_code != 503:
            break

        if tentative < 3:
            time.sleep(1)

    if reponse is None:
        raise RuntimeError(
            "Aucune réponse reçue de l'API Netatmo."
        )

    # ========================================================
    # TOKEN EXPIRÉ
    # ========================================================

    if reponse.status_code == 401:
        return None, False

    if reponse.status_code == 403:

        try:
            erreur_json = reponse.json()

            message = (
                erreur_json
                .get("error", {})
                .get("message", "")
            )

            if "access token expired" in message.lower():
                return None, False

        except (ValueError, AttributeError):
            pass

    # ========================================================
    # AUTRE ERREUR
    # ========================================================

    if not reponse.ok:
        if reponse.status_code == 503:
            raise RuntimeError(
                "Service Netatmo temporairement indisponible "
                "(erreur 503)."
            )

        raise RuntimeError(
            f"Erreur Netatmo {reponse.status_code} : "
            "Reponse serveur masquee."
        )

    # ========================================================
    # RÉPONSE OK
    # ========================================================

    try:
        return reponse.json(), True

    except ValueError:
        raise RuntimeError(
            "Netatmo a retourné une réponse JSON invalide."
        )


# ============================================================
# RÉCUPÉRATION AVEC AUTHENTIFICATION AUTOMATIQUE
# ============================================================

def recuperer_donnees_avec_auth(config):
    """
    Récupère les données Netatmo.

    Fonctionnement :

    1. Utilise l'access_token actuel.
    2. Si Netatmo indique qu'il est expiré :
       - utilise le refresh_token
       - récupère un nouveau token
       - sauvegarde la configuration
       - recommence la requête.
    """

    if not config.get("access_token"):
        raise RuntimeError(
            "Le fichier netatmo_config.json ne contient pas "
            "de access_token."
        )

    # --------------------------------------------------------
    # Première tentative
    # --------------------------------------------------------

    donnees, token_valide = recuperer_donnees(
        config["access_token"]
    )

    if token_valide:
        return donnees

    # --------------------------------------------------------
    # Token expiré
    # --------------------------------------------------------

    nouvel_access_token = rafraichir_token(config)

    # --------------------------------------------------------
    # Deuxième tentative
    # --------------------------------------------------------

    donnees, token_valide = recuperer_donnees(
        nouvel_access_token
    )

    if not token_valide:
        raise RuntimeError(
            "Le nouveau token Netatmo est également refusé. "
            "Une nouvelle autorisation OAuth peut être nécessaire."
        )

    return donnees


# ============================================================
# STATIONS PUBLIQUES PROCHES
# ============================================================

def calculer_zone(latitude, longitude, rayon_metres):
    """Calcule une petite zone GPS autour du point donne."""

    delta_lat = rayon_metres / 111_320
    cos_lat = math.cos(math.radians(latitude))

    if abs(cos_lat) < 0.0001:
        delta_lon = delta_lat
    else:
        delta_lon = rayon_metres / (111_320 * cos_lat)

    return {
        "lat_ne": latitude + delta_lat,
        "lon_ne": longitude + delta_lon,
        "lat_sw": latitude - delta_lat,
        "lon_sw": longitude - delta_lon
    }


def calculer_distance_metres(lat1, lon1, lat2, lon2):
    """Distance approximative entre deux points GPS."""

    rayon_terre = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )

    return rayon_terre * 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


def extraire_nombre(donnees, cles):

    if isinstance(donnees, dict):

        for cle in cles:

            valeur = donnees.get(cle)

            if isinstance(valeur, (int, float)):
                return valeur

        for valeur in donnees.values():

            resultat = extraire_nombre(valeur, cles)

            if resultat is not None:
                return resultat

    if isinstance(donnees, list):

        for valeur in donnees:

            resultat = extraire_nombre(valeur, cles)

            if resultat is not None:
                return resultat

    return None


def extraire_position_publique(station):

    place = station.get("place", {})
    location = place.get("location")

    if (
        isinstance(location, list)
        and len(location) >= 2
    ):
        return location[1], location[0]

    latitude = place.get("latitude") or station.get("latitude")
    longitude = place.get("longitude") or station.get("longitude")

    if latitude is None or longitude is None:
        return None

    return float(latitude), float(longitude)


def est_station_favorite(station):

    if station.get("favorite"):
        return True

    identifiants = [
        station.get("_id"),
        station.get("id")
    ]

    identifiants.extend(
        station.get("modules") or []
    )

    if isinstance(station.get("module_types"), dict):
        identifiants.extend(
            station["module_types"].keys()
        )

    if isinstance(station.get("measures"), dict):
        identifiants.extend(
            station["measures"].keys()
        )

    identifiants = {
        str(identifiant).lower()
        for identifiant in identifiants
        if identifiant
    }

    return bool(
        identifiants.intersection(
            {
                station_id.lower()
                for station_id in STATIONS_PUBLIQUES_FAVORITES
            }
        )
    )


def recuperer_token_weathermap():

    try:
        reponse = _requete("get", 
            URL_WEATHERMAP_TOKEN,
            headers={
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                "User-Agent": "Mozilla/5.0"
            },
            timeout=15
        )

    except requests.RequestException as erreur:
        raise RuntimeError(
            f"Impossible de récupérer le token public Netatmo : {erreur}"
        )

    if not reponse.ok:
        raise RuntimeError(
            f"Erreur token public Netatmo {reponse.status_code}."
        )

    try:
        donnees = reponse.json()

    except ValueError:
        raise RuntimeError(
            "Netatmo a retourné un token public invalide."
        )

    token = donnees.get("body")

    if not token:
        raise RuntimeError(
            "Netatmo n'a pas retourné de token public."
        )

    return f"Bearer {token}"


def recuperer_mesure_publique_station(station_id):

    token = recuperer_token_weathermap()

    try:
        reponse = _requete("post", 
            URL_PUBLIC_MEASURE,
            headers={
                "Authorization": token,
                "User-Agent": "Mozilla/5.0"
            },
            json={
                "device_id": station_id
            },
            timeout=15
        )

    except requests.RequestException as erreur:
        raise RuntimeError(
            f"Impossible de récupérer la station publique Netatmo : {erreur}"
        )

    if not reponse.ok:
        raise RuntimeError(
            f"Erreur station publique Netatmo {reponse.status_code}."
        )

    try:
        donnees = reponse.json()

    except ValueError:
        raise RuntimeError(
            "Netatmo a retourné une station publique invalide."
        )

    body = donnees.get("body", [])

    if not body:
        raise RuntimeError(
            f"Aucune donnée publique pour la station {station_id}."
        )

    station = body[0]
    station["favorite"] = True

    return station


def extraire_mesures_publiques(station):

    resultat = {
        "temperature": None,
        "humidite": None,
        "pression": None,
        "pluie": None,
        "pluie_1h": None,
        "pluie_24h": None,
        "vent": None,
        "rafale": None,
        "direction_vent": None,
        "direction_rafale": None,
        "pluviometre": False,
        "anemometre": False,
        "brut": station
    }

    module_types = station.get("module_types", {})

    if isinstance(module_types, dict):
        resultat["pluviometre"] = "NAModule3" in module_types.values()
        resultat["anemometre"] = "NAModule2" in module_types.values()

    correspondances = {
        "temperature": "temperature",
        "humidity": "humidite",
        "pressure": "pression",
        "rain": "pluie",
        "rain_live": "pluie",
        "rain_60min": "pluie_1h",
        "rain_1h": "pluie_1h",
        "rain_24h": "pluie_24h",
        "wind_strength": "vent",
        "windstrength": "vent",
        "wind": "vent",
        "gust_strength": "rafale",
        "guststrength": "rafale",
        "gust": "rafale",
        "wind_angle": "direction_vent",
        "windangle": "direction_vent",
        "gustangle": "direction_rafale"
    }

    for mesure in station.get("measures", {}).values():

        if not isinstance(mesure, dict):
            continue

        types = mesure.get("type")
        donnees = mesure.get("res")

        if not isinstance(types, list):
            continue

        if not isinstance(donnees, dict) or not donnees:
            continue

        valeurs = list(donnees.values())[-1]

        if not isinstance(valeurs, list):
            continue

        for index, type_mesure in enumerate(types):

            if index >= len(valeurs):
                continue

            cle = correspondances.get(type_mesure)

            if cle:
                resultat[cle] = valeurs[index]

    return resultat


def normaliser_station_publique(station, latitude, longitude):

    position = extraire_position_publique(station)

    if position is None:
        return None

    lat_station, lon_station = position

    distance = calculer_distance_metres(
        latitude,
        longitude,
        lat_station,
        lon_station
    )

    mesures = extraire_mesures_publiques(station)

    favorite = est_station_favorite(station)

    return {
        "id": station.get("_id") or station.get("id"),
        "nom": station.get("name") or "Station publique",
        "favorite": favorite,
        "distance_m": distance,
        "latitude": lat_station,
        "longitude": lon_station,
        "mesures": mesures
    }


def recuperer_stations_publiques(
    latitude=LATITUDE_APPROX,
    longitude=LONGITUDE_APPROX,
    rayon_metres=RAYON_PUBLIC_METRES
):
    """Recupere les stations publiques Netatmo proches."""

    config = charger_configuration()

    if not config.get("access_token"):
        raise RuntimeError(
            "Le fichier netatmo_config.json ne contient pas "
            "de access_token."
        )

    zone = calculer_zone(
        latitude,
        longitude,
        max(
            rayon_metres,
            RAYON_RECHERCHE_FAVORIS_METRES
        )
    )

    headers = {
        "Authorization": f"Bearer {config['access_token']}"
    }

    stations_par_id = {}
    erreurs = []

    for type_requis in ("temperature", "rain", "wind"):

        params = {
            **zone,
            "required_data": type_requis,
            "filter": "true"
        }

        try:
            reponse = _requete("get", 
                URL_PUBLIC,
                headers=headers,
                params=params,
                timeout=15
            )

        except requests.RequestException as erreur:
            raise RuntimeError(
                f"Impossible de contacter l'API publique Netatmo : {erreur}"
            )

        if reponse.status_code in (401, 403):
            config["access_token"] = rafraichir_token(config)
            headers["Authorization"] = f"Bearer {config['access_token']}"

            reponse = _requete("get", 
                URL_PUBLIC,
                headers=headers,
                params=params,
                timeout=15
            )

        if not reponse.ok:
            erreurs.append(
                f"{type_requis}: {reponse.status_code}"
            )
            continue

        try:
            donnees = reponse.json()

        except ValueError:
            raise RuntimeError(
                "Netatmo a retourné une réponse publique JSON invalide."
            )

        for station in donnees.get("body", []):

            station_normale = normaliser_station_publique(
                station,
                latitude,
                longitude
            )

            if station_normale is None:
                continue

            if (
                station_normale["distance_m"] > rayon_metres
                and not station_normale["favorite"]
            ):
                continue

            station_id = (
                station_normale.get("id")
                or f"{station_normale['latitude']:.5f},"
                f"{station_normale['longitude']:.5f}"
            )

            station_existante = stations_par_id.get(station_id)

            if station_existante is None:
                stations_par_id[station_id] = station_normale
                continue

            for cle, valeur in station_normale["mesures"].items():

                if cle == "brut":
                    continue

                if valeur is not None:
                    station_existante["mesures"][cle] = valeur

    for station_id in STATIONS_PUBLIQUES_FAVORITES:

        try:
            station = recuperer_mesure_publique_station(station_id)
        except Exception:
            continue

        station_normale = normaliser_station_publique(
            station,
            latitude,
            longitude
        )

        if station_normale is None:
            continue

        stations_par_id[station_id] = station_normale

    stations = list(stations_par_id.values())

    if not stations and erreurs:
        raise RuntimeError(
            "Stations publiques Netatmo indisponibles : "
            + ", ".join(erreurs)
        )

    stations.sort(
        key=lambda station: station["distance_m"]
    )

    return stations


# ============================================================
# DATES
# ============================================================

def convertir_date(timestamp):
    """Convertit un timestamp Unix en date lisible."""

    if not timestamp:
        return None

    try:
        return datetime.fromtimestamp(
            timestamp
        ).strftime("%d/%m/%Y %H:%M")

    except (TypeError, ValueError, OSError):
        return None


# ============================================================
# EXTRACTION DES MESURES
# ============================================================

def extraire_mesures(element):
    """Extrait uniquement les mesures utiles."""

    mesures = element.get("dashboard_data", {})

    resultat = {
        "temperature": mesures.get("Temperature"),
        "humidite": mesures.get("Humidity"),
        "pression": mesures.get("Pressure"),
        "co2": mesures.get("CO2"),
        "bruit": mesures.get("Noise"),
        "vent": mesures.get("WindStrength"),
        "direction_vent": mesures.get("WindAngle"),
        "rafale": mesures.get("GustStrength"),
        "pluie": mesures.get("Rain"),
        "pluie_1h": mesures.get("sum_rain_1"),
        "pluie_24h": mesures.get("sum_rain_24"),

        "date_max_temp": convertir_date(
            mesures.get("date_max_temp")
        ),

        "date_min_temp": convertir_date(
            mesures.get("date_min_temp")
        ),

        "date_mesure": convertir_date(
            mesures.get("time")
        ),

        # Données brutes conservées
        "brut": mesures
    }

    return resultat


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def recuperer_netatmo():
    """
    Fonction principale utilisée par Botaneo.

    Retourne une liste de stations avec leurs modules.
    """

    config = charger_configuration()

    donnees = recuperer_donnees_avec_auth(config)

    stations_api = (
        donnees
        .get("body", {})
        .get("devices", [])
    )

    stations = []

    for station in stations_api:

        station_resultat = {
            "id": station.get("_id"),
            "nom": station.get("station_name"),
            "type": station.get("type"),
            "mesures": extraire_mesures(station),
            "modules": []
        }

        for module in station.get("modules", []):

            module_resultat = {
                "id": module.get("_id"),
                "nom": module.get("module_name"),
                "type": module.get("type"),
                "mesures": extraire_mesures(module)
            }

            station_resultat["modules"].append(
                module_resultat
            )

        stations.append(station_resultat)

    return stations


# ============================================================
# AFFICHAGE DES MESURES
# ============================================================

def afficher_mesures(nom, type_module, mesures):
    """Affiche les mesures d'un élément Netatmo."""

    print("-" * 60)
    print(f"📦 {nom}")
    print(f"🔧 Type : {type_module}")

    if mesures["temperature"] is not None:
        print(
            f"🌡️ Température : "
            f"{mesures['temperature']} °C"
        )

    if mesures["humidite"] is not None:
        print(
            f"💧 Humidité    : "
            f"{mesures['humidite']} %"
        )

    if mesures["pression"] is not None:
        print(
            f"🔵 Pression    : "
            f"{mesures['pression']} hPa"
        )

    if mesures["co2"] is not None:
        print(
            f"🌬️ CO₂         : "
            f"{mesures['co2']} ppm"
        )

    if mesures["bruit"] is not None:
        print(
            f"🔊 Bruit       : "
            f"{mesures['bruit']} dB"
        )

    if mesures["vent"] is not None:
        print(
            f"💨 Vent        : "
            f"{mesures['vent']} km/h"
        )

    if mesures["direction_vent"] is not None:
        print(
            f"🧭 Direction   : "
            f"{mesures['direction_vent']}°"
        )

    if mesures["rafale"] is not None:
        print(
            f"💨 Rafale      : "
            f"{mesures['rafale']} km/h"
        )

    if mesures["pluie"] is not None:
        print(
            f"🌧️ Pluie       : "
            f"{mesures['pluie']} mm"
        )

    if mesures["pluie_1h"] is not None:
        print(
            f"🌧️ Pluie 1h    : "
            f"{mesures['pluie_1h']} mm"
        )

    if mesures["pluie_24h"] is not None:
        print(
            f"🌧️ Pluie 24h   : "
            f"{mesures['pluie_24h']} mm"
        )

    if mesures["date_max_temp"]:
        print(
            f"🌡️ Date max    : "
            f"{mesures['date_max_temp']}"
        )

    if mesures["date_min_temp"]:
        print(
            f"❄️ Date min    : "
            f"{mesures['date_min_temp']}"
        )

    if mesures["date_mesure"]:
        print(
            f"🕐 Mesure      : "
            f"{mesures['date_mesure']}"
        )


# ============================================================
# AFFICHAGE GLOBAL
# ============================================================

def afficher_resultat(stations):
    """Affiche les données récupérées."""

    print()
    print("=" * 60)
    print("🌦️ BOTANEO - NETATMO")
    print("=" * 60)
    print()

    print(f"📡 Stations trouvées : {len(stations)}")
    print()

    for station in stations:

        print("=" * 60)
        print(
            f"🏠 STATION : "
            f"{station['nom']}"
        )
        print("=" * 60)

        afficher_mesures(
            station["nom"],
            station["type"],
            station["mesures"]
        )

        for module in station["modules"]:

            afficher_mesures(
                module["nom"],
                module["type"],
                module["mesures"]
            )

    print()
    print("=" * 60)
    print("✅ LECTURE TERMINÉE")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        print()
        print("=" * 60)
        print("🌦️ BOTANEO - NETATMO")
        print("=" * 60)
        print()

        print("🔐 Connexion à Netatmo...")

        stations = recuperer_netatmo()

        print("✅ Connexion réussie")

        afficher_resultat(stations)

    except Exception as erreur:

        print()
        print("❌ ERREUR NETATMO")
        print(f"   {erreur}")
        print()


# ============================================================
# EXÉCUTION
# ============================================================

if __name__ == "__main__":
    main()

