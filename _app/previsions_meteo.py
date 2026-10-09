"""Prévisions météo locales sans secret.

Par sécurité, aucun appel externe n'est effectué tant que la prévision n'est pas activée
explicitement dans C:\\Plantes\\_config\\botaneo.local.json.
"""

from i18n import traduire_courant as _tr
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import json

from botaneo_config import lire_json, LOCAL_CONFIG

URL_OPEN_METEO = "https://api.open-meteo.com/v1/meteofrance"


def parametres_prevision():
    try:
        config = lire_json(LOCAL_CONFIG)
    except RuntimeError:
        raise RuntimeError("Configuration locale absente.") from None

    prevision = config.get("previsions_meteo", {})
    if not isinstance(prevision, dict) or not prevision.get("active", False):
        raise RuntimeError(_tr('previsions_meteo_text_24')) from None

    source = prevision.get("source", "open_meteo_meteofrance")
    if source != "open_meteo_meteofrance":
        raise RuntimeError(_tr('previsions_meteo_text_28')) from None

    try:
        latitude = float(prevision["latitude"])
        longitude = float(prevision["longitude"])
    except (KeyError, TypeError, ValueError):
        raise RuntimeError(_tr('previsions_meteo_text_34')) from None

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise RuntimeError(_tr('previsions_meteo_text_37')) from None

    return latitude, longitude


def _nombre(valeur, defaut=0.0):
    try:
        if valeur is None:
            return defaut
        return float(valeur)
    except (TypeError, ValueError):
        return defaut


def _arrondir(valeur, precision=1):
    try:
        return round(float(valeur), precision)
    except (TypeError, ValueError):
        return None


def _interpretation_pluie(cumul):
    if cumul is None:
        return _tr('previsions_meteo_text_60')
    if cumul == 0:
        return _tr('previsions_meteo_text_62')
    if cumul < 0.5:
        return _tr('previsions_meteo_text_64')
    if cumul < 2:
        return _tr('previsions_meteo_text_66')
    if cumul < 5:
        return _tr('previsions_meteo_text_68')
    return _tr('previsions_meteo_text_69')


def _interpretation_code_meteo(code):
    if code is None:
        return None

    try:
        code = int(code)
    except (TypeError, ValueError):
        return None

    if code == 0:
        return _tr('previsions_meteo_text_84_more')
    if code in (1, 2):
        return _tr('previsions_meteo_text_84')
    if code == 3:
        return _tr('previsions_meteo_text_88')
    if code in (45, 48):
        return _tr('previsions_meteo_text_90')
    if code in (51, 53, 55, 56, 57):
        return _tr('previsions_meteo_text_92')
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return _tr('previsions_meteo_text_94')
    if code in (71, 73, 75, 77, 85, 86):
        return _tr('previsions_meteo_text_96')
    if code in (95, 96, 99):
        return _tr('previsions_meteo_text_98')
    return None


def _interpretation_lumiere(rayonnement, nuages):
    if rayonnement is not None:
        if rayonnement < 80:
            return _tr('previsions_meteo_text_103')
        if rayonnement < 250:
            return _tr('previsions_meteo_text_105')
        return _tr('previsions_meteo_text_106')
    if nuages is not None:
        if nuages >= 80:
            return _tr('previsions_meteo_text_109')
        if nuages >= 50:
            return _tr('previsions_meteo_text_113')
        return _tr('previsions_meteo_text_84')
    return _tr('interface_text_5146')


def recuperer_prevision_2h():
    """Retourne une prévision locale synthétique sur les 2 prochaines heures."""

    latitude, longitude = parametres_prevision()
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "wind_speed_10m",
            "wind_gusts_10m",
            "cloud_cover",
            "shortwave_radiation",
            "weather_code"
        ]),
        "forecast_days": 1,
        "timezone": "Europe/Paris",
        "models": "meteofrance_arome_france_hd"
    }

    url = URL_OPEN_METEO + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "Gruterra/1.0"})

    with urlopen(request, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))

    hourly = data.get("hourly", {})
    heures = hourly.get("time", [])
    maintenant = datetime.now().astimezone()

    indexes = []
    for index, heure in enumerate(heures):
        try:
            date_heure = datetime.fromisoformat(heure).astimezone()
        except ValueError:
            continue
        delta = (date_heure - maintenant).total_seconds()
        if 0 <= delta <= 7200:
            indexes.append(index)

    if not indexes and heures:
        indexes = list(range(min(2, len(heures))))

    if not indexes:
        raise RuntimeError(_tr('previsions_meteo_text_163'))

    def valeurs(cle):
        source = hourly.get(cle, [])
        return [source[i] for i in indexes if i < len(source) and source[i] is not None]

    precipitation = valeurs("precipitation")
    pluie = valeurs("rain")
    temperatures = valeurs("temperature_2m")
    humidites = valeurs("relative_humidity_2m")
    vents = valeurs("wind_speed_10m")
    rafales = valeurs("wind_gusts_10m")
    nuages = valeurs("cloud_cover")
    rayonnements = valeurs("shortwave_radiation")
    codes_meteo = valeurs("weather_code")

    cumul_pluie = sum(_nombre(v) for v in pluie or precipitation)
    intensite_max = max([_nombre(v) for v in precipitation], default=0.0)
    temperature_debut = _arrondir(temperatures[0], 1) if temperatures else None
    temperature_fin = _arrondir(temperatures[-1], 1) if temperatures else None
    humidite = round(sum(_nombre(v) for v in humidites) / len(humidites)) if humidites else None
    vent = _arrondir(sum(_nombre(v) for v in vents) / len(vents), 1) if vents else None
    rafale = _arrondir(max(rafales), 1) if rafales else None
    nuage = round(sum(_nombre(v) for v in nuages) / len(nuages)) if nuages else None
    rayonnement = _arrondir(sum(_nombre(v) for v in rayonnements) / len(rayonnements), 0) if rayonnements else None
    code_meteo = codes_meteo[-1] if codes_meteo else None
    ciel = _interpretation_lumiere(rayonnement, nuage)
    if ciel == "non disponible":
        ciel = _interpretation_code_meteo(code_meteo) or ciel
    if ciel == "non disponible":
        if cumul_pluie > 0.5:
            ciel = _tr('previsions_meteo_text_194')
        elif cumul_pluie > 0:
            ciel = _tr('previsions_meteo_text_198_more')
        else:
            ciel = _tr('previsions_meteo_text_198')

    return {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Open-Meteo · Météo-France AROME HD",
        "pluie_2h": round(cumul_pluie, 2),
        "intensite_max": round(intensite_max, 2),
        "temperature_debut": temperature_debut,
        "temperature_fin": temperature_fin,
        "humidite": humidite,
        "vent": vent,
        "rafale": rafale,
        "nuages": nuage,
        "rayonnement": rayonnement,
        "code_meteo": code_meteo,
        "lumiere": ciel,
        "message_pluie": _interpretation_pluie(round(cumul_pluie, 2))
    }
