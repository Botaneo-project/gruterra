from instance_botaneo import exiger_instance_unique
exiger_instance_unique(graphique=True)

import tkinter as tk
from tkinter import ttk, messagebox
import ajout_capteur
from meteo_cache import CacheMeteo, recuperer_sources
from datetime import datetime, timedelta
import threading
import json
from pathlib import Path

import database
import mini_base_plantes
from capteur_infos import lire_infos, resume_infos, details_infos
from botaneo_config import LOCAL_CONFIG, lire_json, ecrire_json, normaliser_station_favorite
from ui_preferences import charger_theme_sombre, sauvegarder_theme_sombre
from vue_historique import ouvrir_historique
import sync_miflora
from capteurs import netatmo
import previsions_meteo
from suivi_raspberry_ui import SuiviRaspberry
from botaneo_config import CONFIG_DIR

# ============================================================
# CONFIGURATION
# ============================================================

root = tk.Tk()

root.title("Botaneo")
root.geometry("1100x850")
root.minsize(900, 650)

BG = "#F2F6F1"
CARD = "#FBFDF9"
TEXT = "#223228"
SECONDARY = "#68786E"
GREEN = "#3F7F52"
LIGHT_GREEN = "#E4F1E7"
ORANGE = "#C77D25"
LIGHT_ORANGE = "#FFF0D8"
RED = "#B94A48"
LIGHT_RED = "#F8E1E0"
BORDER = "#D6E2D8"
BLUE = "#3F6F99"
LIGHT_BLUE = "#E4EEF7"

THEME_CLAIR = {
    "BG": "#F2F6F1",
    "CARD": "#FBFDF9",
    "TEXT": "#223228",
    "SECONDARY": "#68786E",
    "GREEN": "#3F7F52",
    "LIGHT_GREEN": "#E4F1E7",
    "ORANGE": "#C77D25",
    "LIGHT_ORANGE": "#FFF0D8",
    "RED": "#B94A48",
    "LIGHT_RED": "#F8E1E0",
    "BORDER": "#D6E2D8",
    "BLUE": "#3F6F99",
    "LIGHT_BLUE": "#E4EEF7"
}

THEME_SOMBRE = {
    "BG": "#111816",
    "CARD": "#1B2521",
    "TEXT": "#E8F0EA",
    "SECONDARY": "#9FB0A6",
    "GREEN": "#82C990",
    "LIGHT_GREEN": "#203B2A",
    "ORANGE": "#F0B35D",
    "LIGHT_ORANGE": "#3B2C1C",
    "RED": "#EF7979",
    "LIGHT_RED": "#3A2224",
    "BORDER": "#30423A",
    "BLUE": "#8DBAF0",
    "LIGHT_BLUE": "#203044"
}

theme_sombre_actif = charger_theme_sombre()
globals().update(THEME_SOMBRE if theme_sombre_actif else THEME_CLAIR)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
LOGO_PATH = ASSETS_DIR / "botaneo_logo.png"
LOGO_HEADER_PATH = ASSETS_DIR / "botaneo_logo_header.png"
logo_image = None
root.configure(bg=BG)


# ============================================================
# VARIABLES
# ============================================================

status_var = tk.StringVar(value="● Système actif")

sync_var = tk.StringVar(
    value="Aucune synchronisation effectuée"
)

sync_detail_var = tk.StringVar(value="")
sync_progress_var = tk.StringVar(value="")

auto_sync_var = tk.StringVar(value="Auto 18:00 en attente")

netatmo_status_var = tk.StringVar(
    value="🌦️ Données météo non chargées"
)

netatmo_date_var = tk.StringVar(
    value=""
)

content_frame = None
sync_frame = None
sync_button = None

netatmo_frame = None

netatmo_data = []
netatmo_public_data = []
prevision_2h_data = None
prevision_2h_error = None
netatmo_loading = False
auto_sync_config = {}
auto_sync_en_cours = False
import_historique_en_cours = False
derniere_operation_bluetooth = None
netatmo_preferences = {}
interface_layout_config = {}
alertes_config = {}
netatmo_sections_ouvertes = {
    "stations_proches": False,
    "equipements_prives": True
}

filtre_zone_var = tk.StringVar(value="Toutes")
filtre_piece_var = tk.StringVar(value="Toutes")
filtre_capteur_var = tk.StringVar(value="Toutes")
filtre_attention_var = tk.StringVar(value="Toutes")

NETATMO_CACHE = (
    Path(__file__).resolve().parent
    / "data"
    / "netatmo_cache.json"
)

PREVISION_CACHE = (
    Path(__file__).resolve().parent
    / "data"
    / "prevision_2h_cache.json"
)

AUTO_SYNC_CONFIG = (
    Path(__file__).resolve().parent.parent
    / "_config"
    / "sync_auto.local.json"
)

NETATMO_UI_CONFIG = (
    Path(__file__).resolve().parent.parent
    / "_config"
    / "netatmo_ui.local.json"
)

INTERFACE_LAYOUT_CONFIG = (
    Path(__file__).resolve().parent.parent
    / "_config"
    / "interface_layout.local.json"
)

ALERTES_CONFIG = (
    Path(__file__).resolve().parent.parent
    / "_config"
    / "alertes.local.json"
)

HISTORIQUE_IMPORT_CONFIG = (
    Path(__file__).resolve().parent.parent
    / "_config"
    / "historique_import.local.json"
)


# ============================================================
# OUTILS
# ============================================================

def formater_date(date_heure):
    if not date_heure:
        return "Jamais"

    try:
        dt = datetime.fromisoformat(date_heure)
        return dt.strftime("%d/%m/%Y à %H:%M:%S")

    except Exception:
        return str(date_heure)


meteo_etat = CacheMeteo(NETATMO_CACHE)


def charger_config_alertes():
    config = {
        "email_actif": False,
        "email_mode": "outlook",
        "email_destinataire": "",
        "seuil_batterie": 50,
        "delai_min_jours": 1,
        "plantes_rappel_email": []
    }
    try:
        if ALERTES_CONFIG.exists():
            donnees = lire_json(ALERTES_CONFIG)
            if isinstance(donnees, dict):
                config.update(donnees)
    except RuntimeError:
        pass

    try:
        seuil = int(config.get("seuil_batterie", 50))
        config["seuil_batterie"] = min(max(seuil, 1), 100)
    except (TypeError, ValueError):
        config["seuil_batterie"] = 50

    try:
        delai = int(config.get("delai_min_jours", 1))
        config["delai_min_jours"] = max(delai, 1)
    except (TypeError, ValueError):
        config["delai_min_jours"] = 1

    plantes = config.get("plantes_rappel_email", [])
    if not isinstance(plantes, list):
        plantes = []
    config["plantes_rappel_email"] = sorted({int(pid) for pid in plantes if str(pid).isdigit()})
    config["email_actif"] = bool(config.get("email_actif", False))
    if config.get("email_mode") != "outlook":
        config["email_mode"] = "outlook"
    if not isinstance(config.get("email_destinataire"), str):
        config["email_destinataire"] = ""
    return config


def sauvegarder_config_alertes():
    try:
        ecrire_json(ALERTES_CONFIG, alertes_config)
        return True
    except (OSError, RuntimeError):
        return False


def etat_batterie_capteur(info):
    batterie = info.get("batterie")
    seuil = int(alertes_config.get("seuil_batterie", 50))

    if batterie is None:
        return "Batterie : non lue", SECONDARY, BG

    if batterie <= seuil:
        return f"🔴 Batterie faible : {batterie} % · seuil {seuil} %", RED, LIGHT_RED

    if batterie <= min(seuil + 15, 100):
        return f"🟠 Batterie à surveiller : {batterie} % · seuil {seuil} %", ORANGE, LIGHT_ORANGE

    return f"🟢 Batterie OK : {batterie} %", GREEN, LIGHT_GREEN


def plante_avec_rappel_email(plante_id):
    return plante_id in set(alertes_config.get("plantes_rappel_email", []))


def charger_resultats_import_historique():
    try:
        data = lire_json(HISTORIQUE_IMPORT_CONFIG)
        if isinstance(data, dict):
            return data
    except RuntimeError:
        pass
    return {}


def sauvegarder_resultat_import_historique(capteur_id, resultat):
    data = charger_resultats_import_historique()
    resume = resultat.get("resume", {}) if isinstance(resultat, dict) else {}
    data[str(capteur_id)] = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "ok": bool(resultat.get("ok")) if isinstance(resultat, dict) else False,
        "message": resultat.get("message", "") if isinstance(resultat, dict) else "",
        "total_lues": resume.get("total_lues"),
        "ajoutees": resume.get("ajoutees"),
        "doublons": resume.get("doublons"),
        "history_count": resume.get("history_count")
    }
    try:
        ecrire_json(HISTORIQUE_IMPORT_CONFIG, data)
    except RuntimeError:
        pass


def dernier_resultat_import_historique(capteur_id):
    return charger_resultats_import_historique().get(str(capteur_id))


def texte_dernier_import_historique(capteur_id):
    dernier = dernier_resultat_import_historique(capteur_id)
    if not dernier:
        return "Historique Mi Flora : aucun import lancé depuis l'interface."

    date = formater_date(dernier.get("date"))
    if dernier.get("ok"):
        details = []
        if dernier.get("total_lues") is not None:
            details.append(f"{dernier.get('total_lues')} lue(s)")
        if dernier.get("ajoutees") is not None:
            details.append(f"{dernier.get('ajoutees')} nouvelle(s)")
        if dernier.get("doublons") is not None:
            details.append(f"{dernier.get('doublons')} déjà connue(s)")
        suffixe = " · ".join(details) if details else dernier.get("message", "import réussi")
        return f"Historique Mi Flora : dernier import le {date} · {suffixe}"

    return f"Historique Mi Flora : dernier essai le {date} · {dernier.get('message', 'échec')}"


def charger_layout_interface():
    config = {
        "meteo_en_haut": False,
        "vue_compacte_plantes": False
    }
    try:
        if INTERFACE_LAYOUT_CONFIG.exists():
            donnees = lire_json(INTERFACE_LAYOUT_CONFIG)
            if isinstance(donnees, dict):
                config.update(donnees)
    except RuntimeError:
        pass

    config["meteo_en_haut"] = bool(config.get("meteo_en_haut", False))
    config["vue_compacte_plantes"] = bool(config.get("vue_compacte_plantes", False))
    return config


def sauvegarder_layout_interface():
    try:
        ecrire_json(INTERFACE_LAYOUT_CONFIG, interface_layout_config)
        return True
    except (OSError, RuntimeError):
        return False


def meteo_affichee_en_haut():
    return bool(interface_layout_config.get("meteo_en_haut", False))


def vue_compacte_plantes_active():
    return bool(interface_layout_config.get("vue_compacte_plantes", False))


def charger_config_sync_auto():
    """Charge la synchronisation automatique locale."""

    config = {
        "active": True,
        "heure": "18:00",
        "jours": [0, 1, 2, 3, 4, 5, 6],
        "derniere_date": None,
        "derniere_execution": None
    }

    try:
        if AUTO_SYNC_CONFIG.exists():
            donnees = lire_json(AUTO_SYNC_CONFIG)
            if isinstance(donnees, dict):
                config.update(donnees)
    except RuntimeError:
        pass

    if not isinstance(config.get("active"), bool):
        config["active"] = True

    if not isinstance(config.get("heure"), str) or len(config.get("heure", "")) != 5:
        config["heure"] = "18:00"

    jours = config.get("jours")
    if not isinstance(jours, list) or not all(isinstance(jour, int) and 0 <= jour <= 6 for jour in jours):
        config["jours"] = [0, 1, 2, 3, 4, 5, 6]
    else:
        config["jours"] = sorted(set(jours))

    return config


def sauvegarder_config_sync_auto():
    try:
        ecrire_json(AUTO_SYNC_CONFIG, auto_sync_config)
        return True
    except (OSError, RuntimeError):
        return False


def libelle_jours_sync_auto():
    jours = auto_sync_config.get("jours", [0, 1, 2, 3, 4, 5, 6])
    if sorted(jours) == [0, 1, 2, 3, 4, 5, 6]:
        return "tous les jours"
    if sorted(jours) == [0, 1, 2, 3, 4]:
        return "lundi à vendredi"
    noms = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
    return ", ".join(noms[jour] for jour in sorted(jours)) if jours else "aucun jour"


def libelle_sync_auto():
    heure = auto_sync_config.get("heure", "18:00")
    derniere = auto_sync_config.get("derniere_execution")
    jours = libelle_jours_sync_auto()
    aujourd_hui = datetime.now().strftime("%Y-%m-%d")
    faite_aujourdhui = auto_sync_config.get("derniere_date") == aujourd_hui

    if not auto_sync_config.get("active", True):
        return f"Auto désactivée · {heure} · {jours}"

    if faite_aujourdhui and derniere:
        return f"Auto {heure} · déjà faite aujourd'hui à {datetime.fromisoformat(derniere).strftime('%H:%M')}"

    return f"Auto {heure} · {jours} · en attente"


def actualiser_affichage_sync_auto():
    auto_sync_var.set(libelle_sync_auto())


def heure_sync_auto_atteinte(maintenant):
    heure = auto_sync_config.get("heure", "18:00")
    try:
        heure_cible, minute_cible = [int(partie) for partie in heure.split(":", 1)]
    except Exception:
        heure_cible, minute_cible = 18, 0

    return (
        maintenant.hour > heure_cible
        or (maintenant.hour == heure_cible and maintenant.minute >= minute_cible)
    )


def verifier_sync_auto():
    """Vérifie périodiquement si la synchronisation automatique doit partir."""

    if auto_sync_config.get("active", True):
        maintenant = datetime.now()
        date_jour = maintenant.strftime("%Y-%m-%d")

        jours_autorises = auto_sync_config.get("jours", [0, 1, 2, 3, 4, 5, 6])
        jour_autorise = maintenant.weekday() in jours_autorises
        deja_faite = auto_sync_config.get("derniere_date") == date_jour
        sync_occupee = netatmo_loading or str(sync_button["state"]) == "disabled"

        if jour_autorise and heure_sync_auto_atteinte(maintenant) and not deja_faite and not sync_occupee:
            lancer_sync_auto()

    actualiser_affichage_sync_auto()
    root.after(60000, verifier_sync_auto)


def lancer_sync_auto():
    """Lance la synchro du jour en réutilisant le bouton existant."""

    global auto_sync_en_cours

    if auto_sync_en_cours:
        return

    if netatmo_loading or str(sync_button["state"]) == "disabled":
        return

    auto_sync_en_cours = True
    status_var.set("📡 Synchronisation automatique en cours")
    synchroniser()


def appliquer_resultats_meteo(resultats):
    global netatmo_data, netatmo_public_data
    sauvegarde_ok = meteo_etat.appliquer(resultats)
    netatmo_data = meteo_etat.sources['privees']['data']
    netatmo_public_data = meteo_etat.sources['publiques']['data']
    actualiser_statut_meteo()
    if not sauvegarde_ok:
        netatmo_date_var.set(netatmo_date_var.get() + "\nCache non enregistré sur disque.")


def actualiser_statut_meteo():
    netatmo_status_var.set(
        f"{len(netatmo_data)} privée{'s' if len(netatmo_data) != 1 else ''} · "
        f"{len(netatmo_public_data)} publique{'s' if len(netatmo_public_data) != 1 else ''}")
    netatmo_date_var.set(meteo_etat.libelle())


def appliquer_palette(palette):

    global BG, CARD, TEXT, SECONDARY
    global GREEN, LIGHT_GREEN, ORANGE, LIGHT_ORANGE
    global RED, LIGHT_RED, BORDER, BLUE, LIGHT_BLUE

    BG = palette["BG"]
    CARD = palette["CARD"]
    TEXT = palette["TEXT"]
    SECONDARY = palette["SECONDARY"]
    GREEN = palette["GREEN"]
    LIGHT_GREEN = palette["LIGHT_GREEN"]
    ORANGE = palette["ORANGE"]
    LIGHT_ORANGE = palette["LIGHT_ORANGE"]
    RED = palette["RED"]
    LIGHT_RED = palette["LIGHT_RED"]
    BORDER = palette["BORDER"]
    BLUE = palette["BLUE"]
    LIGHT_BLUE = palette["LIGHT_BLUE"]


def basculer_theme():

    global theme_sombre_actif

    theme_sombre_actif = not theme_sombre_actif

    if theme_sombre_actif:
        appliquer_palette(THEME_SOMBRE)
        theme_button.config(
            text="☀️ Mode clair"
        )
    else:
        appliquer_palette(THEME_CLAIR)
        theme_button.config(
            text="🌙 Mode sombre"
        )

    appliquer_theme_interface()
    actualiser_interface()
    if not sauvegarder_theme_sombre(theme_sombre_actif):
        status_var.set("Thème appliqué · préférence non enregistrée")


def configurer_widget(widget, **options):

    try:
        widget.config(**options)
    except Exception:
        pass


def appliquer_theme_interface():

    root.configure(bg=BG)

    for widget in (
        header,
        toolbar,
        main_scroll_container,
        canvas,
        content_frame,
        footer,
        netatmo_frame
    ):
        configurer_widget(widget, bg=BG)

    configurer_widget(add_plant_button, bg=CARD, fg=TEXT, activebackground=CARD, activeforeground=TEXT)
    configurer_widget(add_sensor_button, bg=CARD, fg=TEXT, activebackground=CARD, activeforeground=TEXT)
    configurer_widget(settings_button, bg=CARD, fg=TEXT, activebackground=CARD, activeforeground=TEXT)
    configurer_widget(auto_sync_label, bg=BG, fg=SECONDARY)
    configurer_widget(header, bg=CARD, highlightbackground=BORDER)
    configurer_widget(footer, bg=CARD, highlightbackground=BORDER)
    configurer_widget(netatmo_frame, bg=CARD, highlightbackground=BORDER)
    configurer_widget(sync_frame, bg=LIGHT_BLUE, highlightbackground=BORDER)

    configurer_widget(
        refresh_button,
        bg=CARD,
        fg=TEXT,
        activebackground=CARD
    )

    configurer_widget(
        sync_button,
        bg=GREEN,
        fg="white",
        activebackground=GREEN,
        activeforeground="white"
    )

    configurer_widget(
        theme_button,
        bg=CARD,
        fg=TEXT,
        activebackground=CARD
    )

    for widget in header.winfo_children():
        configurer_widget(widget, bg=CARD, fg=GREEN)

    for widget in footer.winfo_children():
        configurer_widget(widget, bg=CARD, fg=SECONDARY)

    for widget in sync_frame.winfo_children():
        configurer_widget(widget, bg=LIGHT_BLUE, fg=TEXT)


def anciennete(date_heure):
    if not date_heure:
        return "Aucune donnée"

    try:
        dt = datetime.fromisoformat(date_heure)
        maintenant = datetime.now()

        secondes = max(
            0,
            int((maintenant - dt).total_seconds())
        )

        if secondes < 60:
            return (
                f"il y a {secondes} seconde"
                f"{'s' if secondes != 1 else ''}"
            )

        minutes = secondes // 60

        if minutes < 60:
            return (
                f"il y a {minutes} minute"
                f"{'s' if minutes != 1 else ''}"
            )

        heures = minutes // 60

        if heures < 24:
            return (
                f"il y a {heures} heure"
                f"{'s' if heures != 1 else ''}"
            )

        jours = heures // 24

        return (
            f"il y a {jours} jour"
            f"{'s' if jours != 1 else ''}"
        )

    except Exception:
        return "Ancienneté inconnue"


def obtenir_derniere_mesure(plante_id):

    mesures = database.get_mesures(
        plante_id=plante_id,
        limite=1
    )

    if not mesures:
        return None

    return mesures[0]


def obtenir_capteur_plante(plante_id):

    capteurs = database.get_capteurs()

    for capteur in capteurs:

        if capteur[3] == plante_id and capteur[8] == 1:
            return capteur

    return None


def obtenir_capteurs_plante(plante_id):

    return [
        capteur
        for capteur in database.get_capteurs()
        if capteur[3] == plante_id
    ]


def obtenir_derniere_synchronisation_capteur(capteur_id):

    mesures = database.get_mesures_capteur(
        capteur_id,
        limite=1
    )

    if not mesures:
        return None

    return mesures[0][1]


def determiner_etat_humidite(humidite):

    if humidite is None:
        return (
            "⚪ Pas de mesure",
            SECONDARY,
            BG
        )

    if humidite < 20:
        return (
            "🔴 Humidité très basse",
            RED,
            LIGHT_RED
        )

    if humidite < 30:
        return (
            "🟠 Humidité à surveiller",
            ORANGE,
            LIGHT_ORANGE
        )

    return (
        "🟢 Humidité correcte",
        GREEN,
        LIGHT_GREEN
    )


def analyser_lumiere_24h(plante_id):
    """
    Analyse simple de la lumiere recue sur les dernieres 24 heures.
    """

    mesures = database.get_mesures(
        plante_id=plante_id,
        limite=200
    )

    limite = datetime.now() - timedelta(hours=24)
    luminosites = []

    for mesure in mesures:

        date_heure = mesure[1]
        luminosite = mesure[4]

        if luminosite is None:
            continue

        try:
            date_mesure = datetime.fromisoformat(date_heure)
        except Exception:
            continue

        if date_mesure >= limite:
            luminosites.append(float(luminosite))

    if not luminosites:
        return {
            "etat": "inconnu",
            "message": "Lumière 24 h : pas assez de mesures",
            "detail": "Aucune mesure exploitable sur 24 h.",
            "couleur": SECONDARY,
            "fond": BG
        }

    moyenne = sum(luminosites) / len(luminosites)
    maximum = max(luminosites)
    mesures_utiles = sum(
        1
        for luminosite in luminosites
        if luminosite >= 1000
    )

    ratio_utile = mesures_utiles / len(luminosites)

    if maximum < 800 or moyenne < 250:
        message = "Lumière faible sur 24 h"
        detail = (
            f"Moyenne {moyenne:.0f} lux, pic {maximum:.0f} lux. "
            "Éclairage conseillé."
        )
        couleur = ORANGE
        fond = LIGHT_ORANGE

    elif ratio_utile < 0.25:
        message = "Lumière à surveiller"
        detail = (
            f"Moyenne {moyenne:.0f} lux, pic {maximum:.0f} lux. "
            "La plante reçoit peu de vraie lumière utile."
        )
        couleur = ORANGE
        fond = LIGHT_ORANGE

    else:
        message = "Lumière correcte aujourd'hui"
        detail = (
            f"Moyenne {moyenne:.0f} lux, pic {maximum:.0f} lux."
        )
        couleur = GREEN
        fond = LIGHT_GREEN

    return {
        "etat": "analyse",
        "message": message,
        "detail": detail,
        "moyenne": moyenne,
        "maximum": maximum,
        "nombre_mesures": len(luminosites),
        "couleur": couleur,
        "fond": fond
    }


def analyser_tendance_humidite(plante_id):
    """Analyse prudente de l'humidite, sans prediction si l'historique est trop court."""

    mesures = database.get_mesures(
        plante_id=plante_id,
        limite=80
    )

    points = []

    for mesure in mesures:
        date_heure = mesure[1]
        humidite = mesure[3]

        if humidite is None:
            continue

        try:
            points.append((datetime.fromisoformat(date_heure), float(humidite)))
        except Exception:
            continue

    if len(points) < 6:
        return {
            "etat": "insuffisant",
            "message": "Prévision 48-72 h : pas assez de données",
            "detail": "Quelques mesures supplémentaires sont nécessaires avant d'estimer une tendance fiable.",
            "couleur": SECONDARY,
            "fond": BG
        }

    points = sorted(points, key=lambda item: item[0])
    debut_date, debut_humidite = points[0]
    fin_date, fin_humidite = points[-1]
    duree_jours = max((fin_date - debut_date).total_seconds() / 86400, 0)

    if duree_jours < 1:
        return {
            "etat": "insuffisant",
            "message": "Prévision 48-72 h : historique trop court",
            "detail": "Il faut au moins une journée de recul pour éviter une fausse prévision.",
            "couleur": SECONDARY,
            "fond": BG
        }

    tendance = (fin_humidite - debut_humidite) / duree_jours

    if tendance < -3 and fin_humidite < 35:
        message = "Humidité en baisse"
        detail = f"Tendance environ {tendance:.1f} point/jour. À surveiller avant arrosage."
        couleur = ORANGE
        fond = LIGHT_ORANGE
    elif tendance < -1:
        message = "Humidité baisse doucement"
        detail = f"Tendance environ {tendance:.1f} point/jour. Pas d'urgence détectée."
        couleur = SECONDARY
        fond = BG
    else:
        message = "Pas de baisse inquiétante"
        detail = f"Tendance environ {tendance:.1f} point/jour. Prévision prudente seulement."
        couleur = GREEN
        fond = LIGHT_GREEN

    return {
        "etat": "analyse",
        "message": message,
        "detail": detail,
        "tendance": tendance,
        "couleur": couleur,
        "fond": fond
    }


def construire_decisions_plante(plante_id, mesure, analyse_lumiere):
    """Prépare les trois messages courts du tableau de bord plante."""

    if not mesure:
        return [
            ("À faire aujourd'hui", "Synchroniser ou associer un capteur pour obtenir les premières mesures.", BLUE, LIGHT_BLUE),
            ("À surveiller", "Aucune donnée plante exploitable pour le moment.", SECONDARY, BG),
            ("Prévision 48-72 h", "Pas assez de données pour prévoir sans inventer.", SECONDARY, BG),
        ]

    humidite = mesure[3]
    temperature = mesure[2]
    actions = []
    surveillances = []

    if humidite is None:
        surveillances.append("humidité du sol non mesurée")
    elif humidite < 20:
        actions.append("arrosage probablement nécessaire")
    elif humidite < 30:
        surveillances.append("humidité du sol basse")

    if temperature is not None and (temperature < 12 or temperature > 30):
        surveillances.append("température à contrôler")

    if analyse_lumiere.get("couleur") == ORANGE:
        surveillances.append("lumière faible ou irrégulière")

    tendance = analyser_tendance_humidite(plante_id)

    if actions:
        faire = ", ".join(actions).capitalize() + "."
        couleur_faire = RED if humidite is not None and humidite < 20 else ORANGE
        fond_faire = LIGHT_RED if couleur_faire == RED else LIGHT_ORANGE
    else:
        faire = "Aucune action urgente détectée avec les données actuelles."
        couleur_faire = GREEN
        fond_faire = LIGHT_GREEN

    if surveillances:
        surveiller = ", ".join(surveillances).capitalize() + "."
        couleur_surv = ORANGE
        fond_surv = LIGHT_ORANGE
    else:
        surveiller = "Rien de particulier à surveiller pour l'instant."
        couleur_surv = GREEN
        fond_surv = LIGHT_GREEN

    return [
        ("À faire aujourd'hui", faire, couleur_faire, fond_faire),
        ("À surveiller", surveiller, couleur_surv, fond_surv),
        ("Prévision 48-72 h", tendance["message"] + " · " + tendance["detail"], tendance["couleur"], tendance["fond"]),
    ]


def afficher_zone_decision(parent, plante_id, mesure, analyse_lumiere):
    """Affiche une synthèse simple avant les graphiques et mesures détaillées."""

    decisions = construire_decisions_plante(plante_id, mesure, analyse_lumiere)

    zone = tk.Frame(
        parent,
        bg=CARD
    )
    zone.pack(
        fill="x",
        padx=20,
        pady=(5, 10)
    )

    for titre, detail, couleur, fond in decisions:
        bloc = tk.Frame(
            zone,
            bg=fond,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        bloc.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8)
        )

        tk.Label(
            bloc,
            text=titre,
            font=("Segoe UI", 9, "bold"),
            fg=couleur,
            bg=fond,
            anchor="w"
        ).pack(
            fill="x",
            padx=10,
            pady=(8, 0)
        )

        tk.Label(
            bloc,
            text=detail,
            font=("Segoe UI", 9),
            fg=TEXT,
            bg=fond,
            anchor="nw",
            justify="left",
            wraplength=260
        ).pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(2, 8)
        )


def afficher_besoins_plante(parent, plante_id):
    besoins = database.get_besoins_plante(plante_id)
    if not besoins:
        return

    (
        _plante_id,
        type_plante,
        lumiere,
        arrosage,
        humidite_sol,
        temperature,
        notes,
        _image_url
    ) = besoins

    lignes = []
    if type_plante:
        lignes.append(f"Type : {type_plante}")
    if lumiere:
        lignes.append(f"☀️ Lumière : {lumiere}")
    if arrosage:
        lignes.append(f"💧 Arrosage : {arrosage}")
    if humidite_sol:
        lignes.append(f"🌱 Sol : {humidite_sol}")
    if temperature:
        lignes.append(f"🌡️ Température : {temperature}")
    if notes:
        lignes.append(f"📝 Note : {notes}")

    if not lignes:
        return

    bloc = tk.Frame(
        parent,
        bg=LIGHT_GREEN,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    bloc.pack(
        fill="x",
        padx=20,
        pady=(5, 10)
    )

    tk.Label(
        bloc,
        text="📋 Besoins de base",
        font=("Segoe UI", 10, "bold"),
        fg=GREEN,
        bg=LIGHT_GREEN,
        anchor="w"
    ).pack(
        fill="x",
        padx=12,
        pady=(8, 0)
    )

    tk.Label(
        bloc,
        text="\n".join(lignes),
        font=("Segoe UI", 9),
        fg=TEXT,
        bg=LIGHT_GREEN,
        anchor="w",
        justify="left",
        wraplength=900
    ).pack(
        fill="x",
        padx=12,
        pady=(3, 8)
    )


def afficher_resume_arrosage(parent, plante_id):
    dernier = database.get_dernier_arrosage(plante_id)
    rappel = database.get_rappel_arrosage_actif(plante_id)

    if not dernier and not rappel:
        return

    lignes = []

    if dernier:
        quantite = dernier[3]
        quantite_txt = f"{quantite:g} ml" if quantite is not None else "quantité non renseignée"
        lignes.append(f"Dernier arrosage : {formater_date(dernier[2])} · {quantite_txt}")

    if rappel:
        texte_rappel = f"Rappel prévu : {formater_date(rappel[8])}"
        if plante_avec_rappel_email(plante_id):
            texte_rappel += " · mail prévu quand l'envoi sera configuré"
        lignes.append(texte_rappel)

    bloc = tk.Frame(parent, bg=LIGHT_BLUE, highlightbackground=BORDER, highlightthickness=1)
    bloc.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(
        bloc,
        text="💧 Arrosage",
        font=("Segoe UI", 10, "bold"),
        fg=BLUE,
        bg=LIGHT_BLUE,
        anchor="w"
    ).pack(fill="x", padx=12, pady=(8, 0))

    tk.Label(
        bloc,
        text="\n".join(lignes),
        font=("Segoe UI", 9),
        fg=TEXT,
        bg=LIGHT_BLUE,
        anchor="w",
        justify="left"
    ).pack(fill="x", padx=12, pady=(3, 8))


def ouvrir_arrosage_plante(plante_id, nom_plante):
    fenetre = tk.Toplevel(root)
    fenetre.title("Arrosage")
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()

    tk.Label(
        fenetre,
        text=f"💧 Arrosage · {nom_plante}",
        font=("Segoe UI", 15, "bold"),
        fg=TEXT,
        bg=CARD
    ).pack(anchor="w", padx=20, pady=(16, 8))

    tk.Label(fenetre, text="Quantité en ml", bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(6, 3))
    quantite_entry = tk.Entry(fenetre, width=42, bg=BG, fg=TEXT, insertbackground=TEXT)
    quantite_entry.pack(fill="x", padx=20)

    tk.Label(fenetre, text="Type", bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 3))
    type_combo = ttk.Combobox(fenetre, state="readonly", values=["normal", "fertilisant"], width=39)
    type_combo.pack(fill="x", padx=20)
    type_combo.current(0)

    tk.Label(fenetre, text="Commentaire", bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 3))
    commentaire_entry = tk.Entry(fenetre, width=42, bg=BG, fg=TEXT, insertbackground=TEXT)
    commentaire_entry.pack(fill="x", padx=20)

    rappel_var = tk.BooleanVar(value=False)
    tk.Checkbutton(
        fenetre,
        text="Programmer un rappel",
        variable=rappel_var,
        bg=CARD,
        fg=TEXT,
        activebackground=CARD,
        activeforeground=TEXT,
        selectcolor=BG
    ).pack(anchor="w", padx=20, pady=(12, 3))

    rappel_frame = tk.Frame(fenetre, bg=CARD)
    rappel_frame.pack(fill="x", padx=20)
    tk.Label(rappel_frame, text="Dans", bg=CARD, fg=TEXT).pack(side="left")
    rappel_jours_entry = tk.Entry(rappel_frame, width=6, bg=BG, fg=TEXT, insertbackground=TEXT)
    rappel_jours_entry.pack(side="left", padx=6)
    rappel_jours_entry.insert(0, "7")
    tk.Label(rappel_frame, text="jours", bg=CARD, fg=TEXT).pack(side="left")

    erreur = tk.StringVar()
    tk.Label(fenetre, textvariable=erreur, bg=CARD, fg=RED, wraplength=390).pack(fill="x", padx=20, pady=8)

    def enregistrer():
        quantite_txt = quantite_entry.get().strip().replace(",", ".")
        quantite = None
        if quantite_txt:
            try:
                quantite = float(quantite_txt)
                if quantite < 0:
                    raise ValueError()
            except ValueError:
                erreur.set("Quantité invalide. Exemple : 250")
                return

        rappel_date = None
        if rappel_var.get():
            try:
                jours = int(rappel_jours_entry.get().strip())
                if jours <= 0:
                    raise ValueError()
                rappel_date = (datetime.now() + timedelta(days=jours)).isoformat(timespec="seconds")
            except ValueError:
                erreur.set("Nombre de jours invalide pour le rappel.")
                return

        commentaire = commentaire_entry.get().strip() or None

        try:
            database.enregistrer_arrosage_plante(
                plante_id,
                datetime.now().isoformat(timespec="seconds"),
                quantite_ml=quantite,
                type_arrosage=type_combo.get(),
                commentaire=commentaire,
                rappel_date=rappel_date
            )
        except Exception:
            erreur.set("Impossible d'enregistrer l'arrosage.")
            return

        fenetre.destroy()
        actualiser_interface()
        if rappel_date:
            status_var.set(f"Arrosage enregistré · rappel prévu le {formater_date(rappel_date)}")
        else:
            status_var.set("Arrosage enregistré.")

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", padx=20, pady=(0, 15))
    tk.Button(boutons, text="Enregistrer", command=enregistrer, bg=LIGHT_GREEN, fg=TEXT, activebackground=LIGHT_GREEN, relief="flat", cursor="hand2").pack(side="right")
    tk.Button(boutons, text="Annuler", command=fenetre.destroy, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left")

    quantite_entry.focus_set()



# ============================================================
# WIDGET VALEUR
# ============================================================

def creer_valeur(parent, titre, valeur):

    bloc = tk.Frame(
        parent,
        bg=CARD
    )

    bloc.pack(
        side="left",
        expand=True,
        fill="x",
        padx=5
    )

    tk.Label(
        bloc,
        text=titre,
        font=("Segoe UI", 9),
        fg=SECONDARY,
        bg=CARD
    ).pack()

    tk.Label(
        bloc,
        text=valeur,
        font=("Segoe UI", 14, "bold"),
        fg=TEXT,
        bg=CARD
    ).pack(
        pady=(2, 0)
    )

    return bloc


# ============================================================
# CARTE PLANTE
# ============================================================

def alerte_principale_plante(plante_id):
    try:
        plante = database.get_plante(plante_id)
        alertes = construire_alertes([plante]) if plante else []
    except Exception:
        alertes = []
    for niveau in ("danger", "attention", "info"):
        for alerte in alertes:
            if alerte["niveau"] == niveau:
                return alerte
    return None


def valeur_filtre_plante(valeur):
    if valeur is None:
        return "Non renseigné"
    texte = str(valeur).strip()
    return texte if texte else "Non renseigné"


def options_filtre_plantes(plantes, index):
    valeurs = sorted({valeur_filtre_plante(plante[index]) for plante in plantes}, key=str.casefold)
    return ["Toutes"] + valeurs


def plante_passe_filtres(plante):
    plante_id, nom, espece, emplacement, zone = plante

    if filtre_zone_var.get() != "Toutes" and valeur_filtre_plante(zone) != filtre_zone_var.get():
        return False

    if filtre_piece_var.get() != "Toutes" and valeur_filtre_plante(emplacement) != filtre_piece_var.get():
        return False

    capteur = obtenir_capteur_plante(plante_id)
    filtre_capteur = filtre_capteur_var.get()
    if filtre_capteur == "Avec capteur" and not capteur:
        return False
    if filtre_capteur == "Sans capteur" and capteur:
        return False

    filtre_attention = filtre_attention_var.get()
    if filtre_attention == "À surveiller" and not alerte_principale_plante(plante_id):
        return False

    return True


def reinitialiser_filtres_plantes():
    filtre_zone_var.set("Toutes")
    filtre_piece_var.set("Toutes")
    filtre_capteur_var.set("Toutes")
    filtre_attention_var.set("Toutes")
    actualiser_interface()


def creer_menu_filtre(parent, titre, variable, valeurs):
    bloc = tk.Frame(parent, bg=CARD)
    bloc.pack(side="left", padx=(0, 10), pady=(0, 8))

    tk.Label(
        bloc,
        text=titre,
        bg=CARD,
        fg=SECONDARY,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w")

    menu = tk.OptionMenu(bloc, variable, *valeurs, command=lambda _=None: actualiser_interface())
    menu.configure(
        bg=BG,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        activeforeground=TEXT,
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
        cursor="hand2",
        width=13
    )
    menu["menu"].configure(bg=CARD, fg=TEXT)
    menu.pack(anchor="w")


def afficher_filtres_plantes(parent, plantes, plantes_filtrees):
    bloc = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    bloc.pack(fill="x", padx=20, pady=(0, 10))

    haut = tk.Frame(bloc, bg=CARD)
    haut.pack(fill="x", padx=14, pady=(10, 4))

    tk.Label(
        haut,
        text="🔎 Filtrer les plantes",
        font=("Segoe UI", 11, "bold"),
        fg=GREEN,
        bg=CARD
    ).pack(side="left")

    tk.Label(
        haut,
        text=f"{len(plantes_filtrees)} / {len(plantes)} affichée(s)",
        font=("Segoe UI", 8),
        fg=SECONDARY,
        bg=CARD
    ).pack(side="right")

    ligne = tk.Frame(bloc, bg=CARD)
    ligne.pack(fill="x", padx=14, pady=(0, 8))

    creer_menu_filtre(ligne, "Zone", filtre_zone_var, options_filtre_plantes(plantes, 4))
    creer_menu_filtre(ligne, "Pièce", filtre_piece_var, options_filtre_plantes(plantes, 3))
    creer_menu_filtre(ligne, "Capteur", filtre_capteur_var, ["Toutes", "Avec capteur", "Sans capteur"])
    creer_menu_filtre(ligne, "État", filtre_attention_var, ["Toutes", "À surveiller"])

    tk.Button(
        ligne,
        text="Réinitialiser",
        command=reinitialiser_filtres_plantes,
        bg=BG,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        relief="flat",
        cursor="hand2"
    ).pack(side="right", pady=(13, 8))


def creer_carte_plante_compacte(parent, plante):
    plante_id, nom, espece, emplacement, zone = plante
    mesure = obtenir_derniere_mesure(plante_id)
    capteur = obtenir_capteur_plante(plante_id)
    dernier = database.get_dernier_arrosage(plante_id)
    rappel = database.get_rappel_arrosage_actif(plante_id)
    alerte = alerte_principale_plante(plante_id)

    carte = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    carte.pack(fill="x", padx=20, pady=6)

    ligne = tk.Frame(carte, bg=CARD)
    ligne.pack(fill="x", padx=14, pady=(10, 8))

    tk.Label(ligne, text=f"🌿 {nom}", font=("Segoe UI", 13, "bold"), fg=TEXT, bg=CARD, anchor="w").pack(side="left")

    details = []
    if espece:
        details.append(espece)
    if zone:
        details.append(zone)
    elif emplacement:
        details.append(emplacement)
    if details:
        tk.Label(ligne, text=" • ".join(details), font=("Segoe UI", 8), fg=SECONDARY, bg=CARD).pack(side="left", padx=10)

    if capteur:
        etat_capteur = "📡 capteur actif"
        couleur_capteur = GREEN
    else:
        etat_capteur = "⚪ sans capteur"
        couleur_capteur = BLUE
    tk.Label(ligne, text=etat_capteur, font=("Segoe UI", 8, "bold"), fg=couleur_capteur, bg=CARD).pack(side="right")

    ligne2 = tk.Frame(carte, bg=CARD)
    ligne2.pack(fill="x", padx=14, pady=(0, 8))

    if mesure:
        date_heure = mesure[1]
        humidite = mesure[3]
        luminosite = mesure[4]
        humidite_txt = f"{humidite:.0f} %" if humidite is not None else "—"
        lumiere_txt = f"{luminosite:.0f} lux" if luminosite is not None else "—"
        mesure_txt = anciennete(date_heure)
    else:
        humidite_txt = "—"
        lumiere_txt = "—"
        mesure_txt = "aucune mesure"

    infos = [
        ("💧 Sol", humidite_txt),
        ("☀️ Lumière", lumiere_txt),
        ("🕐 Mesure", mesure_txt),
    ]

    if dernier:
        infos.append(("💦 Arrosage", formater_date(dernier[2])))
    if rappel and rappel[8]:
        infos.append(("🔔 Rappel", formater_date(rappel[8])))

    for titre, valeur in infos:
        bloc = tk.Frame(ligne2, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        bloc.pack(side="left", expand=True, fill="x", padx=(0, 6))
        tk.Label(bloc, text=titre, font=("Segoe UI", 8), fg=SECONDARY, bg=BG).pack(pady=(4, 0))
        tk.Label(bloc, text=valeur, font=("Segoe UI", 9, "bold"), fg=TEXT, bg=BG, wraplength=150, justify="center").pack(pady=(0, 5))

    if alerte:
        alerte_frame = tk.Frame(carte, bg=alerte["fond"])
        alerte_frame.pack(fill="x", padx=14, pady=(0, 8))
        tk.Label(alerte_frame, text=f"{alerte['titre']} · {alerte['detail']}", font=("Segoe UI", 9, "bold"), fg=alerte["couleur"], bg=alerte["fond"], anchor="w", wraplength=950, justify="left").pack(fill="x", padx=8, pady=6)

    boutons = tk.Frame(carte, bg=CARD)
    boutons.pack(fill="x", padx=14, pady=(0, 10))
    tk.Button(boutons, text="💧 Arrosage", font=("Segoe UI", 8, "bold"), bg=LIGHT_BLUE, fg=BLUE, relief="flat", cursor="hand2", command=lambda pid=plante_id, n=nom: ouvrir_arrosage_plante(pid, n)).pack(side="left", padx=(0, 8))
    tk.Button(boutons, text="🔎 Analyse", font=("Segoe UI", 8, "bold"), bg=LIGHT_GREEN, fg=GREEN, relief="flat", cursor="hand2", command=lambda pid=plante_id: afficher_message_analyse(pid)).pack(side="left")


def creer_carte_plante(parent, plante):

    (
        plante_id,
        nom,
        espece,
        emplacement,
        zone
    ) = plante

    carte = tk.Frame(
        parent,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    carte.pack(
        fill="x",
        padx=20,
        pady=10
    )

    # --------------------------------------------------------
    # En-tête
    # --------------------------------------------------------

    entete = tk.Frame(
        carte,
        bg=CARD
    )

    entete.pack(
        fill="x",
        padx=20,
        pady=(15, 5)
    )

    tk.Label(
        entete,
        text=f"🌿 {nom}",
        font=("Segoe UI", 17, "bold"),
        fg=TEXT,
        bg=CARD
    ).pack(
        side="left"
    )

    details = []

    if espece:
        details.append(espece)

    if emplacement:
        details.append(emplacement)

    if zone:
        details.append(zone)

    if details:

        tk.Label(
            entete,
            text=" • ".join(details),
            font=("Segoe UI", 9),
            fg=SECONDARY,
            bg=CARD
        ).pack(
            side="left",
            padx=15
        )

    afficher_besoins_plante(
        carte,
        plante_id
    )

    afficher_resume_arrosage(
        carte,
        plante_id
    )

    # --------------------------------------------------------
    # Mesures et decision
    # --------------------------------------------------------

    mesure = obtenir_derniere_mesure(plante_id)
    analyse_lumiere = analyser_lumiere_24h(plante_id)

    afficher_zone_decision(
        carte,
        plante_id,
        mesure,
        analyse_lumiere
    )

    ligne_mesures = tk.Frame(
        carte,
        bg=CARD
    )

    ligne_mesures.pack(
        fill="x",
        padx=15,
        pady=10
    )

    if mesure:

        date_heure = mesure[1]
        temperature = mesure[2]
        humidite = mesure[3]
        luminosite = mesure[4]
        conductivite = mesure[5]

        temp_txt = (
            f"{temperature:.1f} °C"
            if temperature is not None
            else "—"
        )

        humidite_txt = (
            f"{humidite:.0f} %"
            if humidite is not None
            else "—"
        )

        luminosite_txt = (
            f"{luminosite:.0f} lux"
            if luminosite is not None
            else "—"
        )

        conductivite_txt = (
            f"{conductivite:.0f} µS/cm"
            if conductivite is not None
            else "—"
        )

    else:

        date_heure = None
        humidite = None

        temp_txt = "—"
        humidite_txt = "—"
        luminosite_txt = "—"
        conductivite_txt = "—"

    creer_valeur(
        ligne_mesures,
        "🌡️ Température",
        temp_txt
    )

    creer_valeur(
        ligne_mesures,
        "💧 Humidité",
        humidite_txt
    )

    creer_valeur(
        ligne_mesures,
        "☀️ Luminosité",
        luminosite_txt
    )

    creer_valeur(
        ligne_mesures,
        "🧪 Conductivité",
        conductivite_txt
    )

    # --------------------------------------------------------
    # État humidité
    # --------------------------------------------------------

    etat, couleur, fond = determiner_etat_humidite(
        humidite
    )

    etat_frame = tk.Frame(
        carte,
        bg=fond
    )

    etat_frame.pack(
        fill="x",
        padx=20,
        pady=(0, 10)
    )

    tk.Label(
        etat_frame,
        text=etat,
        font=("Segoe UI", 10, "bold"),
        fg=couleur,
        bg=fond,
        anchor="w"
    ).pack(
        fill="x",
        padx=12,
        pady=8
    )

    # --------------------------------------------------------
    # Lumiere sur 24 h
    # --------------------------------------------------------

    lumiere_frame = tk.Frame(
        carte,
        bg=analyse_lumiere["fond"]
    )

    lumiere_frame.pack(
        fill="x",
        padx=20,
        pady=(0, 10)
    )

    tk.Label(
        lumiere_frame,
        text=f"☀️ {analyse_lumiere['message']}",
        font=("Segoe UI", 10, "bold"),
        fg=analyse_lumiere["couleur"],
        bg=analyse_lumiere["fond"],
        anchor="w"
    ).pack(
        fill="x",
        padx=12,
        pady=(8, 0)
    )

    tk.Label(
        lumiere_frame,
        text=analyse_lumiere["detail"],
        font=("Segoe UI", 9),
        fg=SECONDARY,
        bg=analyse_lumiere["fond"],
        anchor="w"
    ).pack(
        fill="x",
        padx=12,
        pady=(2, 8)
    )

    # --------------------------------------------------------
    # Capteur
    # --------------------------------------------------------

    capteur = obtenir_capteur_plante(plante_id)

    capteur_frame = tk.Frame(
        carte,
        bg=CARD
    )

    capteur_frame.pack(
        fill="x",
        padx=20,
        pady=(0, 5)
    )

    if capteur:

        capteur_id = capteur[0]
        nom_capteur = capteur[1]
        adresse_ble = capteur[2]

        tk.Label(
            capteur_frame,
            text=f"📡 {nom_capteur}",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT,
            bg=CARD,
            anchor="w"
        ).pack(
            fill="x"
        )

        tk.Label(
            capteur_frame,
            text=f"Adresse : {adresse_ble}",
            font=("Segoe UI", 8),
            fg=SECONDARY,
            bg=CARD,
            anchor="w"
        ).pack(
            fill="x"
        )

        infos = lire_infos(adresse_ble)
        texte_batterie, couleur_batterie, fond_batterie = etat_batterie_capteur(infos)
        batterie_frame = tk.Frame(capteur_frame, bg=fond_batterie, highlightbackground=BORDER, highlightthickness=1)
        batterie_frame.pack(fill="x", pady=(5, 4))
        tk.Label(batterie_frame, text=texte_batterie, font=("Segoe UI", 9, "bold"),
                 fg=couleur_batterie, bg=fond_batterie, anchor="w", wraplength=800,
                 justify="left").pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(batterie_frame, text="Firmware : " + (infos.get("firmware") or "non lu"), font=("Segoe UI", 8),
                 fg=SECONDARY, bg=fond_batterie, anchor="w", wraplength=800,
                 justify="left").pack(fill="x", padx=10, pady=(0, 6))
        date_infos = infos.get("derniere_tentative")
        if date_infos:
            indication = "Dernière lecture : " + formater_date(date_infos)
            if not infos.get("lecture_complete"):
                indication += " · lecture incomplète, dernières valeurs conservées"
        else:
            indication = "Batterie et firmware disponibles après la prochaine synchronisation."
        tk.Label(capteur_frame, text=indication, font=("Segoe UI", 8),
                 fg=SECONDARY, bg=CARD, anchor="w", wraplength=800,
                 justify="left").pack(fill="x")
        tk.Button(capteur_frame, text="Détails du capteur", bg=LIGHT_BLUE, fg=TEXT,
                  activebackground=LIGHT_BLUE, activeforeground=TEXT, relief="flat",
                  cursor="hand2", command=lambda a=adresse_ble, n=nom_capteur:
                  afficher_details_capteur(a, n)).pack(anchor="w", pady=(4, 5))

        tk.Label(
            capteur_frame,
            text=texte_dernier_import_historique(capteur_id),
            font=("Segoe UI", 8),
            fg=SECONDARY,
            bg=CARD,
            anchor="w",
            wraplength=850,
            justify="left"
        ).pack(fill="x", pady=(0, 4))

        derniere_sync = (
            obtenir_derniere_synchronisation_capteur(
                capteur_id
            )
        )

        if derniere_sync:

            tk.Label(
                capteur_frame,
                text=(
                    "🟢 Données disponibles · "
                    f"{anciennete(derniere_sync)}"
                ),
                font=("Segoe UI", 9, "bold"),
                fg=GREEN,
                bg=CARD,
                anchor="w"
            ).pack(
                fill="x",
                pady=(4, 0)
            )

            tk.Label(
                capteur_frame,
                text=(
                    "Dernière synchronisation : "
                    f"{formater_date(derniere_sync)}"
                ),
                font=("Segoe UI", 9),
                fg=SECONDARY,
                bg=CARD,
                anchor="w"
            ).pack(
                fill="x"
            )

        else:

            tk.Label(
                capteur_frame,
                text="⚪ Aucune synchronisation",
                font=("Segoe UI", 9),
                fg=SECONDARY,
                bg=CARD,
                anchor="w"
            ).pack(
                fill="x",
                pady=(4, 0)
            )

    else:

        capteurs_historique = [
            capteur
            for capteur in obtenir_capteurs_plante(plante_id)
            if not capteur[8]
        ]

        if capteurs_historique:
            texte_capteur = (
                "📡 Aucun capteur actif · "
                f"{len(capteurs_historique)} ancien"
                f"{'s' if len(capteurs_historique) != 1 else ''} "
                "conservé"
            )
            couleur_capteur = ORANGE
            fond_capteur = LIGHT_ORANGE
        else:
            texte_capteur = (
                "📡 Aucun capteur actif · prêt pour une association"
            )
            couleur_capteur = BLUE
            fond_capteur = LIGHT_BLUE

        etat_capteur_frame = tk.Frame(
            capteur_frame,
            bg=fond_capteur
        )

        etat_capteur_frame.pack(
            fill="x"
        )

        tk.Label(
            etat_capteur_frame,
            text=texte_capteur,
            font=("Segoe UI", 9, "bold"),
            fg=couleur_capteur,
            bg=fond_capteur,
            anchor="w"
        ).pack(
            fill="x",
            padx=12,
            pady=8
        )

    # --------------------------------------------------------
    # Dernière mesure
    # --------------------------------------------------------

    tk.Label(
        carte,
        text=(
            f"🕐 Dernière mesure : "
            f"{formater_date(date_heure)}"
        ),
        font=("Segoe UI", 9),
        fg=SECONDARY,
        bg=CARD,
        anchor="w"
    ).pack(
        fill="x",
        padx=20,
        pady=(5, 10)
    )

    # --------------------------------------------------------
    # Boutons
    # --------------------------------------------------------

    boutons = tk.Frame(
        carte,
        bg=CARD
    )

    boutons.pack(
        fill="x",
        padx=20,
        pady=(0, 15)
    )

    tk.Button(
        boutons,
        text="🔎 Voir l'analyse",
        font=("Segoe UI", 9, "bold"),
        bg=LIGHT_GREEN,
        fg=GREEN,
        activebackground=LIGHT_GREEN,
        relief="flat",
        cursor="hand2",
        command=lambda pid=plante_id:
            afficher_message_analyse(pid)
    ).pack(
        side="left",
        padx=(0, 8)
    )

    tk.Button(
        boutons,
        text="💧 Arrosage",
        font=("Segoe UI", 9, "bold"),
        bg=LIGHT_BLUE,
        fg=TEXT,
        activebackground=LIGHT_BLUE,
        activeforeground=TEXT,
        relief="flat",
        cursor="hand2",
        command=lambda pid=plante_id, nom=nom:
            ouvrir_arrosage_plante(pid, nom)
    ).pack(
        side="left",
        padx=(0, 8)
    )

    tk.Button(
        boutons,
        text="📈 Historique",
        font=("Segoe UI", 9, "bold"),
        bg=LIGHT_BLUE,
        fg=TEXT,
        activebackground=LIGHT_BLUE,
        activeforeground=TEXT,
        relief="flat",
        cursor="hand2",
        command=lambda pid=plante_id:
            afficher_message_historique(pid)
    ).pack(
        side="left"
    )

    if capteur is not None:

        tk.Button(
            boutons,
            text="📥 Importer historique Mi Flora",
            font=("Segoe UI", 9, "bold"),
            bg=LIGHT_GREEN,
            fg=GREEN,
            activebackground=LIGHT_GREEN,
            activeforeground=GREEN,
            relief="flat",
            cursor="hand2",
            command=lambda pid=plante_id, nom=nom:
                importer_historique_miflora_plante(pid, nom)
        ).pack(
            side="left",
            padx=(8, 0)
        )

    if capteur is None:

        tk.Button(
            boutons,
            text="＋ Associer un capteur",
            font=("Segoe UI", 9, "bold"),
            bg=LIGHT_BLUE,
            fg=TEXT,
            activebackground=LIGHT_BLUE,
            activeforeground=TEXT,
            relief="flat",
            cursor="hand2",
            command=ouvrir_ajout_capteur
        ).pack(
            side="left",
            padx=(8, 0)
        )


# ============================================================
# CARTE METEO NETATMO
# ============================================================

def charger_cache_prevision_2h():
    try:
        data = lire_json(PREVISION_CACHE)
        if isinstance(data, dict):
            return data
    except RuntimeError:
        pass
    return None


def sauvegarder_cache_prevision_2h(data):
    if not isinstance(data, dict):
        return False
    try:
        PREVISION_CACHE.parent.mkdir(parents=True, exist_ok=True)
        ecrire_json(PREVISION_CACHE, data)
        return True
    except (OSError, RuntimeError):
        return False


def recuperer_prevision_2h_avec_cache():
    global prevision_2h_data, prevision_2h_error

    try:
        data = previsions_meteo.recuperer_prevision_2h()
        prevision_2h_data = data
        prevision_2h_error = None
        sauvegarder_cache_prevision_2h(data)
    except RuntimeError as probleme:
        prevision_2h_error = str(probleme)
        if prevision_2h_data is None:
            prevision_2h_data = charger_cache_prevision_2h()
    except Exception:
        prevision_2h_error = "Prévision +2 h indisponible"
        if prevision_2h_data is None:
            prevision_2h_data = charger_cache_prevision_2h()


def formater_prevision_valeur(valeur, unite=""):
    if valeur is None:
        return "—"
    try:
        if isinstance(valeur, float):
            if valeur.is_integer():
                return f"{int(valeur)}{unite}"
            return f"{valeur:.1f}{unite}"
        return f"{valeur}{unite}"
    except Exception:
        return f"{valeur}{unite}"


def afficher_prevision_2h(parent):
    bloc = tk.Frame(parent, bg=LIGHT_BLUE, highlightbackground=BORDER, highlightthickness=1)
    bloc.pack(fill="x", padx=20, pady=(12, 8))

    entete = tk.Frame(bloc, bg=LIGHT_BLUE)
    entete.pack(fill="x", padx=12, pady=(8, 2))

    tk.Label(entete, text="🔮 Prévision locale +2 h", font=("Segoe UI", 11, "bold"), fg=BLUE, bg=LIGHT_BLUE).pack(side="left")

    source = prevision_2h_data.get("source", "Météo locale") if prevision_2h_data else "Météo locale"
    tk.Label(entete, text=source, font=("Segoe UI", 8), fg=SECONDARY, bg=LIGHT_BLUE).pack(side="right")

    if not prevision_2h_data:
        message = prevision_2h_error or "Prévision non chargée pour le moment."
        tk.Label(bloc, text=message, font=("Segoe UI", 9), fg=SECONDARY, bg=LIGHT_BLUE, anchor="w", wraplength=900, justify="left").pack(fill="x", padx=12, pady=(2, 10))
        return

    pluie = formater_prevision_valeur(prevision_2h_data.get("pluie_2h"), " mm")
    intensite = formater_prevision_valeur(prevision_2h_data.get("intensite_max"), " mm/h")
    temperature_debut = formater_prevision_valeur(prevision_2h_data.get("temperature_debut"), " °C")
    temperature_fin = formater_prevision_valeur(prevision_2h_data.get("temperature_fin"), " °C")
    temperature = f"{temperature_debut} → {temperature_fin}"
    vent = formater_prevision_valeur(prevision_2h_data.get("vent"), " km/h")
    rafale = formater_prevision_valeur(prevision_2h_data.get("rafale"), " km/h")
    ciel = prevision_2h_data.get("lumiere") or "—"

    creer_ligne_netatmo_compacte(bloc, [
        ("🌧️ Pluie 2 h", pluie),
        ("☔ Max", intensite),
        ("🌡️ Température", temperature),
        ("💨 Vent", vent),
        ("💨 Rafales", rafale),
        ("☁️ Ciel", ciel),
    ])

    message = prevision_2h_data.get("message_pluie") or "Prévision locale chargée."
    if prevision_2h_error:
        message += " · Donnée affichée depuis le cache."

    tk.Label(bloc, text=message, font=("Segoe UI", 9, "bold"), fg=TEXT, bg=LIGHT_BLUE, anchor="w", wraplength=900, justify="left").pack(fill="x", padx=12, pady=(0, 10))


def charger_preferences_netatmo():
    preferences = {
        "noms": {},
        "ordre_favoris": []
    }

    try:
        if NETATMO_UI_CONFIG.exists():
            donnees = lire_json(NETATMO_UI_CONFIG)
            if isinstance(donnees, dict):
                preferences.update(donnees)
    except RuntimeError:
        pass

    if not isinstance(preferences.get("noms"), dict):
        preferences["noms"] = {}

    if not isinstance(preferences.get("ordre_favoris"), list):
        preferences["ordre_favoris"] = []

    return preferences


def sauvegarder_preferences_netatmo():
    try:
        ecrire_json(NETATMO_UI_CONFIG, netatmo_preferences)
        return True
    except (OSError, RuntimeError):
        return False


def id_station_netatmo(station):
    return station.get("id") or station.get("_id") or station.get("station_id")


def nom_station_netatmo(station):
    station_id = id_station_netatmo(station)
    nom_local = netatmo_preferences.get("noms", {}).get(station_id)
    return nom_local or station.get("nom") or "Station publique"


def trier_favoris_netatmo(stations):
    ordre = netatmo_preferences.get("ordre_favoris", [])
    rang = {station_id: index for index, station_id in enumerate(ordre)}
    return sorted(
        stations,
        key=lambda station: (
            rang.get(id_station_netatmo(station), 9999),
            station.get("distance_m") if station.get("distance_m") is not None else 999999
        )
    )


def deplacer_favori_netatmo(station_id, direction):
    if not station_id:
        return

    favoris = [id_station_netatmo(station) for station in netatmo_public_data if station.get("favorite")]
    favoris = [station for station in favoris if station]
    ordre = [station for station in netatmo_preferences.get("ordre_favoris", []) if station in favoris]

    for station in favoris:
        if station not in ordre:
            ordre.append(station)

    if station_id not in ordre:
        return

    index = ordre.index(station_id)
    nouveau = index + direction

    if nouveau < 0 or nouveau >= len(ordre):
        return

    ordre[index], ordre[nouveau] = ordre[nouveau], ordre[index]
    netatmo_preferences["ordre_favoris"] = ordre
    sauvegarder_preferences_netatmo()
    afficher_netatmo()


def ajouter_favori_netatmo_config(station_saisie, nom_local=""):
    station_id = normaliser_station_favorite(station_saisie)
    if not station_id:
        return False, "Colle un identifiant Netatmo ou un lien weathermap."

    try:
        config = lire_json(LOCAL_CONFIG)
    except RuntimeError:
        config = {}

    netatmo_public = config.setdefault("netatmo_public", {})
    favoris = netatmo_public.setdefault("stations_favorites", [])
    if not isinstance(favoris, list):
        favoris = []

    favoris_normalises = []
    for favori in favoris:
        favori_normalise = normaliser_station_favorite(favori)
        if favori_normalise and favori_normalise not in favoris_normalises:
            favoris_normalises.append(favori_normalise)

    deja_present = station_id in favoris_normalises
    if not deja_present:
        favoris_normalises.append(station_id)

    netatmo_public["stations_favorites"] = favoris_normalises

    try:
        ecrire_json(LOCAL_CONFIG, config)
    except RuntimeError:
        return False, "Impossible d'enregistrer le favori Netatmo."

    if nom_local.strip():
        netatmo_preferences.setdefault("noms", {})[station_id] = nom_local.strip()
        sauvegarder_preferences_netatmo()

    if station_id not in netatmo_preferences.get("ordre_favoris", []):
        netatmo_preferences.setdefault("ordre_favoris", []).append(station_id)
        sauvegarder_preferences_netatmo()

    if deja_present:
        return True, "Station déjà présente dans les favoris Botaneo."

    return True, "Station ajoutée aux favoris Botaneo. Lance Actualiser Netatmo pour charger ses données."


def renommer_station_netatmo(station):
    station_id = id_station_netatmo(station)
    if not station_id:
        messagebox.showinfo("Netatmo", "Cette station n'a pas d'identifiant local utilisable.", parent=root)
        return

    fenetre = tk.Toplevel(root)
    fenetre.title("Renommer la station")
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()

    tk.Label(
        fenetre,
        text="Nom local de la station",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 9, "bold")
    ).pack(anchor="w", padx=20, pady=(15, 3))

    entree = tk.Entry(
        fenetre,
        width=45,
        bg=BG,
        fg=TEXT,
        insertbackground=TEXT
    )
    entree.pack(padx=20, fill="x")
    entree.insert(0, nom_station_netatmo(station))

    erreur = tk.StringVar()
    tk.Label(fenetre, textvariable=erreur, bg=CARD, fg=RED).pack(padx=20, pady=8)

    def enregistrer():
        nouveau_nom = entree.get().strip()
        if not nouveau_nom:
            erreur.set("Le nom ne peut pas être vide.")
            return
        netatmo_preferences.setdefault("noms", {})[station_id] = nouveau_nom
        sauvegarder_preferences_netatmo()
        fenetre.destroy()
        afficher_netatmo()

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", pady=(0, 10))

    tk.Button(
        boutons,
        text="Enregistrer",
        command=enregistrer,
        bg=LIGHT_GREEN,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        relief="flat",
        cursor="hand2"
    ).pack(side="right", padx=20, pady=10)

    tk.Button(
        boutons,
        text="Annuler",
        command=fenetre.destroy,
        bg=BG,
        fg=TEXT,
        relief="flat",
        cursor="hand2"
    ).pack(side="left", padx=20, pady=10)

    entree.focus_set()
    entree.selection_range(0, "end")


def basculer_section_netatmo(cle):
    netatmo_sections_ouvertes[cle] = not netatmo_sections_ouvertes.get(cle, True)
    afficher_netatmo()


def creer_titre_netatmo_repliable(parent, cle, titre, sous_titre=None, nombre=None):
    ouvert = netatmo_sections_ouvertes.get(cle, True)
    libelle = ("▼ " if ouvert else "▶ ") + titre
    if nombre is not None:
        libelle += f" ({nombre})"

    bouton = tk.Button(
        parent,
        text=libelle,
        command=lambda: basculer_section_netatmo(cle),
        font=("Segoe UI", 14, "bold"),
        fg=TEXT,
        bg=CARD,
        activebackground=CARD,
        activeforeground=TEXT,
        relief="flat",
        cursor="hand2",
        anchor="w"
    )
    bouton.pack(fill="x", padx=16, pady=(18, 2))

    if sous_titre:
        tk.Label(
            parent,
            text=sous_titre,
            font=("Segoe UI", 9),
            fg=SECONDARY,
            bg=CARD,
            anchor="w",
            wraplength=900,
            justify="left"
        ).pack(fill="x", padx=20, pady=(0, 6))

    return ouvert


def formater_nombre(valeur, unite=""):

    if valeur is None:
        return "—"

    try:

        if isinstance(valeur, float):
            return f"{valeur:.1f}{unite}"

        return f"{valeur}{unite}"

    except Exception:
        return f"{valeur}{unite}"


NETATMO_LIBELLES_BRUTS = {
    "Temperature": "Température",
    "Humidity": "Humidité",
    "Pressure": "Pression",
    "CO2": "CO₂",
    "Noise": "Bruit",
    "WindStrength": "Vent",
    "WindAngle": "Direction du vent",
    "GustStrength": "Rafale",
    "GustAngle": "Direction rafale",
    "Rain": "Pluie actuelle",
    "sum_rain_1": "Pluie 1 h",
    "sum_rain_24": "Pluie 24 h",
    "min_temp": "Température min",
    "max_temp": "Température max",
    "date_min_temp": "Date temp. min",
    "date_max_temp": "Date temp. max",
    "time_utc": "Horodatage UTC",
    "time": "Horodatage"
}


NETATMO_UNITES_BRUTES = {
    "Temperature": " °C",
    "min_temp": " °C",
    "max_temp": " °C",
    "Humidity": " %",
    "Pressure": " hPa",
    "CO2": " ppm",
    "Noise": " dB",
    "WindStrength": " km/h",
    "GustStrength": " km/h",
    "WindAngle": "°",
    "GustAngle": "°",
    "Rain": " mm",
    "sum_rain_1": " mm",
    "sum_rain_24": " mm"
}


NETATMO_CHAMPS_AFFICHES = {
    "Temperature",
    "Humidity",
    "Pressure",
    "CO2",
    "Noise",
    "WindStrength",
    "WindAngle",
    "GustStrength",
    "Rain",
    "sum_rain_1",
    "sum_rain_24",
    "time"
}


def formater_valeur_netatmo(cle, valeur):

    if valeur is None:
        return "—"

    if cle in {
        "date_min_temp",
        "date_max_temp",
        "time",
        "time_utc"
    }:

        date_lisible = netatmo.convertir_date(valeur)

        if date_lisible:
            return date_lisible

    unite = NETATMO_UNITES_BRUTES.get(cle, "")

    if isinstance(valeur, float):
        return f"{valeur:.1f}{unite}"

    return f"{valeur}{unite}"


def creer_titre_section(parent, titre):

    tk.Label(
        parent,
        text=titre,
        font=("Segoe UI", 9, "bold"),
        fg=SECONDARY,
        bg=CARD,
        anchor="w"
    ).pack(
        fill="x",
        padx=15,
        pady=(8, 2)
    )


def style_valeur_netatmo(titre, valeur):

    valeur_txt = str(valeur)

    if valeur_txt in ("—", "non remonté", "non disponible"):
        return CARD, SECONDARY

    titre_min = titre.lower()

    if "pluie" in titre_min or "☔" in titre_min or "🌧" in titre_min:
        return CARD, BLUE

    if "vent" in titre_min or "rafale" in titre_min or "direction" in titre_min or "💨" in titre_min or "🧭" in titre_min:
        return CARD, "#16898D"

    if "temp" in titre_min or "🌡" in titre_min:
        return CARD, ORANGE

    if "humid" in titre_min or "💧" in titre_min:
        return CARD, GREEN

    if "pression" in titre_min or "🔵" in titre_min:
        return CARD, "#4867C8"

    if "co₂" in titre_min or "co2" in titre_min or "🌬" in titre_min:
        return CARD, "#7650B8"

    if "bruit" in titre_min or "🔊" in titre_min:
        return CARD, SECONDARY

    return CARD, TEXT


def creer_valeur_netatmo(parent, titre, valeur):

    fond, couleur = style_valeur_netatmo(
        titre,
        valeur
    )

    bloc = tk.Frame(
        parent,
        bg=fond,
        highlightbackground=BORDER,
        highlightthickness=1,
        width=145,
        height=76
    )

    bloc.pack(
        side="left",
        expand=True,
        fill="both",
        padx=4
    )
    bloc.pack_propagate(False)

    valeur_txt = str(valeur)
    if valeur_txt in ("—", "non remonté", "non disponible"):
        valeur_font = ("Segoe UI", 9, "bold")
    else:
        valeur_font = ("Segoe UI", 14, "bold")

    tk.Label(
        bloc,
        text=valeur,
        font=valeur_font,
        fg=couleur,
        bg=fond,
        wraplength=130,
        justify="center"
    ).pack(
        fill="x",
        pady=(10, 0)
    )

    tk.Label(
        bloc,
        text=titre,
        font=("Segoe UI", 8),
        fg=SECONDARY,
        bg=fond,
        wraplength=130,
        justify="center"
    ).pack(
        fill="x",
        pady=(1, 8)
    )


def creer_ligne_netatmo_compacte(parent, valeurs, colonnes=4):

    if not valeurs:
        return

    for debut in range(0, len(valeurs), colonnes):
        groupe = valeurs[debut:debut + colonnes]

        ligne = tk.Frame(
            parent,
            bg=CARD
        )

        ligne.pack(
            fill="x",
            padx=12,
            pady=(0, 8)
        )

        for titre, valeur in groupe:
            creer_valeur_netatmo(
                ligne,
                titre,
                valeur
            )

        # Complete visuellement la ligne pour garder une grille stable.
        for _ in range(max(0, colonnes - len(groupe))):
            spacer = tk.Frame(
                ligne,
                bg=CARD,
                highlightbackground=CARD,
                highlightthickness=1,
                width=145,
                height=76
            )
            spacer.pack(side="left", expand=True, fill="both", padx=4)
            spacer.pack_propagate(False)


def contient_mesure(mesures, cles):

    return any(
        mesures.get(cle) is not None
        for cle in cles
    )


def creer_badge_netatmo(parent, texte, fond, couleur):
    tk.Label(
        parent,
        text=texte,
        font=("Segoe UI", 8, "bold"),
        fg=couleur,
        bg=fond,
        padx=8,
        pady=3
    ).pack(side="left", padx=(0, 6))


def libelle_capteur_public(disponible, present):
    if disponible:
        return "dispo"
    if present:
        return "présent, non remonté"
    return "absent"


def adresse_station_netatmo(station):
    mesures = station.get("mesures", {}) if isinstance(station, dict) else {}
    brut = mesures.get("brut") if isinstance(mesures, dict) else None
    place = brut.get("place", {}) if isinstance(brut, dict) else {}

    rue = place.get("street")
    ville = place.get("city")

    morceaux = []
    if rue:
        morceaux.append(str(rue))
    if ville:
        morceaux.append(str(ville))

    if morceaux:
        return " · ".join(morceaux)

    latitude = station.get("latitude")
    longitude = station.get("longitude")
    if latitude is not None and longitude is not None:
        return f"Coordonnées : {latitude:.5f}, {longitude:.5f}"

    return "Adresse non fournie"


def resume_station_publique(mesures):
    morceaux = []
    temperature = formater_nombre(mesures.get("temperature"), " °C")
    humidite = formater_nombre(mesures.get("humidite"), " %")

    if temperature != "—":
        morceaux.append(f"Température {temperature}")
    if humidite != "—":
        morceaux.append(f"humidité {humidite}")

    pluie_dispo = any(mesures.get(cle) is not None for cle in ("pluie", "pluie_1h", "pluie_24h"))
    vent_dispo = any(mesures.get(cle) is not None for cle in ("vent", "rafale", "direction_vent", "direction_rafale"))

    morceaux.append("pluie " + libelle_capteur_public(pluie_dispo, bool(mesures.get("pluviometre"))))
    morceaux.append("vent " + libelle_capteur_public(vent_dispo, bool(mesures.get("anemometre"))))

    return " · ".join(morceaux)


def creer_bloc_netatmo(parent, element):

    nom = element.get("nom") or "Équipement Netatmo"
    type_element = element.get("type") or "Inconnu"
    mesures = element.get("mesures", {})

    bloc = tk.Frame(
        parent,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    bloc.pack(
        fill="x",
        padx=20,
        pady=6
    )

    # --------------------------------------------------------
    # Nom
    # --------------------------------------------------------

    entete = tk.Frame(
        bloc,
        bg=CARD
    )

    entete.pack(
        fill="x",
        padx=15,
        pady=(10, 5)
    )

    tk.Label(
        entete,
        text=f"🌦️ {nom}",
        font=("Segoe UI", 12, "bold"),
        fg=TEXT,
        bg=CARD
    ).pack(
        side="left"
    )

    tk.Label(
        entete,
        text=type_element,
        font=("Segoe UI", 8),
        fg=SECONDARY,
        bg=CARD
    ).pack(
        side="left",
        padx=10
    )

    brut = mesures.get("brut", {})

    creer_titre_section(
        bloc,
        "Conditions"
    )

    creer_ligne_netatmo_compacte(
        bloc,
        [
        (
            "🌡️ Température",
            formater_nombre(
                mesures.get("temperature"),
                " °C"
            )
        ),
        (
            "💧 Humidité",
            formater_nombre(
                mesures.get("humidite"),
                " %"
            )
        ),
        (
            "🌬️ Pression",
            formater_nombre(
                mesures.get("pression"),
                " hPa"
            )
        )
        ]
    )

    if contient_mesure(mesures, ("co2", "bruit")):

        creer_titre_section(
            bloc,
            "Air intérieur"
        )

        creer_ligne_netatmo_compacte(
            bloc,
            [
            (
                "🌬️ CO₂",
                formater_nombre(
                    mesures.get("co2"),
                    " ppm"
                )
            ),
            (
                "🔊 Bruit",
                formater_nombre(
                    mesures.get("bruit"),
                    " dB"
                )
            )
            ]
        )

    if contient_mesure(
        mesures,
        ("pluie", "pluie_1h", "pluie_24h")
    ):

        creer_titre_section(
            bloc,
            "Pluie"
        )

        creer_ligne_netatmo_compacte(
            bloc,
            [
            (
                "🌧️ Actuelle",
                formater_nombre(
                    mesures.get("pluie"),
                    " mm"
                )
            ),
            (
                "☔ 1 h",
                formater_nombre(
                    mesures.get("pluie_1h"),
                    " mm"
                )
            ),
            (
                "🌧️ 24 h",
                formater_nombre(
                    mesures.get("pluie_24h"),
                    " mm"
                )
            )
            ]
        )

    if contient_mesure(
        mesures,
        ("vent", "rafale", "direction_vent")
    ):

        creer_titre_section(
            bloc,
            "Vent"
        )

        creer_ligne_netatmo_compacte(
            bloc,
            [
            (
                "💨 Vent",
                formater_nombre(
                    mesures.get("vent"),
                    " km/h"
                )
            ),
            (
                "🌪️ Rafale",
                formater_nombre(
                    mesures.get("rafale"),
                    " km/h"
                )
            ),
            (
                "🧭 Direction",
                formater_nombre(
                    mesures.get("direction_vent"),
                    "°"
                )
            )
            ]
        )

    creer_titre_section(
        bloc,
        "Dates"
    )

    creer_ligne_netatmo_compacte(
        bloc,
        [
        (
            "🕐 Mesure",
            mesures.get("date_mesure") or "—"
        ),
        (
            "⬆️ Max",
            mesures.get("date_max_temp") or "—"
        ),
        (
            "⬇️ Min",
            mesures.get("date_min_temp") or "—"
        )
        ]
    )

    autres_donnees = []

    for cle in sorted(brut):

        if cle in NETATMO_CHAMPS_AFFICHES:
            continue

        autres_donnees.append(
            (
                NETATMO_LIBELLES_BRUTS.get(cle, cle),
                formater_valeur_netatmo(cle, brut.get(cle))
            )
        )

    if autres_donnees:

        creer_titre_section(
            bloc,
            "Autres données Netatmo"
        )

        for index in range(0, len(autres_donnees), 4):

            creer_ligne_netatmo_compacte(
                bloc,
                autres_donnees[index:index + 4]
            )


def creer_bloc_station_publique(parent, station):

    mesures = station.get("mesures", {})
    distance = station.get("distance_m")
    favorite = station.get("favorite")
    station_id = id_station_netatmo(station)

    fond_carte = CARD
    fond_entete = CARD

    bloc = tk.Frame(
        parent,
        bg=fond_carte,
        highlightbackground=BLUE if favorite else BORDER,
        highlightthickness=2 if favorite else 1
    )

    bloc.pack(
        fill="x",
        padx=20,
        pady=(8 if favorite else 6)
    )

    entete = tk.Frame(
        bloc,
        bg=fond_entete
    )

    entete.pack(
        fill="x",
        padx=10,
        pady=(10, 6)
    )

    distance_txt = (
        f"{distance:.0f} m"
        if distance is not None
        else "distance inconnue"
    )

    pluie_txt = formater_nombre(
        mesures.get("pluie"),
        " mm"
    )

    if pluie_txt == "—" and mesures.get("pluviometre"):
        pluie_txt = "non remonté"
    elif pluie_txt == "—":
        pluie_txt = "non disponible"

    vent_txt = formater_nombre(
        mesures.get("vent"),
        " km/h"
    )

    if vent_txt == "—" and mesures.get("anemometre"):
        vent_txt = "non remonté"
    elif vent_txt == "—":
        vent_txt = "non disponible"

    pluie_1h_txt = formater_nombre(
        mesures.get("pluie_1h"),
        " mm"
    )

    if pluie_1h_txt == "—" and mesures.get("pluviometre"):
        pluie_1h_txt = "non remonté"
    elif pluie_1h_txt == "—":
        pluie_1h_txt = "non disponible"

    pluie_24h_txt = formater_nombre(
        mesures.get("pluie_24h"),
        " mm"
    )

    if pluie_24h_txt == "—" and mesures.get("pluviometre"):
        pluie_24h_txt = "non remonté"
    elif pluie_24h_txt == "—":
        pluie_24h_txt = "non disponible"

    rafale_txt = formater_nombre(
        mesures.get("rafale"),
        " km/h"
    )

    if rafale_txt == "—" and mesures.get("anemometre"):
        rafale_txt = "non remonté"
    elif rafale_txt == "—":
        rafale_txt = "non disponible"

    direction_txt = formater_nombre(
        mesures.get("direction_vent"),
        "°"
    )

    if direction_txt == "—" and mesures.get("anemometre"):
        direction_txt = "non remonté"
    elif direction_txt == "—":
        direction_txt = "non disponible"

    direction_rafale_txt = formater_nombre(
        mesures.get("direction_rafale"),
        "°"
    )

    if direction_rafale_txt == "—" and mesures.get("anemometre"):
        direction_rafale_txt = "non remonté"
    elif direction_rafale_txt == "—":
        direction_rafale_txt = "non disponible"

    titre_station = "⭐ Station favorite" if favorite else "📍 Station proche"

    bloc_titre = tk.Frame(entete, bg=fond_entete)
    bloc_titre.pack(fill="x")

    tk.Label(
        bloc_titre,
        text=f"{titre_station} · {nom_station_netatmo(station)}",
        font=("Segoe UI", 13, "bold"),
        fg=TEXT,
        bg=fond_entete,
        anchor="w"
    ).pack(
        side="left",
        fill="x",
        expand=True
    )

    adresse_txt = adresse_station_netatmo(station)
    tk.Label(
        entete,
        text=f"📍 {adresse_txt}",
        font=("Segoe UI", 9),
        fg=SECONDARY,
        bg=fond_entete,
        anchor="w",
        wraplength=900,
        justify="left"
    ).pack(fill="x", pady=(4, 0))

    if favorite:
        tk.Button(
            bloc_titre,
            text="Renommer",
            command=lambda s=station: renommer_station_netatmo(s),
            bg=CARD,
            fg=BLUE,
            activebackground=CARD,
            relief="flat",
            cursor="hand2"
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            bloc_titre,
            text="↓",
            command=lambda sid=station_id: deplacer_favori_netatmo(sid, 1),
            bg=CARD,
            fg=TEXT,
            relief="flat",
            cursor="hand2"
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            bloc_titre,
            text="↑",
            command=lambda sid=station_id: deplacer_favori_netatmo(sid, -1),
            bg=CARD,
            fg=TEXT,
            relief="flat",
            cursor="hand2"
        ).pack(side="right")

    ligne_infos = tk.Frame(entete, bg=fond_entete)
    ligne_infos.pack(fill="x", pady=(6, 0))

    creer_badge_netatmo(ligne_infos, distance_txt, CARD, SECONDARY)

    pluie_dispo = any(mesures.get(cle) is not None for cle in ("pluie", "pluie_1h", "pluie_24h"))
    vent_dispo = any(mesures.get(cle) is not None for cle in ("vent", "rafale", "direction_vent", "direction_rafale"))

    creer_badge_netatmo(
        ligne_infos,
        "Pluie " + libelle_capteur_public(pluie_dispo, bool(mesures.get("pluviometre"))),
        LIGHT_BLUE if pluie_dispo else BG,
        BLUE if pluie_dispo else SECONDARY
    )
    creer_badge_netatmo(
        ligne_infos,
        "Vent " + libelle_capteur_public(vent_dispo, bool(mesures.get("anemometre"))),
        LIGHT_BLUE if vent_dispo else BG,
        BLUE if vent_dispo else SECONDARY
    )

    tk.Label(
        bloc,
        text=resume_station_publique(mesures),
        font=("Segoe UI", 9),
        fg=SECONDARY,
        bg=fond_carte,
        anchor="w",
        wraplength=950,
        justify="left"
    ).pack(fill="x", padx=14, pady=(0, 8))

    creer_ligne_netatmo_compacte(
        bloc,
        [
        (
            "🌡️ Température",
            formater_nombre(
                mesures.get("temperature"),
                " °C"
            )
        ),
        (
            "💧 Humidité",
            formater_nombre(
                mesures.get("humidite"),
                " %"
            )
        ),
        (
            "🌧️ Pluie",
            pluie_txt
        ),
        (
            "☔ 1 h",
            pluie_1h_txt
        )
        ]
    )

    creer_ligne_netatmo_compacte(
        bloc,
        [
        (
            "🌧️ 24 h",
            pluie_24h_txt
        ),
        (
            "💨 Vent",
            vent_txt
        ),
        (
            "🌪️ Rafale",
            rafale_txt
        ),
        (
            "🧭 Direction",
            direction_txt
        ),
        (
            "🌪️ Dir. rafale",
            direction_rafale_txt
        )
        ]
    )


def source_station_netatmo(station, privee=False):
    if privee:
        return station.get("nom") or "Netatmo intérieur"
    return nom_station_netatmo(station)


def choisir_mesure_netatmo(cle, unite=""):
    candidats = []

    for station in netatmo_public_data:
        mesures = station.get("mesures", {})
        valeur = mesures.get(cle)
        if valeur is None:
            continue
        candidats.append({
            "valeur": valeur,
            "texte": formater_nombre(valeur, unite),
            "source": source_station_netatmo(station),
            "favorite": bool(station.get("favorite")),
            "distance": station.get("distance_m") if station.get("distance_m") is not None else 999999,
        })

    for element in netatmo_data:
        mesures = element.get("mesures", {})
        valeur = mesures.get(cle)
        if valeur is None:
            continue
        candidats.append({
            "valeur": valeur,
            "texte": formater_nombre(valeur, unite),
            "source": source_station_netatmo(element, privee=True),
            "favorite": False,
            "distance": 999998,
        })

    if not candidats:
        return {
            "texte": "non disponible",
            "source": "aucune station",
            "etat": "absent",
        }

    candidats.sort(key=lambda c: (not c["favorite"], c["distance"]))
    choix = candidats[0]
    return {
        "texte": choix["texte"],
        "source": choix["source"],
        "etat": "ok",
    }


def creer_tuile_synthese_netatmo(parent, titre, info, couleur_fond, couleur):
    fond_auto, couleur_auto = style_valeur_netatmo(titre, info["texte"])
    if info["etat"] == "ok":
        couleur_fond = fond_auto
        couleur = couleur_auto
    else:
        couleur_fond = BG
        couleur = SECONDARY

    bloc = tk.Frame(
        parent,
        bg=couleur_fond,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    bloc.pack(side="left", expand=True, fill="x", padx=4)

    tk.Label(
        bloc,
        text=titre,
        font=("Segoe UI Emoji", 9, "bold"),
        fg=couleur,
        bg=couleur_fond
    ).pack(pady=(7, 0))

    tk.Label(
        bloc,
        text=info["texte"],
        font=("Segoe UI", 14, "bold") if info["etat"] == "ok" else ("Segoe UI", 9, "bold"),
        fg=couleur,
        bg=couleur_fond,
        wraplength=135,
        justify="center"
    ).pack(pady=(2, 0))

    tk.Label(
        bloc,
        text=info["source"],
        font=("Segoe UI", 7),
        fg=SECONDARY,
        bg=couleur_fond,
        wraplength=145,
        justify="center"
    ).pack(pady=(0, 7))


def afficher_synthese_netatmo(parent):
    if not netatmo_data and not netatmo_public_data:
        return

    bloc = tk.Frame(
        parent,
        bg=LIGHT_GREEN,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    bloc.pack(fill="x", padx=20, pady=(10, 8))

    entete = tk.Frame(bloc, bg=LIGHT_GREEN)
    entete.pack(fill="x", padx=12, pady=(8, 3))

    tk.Label(
        entete,
        text="🌍 Synthèse météo locale",
        font=("Segoe UI", 12, "bold"),
        fg=GREEN,
        bg=LIGHT_GREEN,
        anchor="w"
    ).pack(side="left")

    tk.Label(
        entete,
        text="Meilleure source disponible parmi vos stations Netatmo",
        font=("Segoe UI", 8),
        fg=SECONDARY,
        bg=LIGHT_GREEN,
        anchor="e"
    ).pack(side="right")

    ligne1 = tk.Frame(bloc, bg=LIGHT_GREEN)
    ligne1.pack(fill="x", padx=8, pady=(4, 6))

    creer_tuile_synthese_netatmo(
        ligne1,
        "🌡️ Température",
        choisir_mesure_netatmo("temperature", " °C"),
        CARD,
        ORANGE
    )
    creer_tuile_synthese_netatmo(
        ligne1,
        "💧 Humidité",
        choisir_mesure_netatmo("humidite", " %"),
        CARD,
        GREEN
    )
    creer_tuile_synthese_netatmo(
        ligne1,
        "🌬️ Pression",
        choisir_mesure_netatmo("pression", " hPa"),
        CARD,
        BLUE
    )
    creer_tuile_synthese_netatmo(
        ligne1,
        "🌧️ Pluie 1h",
        choisir_mesure_netatmo("pluie_1h", " mm"),
        CARD,
        BLUE
    )

    ligne2 = tk.Frame(bloc, bg=LIGHT_GREEN)
    ligne2.pack(fill="x", padx=8, pady=(0, 10))

    creer_tuile_synthese_netatmo(
        ligne2,
        "🌧️ 24 h",
        choisir_mesure_netatmo("pluie_24h", " mm"),
        CARD,
        BLUE
    )
    creer_tuile_synthese_netatmo(
        ligne2,
        "💨 Vent",
        choisir_mesure_netatmo("vent", " km/h"),
        CARD,
        BLUE
    )
    creer_tuile_synthese_netatmo(
        ligne2,
        "🌪️ Rafale",
        choisir_mesure_netatmo("rafale", " km/h"),
        CARD,
        BLUE
    )
    creer_tuile_synthese_netatmo(
        ligne2,
        "🧭 Direction",
        choisir_mesure_netatmo("direction_vent", "°"),
        CARD,
        TEXT
    )


def creer_titre_netatmo_liste(parent, titre, sous_titre=None):

    tk.Label(
        parent,
        text=titre,
        font=("Segoe UI", 14, "bold"),
        fg=TEXT,
        bg=CARD,
        anchor="w"
    ).pack(
        fill="x",
        padx=20,
        pady=(18, 2)
    )

    if sous_titre:

        tk.Label(
            parent,
            text=sous_titre,
            font=("Segoe UI", 9),
            fg=SECONDARY,
            bg=CARD,
            anchor="w",
            wraplength=900,
            justify="left"
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 6)
        )


def actualiser_netatmo_seul():
    global netatmo_loading
    if netatmo_loading or str(sync_button['state']) == 'disabled':
        return
    netatmo_loading = True
    sync_button.config(state='disabled')
    netatmo_status_var.set('Actualisation en cours…')
    def terminer(resultats):
        global netatmo_loading
        try:
            appliquer_resultats_meteo(resultats)
            afficher_netatmo()
        finally:
            netatmo_loading = False
            sync_button.config(state='normal')
    def charger():
        resultats = recuperer_sources(netatmo)
        recuperer_prevision_2h_avec_cache()
        root.after(0, terminer, resultats)
    threading.Thread(target=charger, daemon=True).start()



def afficher_netatmo():

    # --------------------------------------------------------
    # Nettoyage
    # --------------------------------------------------------

    for widget in netatmo_frame.winfo_children():
        widget.destroy()

    # --------------------------------------------------------
    # Titre
    # --------------------------------------------------------

    titre_frame = tk.Frame(
        netatmo_frame,
        bg=CARD
    )

    titre_frame.pack(
        fill="x",
        padx=20,
        pady=(15, 5)
    )

    tk.Label(
        titre_frame,
        text="🌦️ MÉTÉO NETATMO",
        font=("Segoe UI", 16, "bold"),
        fg=TEXT,
        bg=CARD
    ).pack(
        side="left"
    )

    tk.Label(
        titre_frame,
        textvariable=netatmo_status_var,
        font=("Segoe UI", 9, "bold"),
        fg=GREEN,
        bg=CARD
    ).pack(
        side="right"
    )

    tk.Button(titre_frame, text="Actualiser Netatmo", command=actualiser_netatmo_seul,
              bg=LIGHT_BLUE, fg=BLUE, relief="flat", cursor="hand2").pack(side="right", padx=12)

    # --------------------------------------------------------
    # Dernière synchronisation
    # --------------------------------------------------------

    tk.Label(
        netatmo_frame,
        textvariable=netatmo_date_var,
        font=("Segoe UI", 8),
        fg=SECONDARY,
        bg=CARD,
        anchor="w"
    ).pack(
        fill="x",
        padx=20
    )

    afficher_prevision_2h(netatmo_frame)
    afficher_synthese_netatmo(netatmo_frame)

    # --------------------------------------------------------
    # Pas encore de données
    # --------------------------------------------------------

    if not netatmo_data and not netatmo_public_data:

        tk.Label(
            netatmo_frame,
            text="🌦️ Aucune donnée Netatmo chargée.",
            font=("Segoe UI", 10),
            fg=SECONDARY,
            bg=CARD
        ).pack(
            pady=25
        )

        return

    # --------------------------------------------------------
    # Stations
    # --------------------------------------------------------

    equipements_prives_ouverts = True

    if netatmo_data:

        equipements_prives_ouverts = creer_titre_netatmo_repliable(
            netatmo_frame,
            "equipements_prives",
            "Mes équipements Netatmo",
            None,
            len(netatmo_data)
        )

    if not equipements_prives_ouverts:
        station_iterable = []
    else:
        station_iterable = netatmo_data

    for station in station_iterable:

        station_element = {
            "nom": station.get("nom"),
            "type": station.get("type"),
            "mesures": station.get("mesures", {})
        }

        creer_bloc_netatmo(
            netatmo_frame,
            station_element
        )

        for module in station.get("modules", []):

            module_element = {
                "nom": module.get("nom"),
                "type": module.get("type"),
                "mesures": module.get("mesures", {})
            }

            creer_bloc_netatmo(
                netatmo_frame,
                module_element
            )

    stations_favorites = [
        station
        for station in netatmo_public_data
        if station.get("favorite")
    ]

    stations_proches = [
        station
        for station in netatmo_public_data
        if not station.get("favorite")
    ]

    stations_favorites = trier_favoris_netatmo(stations_favorites)

    if stations_favorites:

        creer_titre_netatmo_liste(
            netatmo_frame,
            "Stations favorites",
            "Toujours affichées en haut. Les boutons ↑ ↓ changent leur ordre local, Renommer change seulement le nom affiché dans Botaneo."
        )

        for station_publique in stations_favorites:

            creer_bloc_station_publique(
                netatmo_frame,
                station_publique
            )

    stations_proches_ouvertes = creer_titre_netatmo_repliable(
        netatmo_frame,
        "stations_proches",
        "Stations publiques proches",
        "Stations publiques Netatmo autour du point approximatif. Les favoris restent visibles au-dessus.",
        len(stations_proches)
    )

    if not stations_proches_ouvertes:
        return

    if not stations_proches:

        tk.Label(
            netatmo_frame,
            text=(
                "Aucune autre station publique proche chargée. "
                "Netatmo n'affiche ici que les stations partagées "
                "publiquement par leurs propriétaires."
            ),
            font=("Segoe UI", 9),
            fg=SECONDARY,
            bg=CARD,
            anchor="w",
            wraplength=900,
            justify="left"
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

    for station_publique in stations_proches:

        creer_bloc_station_publique(
            netatmo_frame,
            station_publique
        )


# ============================================================
# SYNCHRONISATION
# ============================================================

def afficher_etape_netatmo(texte, progression=None):

    sync_detail_var.set(texte)

    if progression is not None:

        sync_progress_var.set(
            f"Progression : {progression}%"
        )

    root.update_idletasks()


def synchroniser():
    if netatmo_loading or str(sync_button['state']) == 'disabled':
        return

    sync_button.config(
        state="disabled",
        text="⏳ Synchronisation..."
    )

    status_var.set(
        "📡 Synchronisation en cours"
    )

    sync_var.set(
        "Synchronisation Mi Flora + historique + Netatmo..."
    )

    sync_detail_var.set(
        "Préparation..."
    )

    sync_progress_var.set(
        "Progression : 0%"
    )

    afficher_synchronisation_visible()

    thread = threading.Thread(
        target=synchroniser_arriere_plan,
        daemon=True
    )

    thread.start()


def synchroniser_arriere_plan():

    # --------------------------------------------------------
    # Mi Flora
    # --------------------------------------------------------

    try:

        root.after(
            0,
            afficher_etape_netatmo,
            "🌱 Recherche du Mi Flora...",
            5
        )

        def progression_miflora(index, total, nom, etape="mesure"):
            if etape == "historique":
                texte = f"📥 Historique Mi Flora {index}/{total} : {nom}"
                progression = 8 + int(22 * (index - 1) / max(total, 1))
            else:
                texte = f"🌱 Mesure Mi Flora {index}/{total} : {nom}"
                progression = 30 + int(20 * (index - 1) / max(total, 1))
            root.after(0, afficher_etape_netatmo, texte, progression)

        resultat_miflora = (
            sync_miflora.synchroniser_tous_avec_historique_sync(
                progression_miflora
            )
        )

    except Exception as e:

        resultat_miflora = {
            "ok": False,
            "message": str(e)
        }

    # --------------------------------------------------------
    # Netatmo : lectures et dates independantes.
    root.after(0, afficher_etape_netatmo, "Lecture des stations météo...", 55)
    resultats_meteo = recuperer_sources(netatmo)
    recuperer_prevision_2h_avec_cache()
    root.after(0, synchronisation_terminee, resultat_miflora, resultats_meteo)


def synchronisation_terminee(resultat_miflora, resultats_meteo):
    global auto_sync_en_cours

    appliquer_resultats_meteo(resultats_meteo)
    erreur_netatmo = resultats_meteo['privees']['error']
    donnees_netatmo = resultats_meteo['privees']['data']
    erreur_netatmo_publique = resultats_meteo['publiques']['error']

    # Mi Flora
    # --------------------------------------------------------

    if resultat_miflora.get("ok"):

        afficher_etape_netatmo(
            "✓ Mi Flora + historique synchronisés",
            90
        )

    else:

        afficher_etape_netatmo(
            "⚠ Mi Flora : "
            + resultat_miflora.get(
                "message",
                "erreur"
            ),
            90
        )

    # --------------------------------------------------------
    # Actualisation
    # --------------------------------------------------------

    actualiser_interface()
    afficher_netatmo()

    sources_en_echec = []
    if not resultat_miflora.get("ok"):
        sources_en_echec.append("Mi Flora")
    if erreur_netatmo or donnees_netatmo is None:
        sources_en_echec.append("Netatmo privée")
    if erreur_netatmo_publique:
        sources_en_echec.append("Netatmo publiques")
    bilan_sync = "⚠ Synchronisation terminée avec erreurs" if sources_en_echec else "✓ Synchronisation terminée"
    sync_var.set(
        bilan_sync + " · "
        + f"{datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}"
    )

    sync_detail_var.set(
        resultat_miflora.get("message", "Synchronisation Mi Flora terminée")
        + ("\n" + resultat_miflora['detail'] if resultat_miflora.get('detail') else "")
        + (" · À vérifier : " + ", ".join(sources_en_echec) if sources_en_echec else "")
    )

    sync_progress_var.set(
        "Progression : 100%"
    )

    status_var.set(
        "● Système actif"
    )

    global derniere_operation_bluetooth
    derniere_operation_bluetooth = datetime.now()

    sync_button.config(
        state="normal",
        text="📡 Synchroniser"
    )

    if auto_sync_en_cours:
        maintenant = datetime.now()
        auto_sync_config["derniere_date"] = maintenant.strftime("%Y-%m-%d")
        auto_sync_config["derniere_execution"] = maintenant.isoformat(timespec="seconds")
        auto_sync_en_cours = False
        sauvegarder_config_sync_auto()
        actualiser_affichage_sync_auto()


# ============================================================
# PANNEAU SYNCHRONISATION
# ============================================================

def afficher_synchronisation_visible():

    sync_frame.pack(
        fill="x",
        padx=20,
        pady=(0, 10),
        before=main_scroll_container
    )



def ouvrir_parametres():
    fenetre = tk.Toplevel(root)
    fenetre.title("Paramètres Botaneo")
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()

    tk.Label(
        fenetre,
        text="⚙ Paramètres",
        font=("Segoe UI", 16, "bold"),
        fg=TEXT,
        bg=CARD
    ).pack(anchor="w", padx=20, pady=(18, 8))

    affichage_bloc = tk.Frame(fenetre, bg=LIGHT_GREEN, highlightbackground=BORDER, highlightthickness=1)
    affichage_bloc.pack(fill="x", padx=20, pady=(0, 12))

    tk.Label(
        affichage_bloc,
        text="Affichage",
        font=("Segoe UI", 11, "bold"),
        fg=GREEN,
        bg=LIGHT_GREEN
    ).pack(anchor="w", padx=12, pady=(10, 4))

    meteo_haut_var = tk.BooleanVar(value=meteo_affichee_en_haut())
    tk.Checkbutton(
        affichage_bloc,
        text="Afficher météo locale et prévisions tout en haut",
        variable=meteo_haut_var,
        bg=LIGHT_GREEN,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        activeforeground=TEXT,
        selectcolor=CARD
    ).pack(anchor="w", padx=12, pady=(0, 10))

    vue_compacte_var = tk.BooleanVar(value=vue_compacte_plantes_active())
    tk.Checkbutton(
        affichage_bloc,
        text="Vue compacte des plantes",
        variable=vue_compacte_var,
        bg=LIGHT_GREEN,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        activeforeground=TEXT,
        selectcolor=CARD
    ).pack(anchor="w", padx=12, pady=(0, 10))

    bloc = tk.Frame(fenetre, bg=LIGHT_BLUE, highlightbackground=BORDER, highlightthickness=1)
    bloc.pack(fill="x", padx=20, pady=(0, 12))

    tk.Label(
        bloc,
        text="Synchronisation automatique",
        font=("Segoe UI", 11, "bold"),
        fg=BLUE,
        bg=LIGHT_BLUE
    ).pack(anchor="w", padx=12, pady=(10, 4))

    active_var = tk.BooleanVar(value=bool(auto_sync_config.get("active", True)))
    tk.Checkbutton(
        bloc,
        text="Activer la synchronisation automatique",
        variable=active_var,
        bg=LIGHT_BLUE,
        fg=TEXT,
        activebackground=LIGHT_BLUE,
        activeforeground=TEXT,
        selectcolor=CARD
    ).pack(anchor="w", padx=12, pady=(0, 8))

    ligne_heure = tk.Frame(bloc, bg=LIGHT_BLUE)
    ligne_heure.pack(fill="x", padx=12, pady=(0, 8))

    tk.Label(ligne_heure, text="Heure", bg=LIGHT_BLUE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
    heure_var = tk.StringVar(value=auto_sync_config.get("heure", "18:00"))
    heure_entry = tk.Entry(ligne_heure, textvariable=heure_var, width=8, bg=BG, fg=TEXT, insertbackground=TEXT)
    heure_entry.pack(side="left", padx=(10, 4))
    tk.Label(ligne_heure, text="format 18:00", bg=LIGHT_BLUE, fg=SECONDARY, font=("Segoe UI", 8)).pack(side="left")

    tk.Label(
        bloc,
        text="Jours autorisés",
        bg=LIGHT_BLUE,
        fg=TEXT,
        font=("Segoe UI", 9, "bold")
    ).pack(anchor="w", padx=12, pady=(4, 3))

    jours_frame = tk.Frame(bloc, bg=LIGHT_BLUE)
    jours_frame.pack(fill="x", padx=12, pady=(0, 8))

    jours_vars = []
    jours_config = set(auto_sync_config.get("jours", [0, 1, 2, 3, 4, 5, 6]))
    for index, nom in enumerate(["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]):
        var = tk.BooleanVar(value=index in jours_config)
        jours_vars.append(var)
        tk.Checkbutton(
            jours_frame,
            text=nom,
            variable=var,
            bg=LIGHT_BLUE,
            fg=TEXT,
            activebackground=LIGHT_BLUE,
            activeforeground=TEXT,
            selectcolor=CARD
        ).pack(side="left", padx=(0, 6))

    netatmo_bloc = tk.Frame(fenetre, bg=LIGHT_GREEN, highlightbackground=BORDER, highlightthickness=1)
    netatmo_bloc.pack(fill="x", padx=20, pady=(0, 12))

    tk.Label(netatmo_bloc, text="Netatmo", font=("Segoe UI", 11, "bold"), fg=GREEN, bg=LIGHT_GREEN).pack(anchor="w", padx=12, pady=(10, 4))

    tk.Label(
        netatmo_bloc,
        text="Ajouter une station favorite publique par identifiant ou lien weathermap",
        bg=LIGHT_GREEN,
        fg=TEXT,
        font=("Segoe UI", 9, "bold")
    ).pack(anchor="w", padx=12, pady=(0, 3))

    ligne_favori_netatmo = tk.Frame(netatmo_bloc, bg=LIGHT_GREEN)
    ligne_favori_netatmo.pack(fill="x", padx=12, pady=(0, 6))

    favori_netatmo_var = tk.StringVar(value="")
    tk.Entry(ligne_favori_netatmo, textvariable=favori_netatmo_var, width=42, bg=BG, fg=TEXT, insertbackground=TEXT).pack(side="left", fill="x", expand=True)

    nom_favori_netatmo_var = tk.StringVar(value="")
    tk.Entry(ligne_favori_netatmo, textvariable=nom_favori_netatmo_var, width=20, bg=BG, fg=TEXT, insertbackground=TEXT).pack(side="left", padx=(8, 0))

    tk.Label(netatmo_bloc, text="À gauche : lien ou stationid. À droite : nom local optionnel.",
             bg=LIGHT_GREEN, fg=SECONDARY, font=("Segoe UI", 8), wraplength=420,
             justify="left").pack(anchor="w", padx=12, pady=(0, 8))

    alertes_bloc = tk.Frame(fenetre, bg=LIGHT_ORANGE, highlightbackground=BORDER, highlightthickness=1)
    alertes_bloc.pack(fill="x", padx=20, pady=(0, 12))

    tk.Label(alertes_bloc, text="Alertes", font=("Segoe UI", 11, "bold"), fg=ORANGE, bg=LIGHT_ORANGE).pack(anchor="w", padx=12, pady=(10, 4))

    email_var = tk.BooleanVar(value=bool(alertes_config.get("email_actif", False)))
    tk.Checkbutton(alertes_bloc, text="Préparer les alertes e-mail via Outlook", variable=email_var,
                  bg=LIGHT_ORANGE, fg=TEXT, activebackground=LIGHT_ORANGE,
                  activeforeground=TEXT, selectcolor=CARD).pack(anchor="w", padx=12, pady=(0, 6))

    ligne_email = tk.Frame(alertes_bloc, bg=LIGHT_ORANGE)
    ligne_email.pack(fill="x", padx=12, pady=(0, 6))
    tk.Label(ligne_email, text="Destinataire", bg=LIGHT_ORANGE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
    email_destinataire_var = tk.StringVar(value=alertes_config.get("email_destinataire", ""))
    tk.Entry(ligne_email, textvariable=email_destinataire_var, width=32, bg=BG, fg=TEXT, insertbackground=TEXT).pack(side="left", padx=(10, 4))

    ligne_batterie = tk.Frame(alertes_bloc, bg=LIGHT_ORANGE)
    ligne_batterie.pack(fill="x", padx=12, pady=(0, 6))
    tk.Label(ligne_batterie, text="Seuil batterie", bg=LIGHT_ORANGE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
    seuil_batterie_var = tk.StringVar(value=str(alertes_config.get("seuil_batterie", 50)))
    tk.Entry(ligne_batterie, textvariable=seuil_batterie_var, width=6, bg=BG, fg=TEXT, insertbackground=TEXT).pack(side="left", padx=(10, 4))
    tk.Label(ligne_batterie, text="%", bg=LIGHT_ORANGE, fg=TEXT).pack(side="left")

    tk.Label(alertes_bloc, text="Plantes avec rappel e-mail", bg=LIGHT_ORANGE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(4, 3))
    plantes_alertes_frame = tk.Frame(alertes_bloc, bg=LIGHT_ORANGE)
    plantes_alertes_frame.pack(fill="x", padx=12, pady=(0, 10))
    plantes_alertes_vars = []
    plantes_email = set(alertes_config.get("plantes_rappel_email", []))
    for plante in database.get_plantes():
        plante_id_param, nom_param = plante[0], plante[1]
        var = tk.BooleanVar(value=plante_id_param in plantes_email)
        plantes_alertes_vars.append((plante_id_param, var))
        tk.Checkbutton(plantes_alertes_frame, text=nom_param, variable=var,
                      bg=LIGHT_ORANGE, fg=TEXT, activebackground=LIGHT_ORANGE,
                      activeforeground=TEXT, selectcolor=CARD).pack(anchor="w")

    tk.Label(alertes_bloc, text="Outlook est prévu comme mode d'envoi. Aucun mot de passe e-mail ne sera stocké dans Botaneo.",
             bg=LIGHT_ORANGE, fg=SECONDARY, font=("Segoe UI", 8), wraplength=420,
             justify="left").pack(anchor="w", padx=12, pady=(0, 8))

    erreur = tk.StringVar()
    tk.Label(fenetre, textvariable=erreur, bg=CARD, fg=RED, wraplength=420).pack(fill="x", padx=20, pady=(0, 6))

    def selectionner_tous():
        for var in jours_vars:
            var.set(True)

    def jours_semaine():
        for index, var in enumerate(jours_vars):
            var.set(index < 5)

    raccourcis = tk.Frame(fenetre, bg=CARD)
    raccourcis.pack(fill="x", padx=20, pady=(0, 8))

    tk.Button(raccourcis, text="Tous les jours", command=selectionner_tous, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(raccourcis, text="Lundi à vendredi", command=jours_semaine, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left")

    def enregistrer():
        heure = heure_var.get().strip()
        try:
            heure_part, minute_part = heure.split(":", 1)
            heure_int = int(heure_part)
            minute_int = int(minute_part)
            if not (0 <= heure_int <= 23 and 0 <= minute_int <= 59):
                raise ValueError()
            heure = f"{heure_int:02d}:{minute_int:02d}"
        except Exception:
            erreur.set("Heure invalide. Exemple accepté : 18:00")
            return

        jours = [index for index, var in enumerate(jours_vars) if var.get()]
        if not jours:
            erreur.set("Sélectionnez au moins un jour, ou désactivez la synchronisation automatique.")
            return

        ancienne_heure = auto_sync_config.get("heure", "18:00")
        anciens_jours = list(auto_sync_config.get("jours", [0, 1, 2, 3, 4, 5, 6]))
        ancien_actif = bool(auto_sync_config.get("active", True))

        auto_sync_config["active"] = bool(active_var.get())
        auto_sync_config["heure"] = heure
        auto_sync_config["jours"] = jours

        reglages_changes = (
            ancienne_heure != heure
            or sorted(anciens_jours) != sorted(jours)
            or ancien_actif != bool(active_var.get())
        )

        if reglages_changes:
            auto_sync_config["derniere_date"] = None

        try:
            seuil_batterie = int(seuil_batterie_var.get().strip())
            if not (1 <= seuil_batterie <= 100):
                raise ValueError()
        except ValueError:
            erreur.set("Seuil batterie invalide. Exemple : 50")
            return

        station_favorite_saisie = favori_netatmo_var.get().strip()
        if station_favorite_saisie:
            favori_ok, favori_message = ajouter_favori_netatmo_config(
                station_favorite_saisie,
                nom_favori_netatmo_var.get()
            )
            if not favori_ok:
                erreur.set(favori_message)
                return

        interface_layout_config["meteo_en_haut"] = bool(meteo_haut_var.get())
        interface_layout_config["vue_compacte_plantes"] = bool(vue_compacte_var.get())
        destinataire = email_destinataire_var.get().strip()
        if email_var.get() and not destinataire:
            erreur.set("Ajoutez un destinataire pour activer les alertes e-mail.")
            return

        alertes_config["email_actif"] = bool(email_var.get())
        alertes_config["email_mode"] = "outlook"
        alertes_config["email_destinataire"] = destinataire
        alertes_config["seuil_batterie"] = seuil_batterie
        alertes_config["plantes_rappel_email"] = [pid for pid, var in plantes_alertes_vars if var.get()]

        sauvegarde_sync = sauvegarder_config_sync_auto()
        sauvegarde_layout = sauvegarder_layout_interface()
        sauvegarde_alertes = sauvegarder_config_alertes()

        if sauvegarde_sync and sauvegarde_layout and sauvegarde_alertes:
            actualiser_affichage_sync_auto()
            fenetre.destroy()
            actualiser_interface()
            if station_favorite_saisie:
                status_var.set(favori_message)
            else:
                status_var.set("Paramètres enregistrés.")
        else:
            erreur.set("Impossible d'enregistrer tous les paramètres.")

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", padx=20, pady=(0, 15))

    tk.Button(boutons, text="Enregistrer", command=enregistrer, bg=LIGHT_GREEN, fg=TEXT, activebackground=LIGHT_GREEN, relief="flat", cursor="hand2").pack(side="right")
    tk.Button(boutons, text="Annuler", command=fenetre.destroy, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left")

    heure_entry.focus_set()


# ============================================================
# ACTIONS
# ============================================================

def ouvrir_ajout_plante():

    fenetre = tk.Toplevel(root)
    fenetre.title("Ajouter une plante")
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()

    champs = {}
    plante_selectionnee = tk.StringVar(value="")

    tk.Label(
        fenetre,
        text="Nom de la plante",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 9, "bold")
    ).pack(
        anchor="w",
        padx=20,
        pady=(12, 3)
    )

    nom_plante = ttk.Combobox(
        fenetre,
        width=46,
        values=mini_base_plantes.noms_plantes_connues()
    )
    nom_plante.pack(
        padx=20,
        fill="x"
    )
    champs["nom"] = nom_plante

    tk.Label(
        fenetre,
        text="Tapez librement ou choisissez une plante connue dans la liste.",
        bg=CARD,
        fg=SECONDARY,
        font=("Segoe UI", 8)
    ).pack(
        anchor="w",
        padx=20,
        pady=(3, 0)
    )

    for cle, titre in (
        ("espece", "Espèce"),
        ("zone", "Zone ou pièce")
    ):
        tk.Label(
            fenetre,
            text=titre,
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(12, 3)
        )

        entree = tk.Entry(
            fenetre,
            width=48,
            bg=BG,
            fg=TEXT,
            insertbackground=TEXT
        )

        entree.pack(
            padx=20,
            fill="x"
        )

        champs[cle] = entree

    tk.Label(
        fenetre,
        text="Besoins connus",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 9, "bold")
    ).pack(
        anchor="w",
        padx=20,
        pady=(12, 3)
    )

    besoins = tk.Label(
        fenetre,
        textvariable=plante_selectionnee,
        bg=BG,
        fg=TEXT,
        justify="left",
        anchor="nw",
        wraplength=410,
        padx=10,
        pady=8
    )
    besoins.pack(
        padx=20,
        fill="x"
    )

    plante_selectionnee.set(
        "Choisissez une plante connue pour remplir automatiquement les informations disponibles."
    )

    def appliquer_plante_connue(event=None):

        plante = mini_base_plantes.trouver_plante(nom_plante.get())
        if not plante:
            plante_selectionnee.set(
                mini_base_plantes.resume_besoins(None)
            )
            return

        espece = plante.get("espece") or ""
        if espece:
            champs["espece"].delete(0, "end")
            champs["espece"].insert(0, espece)

        plante_selectionnee.set(
            mini_base_plantes.resume_besoins(plante)
        )

    def actualiser_propositions(event=None):

        texte = nom_plante.get()
        propositions = mini_base_plantes.chercher_plantes(texte)
        nom_plante.configure(values=propositions)

        plante = mini_base_plantes.trouver_plante(texte)
        if plante:
            appliquer_plante_connue()
        elif texte.strip():
            plante_selectionnee.set(
                "Plante non connue dans la mini base. Vous pouvez quand même l'ajouter manuellement."
            )
        else:
            plante_selectionnee.set(
                "Choisissez une plante connue pour remplir automatiquement les informations disponibles."
            )

    nom_plante.bind("<KeyRelease>", actualiser_propositions)
    nom_plante.bind("<<ComboboxSelected>>", appliquer_plante_connue)
    nom_plante.bind("<FocusOut>", appliquer_plante_connue)

    tk.Label(
        fenetre,
        text="Emplacement",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 9, "bold")
    ).pack(
        anchor="w",
        padx=20,
        pady=(12, 3)
    )

    emplacement = ttk.Combobox(
        fenetre,
        state="readonly",
        width=46,
        values=[
            "Intérieur",
            "Extérieur"
        ]
    )

    emplacement.pack(
        padx=20,
        fill="x"
    )

    emplacement.current(0)

    erreur = tk.StringVar()

    tk.Label(
        fenetre,
        textvariable=erreur,
        bg=CARD,
        fg=RED,
        wraplength=390
    ).pack(
        padx=20,
        pady=8
    )

    def enregistrer():

        appliquer_plante_connue()

        nom = champs["nom"].get().strip()
        espece = champs["espece"].get().strip() or None
        zone = champs["zone"].get().strip() or None

        if not nom:
            erreur.set("Le nom de la plante est obligatoire.")
            return

        try:
            database.ajouter_plante(
                nom,
                espece,
                emplacement.get(),
                zone
            )

        except Exception:
            erreur.set(
                "Ajout impossible. Vérifiez l'accès à la base."
            )
            return

        fenetre.destroy()
        actualiser_interface()
        status_var.set(
            "Plante ajoutée. Elle peut rester sans capteur "
            "ou recevoir un capteur plus tard."
        )

    boutons = tk.Frame(
        fenetre,
        bg=CARD
    )
    boutons.pack(
        fill="x",
        padx=0,
        pady=(0, 5)
    )

    tk.Button(
        boutons,
        text="Ajouter",
        command=enregistrer,
        bg=LIGHT_GREEN,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        activeforeground=TEXT
    ).pack(
        side="right",
        padx=20,
        pady=15
    )

    tk.Button(
        boutons,
        text="Annuler",
        command=fenetre.destroy,
        bg=BG,
        fg=TEXT
    ).pack(
        side="left",
        padx=20,
        pady=15
    )

    champs["nom"].focus_set()

def ouvrir_ajout_capteur():
    if netatmo_loading or str(sync_button['state']) == 'disabled':
        messagebox.showinfo("Ajouter un capteur", "Attendez la fin de la synchronisation.", parent=root)
        return
    plantes = database.get_plantes()
    occupes = {c[3] for c in database.get_capteurs() if c[8]}
    disponibles = [p for p in plantes if p[0] not in occupes]
    if not disponibles:
        messagebox.showinfo("Ajouter un capteur", "Il faut une plante sans capteur actif. Ajoutez d'abord une plante depuis l'interface.", parent=root)
        return
    fenetre = tk.Toplevel(root)
    fenetre.title("Ajouter un capteur")
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()
    champs = []
    for titre in ("Nom du capteur", "Adresse Bluetooth (AA:BB:CC:DD:EE:FF)"):
        tk.Label(fenetre, text=titre, bg=CARD, fg=TEXT).pack(anchor='w', padx=20, pady=(12, 3))
        entree = tk.Entry(fenetre, width=48, bg=BG, fg=TEXT, insertbackground=TEXT)
        entree.pack(padx=20, fill='x')
        champs.append(entree)
    tk.Label(fenetre, text="Plante à associer", bg=CARD, fg=TEXT).pack(anchor='w', padx=20, pady=(12,3))
    choix = ttk.Combobox(fenetre, state='readonly', width=46,
                          values=[f"{p[1]} (n° {p[0]})" for p in disponibles])
    choix.pack(padx=20, fill='x')
    choix.current(0)
    erreur = tk.StringVar()
    tk.Label(fenetre, textvariable=erreur, bg=CARD, fg=RED, wraplength=390).pack(padx=20, pady=8)
    def enregistrer():
        try:
            ajout_capteur.ajouter(champs[0].get(), champs[1].get(), disponibles[choix.current()][0])
        except (ValueError, RuntimeError) as probleme:
            erreur.set(str(probleme))
            return
        except Exception:
            erreur.set("Ajout impossible. Vérifiez l'accès à la base et à la sauvegarde.")
            return
        fenetre.destroy()
        actualiser_interface()
        status_var.set("Capteur ajouté. Cliquez sur Synchroniser pour effectuer sa première lecture.")
    tk.Button(fenetre, text="Ajouter", command=enregistrer, bg=LIGHT_GREEN, fg=TEXT,
              activebackground=LIGHT_GREEN, activeforeground=TEXT).pack(side='right', padx=20, pady=15)
    tk.Button(fenetre, text="Annuler", command=fenetre.destroy, bg=BG, fg=TEXT).pack(side='left', padx=20, pady=15)
    champs[0].focus_set()


def afficher_message_analyse(plante_id):

    analyse_lumiere = analyser_lumiere_24h(plante_id)

    status_var.set(
        f"🔎 {analyse_lumiere['message']} - "
        f"{analyse_lumiere['detail']}"
    )


def afficher_details_capteur(adresse, nom):
    fenetre = tk.Toplevel(root)
    fenetre.title("Détails du capteur — " + str(nom))
    fenetre.geometry("720x520")
    fenetre.configure(bg=BG)
    zone = tk.Text(fenetre, bg=CARD, fg=TEXT, insertbackground=TEXT,
                   wrap="word", relief="flat", font=("Segoe UI", 10), padx=15, pady=15)
    scroll = tk.Scrollbar(fenetre, command=zone.yview)
    zone.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    zone.pack(fill="both", expand=True, padx=12, pady=12)
    zone.insert("1.0", "Adresse Bluetooth : " + str(adresse) + "\n\n" + details_infos(lire_infos(adresse)))
    zone.configure(state="disabled")


def bluetooth_pret_pour_historique():
    if derniere_operation_bluetooth is None:
        return True, 0

    ecoule = (datetime.now() - derniere_operation_bluetooth).total_seconds()
    attente = 45

    if ecoule >= attente:
        return True, 0

    return False, int(attente - ecoule) + 1


def importer_historique_miflora_plante(plante_id, nom_plante):
    """Import manuel de l'historique Mi Flora, sans effacement."""

    global import_historique_en_cours

    if import_historique_en_cours:
        messagebox.showinfo(
            "Historique Mi Flora",
            "Un import historique est déjà en cours.",
            parent=root
        )
        return

    if netatmo_loading or str(sync_button["state"]) == "disabled":
        messagebox.showinfo(
            "Historique Mi Flora",
            "Une synchronisation est déjà en cours. Attendez qu'elle soit terminée avant d'importer l'historique Mi Flora.",
            parent=root
        )
        return

    pret_bluetooth, secondes_attente = bluetooth_pret_pour_historique()
    if not pret_bluetooth:
        messagebox.showinfo(
            "Historique Mi Flora",
            f"Bluetooth vient d'être utilisé. Attendez encore environ {secondes_attente} seconde(s), puis réessayez l'import historique.",
            parent=root
        )
        return

    capteur = obtenir_capteur_plante(plante_id)
    if capteur is None:
        messagebox.showinfo(
            "Historique Mi Flora",
            "Cette plante n'a pas de capteur actif.",
            parent=root
        )
        return

    import_historique_en_cours = True
    status_var.set(f"📥 Import historique Mi Flora · {nom_plante}")
    sync_detail_var.set("Lecture mémoire Mi Flora sans effacement...")

    def arriere_plan():
        global import_historique_en_cours
        try:
            resultat = sync_miflora.importer_historique_capteur_sync(capteur[0])
        except Exception as erreur:
            resultat = {
                "ok": False,
                "message": f"Import historique impossible : {erreur}"
            }

        def terminer():
            global import_historique_en_cours, derniere_operation_bluetooth
            import_historique_en_cours = False
            derniere_operation_bluetooth = datetime.now()
            sauvegarder_resultat_import_historique(capteur[0], resultat)

            if resultat.get("ok"):
                status_var.set("Historique Mi Flora importé.")
                sync_detail_var.set(resultat.get("message", "Historique importé."))
                actualiser_interface()
                messagebox.showinfo(
                    "Historique Mi Flora",
                    resultat.get("message", "Historique importé."),
                    parent=root
                )
            else:
                status_var.set("Import historique Mi Flora impossible.")
                sync_detail_var.set(resultat.get("message", "Historique non importé."))
                actualiser_interface()
                messagebox.showerror(
                    "Historique Mi Flora",
                    resultat.get("message", "Historique non importé."),
                    parent=root
                )

        root.after(0, terminer)

    threading.Thread(
        target=arriere_plan,
        daemon=True
    ).start()


def afficher_message_historique(plante_id):
    ouvrir_historique(root, plante_id)



def capteurs_actifs_par_plante():
    capteurs = {}
    try:
        for capteur in database.get_capteurs():
            plante_id = capteur[3]
            actif = bool(capteur[8]) if len(capteur) > 8 else False
            if plante_id is not None and actif:
                capteurs.setdefault(plante_id, []).append(capteur)
    except Exception:
        pass
    return capteurs


def ajouter_alerte(liste, niveau, titre, detail):
    couleurs = {
        "danger": (RED, LIGHT_RED),
        "attention": (ORANGE, LIGHT_ORANGE),
        "info": (BLUE, LIGHT_BLUE),
        "ok": (GREEN, LIGHT_GREEN),
    }
    couleur, fond = couleurs.get(niveau, (SECONDARY, BG))
    liste.append({"niveau": niveau, "titre": titre, "detail": detail, "couleur": couleur, "fond": fond})


def construire_alertes(plantes):
    alertes = []
    capteurs_par_plante = capteurs_actifs_par_plante()
    maintenant = datetime.now()

    for plante in plantes:
        plante_id = plante[0]
        nom = plante[1]
        capteurs = capteurs_par_plante.get(plante_id, [])

        if not capteurs:
            ajouter_alerte(alertes, "info", f"🌱 {nom} sans capteur actif", "Suivi manuel possible : arrosage, notes et rappel.")
        else:
            for capteur in capteurs:
                adresse = capteur[2]
                nom_capteur = capteur[1]
                infos = lire_infos(adresse)
                batterie = infos.get("batterie")
                seuil = int(alertes_config.get("seuil_batterie", 50))
                if batterie is not None and batterie <= seuil:
                    ajouter_alerte(alertes, "danger", f"🔋 Batterie faible · {nom}", f"{nom_capteur} : {batterie} % · seuil {seuil} %.")
                elif batterie is not None and batterie <= min(seuil + 15, 100):
                    ajouter_alerte(alertes, "attention", f"🔋 Batterie à surveiller · {nom}", f"{nom_capteur} : {batterie} %.")

                derniere_sync = obtenir_derniere_synchronisation_capteur(capteur[0])
                if derniere_sync:
                    try:
                        date_sync = datetime.fromisoformat(derniere_sync)
                        heures = (maintenant - date_sync).total_seconds() / 3600
                        if heures >= 48:
                            ajouter_alerte(alertes, "attention", f"📡 Donnée ancienne · {nom}", f"Dernière mesure {anciennete(derniere_sync)}.")
                    except Exception:
                        pass

        try:
            rappel = database.get_rappel_arrosage_actif(plante_id)
        except Exception:
            rappel = None

        if rappel and rappel[8]:
            try:
                date_rappel = datetime.fromisoformat(rappel[8])
                if date_rappel.date() <= maintenant.date():
                    ajouter_alerte(alertes, "danger", f"💧 Arrosage à faire · {nom}", f"Rappel prévu le {formater_date(rappel[8])}.")
                elif (date_rappel - maintenant).days <= 2:
                    ajouter_alerte(alertes, "attention", f"💧 Arrosage bientôt · {nom}", f"Rappel prévu le {formater_date(rappel[8])}.")
            except Exception:
                pass

    if prevision_2h_data:
        try:
            pluie = prevision_2h_data.get("pluie_2h")
            if pluie is not None and float(pluie) > 0:
                ajouter_alerte(alertes, "info", "🌧️ Pluie locale prévue", f"Prévision +2 h : {pluie} mm.")
        except Exception:
            pass
        try:
            rafale = prevision_2h_data.get("rafale")
            if rafale is not None and float(rafale) >= 35:
                ajouter_alerte(alertes, "attention", "💨 Rafales à surveiller", f"Prévision +2 h : rafales jusqu’à {rafale} km/h.")
        except Exception:
            pass

    return alertes


def afficher_tuile_alerte(parent, alerte):
    tuile = tk.Frame(parent, bg=alerte["fond"], highlightbackground=BORDER, highlightthickness=1)
    tuile.pack(fill="x", padx=12, pady=(0, 6))

    tk.Label(tuile, text=alerte["titre"], font=("Segoe UI", 10, "bold"), fg=alerte["couleur"], bg=alerte["fond"], anchor="w").pack(fill="x", padx=10, pady=(7, 0))
    tk.Label(tuile, text=alerte["detail"], font=("Segoe UI", 9), fg=TEXT, bg=alerte["fond"], anchor="w", wraplength=950, justify="left").pack(fill="x", padx=10, pady=(0, 7))


def afficher_centre_alertes(parent, plantes):
    alertes = construire_alertes(plantes)

    bloc = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    bloc.pack(fill="x", padx=20, pady=(10, 12))

    entete = tk.Frame(bloc, bg=CARD)
    entete.pack(fill="x", padx=12, pady=(10, 6))

    nb_urgentes = sum(1 for a in alertes if a["niveau"] == "danger")
    nb_surveillance = sum(1 for a in alertes if a["niveau"] == "attention")

    if nb_urgentes:
        resume = f"{nb_urgentes} urgente(s) · {nb_surveillance} à surveiller"
        couleur = RED
    elif nb_surveillance:
        resume = f"{nb_surveillance} point(s) à surveiller"
        couleur = ORANGE
    elif alertes:
        resume = f"{len(alertes)} information(s)"
        couleur = BLUE
    else:
        resume = "Aucune alerte importante"
        couleur = GREEN

    tk.Label(entete, text="🔔 Centre d’alertes", font=("Segoe UI", 13, "bold"), fg=TEXT, bg=CARD, anchor="w").pack(side="left")
    tk.Label(entete, text=resume, font=("Segoe UI", 9, "bold"), fg=couleur, bg=CARD, anchor="e").pack(side="right")

    if not alertes:
        tk.Label(bloc, text="Tout semble calme avec les données actuelles.", font=("Segoe UI", 9), fg=SECONDARY, bg=CARD, anchor="w").pack(fill="x", padx=12, pady=(0, 10))
        return

    for alerte in alertes[:6]:
        afficher_tuile_alerte(bloc, alerte)

    if len(alertes) > 6:
        tk.Label(bloc, text=f"+ {len(alertes) - 6} autre(s) information(s) dans les fiches plantes.", font=("Segoe UI", 8), fg=SECONDARY, bg=CARD, anchor="w").pack(fill="x", padx=12, pady=(0, 10))


# ============================================================
# ACTUALISATION PLANTES
# ============================================================

def actualiser_interface():

    for widget in content_frame.winfo_children():
        if widget is not netatmo_frame:
            widget.destroy()
    netatmo_frame.pack_forget()

    plantes = database.get_plantes()
    meteo_en_haut = meteo_affichee_en_haut()

    if meteo_en_haut:
        netatmo_frame.pack(fill="x", padx=20, pady=(10, 15))
        afficher_netatmo()

    afficher_centre_alertes(content_frame, plantes)
    suivi_raspberry.card(content_frame, globals())

    if not plantes:

        tk.Label(
            content_frame,
            text="🌱 Aucune plante dans Botaneo",
            font=("Segoe UI", 16, "bold"),
            fg=TEXT,
            bg=BG
        ).pack(
            pady=80
        )

        if not meteo_en_haut:
            netatmo_frame.pack(fill="x", padx=20, pady=15)
            afficher_netatmo()
        return

    plantes_filtrees = [plante for plante in plantes if plante_passe_filtres(plante)]
    afficher_filtres_plantes(content_frame, plantes, plantes_filtrees)

    if not plantes_filtrees:
        tk.Label(
            content_frame,
            text="Aucune plante ne correspond aux filtres actuels.",
            font=("Segoe UI", 11, "bold"),
            fg=SECONDARY,
            bg=BG
        ).pack(pady=25)

    for plante in plantes_filtrees:

        if vue_compacte_plantes_active():
            creer_carte_plante_compacte(
                content_frame,
                plante
            )
        else:
            creer_carte_plante(
                content_frame,
                plante
            )

    if not meteo_en_haut:
        netatmo_frame.pack(fill="x", padx=20, pady=15)
        afficher_netatmo()


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    root,
    bg=CARD,
    height=105,
    highlightbackground=BORDER,
    highlightthickness=1
)

header.pack(
    fill="x"
)

header.pack_propagate(False)

try:
    logo_source = tk.PhotoImage(file=str(LOGO_PATH))
    logo_image = tk.PhotoImage(file=str(LOGO_HEADER_PATH))
    root.iconphoto(True, logo_source)
except tk.TclError:
    logo_image = None

if logo_image:
    tk.Label(
        header,
        image=logo_image,
        bg=CARD
    ).pack(
        side="left",
        padx=(18, 10)
    )


tk.Label(
    header,
    text="BOTANEO",
    font=("Segoe UI", 21, "bold"),
    fg=GREEN,
    bg=CARD
).pack(
    side="left",
    padx=(0, 25)
)


tk.Label(
    header,
    textvariable=status_var,
    font=("Segoe UI", 9, "bold"),
    fg=GREEN,
    bg=CARD
).pack(
    side="left",
    padx=10
)


# ============================================================
# BARRE OUTILS
# ============================================================

toolbar = tk.Frame(
    root,
    bg=BG
)

toolbar.pack(
    fill="x",
    padx=20,
    pady=15
)


refresh_button = tk.Button(
    toolbar,
    text="⟳ Actualiser",
    font=("Segoe UI", 9, "bold"),
    bg=CARD,
    fg=TEXT,
    activebackground=CARD,
    relief="flat",
    cursor="hand2",
    command=actualiser_interface
)

refresh_button.pack(
    side="left",
    padx=(0, 8)
)


sync_button = tk.Button(
    toolbar,
    text="📡 Synchroniser",
    font=("Segoe UI", 9, "bold"),
    bg=GREEN,
    fg="white",
    activebackground=GREEN,
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    command=synchroniser
)

sync_button.pack(
    side="left"
)


add_plant_button = tk.Button(
    toolbar,
    text="＋ Ajouter une plante",
    command=ouvrir_ajout_plante,
    font=("Segoe UI", 9, "bold"),
    bg=CARD,
    fg=TEXT,
    activebackground=CARD,
    activeforeground=TEXT,
    relief="flat",
    cursor="hand2"
)

add_plant_button.pack(
    side="left",
    padx=(8, 0)
)


add_sensor_button = tk.Button(toolbar, text="＋ Ajouter un capteur", command=ouvrir_ajout_capteur,
                              font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT,
                              activebackground=CARD, activeforeground=TEXT, relief="flat", cursor="hand2")
add_sensor_button.pack(side="left", padx=8)


settings_button = tk.Button(
    toolbar,
    text="⚙ Paramètres",
    command=ouvrir_parametres,
    font=("Segoe UI", 9, "bold"),
    bg=CARD,
    fg=TEXT,
    activebackground=CARD,
    activeforeground=TEXT,
    relief="flat",
    cursor="hand2"
)
settings_button.pack(side="left", padx=(0, 8))

auto_sync_label = tk.Label(
    toolbar,
    textvariable=auto_sync_var,
    font=("Segoe UI", 8),
    bg=BG,
    fg=SECONDARY
)
auto_sync_label.pack(side="left", padx=(0, 8))


theme_button = tk.Button(
    toolbar,
    text="☀️ Mode clair" if theme_sombre_actif else "🌙 Mode sombre",
    font=("Segoe UI", 9, "bold"),
    bg=CARD,
    fg=TEXT,
    activebackground=CARD,
    relief="flat",
    cursor="hand2",
    command=basculer_theme
)

theme_button.pack(
    side="right"
)


# ============================================================
# PANNEAU SYNCHRONISATION
# ============================================================

sync_frame = tk.Frame(
    root,
    bg=LIGHT_BLUE,
    highlightbackground=BORDER,
    highlightthickness=1
)

tk.Label(
    sync_frame,
    text="📡 Synchronisation Botaneo",
    font=("Segoe UI", 10, "bold"),
    fg=BLUE,
    bg=LIGHT_BLUE,
    anchor="w"
).pack(
    fill="x",
    padx=15,
    pady=(10, 2)
)


tk.Label(
    sync_frame,
    textvariable=sync_detail_var,
    font=("Segoe UI", 9),
    fg=TEXT,
    bg=LIGHT_BLUE,
    anchor="w"
).pack(
    fill="x",
    padx=15
)


tk.Label(
    sync_frame,
    textvariable=sync_progress_var,
    font=("Segoe UI", 8, "bold"),
    fg=BLUE,
    bg=LIGHT_BLUE,
    anchor="w"
).pack(
    fill="x",
    padx=15,
    pady=(3, 10)
)


# ============================================================
# ZONE PRINCIPALE SCROLLABLE
# ============================================================

main_scroll_container = tk.Frame(
    root,
    bg=BG
)

main_scroll_container.pack(
    fill="both",
    expand=True
)


canvas = tk.Canvas(
    main_scroll_container,
    bg=BG,
    highlightthickness=0
)

scrollbar = tk.Scrollbar(
    main_scroll_container,
    orient="vertical",
    command=canvas.yview
)

canvas.configure(
    yscrollcommand=scrollbar.set
)

scrollbar.pack(
    side="right",
    fill="y"
)

canvas.pack(
    side="left",
    fill="both",
    expand=True
)


content_frame = tk.Frame(
    canvas,
    bg=BG
)

canvas_window = canvas.create_window(
    (0, 0),
    window=content_frame,
    anchor="nw"
)


def ajuster_scroll(event=None):

    canvas.configure(
        scrollregion=canvas.bbox("all")
    )


def ajuster_largeur(event):

    canvas.itemconfig(
        canvas_window,
        width=event.width
    )


_reste_molette = 0


def defiler_molette(event):
    global _reste_molette
    widget = root.winfo_containing(event.x_root, event.y_root)
    if widget is None or widget.winfo_toplevel() is not root:
        return
    while widget is not None and widget is not canvas:
        widget = getattr(widget, 'master', None)
    if widget is not canvas:
        return
    if canvas.yview() == (0.0, 1.0):
        return
    if getattr(event, 'num', None) in (4, 5):
        pas = -3 if event.num == 4 else 3
    else:
        _reste_molette += event.delta
        crans = int(_reste_molette / 120)
        _reste_molette -= crans * 120
        pas = -3 * crans
    if pas:
        canvas.yview_scroll(pas, 'units')
    return 'break'


root.bind('<MouseWheel>', defiler_molette, add='+')
root.bind('<Button-4>', defiler_molette, add='+')
root.bind('<Button-5>', defiler_molette, add='+')


content_frame.bind(
    "<Configure>",
    ajuster_scroll
)

canvas.bind(
    "<Configure>",
    ajuster_largeur
)


# ============================================================
# CARTE NETATMO
# ============================================================

netatmo_frame = tk.Frame(
    content_frame,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)

netatmo_frame.pack(
    fill="x",
    padx=20,
    pady=15
)


afficher_netatmo()


# ============================================================
# FOOTER
# ============================================================

footer = tk.Frame(
    root,
    bg=CARD,
    height=35,
    highlightbackground=BORDER,
    highlightthickness=1
)

footer.pack(
    fill="x"
)

footer.pack_propagate(False)


tk.Label(
    footer,
    text="Botaneo",
    font=("Segoe UI", 8),
    fg=SECONDARY,
    bg=CARD
).pack(
    side="left",
    padx=20
)


tk.Label(
    footer,
    textvariable=sync_var,
    font=("Segoe UI", 8),
    fg=SECONDARY,
    bg=CARD
).pack(
    side="right",
    padx=20
)


# ============================================================
# DÉMARRAGE
# ============================================================

netatmo_data = meteo_etat.sources['privees']['data']
netatmo_public_data = meteo_etat.sources['publiques']['data']
actualiser_statut_meteo()

auto_sync_config = charger_config_sync_auto()
actualiser_affichage_sync_auto()
netatmo_preferences = charger_preferences_netatmo()

suivi_raspberry = SuiviRaspberry(root, CONFIG_DIR, Path(__file__).resolve().parent / 'data')
actualiser_interface()
root.after(1000, suivi_raspberry.start)
root.after(500, actualiser_netatmo_seul)
root.after(5000, verifier_sync_auto)

root.mainloop()





