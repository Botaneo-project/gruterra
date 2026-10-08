import os
import json
from instance_botaneo import exiger_instance_unique
exiger_instance_unique(graphique=True)

import tkinter as tk
from tkinter import ttk, messagebox
import ajout_capteur
from meteo_cache import CacheMeteo, recuperer_sources
from datetime import datetime, timedelta
import threading
import json
import subprocess
import sys
from pathlib import Path

import database
from evolutions_lumiere import lire_evolutions
import mini_base_plantes
from capteur_infos import lire_infos, resume_infos, details_infos
from botaneo_config import LOCAL_CONFIG, lire_json, ecrire_json, normaliser_station_favorite, diagnostiquer_config_netatmo, creer_config_netatmo_exemple
from ui_preferences import charger_theme_sombre, sauvegarder_theme_sombre, charger_langue_interface, sauvegarder_langue_interface
from vue_historique import ouvrir_historique
import sync_miflora
import raspberry_sync
import botaneo_email
import botaneo_update
import sauvegarde_utilisateur
from capteurs import netatmo
import previsions_meteo
from suivi_raspberry_ui import SuiviRaspberry
from i18n import traduire, normaliser_langue
from botaneo_config import CONFIG_DIR

# ============================================================
# CONFIGURATION
# ============================================================

APP_VERSION = "0.1.5-dev"

root = tk.Tk()

root.title("Gruterra")
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
langue_interface = normaliser_langue(charger_langue_interface())
globals().update(THEME_SOMBRE if theme_sombre_actif else THEME_CLAIR)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
LOGO_PATH = ASSETS_DIR / "botaneo_logo.png"
LOGO_HEADER_PATH = ASSETS_DIR / "botaneo_logo_header.png"
logo_image = None
root.configure(bg=BG)


def t(cle):
    return traduire(cle, langue_interface)


def texte_interface_utf8_sur(texte):
    """Prépare un texte Unicode pour Tkinter sans supprimer accents ni emojis valides."""

    if texte is None:
        return ""
    propre = str(texte).encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return propre.replace("\ufffd", "?")


# ============================================================
# VARIABLES
# ============================================================

status_var = tk.StringVar(value=t("system_active"))

sync_var = tk.StringVar(
    value=t("no_sync")
)

sync_detail_var = tk.StringVar(value="")
sync_progress_var = tk.StringVar(value="")
sync_detail_text = None


def texte_synchronisation_copiable():
    morceaux = [
        sync_var.get().strip(),
        sync_detail_var.get().strip(),
        sync_progress_var.get().strip(),
    ]
    return "\n".join(m for m in morceaux if m)


def copier_statut_synchronisation():
    texte = texte_synchronisation_copiable()
    root.clipboard_clear()
    root.clipboard_append(texte)
    status_var.set(t("sync_status_copied"))


def rafraichir_texte_synchronisation(*_):
    if sync_detail_text is None:
        return
    sync_detail_text.configure(state="normal")
    sync_detail_text.delete("1.0", "end")
    sync_detail_text.insert("1.0", texte_synchronisation_copiable())
    sync_detail_text.configure(state="disabled")


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
        "email_mode": "preview",
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
    if config.get("email_mode") not in {"preview", "smtp", "outlook"}:
        config["email_mode"] = "preview"
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
        "vue_compacte_plantes": False,
        "plantes_sur_accueil": True
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
    config["plantes_sur_accueil"] = bool(config.get("plantes_sur_accueil", True))
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


def plantes_affichees_sur_accueil():
    return bool(interface_layout_config.get("plantes_sur_accueil", True))


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
    status_var.set(t("auto_sync_running"))
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
            text=t("light_mode")
        )
    else:
        appliquer_palette(THEME_CLAIR)
        theme_button.config(
            text=t("dark_mode")
        )

    appliquer_theme_interface()
    actualiser_interface()
    if not sauvegarder_theme_sombre(theme_sombre_actif):
        status_var.set(t("theme_applied_unsaved"))


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
    configurer_widget(about_button, bg=CARD, fg=TEXT, activebackground=CARD, activeforeground=TEXT)
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


def age_mesure_minutes(date_heure):
    if not date_heure:
        return None
    try:
        dt = datetime.fromisoformat(date_heure)
        if dt.tzinfo:
            dt = dt.astimezone().replace(tzinfo=None)
        return max(0, int((datetime.now() - dt).total_seconds() // 60))
    except Exception:
        return None


def anciennete(date_heure):
    minutes_total = age_mesure_minutes(date_heure)
    if minutes_total is None:
        return t("age_no_data") if not date_heure else t("age_unknown")

    if minutes_total < 1:
        return t("age_less_than_minute")

    if minutes_total < 60:
        return (
            t("age_minutes").format(count=minutes_total)
        )

    heures = minutes_total // 60

    if heures < 24:
        return (
            t("age_hours").format(count=heures)
        )

    jours = heures // 24

    return (
        t("age_days").format(count=jours)
    )


def etat_fraicheur_mesure(date_heure):
    minutes = age_mesure_minutes(date_heure)
    texte_age = anciennete(date_heure)
    if minutes is None:
        return t("fresh_no_measure"), SECONDARY, BG
    if minutes <= 90:
        return t("fresh_recent").format(age=texte_age), GREEN, LIGHT_GREEN
    if minutes <= 8 * 60:
        return t("fresh_watch").format(age=texte_age), ORANGE, LIGHT_ORANGE
    return t("fresh_old").format(age=texte_age), RED, LIGHT_RED

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


def derniere_session_arrosage_recente(plante_id, heures=48):
    try:
        session = database.get_derniere_session_arrosage(plante_id)
    except Exception:
        return None
    if not session:
        return None
    date_source = session.get("date_debut") if isinstance(session, dict) else None
    if not date_source and isinstance(session, dict):
        premier = session.get("premier")
        date_source = premier[2] if premier and len(premier) > 2 else None
    try:
        date_arrosage = date_source if isinstance(date_source, datetime) else datetime.fromisoformat(str(date_source))
    except (TypeError, ValueError):
        return None
    age_h = (datetime.now() - date_arrosage).total_seconds() / 3600
    if 0 <= age_h <= heures:
        return {"session": session, "date": date_arrosage, "age_h": age_h}
    return None


def determiner_etat_humidite(humidite, plante_id=None):

    if humidite is None:
        return (
            t("humidity_no_measure"),
            SECONDARY,
            BG
        )

    arrosage_recent = derniere_session_arrosage_recente(plante_id) if plante_id is not None else None

    if humidite < 20:
        if arrosage_recent:
            return (
                t("humidity_post_watering_low"),
                ORANGE,
                LIGHT_ORANGE
            )
        return (
            t("humidity_very_low"),
            RED,
            LIGHT_RED
        )

    if humidite < 30:
        if arrosage_recent:
            return (
                t("humidity_post_watering"),
                GREEN,
                LIGHT_GREEN
            )
        return (
            t("humidity_watch"),
            ORANGE,
            LIGHT_ORANGE
        )

    return (
        t("humidity_ok"),
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
            "message": t("light_24_not_enough"),
            "detail": t("light_24_no_usable"),
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
    mesures_tres_lumineuses = sum(
        1
        for luminosite in luminosites
        if luminosite >= 10000
    )

    ratio_utile = mesures_utiles / len(luminosites)
    ratio_tres_lumineux = mesures_tres_lumineuses / len(luminosites)
    detail_base = (
        t("light_detail_base").format(average=moyenne, maximum=maximum, useful=mesures_utiles, total=len(luminosites))
    )
    pic_isole = maximum >= 10000 and moyenne < 500 and ratio_tres_lumineux < 0.20

    if maximum < 800 or moyenne < 250:
        message = t("light_24_low")
        detail = detail_base + t("light_advised")
        couleur = ORANGE
        fond = LIGHT_ORANGE

    elif pic_isole:
        message = t("light_isolated_peak")
        detail = (
            detail_base
            + t("light_isolated_peak_detail")
        )
        couleur = ORANGE
        fond = LIGHT_ORANGE

    elif ratio_utile < 0.25:
        message = t("light_watch")
        detail = (
            detail_base
            + t("light_watch_detail")
        )
        couleur = ORANGE
        fond = LIGHT_ORANGE

    else:
        message = t("light_ok_today")
        detail = detail_base.rstrip()
        couleur = GREEN
        fond = LIGHT_GREEN

    return {
        "etat": "analyse",
        "message": message,
        "detail": detail,
        "moyenne": moyenne,
        "maximum": maximum,
        "nombre_mesures": len(luminosites),
        "mesures_utiles": mesures_utiles,
        "ratio_utile": ratio_utile,
        "pic_isole": pic_isole,
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
            "message": t("forecast_not_enough"),
            "detail": t("forecast_need_more"),
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
            "message": t("forecast_too_short"),
            "detail": t("forecast_need_one_day"),
            "couleur": SECONDARY,
            "fond": BG
        }

    tendance = (fin_humidite - debut_humidite) / duree_jours

    if tendance < -3 and fin_humidite < 35:
        message = t("humidity_dropping")
        detail = t("trend_watch_detail").format(trend=tendance)
        couleur = ORANGE
        fond = LIGHT_ORANGE
    elif tendance < -1:
        message = t("humidity_dropping_slow")
        detail = t("trend_no_urgency_detail").format(trend=tendance)
        couleur = SECONDARY
        fond = BG
    else:
        message = t("humidity_no_worrying_drop")
        detail = t("trend_prudent_detail").format(trend=tendance)
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
            (t("decision_todo_today"), t("decision_sync_first"), BLUE, LIGHT_BLUE),
            (t("decision_watch"), t("decision_no_usable_data"), SECONDARY, BG),
            (t("forecast_not_enough").split(":")[0], t("decision_not_enough_forecast"), SECONDARY, BG),
        ]

    humidite = mesure[3]
    temperature = mesure[2]
    actions = []
    surveillances = []

    arrosage_recent = derniere_session_arrosage_recente(plante_id)

    if humidite is None:
        surveillances.append(t("watch_soil_humidity_missing"))
    elif humidite < 20:
        if arrosage_recent:
            surveillances.append(t("watch_post_watering_low_zone"))
        else:
            actions.append(t("action_watering_probably_needed"))
    elif humidite < 30:
        if arrosage_recent:
            surveillances.append(t("watch_post_watering_no_urgency"))
        else:
            surveillances.append(t("watch_soil_low"))

    if temperature is not None and (temperature < 12 or temperature > 30):
        surveillances.append(t("watch_temperature"))

    if analyse_lumiere.get("couleur") == ORANGE:
        surveillances.append(t("watch_light_low"))

    tendance = analyser_tendance_humidite(plante_id)

    if actions:
        faire = ", ".join(actions).capitalize() + "."
        couleur_faire = RED if humidite is not None and humidite < 20 else ORANGE
        fond_faire = LIGHT_RED if couleur_faire == RED else LIGHT_ORANGE
    else:
        faire = t("decision_no_urgent_action")
        couleur_faire = GREEN
        fond_faire = LIGHT_GREEN

    if surveillances:
        surveiller = ", ".join(surveillances).capitalize() + "."
        couleur_surv = ORANGE
        fond_surv = LIGHT_ORANGE
    else:
        surveiller = t("decision_nothing_special")
        couleur_surv = GREEN
        fond_surv = LIGHT_GREEN

    return [
        (t("decision_todo_today"), faire, couleur_faire, fond_faire),
        (t("decision_watch"), surveiller, couleur_surv, fond_surv),
        (t("forecast_not_enough").split(":")[0], tendance["message"] + " · " + tendance["detail"], tendance["couleur"], tendance["fond"]),
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


    historique = tk.Frame(parent, bg=CARD)
    historique.pack(fill="x", padx=20, pady=(0, 10))
    tk.Label(historique, text=t("light_history_7d"),
             font=("Segoe UI", 10, "bold"), fg=TEXT, bg=CARD,
             anchor="w").pack(fill="x", padx=10, pady=(8, 4))
    try:
        evenements = lire_evolutions(database, plante_id)
        vide = "Aucune variation marquée détectée sur les journées comparables. Si les relevés sont insuffisants, aucune conclusion n’est tirée."
    except Exception:
        evenements = []
        vide = "Historique lumineux indisponible : actualisez le panneau pour réessayer."
    for evenement in evenements:
        couleur = GREEN if evenement["sens"] == "hausse" else ORANGE
        tk.Label(historique, text=evenement["titre"], fg=couleur, bg=CARD,
                 font=("Segoe UI", 9, "bold"), anchor="w",
                 justify="left", wraplength=780).pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(historique, text=evenement["detail"], fg=TEXT, bg=CARD,
                 font=("Segoe UI", 9), anchor="w", justify="left",
                 wraplength=780).pack(fill="x", padx=10)
    note = ("Une hausse ne garantit pas que les besoins de la plante sont couverts. "
            "Les mesures seules ne permettent pas de déduire une sortie dehors ni sa durée.") if evenements else vide
    tk.Label(historique, text=note, fg=SECONDARY, bg=CARD,
             font=("Segoe UI", 9), anchor="w", justify="left",
             wraplength=780).pack(fill="x", padx=10, pady=(6, 8))


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
        text=t("basic_needs"),
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


def formater_duree_heures(heures):
    try:
        heures = float(heures)
    except (TypeError, ValueError):
        return "durée inconnue"
    if heures < 1:
        minutes = max(1, int(round(heures * 60)))
        return f"{minutes} min"
    if heures < 48:
        return f"{heures:.1f} h"
    jours = heures / 24
    return f"{jours:.1f} j"


def formater_session_arrosage(session):
    """Libellé prudent d'une session logique, sans fusionner les lignes brutes."""
    if not session:
        return None
    total = session.get("quantite_totale_ml")
    total_txt = f"{total:g} ml" if total is not None else "quantité non renseignée"
    apports = session.get("apports") or []
    if len(apports) <= 1:
        apport = apports[0] if apports else None
        type_eau = apport[8] if apport and len(apport) > 8 else None
        eau_txt = f" · eau : {type_eau}" if type_eau else ""
        return f"{total_txt}{eau_txt}"
    details = []
    for apport in apports:
        try:
            heure = datetime.fromisoformat(apport[2]).strftime("%H:%M")
        except (TypeError, ValueError):
            heure = "heure inconnue"
        quantite = apport[3]
        quantite_txt = f"{quantite:g} ml" if quantite is not None else "quantité non renseignée"
        details.append(f"{quantite_txt} à {heure}")
    return f"session {total_txt} ({' + '.join(details)})"


def date_debut_session_iso(session):
    if not session:
        return None
    date = session.get("date_debut")
    if hasattr(date, "isoformat"):
        return date.isoformat(timespec="seconds")
    return None


def analyser_cycle_arrosage(plante_id):
    sessions = database.get_sessions_arrosage_plante(plante_id, limite=50)
    session_arrosage = sessions[0] if sessions else None
    dernier = session_arrosage.get("premier") if session_arrosage else database.get_dernier_arrosage(plante_id)
    date_session_iso = date_debut_session_iso(session_arrosage) if session_arrosage else (dernier[2] if dernier else None)
    if not dernier or not date_session_iso:
        return None
    try:
        date_arrosage = datetime.fromisoformat(date_session_iso)
    except (TypeError, ValueError):
        return None

    date_arrosage_suivant = None
    if len(sessions) >= 2:
        date_arrosage_suivant = sessions[1].get("date_debut")

    mesures = database.get_mesures(plante_id=plante_id, limite=-1)
    points_avant = []
    points_apres = []
    for mesure in mesures:
        date_mesure = _date_locale_depuis_mesure(mesure[1])
        if not date_mesure or mesure[3] is None:
            continue
        try:
            humidite = float(mesure[3])
        except (TypeError, ValueError):
            continue
        if date_mesure < date_arrosage:
            points_avant.append((date_mesure, humidite))
        elif date_arrosage_suivant is None or date_mesure < date_arrosage_suivant:
            points_apres.append((date_mesure, humidite))

    points_avant.sort(key=lambda item: item[0])
    points_apres.sort(key=lambda item: item[0])
    if not points_apres:
        return None

    avant = points_avant[-1] if points_avant else None
    premiere = points_apres[0]
    pic = max(points_apres, key=lambda item: item[1])
    derniere = points_apres[-1]
    duree_suivi_h = max((derniere[0] - date_arrosage).total_seconds() / 3600, 0)
    vitesse_baisse = None
    if derniere[0] > pic[0] and derniere[1] < pic[1]:
        jours = max((derniere[0] - pic[0]).total_seconds() / 86400, 0.05)
        vitesse_baisse = (pic[1] - derniere[1]) / jours

    ecarts = [(b[0] - a[0]).total_seconds() / 3600 for a, b in zip(points_apres, points_apres[1:])]
    plus_grand_trou = max(ecarts) if ecarts else 0
    if plus_grand_trou > 6:
        qualite = f"prudence : trou de mesure jusqu’à {plus_grand_trou:.1f} h"
    elif plus_grand_trou > 1.8:
        qualite = f"correcte avec quelques trous, maximum {plus_grand_trou:.1f} h"
    else:
        qualite = "bonne sur les mesures disponibles"

    session_txt = formater_session_arrosage(session_arrosage) if session_arrosage else None
    if session_txt:
        quantite_txt = session_txt
        eau_txt = ""
    else:
        quantite = dernier[3]
        quantite_txt = f"{quantite:g} ml" if quantite is not None else "quantité non renseignée"
        type_eau = dernier[8] if len(dernier) > 8 else None
        eau_txt = f" · {type_eau}" if type_eau else ""
    contexte = dernier[7] if len(dernier) > 7 else None

    lignes = [
        f"Cycle du {formater_date(date_session_iso)} · {quantite_txt}{eau_txt}",
    ]
    if avant:
        ecart_avant = (date_arrosage - avant[0]).total_seconds() / 3600
        lignes.append(f"Avant arrosage : {avant[1]:.0f} %, {formater_duree_heures(ecart_avant)} avant.")
    else:
        lignes.append("Avant arrosage : aucune mesure exploitable juste avant.")
    lignes.append(f"Première mesure après : {premiere[1]:.0f} %.")
    lignes.append(f"Pic observé : {pic[1]:.0f} %.")
    lignes.append(f"Dernière mesure du cycle : {derniere[1]:.0f} %, suivi sur {formater_duree_heures(duree_suivi_h)}.")
    if date_arrosage_suivant:
        lignes.append(f"Cycle borné par l’arrosage suivant du {formater_date(date_arrosage_suivant.isoformat(timespec='seconds'))}.")
    if vitesse_baisse is not None:
        lignes.append(f"Vitesse de baisse observée après le pic : environ {vitesse_baisse:.1f} point(s)/jour.")
    else:
        lignes.append("Vitesse de baisse : recul insuffisant ou pas de baisse nette après le pic.")
    lignes.append(f"Qualité des données : {qualite}.")
    lignes.append("Lecture prudente : ces valeurs décrivent la zone du capteur, pas forcément toute la motte.")
    if contexte:
        lignes.append(f"Contexte noté : {contexte}")

    return {
        "titre": "💧 Cycle d’arrosage",
        "resume": " ".join(lignes),
        "lignes": lignes,
        "qualite": qualite,
    }

def _resume_reperes_post_arrosage(points, date_arrosage, avant=None):
    """Construit une ligne courte avec les repères 10 min, 1 h, 24 h et 48 h."""
    if not points:
        return "Repères : en attente de mesures après arrosage."

    def mesure_proche(minutes):
        cible = date_arrosage + timedelta(minutes=minutes)
        candidates = []
        tolerance = timedelta(minutes=max(25, minutes * 0.35))
        for date_mesure, humidite in points:
            if date_mesure < date_arrosage:
                continue
            ecart = abs(date_mesure - cible)
            if ecart <= tolerance:
                candidates.append((ecart, date_mesure, humidite))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1], candidates[0][2]

    morceaux = []
    for libelle, minutes in (("10 min", 10), ("1 h", 60), ("24 h", 1440), ("48 h", 2880)):
        trouve = mesure_proche(minutes)
        if trouve:
            morceaux.append(f"{libelle} : {trouve[1]:.0f} %")
        else:
            morceaux.append(f"{libelle} : —")

    if avant:
        premiere = points[0]
        comparaison = f"Avant/après : {avant[1]:.0f} % → {premiere[1]:.0f} %."
    else:
        comparaison = "Avant/après : mesure avant arrosage non disponible."
    return comparaison + " Repères : " + " · ".join(morceaux) + "."


def analyser_apres_arrosage(plante_id):
    """Analyse prudente des mesures qui suivent le dernier arrosage."""
    session_arrosage = database.get_derniere_session_arrosage(plante_id)
    dernier = session_arrosage.get("premier") if session_arrosage else database.get_dernier_arrosage(plante_id)
    date_session_iso = date_debut_session_iso(session_arrosage) if session_arrosage else (dernier[2] if dernier else None)
    if not dernier or not date_session_iso:
        return None

    try:
        date_arrosage = datetime.fromisoformat(date_session_iso)
    except (TypeError, ValueError):
        return None

    maintenant = datetime.now()
    heures_depuis = (maintenant - date_arrosage).total_seconds() / 3600
    if heures_depuis < 0 or heures_depuis > 10 * 24:
        return None

    # On utilise toutes les mesures disponibles depuis l'arrosage.
    # La limite historique de 200 créait un écart avec le résumé exporté,
    # qui comptait bien toutes les mesures depuis le dernier arrosage.
    mesures = database.get_mesures(plante_id=plante_id, limite=-1)
    points = []
    for mesure in mesures:
        date_heure = mesure[1]
        humidite = mesure[3]
        if humidite is None:
            continue
        try:
            date_mesure = datetime.fromisoformat(date_heure)
            if date_mesure.tzinfo:
                date_mesure = date_mesure.astimezone().replace(tzinfo=None)
        except (TypeError, ValueError):
            continue
        if date_mesure >= date_arrosage:
            try:
                points.append((date_mesure, float(humidite)))
            except (TypeError, ValueError):
                pass

    points = sorted(points, key=lambda item: item[0])
    derniere_avant = None
    for mesure in mesures:
        date_heure = mesure[1]
        humidite = mesure[3]
        if humidite is None:
            continue
        try:
            date_mesure = datetime.fromisoformat(date_heure)
            if date_mesure.tzinfo:
                date_mesure = date_mesure.astimezone().replace(tzinfo=None)
        except (TypeError, ValueError):
            continue
        if date_mesure < date_arrosage:
            if derniere_avant is None or date_mesure > derniere_avant[0]:
                try:
                    derniere_avant = (date_mesure, float(humidite))
                except (TypeError, ValueError):
                    pass
    reperes_post_arrosage = _resume_reperes_post_arrosage(points, date_arrosage, derniere_avant)
    arrosage_txt = formater_session_arrosage(session_arrosage) if session_arrosage else None
    if not arrosage_txt:
        quantite = dernier[3]
        quantite_txt = f"{quantite:g} ml" if quantite is not None else "quantité non renseignée"
        type_eau = dernier[8] if len(dernier) > 8 else None
        eau_txt = f" · eau : {type_eau}" if type_eau else ""
        arrosage_txt = f"{quantite_txt}{eau_txt}"

    if not points:

        if derniere_avant:
            ecart_heures = (date_arrosage - derniere_avant[0]).total_seconds() / 3600
            resume = (
                f"Suivi post-arrosage : aucune mesure après l'arrosage. "
                f"Dernière avant : {derniere_avant[1]:.0f} %, {ecart_heures:.1f} h avant."
            )
            detail = (
                f"Arrosage du {formater_date(date_session_iso)} · {arrosage_txt}. "
                f"Aucune mesure Mi Flora enregistrée depuis. Dernière mesure avant arrosage : "
                f"{derniere_avant[1]:.0f} %, {ecart_heures:.1f} h avant. Relancer une mesure directe pour démarrer le suivi. "
                f"{reperes_post_arrosage}"
            )
        else:
            resume = "Suivi post-arrosage : en attente de la prochaine mesure."
            detail = f"Arrosage du {formater_date(dernier[2])} · {arrosage_txt}. Aucune mesure Mi Flora enregistrée depuis. {reperes_post_arrosage}"

        return {
            "niveau": "info",
            "titre": "💧 Suivi post-arrosage en attente",
            "detail": detail,
            "resume": resume,
            "couleur": BLUE,
            "fond": LIGHT_BLUE
        }

    derniere_date, derniere_humidite = points[-1]
    heures_depuis_derniere = (maintenant - derniere_date).total_seconds() / 3600
    duree_suivi = max((derniere_date - date_arrosage).total_seconds() / 3600, 0)
    resume_contexte = (
        f"{len(points)} mesure(s) retenue(s) depuis arrosage, "
        f"suivi sur {formater_duree_heures(duree_suivi)}, "
        f"dernière mesure {anciennete(derniere_date.isoformat(timespec='seconds'))}"
    )

    if len(points) == 1 or heures_depuis < 12:
        return {
            "niveau": "info",
            "titre": "💧 Suivi post-arrosage lancé",
            "detail": f"Dernière humidité après arrosage : {derniere_humidite:.0f} %. {resume_contexte}. {reperes_post_arrosage} Il faut encore du recul avant d'interpréter.",
            "resume": f"Suivi post-arrosage : {derniere_humidite:.0f} %, recul encore court · {reperes_post_arrosage}",
            "couleur": BLUE,
            "fond": LIGHT_BLUE
        }

    premiere_humidite = points[0][1]
    variation = derniere_humidite - premiere_humidite
    duree_jours = max((points[-1][0] - points[0][0]).total_seconds() / 86400, 0.05)
    tendance_jour = variation / duree_jours

    if heures_depuis >= 72 and derniere_humidite >= 40:
        return {
            "niveau": "danger",
            "titre": "💧 Humidité persistante après arrosage",
            "detail": f"{derniere_humidite:.0f} % encore mesurés environ {formater_duree_heures(heures_depuis)} après l'arrosage. {resume_contexte}. {reperes_post_arrosage} Vérifier le substrat avant tout nouvel arrosage.",
            "resume": f"Suivi post-arrosage : humidité encore haute ({derniere_humidite:.0f} %) après {formater_duree_heures(heures_depuis)} · {reperes_post_arrosage}",
            "couleur": RED,
            "fond": LIGHT_RED
        }

    if heures_depuis >= 48 and derniere_humidite >= 35 and tendance_jour > -3:
        return {
            "niveau": "attention",
            "titre": "💧 Séchage lent après arrosage",
            "detail": f"{derniere_humidite:.0f} % après {formater_duree_heures(heures_depuis)}, tendance {tendance_jour:.1f} point/jour. {resume_contexte}. {reperes_post_arrosage} Surveiller avant de remettre de l'eau.",
            "resume": f"Suivi post-arrosage : séchage lent ({derniere_humidite:.0f} %, {tendance_jour:.1f} point/jour) · {reperes_post_arrosage}",
            "couleur": ORANGE,
            "fond": LIGHT_ORANGE
        }

    if derniere_humidite < 25 and heures_depuis >= 24:
        return {
            "niveau": "ok",
            "titre": "💧 Retour au niveau initial détecté",
            "detail": f"Humidité revenue à {derniere_humidite:.0f} % dans la zone du capteur. {resume_contexte}. {reperes_post_arrosage} Le Mi Flora ne permet pas de confirmer le séchage complet de toute la motte.",
            "resume": f"Suivi post-arrosage : retour au niveau initial dans la zone du capteur, {derniere_humidite:.0f} % · {reperes_post_arrosage}",
            "couleur": GREEN,
            "fond": LIGHT_GREEN
        }

    return {
        "niveau": "info",
        "titre": "💧 Suivi post-arrosage",
        "detail": f"Dernière humidité : {derniere_humidite:.0f} %, tendance {tendance_jour:.1f} point/jour. {resume_contexte}. {reperes_post_arrosage} Rien d'inquiétant détecté pour l'instant.",
        "resume": f"Suivi post-arrosage : {derniere_humidite:.0f} %, tendance {tendance_jour:.1f} point/jour · {reperes_post_arrosage}",
        "couleur": BLUE,
        "fond": LIGHT_BLUE
    }



def afficher_resume_arrosage(parent, plante_id):
    session_arrosage = database.get_derniere_session_arrosage(plante_id)
    dernier = session_arrosage.get("dernier") if session_arrosage else database.get_dernier_arrosage(plante_id)
    rappel = database.get_rappel_arrosage_actif(plante_id)
    suivi = analyser_apres_arrosage(plante_id)
    cycle = analyser_cycle_arrosage(plante_id)

    if not dernier and not rappel and not suivi and not cycle:
        return

    lignes = []

    if dernier:
        if session_arrosage:
            session_txt = formater_session_arrosage(session_arrosage)
            date_txt = formater_date(date_debut_session_iso(session_arrosage))
            prefixe = "Dernière session d’arrosage" if session_arrosage.get("fractionnee") else "Dernier arrosage"
            lignes.append(f"{prefixe} : {date_txt} · {session_txt}")
        else:
            quantite = dernier[3]
            quantite_txt = f"{quantite:g} ml" if quantite is not None else "quantité non renseignée"
            type_eau = dernier[8] if len(dernier) > 8 else None
            eau_txt = f" · eau : {type_eau}" if type_eau else ""
            lignes.append(f"Dernier arrosage : {formater_date(dernier[2])} · {quantite_txt}{eau_txt}")

    if suivi:
        lignes.append(suivi["resume"])

    if cycle:
        lignes.append(cycle["resume"])

    if rappel:
        texte_rappel = f"Rappel prévu : {formater_date(rappel[9])}"
        if plante_avec_rappel_email(plante_id):
            texte_rappel += " · mail prévu quand l'envoi sera configuré"
        lignes.append(texte_rappel)

    bloc = tk.Frame(parent, bg=LIGHT_BLUE, highlightbackground=BORDER, highlightthickness=1)
    bloc.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(
        bloc,
        text=t("watering"),
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


def lancer_collecte_prioritaire(
    plante_id,
    reason="controle",
    libelle="contrôle",
    delai_ms=1000,
    demande_id=None,
    message_sans_capteur="Aucune collecte prioritaire : pas de capteur actif",
    message_lancement="Collecte prioritaire demandée"
):
    """Demande une collecte prioritaire au collecteur responsable du capteur."""

    def lancer():
        try:
            capteur = obtenir_capteur_plante(plante_id)
            if capteur is None:
                status_var.set(message_sans_capteur)
                return

            status_var.set(message_lancement)

            def arriere_plan():
                try:
                    resultat = sync_miflora.synchroniser_capteur_prioritaire_sync(
                        capteur[0],
                        reason=reason
                    )
                except Exception as erreur:
                    resultat = {
                        "ok": False,
                        "message": f"Collecte prioritaire impossible : {erreur}"
                    }

                def terminer():
                    message = resultat.get("message", "Collecte prioritaire terminée.")
                    collecteur = resultat.get("collecteur")
                    prefixe = "Raspberry" if collecteur == "raspberry" else "PC"
                    if demande_id:
                        try:
                            database.marquer_collecte_prioritaire_tentee(
                                demande_id,
                                statut="reussie" if resultat.get("ok") else "echec",
                                commentaire=message
                            )
                        except Exception:
                            pass
                    status_var.set(f"Collecte {libelle} {prefixe} : {message}")
                    actualiser_interface()

                root.after(0, terminer)

            threading.Thread(target=arriere_plan, daemon=True).start()
        except Exception:
            status_var.set(f"Collecte {libelle} non lancée")

    root.after(delai_ms, lancer)


def lancer_collecte_prioritaire_apres_arrosage(plante_id, demande_id=None, delai_ms=1000):
    lancer_collecte_prioritaire(
        plante_id,
        reason="post_arrosage",
        libelle="post-arrosage",
        delai_ms=delai_ms,
        demande_id=demande_id,
        message_sans_capteur="Arrosage enregistré · aucune collecte prioritaire : pas de capteur actif",
        message_lancement="Arrosage enregistré · collecte prioritaire demandée"
    )


def lancer_controle_humidite_zero(plante_id, delai_ms=10 * 60 * 1000):
    lancer_collecte_prioritaire(
        plante_id,
        reason="controle_humidite_zero",
        libelle="contrôle humidité 0 %",
        delai_ms=delai_ms,
        message_sans_capteur="Humidité 0 % détectée · aucun contrôle : pas de capteur actif",
        message_lancement="Humidité 0 % détectée · contrôle programmé lancé"
    )


def parser_date_saisie_utilisateur(valeur):
    valeur = (valeur or "").strip()
    formats = (
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    )
    for format_date in formats:
        try:
            return datetime.strptime(valeur, format_date)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(valeur)
    except Exception:
        return None


def ouvrir_exposition_balcon_passee(plante_id, nom_plante):
    """Ajoute une sortie balcon passée avec date de sortie et de retour."""

    maintenant = datetime.now().replace(second=0, microsecond=0)
    sortie_defaut = maintenant - timedelta(hours=2)

    fenetre = tk.Toplevel(root)
    fenetre.title(t("past_balcony_exposure_title"))
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()

    tk.Label(
        fenetre,
        text=f"☀️ Exposition balcon · {nom_plante}",
        font=("Segoe UI", 15, "bold"),
        fg=TEXT,
        bg=CARD
    ).pack(anchor="w", padx=20, pady=(16, 6))

    tk.Label(
        fenetre,
        text=t("past_balcony_exposure_help"),
        font=("Segoe UI", 9),
        fg=SECONDARY,
        bg=CARD,
        wraplength=420,
        justify="left"
    ).pack(anchor="w", padx=20, pady=(0, 12))

    tk.Label(fenetre, text=t("out"), bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(4, 3))
    sortie_var = tk.StringVar(value=sortie_defaut.strftime("%d/%m/%Y %H:%M"))
    sortie_entry = tk.Entry(fenetre, textvariable=sortie_var, width=42, bg=BG, fg=TEXT, insertbackground=TEXT)
    sortie_entry.pack(fill="x", padx=20)

    tk.Label(fenetre, text=t("return_in"), bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 3))
    retour_var = tk.StringVar(value=maintenant.strftime("%d/%m/%Y %H:%M"))
    retour_entry = tk.Entry(fenetre, textvariable=retour_var, width=42, bg=BG, fg=TEXT, insertbackground=TEXT)
    retour_entry.pack(fill="x", padx=20)

    tk.Label(fenetre, text=t("optional_comment"), bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 3))
    commentaire_entry = tk.Entry(fenetre, width=42, bg=BG, fg=TEXT, insertbackground=TEXT)
    commentaire_entry.pack(fill="x", padx=20)

    erreur = tk.StringVar()
    tk.Label(fenetre, textvariable=erreur, bg=CARD, fg=RED, wraplength=420, justify="left").pack(fill="x", padx=20, pady=8)

    def enregistrer():
        sortie = parser_date_saisie_utilisateur(sortie_var.get())
        retour = parser_date_saisie_utilisateur(retour_var.get())
        if sortie is None or retour is None:
            erreur.set("Date invalide. Format conseillé : 25/09/2026 14:30")
            return
        if retour <= sortie:
            erreur.set("Le retour doit être après la sortie.")
            return

        commentaire_libre = commentaire_entry.get().strip()
        duree = formater_duree_heures((retour - sortie).total_seconds() / 3600)
        suffixe = f" Commentaire : {commentaire_libre}" if commentaire_libre else ""

        try:
            database.ajouter_observation_plante(
                plante_id,
                sortie.isoformat(timespec="seconds"),
                f"Plante sortie temporairement sur le balcon. Durée déclarée : {duree}.{suffixe} Les pics de lumière de cette période doivent être interprétés comme une exposition extérieure ponctuelle.",
                titre="Sortie balcon",
                type_evenement="exposition",
                source="botaneo"
            )
            database.ajouter_observation_plante(
                plante_id,
                retour.isoformat(timespec="seconds"),
                f"Plante rentrée à l'intérieur après une exposition balcon déclarée de {duree}.{suffixe} Les mesures suivantes correspondent de nouveau à l'emplacement habituel.",
                titre="Retour intérieur",
                type_evenement="exposition",
                source="botaneo"
            )
        except Exception as exception:
            erreur.set(f"Impossible d'enregistrer l'exposition : {exception}")
            return

        fenetre.destroy()
        actualiser_interface()
        status_var.set(f"Exposition balcon ajoutée pour {nom_plante} · {duree}.")

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", padx=20, pady=(0, 15))
    tk.Button(boutons, text=t("save"), command=enregistrer, bg=LIGHT_GREEN, fg=GREEN, activebackground=LIGHT_GREEN, relief="flat", cursor="hand2").pack(side="right")
    tk.Button(boutons, text=t("cancel"), command=fenetre.destroy, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left")

    sortie_entry.focus_set()


def enregistrer_evenement_balcon(plante_id, nom_plante, action):
    """Enregistre un événement d'exposition extérieure dans le journal de la plante après validation."""

    maintenant_dt = datetime.now()
    maintenant = maintenant_dt.isoformat(timespec="seconds")
    heure_lisible = maintenant_dt.strftime("%d/%m/%Y à %H:%M")
    if action == "sortie":
        titre = "Sortie balcon"
        commentaire = "Plante sortie temporairement sur le balcon. Les pics de lumière suivants doivent être interprétés comme une exposition extérieure ponctuelle."
        message = f"Sortie balcon notée pour {nom_plante}."
        question = f"Confirmer la sortie balcon de {nom_plante} maintenant ({heure_lisible}) ?"
    else:
        titre = "Retour intérieur"
        commentaire = "Plante rentrée à l'intérieur. Les mesures suivantes correspondent de nouveau à l'emplacement habituel."
        message = f"Retour intérieur noté pour {nom_plante}."
        question = f"Confirmer le retour intérieur de {nom_plante} maintenant ({heure_lisible}) ?"

    if not messagebox.askyesno(t("confirm_balcony_exposure"), question, parent=root):
        status_var.set(f"{titre} annulé : aucun événement ajouté.")
        return

    try:
        database.ajouter_observation_plante(
            plante_id,
            maintenant,
            commentaire,
            titre=titre,
            type_evenement="exposition",
            source="botaneo"
        )
    except Exception as erreur:
        status_var.set(f"Événement balcon impossible : {erreur}")
        return

    actualiser_interface()
    status_var.set(message)


def ouvrir_arrosage_plante(plante_id, nom_plante):
    fenetre = tk.Toplevel(root)
    fenetre.title(t("watering_title"))
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

    tk.Label(fenetre, text=t("quantity_ml"), bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(6, 3))
    quantite_entry = tk.Entry(fenetre, width=42, bg=BG, fg=TEXT, insertbackground=TEXT)
    quantite_entry.pack(fill="x", padx=20)

    tk.Label(fenetre, text=t("type"), bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 3))
    type_combo = ttk.Combobox(fenetre, state="readonly", values=["normal", "fertilisant"], width=39)
    type_combo.pack(fill="x", padx=20)
    type_combo.current(0)

    tk.Label(fenetre, text=t("water_type"), bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 3))
    type_eau_combo = ttk.Combobox(
        fenetre,
        state="readonly",
        values=[
            "Non renseigné",
            "Eau du robinet",
            "Eau reposée",
            "Eau filtrée",
            "Eau de pluie",
            "Eau minérale",
            "Volvic",
            "Autre"
        ],
        width=39
    )
    type_eau_combo.pack(fill="x", padx=20)
    type_eau_combo.current(0)

    contexte_frame = tk.Frame(fenetre, bg=CARD)
    contexte_frame.pack(fill="x", padx=20, pady=(10, 0))

    tk.Label(contexte_frame, text=t("optional_context"), bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 3))

    tk.Label(contexte_frame, text=t("distribution"), bg=CARD, fg=SECONDARY, font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w")
    repartition_combo = ttk.Combobox(
        contexte_frame,
        state="readonly",
        values=["Non renseigné", "Surface répartie", "Un côté du pot", "Centre du pot", "Bords du pot", "Autre"],
        width=18
    )
    repartition_combo.grid(row=2, column=0, sticky="ew", padx=(0, 8))
    repartition_combo.current(0)

    tk.Label(contexte_frame, text=t("drainage"), bg=CARD, fg=SECONDARY, font=("Segoe UI", 8)).grid(row=1, column=1, sticky="w")
    ecoulement_combo = ttk.Combobox(
        contexte_frame,
        state="readonly",
        values=["Non renseigné", "Aucun écoulement observé", "Écoulement léger", "Écoulement net", "Non vérifié"],
        width=20
    )
    ecoulement_combo.grid(row=2, column=1, sticky="ew")
    ecoulement_combo.current(0)

    tk.Label(contexte_frame, text=t("cache_pot"), bg=CARD, fg=SECONDARY, font=("Segoe UI", 8)).grid(row=3, column=0, sticky="w", pady=(6, 0))
    cachepot_combo = ttk.Combobox(
        contexte_frame,
        state="readonly",
        values=["Non renseigné", "Pas d'eau stagnante", "Eau stagnante retirée", "Eau stagnante présente", "Pas de cache-pot"],
        width=18
    )
    cachepot_combo.grid(row=4, column=0, sticky="ew", padx=(0, 8))
    cachepot_combo.current(0)

    tk.Label(contexte_frame, text=t("substrate"), bg=CARD, fg=SECONDARY, font=("Segoe UI", 8)).grid(row=3, column=1, sticky="w", pady=(6, 0))
    substrat_combo = ttk.Combobox(
        contexte_frame,
        state="readonly",
        values=["Non renseigné", "Sec en surface", "Légèrement humide", "Humide", "Très humide", "Non vérifié"],
        width=20
    )
    substrat_combo.grid(row=4, column=1, sticky="ew")
    substrat_combo.current(0)

    tk.Label(contexte_frame, text=t("mode"), bg=CARD, fg=SECONDARY, font=("Segoe UI", 8)).grid(row=5, column=0, sticky="w", pady=(6, 0))
    progressif_combo = ttk.Combobox(
        contexte_frame,
        state="readonly",
        values=["Non renseigné", "Arrosage en une fois", "Arrosage progressif", "Complément d'arrosage", "Autre"],
        width=18
    )
    progressif_combo.grid(row=6, column=0, sticky="ew", padx=(0, 8))
    progressif_combo.current(0)

    tk.Label(contexte_frame, text=t("pot"), bg=CARD, fg=SECONDARY, font=("Segoe UI", 8)).grid(row=5, column=1, sticky="w", pady=(6, 0))
    pot_combo = ttk.Combobox(
        contexte_frame,
        state="readonly",
        values=["Non renseigné", "Pot sorti du cache-pot", "Pot laissé dans le cache-pot", "Pas de cache-pot", "Non vérifié"],
        width=20
    )
    pot_combo.grid(row=6, column=1, sticky="ew")
    pot_combo.current(0)

    tk.Label(contexte_frame, text=t("drainage_delay"), bg=CARD, fg=SECONDARY, font=("Segoe UI", 8)).grid(row=7, column=0, sticky="w", pady=(6, 0))
    drainage_delai_entry = tk.Entry(contexte_frame, bg=BG, fg=TEXT, insertbackground=TEXT)
    drainage_delai_entry.grid(row=8, column=0, columnspan=2, sticky="ew")
    drainage_delai_entry.insert(0, "")

    contexte_frame.columnconfigure(0, weight=1)
    contexte_frame.columnconfigure(1, weight=1)

    tk.Label(fenetre, text=t("comment"), bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 3))
    commentaire_entry = tk.Entry(fenetre, width=42, bg=BG, fg=TEXT, insertbackground=TEXT)
    commentaire_entry.pack(fill="x", padx=20)

    rappel_var = tk.BooleanVar(value=False)
    tk.Checkbutton(
        fenetre,
        text=t("schedule_reminder"),
        variable=rappel_var,
        bg=CARD,
        fg=TEXT,
        activebackground=CARD,
        activeforeground=TEXT,
        selectcolor=BG
    ).pack(anchor="w", padx=20, pady=(12, 3))

    rappel_frame = tk.Frame(fenetre, bg=CARD)
    rappel_frame.pack(fill="x", padx=20)
    tk.Label(rappel_frame, text=t("in_days_prefix"), bg=CARD, fg=TEXT).pack(side="left")
    rappel_jours_entry = tk.Entry(rappel_frame, width=6, bg=BG, fg=TEXT, insertbackground=TEXT)
    rappel_jours_entry.pack(side="left", padx=6)
    rappel_jours_entry.insert(0, "7")
    tk.Label(rappel_frame, text=t("days"), bg=CARD, fg=TEXT).pack(side="left")

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

        commentaire_libre = commentaire_entry.get().strip()
        type_eau = type_eau_combo.get().strip()
        if type_eau == "Non renseigné":
            type_eau = None

        contexte_arrosage = []
        for libelle, combo in (
                ("Répartition", repartition_combo),
                ("Écoulement", ecoulement_combo),
                ("Cache-pot", cachepot_combo),
                ("Substrat début session", substrat_combo),
                ("Mode", progressif_combo),
                ("Pot", pot_combo)):
            valeur = combo.get().strip()
            if valeur and valeur != "Non renseigné":
                contexte_arrosage.append(f"{libelle} : {valeur}")
        delai_drainage = drainage_delai_entry.get().strip()
        if delai_drainage:
            contexte_arrosage.append(f"Délai drainage : {delai_drainage}")

        commentaire_lignes = []
        if commentaire_libre:
            commentaire_lignes.append(commentaire_libre)
        commentaire_lignes.extend(contexte_arrosage)
        commentaire = " | ".join(commentaire_lignes) or None

        confirmation = [
            f"Plante : {nom_plante}",
            f"Quantité : {quantite:g} ml" if quantite is not None else "Quantité : non renseignée",
            f"Type : {type_combo.get()}",
            f"Type d'eau : {type_eau or 'non renseigné'}",
        ]
        confirmation.extend(contexte_arrosage)
        if rappel_date:
            confirmation.append(f"Rappel : {formater_date(rappel_date)}")
        if commentaire_libre:
            confirmation.append(f"Commentaire : {commentaire_libre}")

        if not messagebox.askyesno(
            "Confirmer l'arrosage",
            "Confirmer cet arrosage ?\n\n" + "\n".join(confirmation),
            parent=fenetre
        ):
            return

        date_arrosage = datetime.now().isoformat(timespec="seconds")
        try:
            arrosage_id = database.enregistrer_arrosage_plante(
                plante_id,
                date_arrosage,
                quantite_ml=quantite,
                type_arrosage=type_combo.get(),
                commentaire=commentaire,
                rappel_date=rappel_date,
                type_eau=type_eau
            )
            demande_id = database.enregistrer_collecte_prioritaire(
                plante_id,
                arrosage_id=arrosage_id,
                date_creation=date_arrosage,
                raison="post_arrosage",
                priorite=10,
                commentaire="Collecte prioritaire déclenchée après validation d'arrosage."
            )
        except Exception:
            erreur.set("Impossible d'enregistrer l'arrosage.")
            return

        fenetre.destroy()
        actualiser_interface()
        suivi = analyser_apres_arrosage(plante_id)
        suffixe_suivi = " · suivi post-arrosage lancé" if suivi else ""
        if rappel_date:
            status_var.set(f"Arrosage enregistré · rappel prévu le {formater_date(rappel_date)}{suffixe_suivi}")
        else:
            status_var.set(f"Arrosage enregistré{suffixe_suivi}.")
        lancer_collecte_prioritaire_apres_arrosage(plante_id, demande_id, 1000)
        lancer_collecte_prioritaire_apres_arrosage(plante_id, demande_id, 10 * 60 * 1000)

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", padx=20, pady=(0, 15))
    tk.Button(boutons, text=t("save"), command=enregistrer, bg=LIGHT_GREEN, fg=TEXT, activebackground=LIGHT_GREEN, relief="flat", cursor="hand2").pack(side="right")
    tk.Button(boutons, text=t("cancel"), command=fenetre.destroy, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left")

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
    if filtre_attention == t("decision_watch") and not alerte_principale_plante(plante_id):
        return False

    return True


def reinitialiser_filtres_plantes(commande=None):
    filtre_zone_var.set("Toutes")
    filtre_piece_var.set("Toutes")
    filtre_capteur_var.set("Toutes")
    filtre_attention_var.set("Toutes")
    if commande:
        commande()
    else:
        actualiser_interface()


def creer_menu_filtre(parent, titre, variable, valeurs, commande=None):
    bloc = tk.Frame(parent, bg=CARD)
    bloc.pack(side="left", padx=(0, 10), pady=(0, 8))

    tk.Label(
        bloc,
        text=titre,
        bg=CARD,
        fg=SECONDARY,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w")

    action = commande or actualiser_interface
    menu = tk.OptionMenu(bloc, variable, *valeurs, command=lambda _=None: action())
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


def afficher_filtres_plantes(parent, plantes, plantes_filtrees, commande=None):
    bloc = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    bloc.pack(fill="x", padx=20, pady=(0, 10))

    haut = tk.Frame(bloc, bg=CARD)
    haut.pack(fill="x", padx=14, pady=(10, 4))

    tk.Label(
        haut,
        text=t("search_plants"),
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

    action = commande or actualiser_interface
    creer_menu_filtre(ligne, "Zone", filtre_zone_var, options_filtre_plantes(plantes, 4), action)
    creer_menu_filtre(ligne, "Pièce", filtre_piece_var, options_filtre_plantes(plantes, 3), action)
    creer_menu_filtre(ligne, "Capteur", filtre_capteur_var, ["Toutes", "Avec capteur", "Sans capteur"], action)
    creer_menu_filtre(ligne, "État", filtre_attention_var, ["Toutes", t("decision_watch")], action)

    tk.Button(
        ligne,
        text=t("reset"),
        command=lambda: reinitialiser_filtres_plantes(action),
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
        fraicheur_txt, fraicheur_couleur, fraicheur_fond = etat_fraicheur_mesure(date_heure)
    else:
        humidite_txt = "—"
        lumiere_txt = "—"
        mesure_txt = "aucune mesure"
        fraicheur_txt, fraicheur_couleur, fraicheur_fond = etat_fraicheur_mesure(None)

    infos = [
        ("💧 Sol", humidite_txt),
        ("☀️ Lumière", lumiere_txt),
        ("🕐 Mesure", mesure_txt),
    ]

    if dernier:
        infos.append(("💦 Arrosage", formater_date(dernier[2])))
    if rappel and rappel[9]:
        infos.append(("🔔 Rappel", formater_date(rappel[9])))

    for titre, valeur in infos:
        bloc = tk.Frame(ligne2, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        bloc.pack(side="left", expand=True, fill="x", padx=(0, 6))
        tk.Label(bloc, text=titre, font=("Segoe UI", 8), fg=SECONDARY, bg=BG).pack(pady=(4, 0))
        tk.Label(bloc, text=valeur, font=("Segoe UI", 9, "bold"), fg=TEXT, bg=BG, wraplength=150, justify="center").pack(pady=(0, 5))

    fraicheur_frame = tk.Frame(carte, bg=fraicheur_fond)
    fraicheur_frame.pack(fill="x", padx=14, pady=(0, 8))
    tk.Label(fraicheur_frame, text=fraicheur_txt, font=("Segoe UI", 9, "bold"), fg=fraicheur_couleur, bg=fraicheur_fond, anchor="w", wraplength=950, justify="left").pack(fill="x", padx=8, pady=5)

    if alerte:
        alerte_frame = tk.Frame(carte, bg=alerte["fond"])
        alerte_frame.pack(fill="x", padx=14, pady=(0, 8))
        tk.Label(alerte_frame, text=f"{alerte['titre']} · {alerte['detail']}", font=("Segoe UI", 9, "bold"), fg=alerte["couleur"], bg=alerte["fond"], anchor="w", wraplength=950, justify="left").pack(fill="x", padx=8, pady=6)

    boutons = tk.Frame(carte, bg=CARD)
    boutons.pack(fill="x", padx=14, pady=(0, 10))
    tk.Button(boutons, text=t("watering"), font=("Segoe UI", 8, "bold"), bg=LIGHT_BLUE, fg=BLUE, relief="flat", cursor="hand2", command=lambda pid=plante_id, n=nom: ouvrir_arrosage_plante(pid, n)).pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("balcony_out"), font=("Segoe UI", 8, "bold"), bg=BG, fg=ORANGE, relief="flat", cursor="hand2", command=lambda pid=plante_id, n=nom: enregistrer_evenement_balcon(pid, n, "sortie")).pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("back_inside"), font=("Segoe UI", 8, "bold"), bg=BG, fg=BLUE, relief="flat", cursor="hand2", command=lambda pid=plante_id, n=nom: enregistrer_evenement_balcon(pid, n, "retour")).pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("past_exposure"), font=("Segoe UI", 8, "bold"), bg=BG, fg=SECONDARY, relief="flat", cursor="hand2", command=lambda pid=plante_id, n=nom: ouvrir_exposition_balcon_passee(pid, n)).pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("analysis"), font=("Segoe UI", 8, "bold"), bg=LIGHT_GREEN, fg=GREEN, relief="flat", cursor="hand2", command=lambda pid=plante_id: afficher_message_analyse(pid)).pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("copy_plant_analysis"), font=("Segoe UI", 8, "bold"), bg=BG, fg=BLUE, relief="flat", cursor="hand2", command=lambda pid=plante_id: copier_analyse_plante(pid)).pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("history"), font=("Segoe UI", 8, "bold"), bg=BG, fg=TEXT, relief="flat", cursor="hand2", command=lambda pid=plante_id: afficher_message_historique(pid)).pack(side="left")


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
        humidite,
        plante_id
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
        tk.Button(capteur_frame, text=t("sensor_details"), bg=LIGHT_BLUE, fg=TEXT,
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

            texte_fraicheur, couleur_fraicheur, fond_fraicheur = etat_fraicheur_mesure(derniere_sync)
            fraicheur_frame = tk.Frame(
                capteur_frame,
                bg=fond_fraicheur
            )
            fraicheur_frame.pack(
                fill="x",
                pady=(4, 2)
            )

            tk.Label(
                fraicheur_frame,
                text=texte_fraicheur,
                font=("Segoe UI", 9, "bold"),
                fg=couleur_fraicheur,
                bg=fond_fraicheur,
                anchor="w"
            ).pack(
                fill="x",
                padx=10,
                pady=6
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
                text=t("no_sync_badge"),
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

    texte_fraicheur_mesure, couleur_fraicheur_mesure, fond_fraicheur_mesure = etat_fraicheur_mesure(date_heure)
    derniere_mesure_frame = tk.Frame(carte, bg=fond_fraicheur_mesure)
    derniere_mesure_frame.pack(fill="x", padx=20, pady=(5, 10))
    tk.Label(
        derniere_mesure_frame,
        text=(
            f"{texte_fraicheur_mesure} · "
            f"{formater_date(date_heure)}"
        ),
        font=("Segoe UI", 9, "bold"),
        fg=couleur_fraicheur_mesure,
        bg=fond_fraicheur_mesure,
        anchor="w"
    ).pack(
        fill="x",
        padx=10,
        pady=6
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
        text=t("history_analysis"),
        font=("Segoe UI", 9, "bold"),
        bg=LIGHT_GREEN,
        fg=GREEN,
        activebackground=LIGHT_GREEN,
        relief="flat",
        cursor="hand2",
        command=lambda pid=plante_id:
            ouvrir_historique(root, pid, synchroniser)
    ).pack(
        side="left",
        padx=(0, 8)
    )

    tk.Button(
        boutons,
        text=t("copy_plant_analysis"),
        font=("Segoe UI", 9, "bold"),
        bg=BG,
        fg=BLUE,
        activebackground=BG,
        activeforeground=BLUE,
        relief="flat",
        cursor="hand2",
        command=lambda pid=plante_id:
            copier_analyse_plante(pid)
    ).pack(
        side="left",
        padx=(0, 8)
    )

    tk.Button(
        boutons,
        text=t("watering"),
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
        text=t("balcony_out"),
        font=("Segoe UI", 9, "bold"),
        bg=BG,
        fg=ORANGE,
        activebackground=BG,
        activeforeground=ORANGE,
        relief="flat",
        cursor="hand2",
        command=lambda pid=plante_id, nom=nom:
            enregistrer_evenement_balcon(pid, nom, "sortie")
    ).pack(
        side="left",
        padx=(0, 8)
    )

    tk.Button(
        boutons,
        text=t("back_inside"),
        font=("Segoe UI", 9, "bold"),
        bg=BG,
        fg=BLUE,
        activebackground=BG,
        activeforeground=BLUE,
        relief="flat",
        cursor="hand2",
        command=lambda pid=plante_id, nom=nom:
            enregistrer_evenement_balcon(pid, nom, "retour")
    ).pack(
        side="left",
        padx=(0, 8)
    )

    tk.Button(
        boutons,
        text=t("past_exposure"),
        font=("Segoe UI", 9, "bold"),
        bg=BG,
        fg=SECONDARY,
        activebackground=BG,
        activeforeground=SECONDARY,
        relief="flat",
        cursor="hand2",
        command=lambda pid=plante_id, nom=nom:
            ouvrir_exposition_balcon_passee(pid, nom)
    ).pack(
        side="left",
        padx=(0, 8)
    )

    historique_disponible = plante_a_historique_mesures(plante_id)
    texte_bouton_historique = (
        "📈 Historique mesures"
        if historique_disponible
        else "📈 Historique / raccourci"
    )
    fond_bouton_historique = LIGHT_BLUE if historique_disponible else BG
    couleur_bouton_historique = TEXT if historique_disponible else SECONDARY

    tk.Button(
        boutons,
        text=texte_bouton_historique,
        font=("Segoe UI", 9, "bold"),
        bg=fond_bouton_historique,
        fg=couleur_bouton_historique,
        activebackground=fond_bouton_historique,
        activeforeground=couleur_bouton_historique,
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
            text=t("import_simple_history"),
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
            text=t("associate_sensor"),
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

    tk.Label(entete, text=t("local_forecast_2h"), font=("Segoe UI", 11, "bold"), fg=BLUE, bg=LIGHT_BLUE).pack(side="left")

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
        return True, "Station déjà présente dans les favoris Gruterra."

    return True, "Station ajoutée aux favoris Gruterra. Lance Actualiser Netatmo pour charger ses données."


def renommer_station_netatmo(station):
    station_id = id_station_netatmo(station)
    if not station_id:
        messagebox.showinfo(t("netatmo"), "Cette station n'a pas d'identifiant local utilisable.", parent=root)
        return

    fenetre = tk.Toplevel(root)
    fenetre.title(t("rename_station_title"))
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()

    tk.Label(
        fenetre,
        text=t("local_station_name"),
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
        text=t("save"),
        command=enregistrer,
        bg=LIGHT_GREEN,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        relief="flat",
        cursor="hand2"
    ).pack(side="right", padx=20, pady=10)

    tk.Button(
        boutons,
        text=t("cancel"),
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
            text=t("rename"),
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
        text=t("local_weather_summary"),
        font=("Segoe UI", 12, "bold"),
        fg=GREEN,
        bg=LIGHT_GREEN,
        anchor="w"
    ).pack(side="left")

    tk.Label(
        entete,
        text=t("best_netatmo_source"),
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
        text=t("netatmo_title"),
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

    tk.Button(titre_frame, text=t("refresh_netatmo"), command=actualiser_netatmo_seul,
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
            text=t("netatmo_no_data"),
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
            "Toujours affichées en haut. Les boutons ↑ ↓ changent leur ordre local, Renommer change seulement le nom affiché dans Gruterra."
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


def resume_acquisition_miflora(resultat_miflora):
    resultats = resultat_miflora.get("resultats") or []
    if not resultats:
        return None

    nouvelles_pc = sum(1 for resultat in resultats if resultat.get("mesure"))
    nouvelles_pi = sum(resultat.get("raspberry_current_added", 0) or 0 for resultat in resultats)
    historiques_pi = sum(resultat.get("raspberry_added", 0) or 0 for resultat in resultats)
    attente_pi = sum(1 for resultat in resultats if resultat.get("collect_accepted") is True and not resultat.get("raspberry_current_added", 0) and not resultat.get("mesure"))

    lignes = []
    if nouvelles_pc or nouvelles_pi:
        morceaux = []
        if nouvelles_pi:
            morceaux.append(f"{nouvelles_pi} via Raspberry")
        if nouvelles_pc:
            morceaux.append(f"{nouvelles_pc} via PC")
        lignes.append("✅ Nouvelle mesure effectivement acquise : " + ", ".join(morceaux) + ".")
    else:
        lignes.append("ℹ Aucune nouvelle mesure immédiate acquise sur ce passage.")

    if historiques_pi:
        lignes.append(f"Mesures rapatriées depuis le Raspberry : {historiques_pi} mesure(s) ajoutée(s) au PC. Elles peuvent avoir été collectées pendant que Gruterra était fermé.")
    if attente_pi:
        lignes.append("Mesure Raspberry demandée : résultat attendu lors du prochain contrôle automatique ou de la prochaine synchronisation.")
    return texte_interface_utf8_sur("\n".join(lignes))


def synchroniser():
    if netatmo_loading or str(sync_button['state']) == 'disabled':
        return

    sync_button.config(
        state="disabled",
        text=t("syncing")
    )

    status_var.set(
        t("sync_running_status")
    )

    sync_var.set(
        t("sync_running_summary")
    )

    sync_detail_var.set(
        t("sync_preparing")
    )

    sync_progress_var.set(
        t("sync_progress_percent").format(percent=0)
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
            t("sync_searching_miflora"),
            5
        )

        def progression_miflora(index, total, nom, etape="mesure", info=None):
            info = info or {}
            if etape == "historique_detail":
                phase = info.get("phase")
                passe = info.get("passe")
                max_passes = info.get("max_passes")
                index_depart = info.get("index_depart", 0)
                total_lues = info.get("total_lues", 0)
                history_count = info.get("history_count")
                compteur = f"{total_lues}/{history_count}" if history_count else f"{total_lues}"
                progression = 10 + int(18 * (min(passe or 1, max_passes or 5) - 1) / max(max_passes or 5, 1))

                if phase == "historique_scan_tentative":
                    texte = (
                        f"📥 Historique Mi Flora {index}/{total} : {nom} · "
                        f"scan passe {passe}/{max_passes}, tentative {info.get('tentative')}/{info.get('tentatives')} "
                        f"depuis l’entrée {index_depart} · {compteur} récupérée(s)"
                    )
                elif phase == "historique_connexion":
                    texte = (
                        f"📥 Historique Mi Flora {index}/{total} : {nom} · "
                        f"connexion Bluetooth, passe {passe}/{max_passes} · {compteur} récupérée(s)"
                    )
                elif phase == "historique_lecture":
                    texte = (
                        f"📥 Historique Mi Flora {index}/{total} : {nom} · "
                        f"lecture mémoire depuis l’entrée {index_depart}, passe {passe}/{max_passes} · {compteur} récupérée(s)"
                    )
                elif phase == "historique_passe_finie":
                    texte = (
                        f"📥 Historique Mi Flora {index}/{total} : {nom} · "
                        f"passe {passe}/{max_passes} terminée, {info.get('entries_passe', 0)} entrée(s) lue(s) · {compteur} récupérée(s)"
                    )
                elif phase == "historique_enregistrement":
                    progression = 28
                    texte = (
                        f"📥 Historique Mi Flora {index}/{total} : {nom} · "
                        f"enregistrement local, {compteur} entrée(s) récupérée(s), {info.get('passes', 0)} passe(s)"
                    )
                elif phase == "historique_raspberry":
                    texte = f"📥 Historique Mi Flora {index}/{total} : {nom} · récupération via Raspberry"
                else:
                    texte = f"📥 Historique Mi Flora {index}/{total} : {nom} · traitement en cours"
            elif etape == "historique":
                texte = f"📥 Historique Mi Flora {index}/{total} : {nom} · préparation"
                progression = 8 + int(22 * (index - 1) / max(total, 1))
            else:
                texte = f"🌱 Mesure Mi Flora {index}/{total} : {nom} · mesure directe ou Raspberry"
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
    root.after(0, afficher_etape_netatmo, t("sync_netatmo_reading"), 55)
    resultats_meteo = recuperer_sources(netatmo)
    root.after(0, afficher_etape_netatmo, t("sync_forecast_reading"), 70)
    recuperer_prevision_2h_avec_cache()
    root.after(0, synchronisation_terminee, resultat_miflora, resultats_meteo)


def controle_raspberry_a_programmer(resultat_miflora):
    for resultat in resultat_miflora.get("resultats", []) or []:
        raspberry_resultat = resultat.get("raspberry_result") or {}
        if not raspberry_resultat:
            # Quand le Raspberry suffit, ses champs sont directement dans le résultat capteur.
            raspberry_resultat = resultat
        if raspberry_resultat.get("collect_accepted") is not True:
            continue
        if (raspberry_resultat.get("current_added", 0) or 0) > 0:
            continue
        return True
    return False


def programmer_controle_raspberry(delai_ms=2 * 60 * 1000):
    def lancer():
        if str(sync_button['state']) == 'disabled':
            root.after(60 * 1000, lancer)
            return
        status_var.set(t("sync_raspberry_auto_check"))

        def arriere_plan():
            try:
                resultat = raspberry_sync.synchronize(collect_now=False)
            except Exception as erreur:
                resultat = {"ok": False, "message": t("sync_raspberry_check_failed").format(error=erreur)}

            def terminer():
                message = resultat.get("message", t("sync_raspberry_check_done"))
                if resultat.get("ok"):
                    status_var.set(t("sync_raspberry_check_done_with_message").format(message=message))
                    actualiser_interface()
                else:
                    status_var.set(message)

            root.after(0, terminer)

        threading.Thread(target=arriere_plan, daemon=True).start()

    root.after(delai_ms, lancer)


def controles_humidite_zero_a_programmer(resultat_miflora):
    controles = []
    deja_vus = set()
    for resultat in resultat_miflora.get("resultats", []) or []:
        mesure = resultat.get("mesure") or {}
        try:
            humidite = float(mesure.get("humidite"))
        except (TypeError, ValueError):
            continue
        if humidite != 0:
            continue
        plante_id = mesure.get("plante_id")
        capteur_id = resultat.get("capteur_id") or mesure.get("capteur_id")
        cle = (plante_id, capteur_id)
        if cle in deja_vus:
            continue
        deja_vus.add(cle)
        controles.append({
            "plante_id": plante_id,
            "nom": resultat.get("nom") or mesure.get("capteur") or "Mi Flora",
            "date": mesure.get("date_heure")
        })
    return controles


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
            t("sync_miflora_done"),
            90
        )

    else:

        afficher_etape_netatmo(
            "⚠ Mi Flora : "
            + resultat_miflora.get(
                "message",
                t("sync_error_fallback")
            ),
            90
        )

    # --------------------------------------------------------
    # Actualisation
    # --------------------------------------------------------

    actualiser_interface()
    afficher_netatmo()

    def rafraichir_apres_synchronisation():
        """Relit l'affichage peu après la synchro pour éviter un reste visuel."""
        try:
            actualiser_interface()
            if meteo_affichee_en_haut():
                afficher_netatmo()
        except Exception:
            pass

    root.after(1500, rafraichir_apres_synchronisation)

    sources_en_echec = []
    if not resultat_miflora.get("ok"):
        sources_en_echec.append("Mi Flora")
    if erreur_netatmo or donnees_netatmo is None:
        sources_en_echec.append(t("sync_netatmo_private_source"))
    if erreur_netatmo_publique:
        sources_en_echec.append(t("sync_netatmo_public_source"))
    bilan_sync = t("sync_finished_with_errors") if sources_en_echec else t("sync_finished")
    sync_var.set(
        bilan_sync + " · "
        + f"{datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}"
    )

    lignes_detail = [resultat_miflora.get("message", t("sync_miflora_default_done"))]
    lignes_detail.append(t("sync_display_refreshed"))
    acquisition_miflora = resume_acquisition_miflora(resultat_miflora)
    if acquisition_miflora:
        lignes_detail.append(acquisition_miflora)

    historiques_incomplets = resultat_miflora.get("historiques_incomplets") or []
    historiques_complets = resultat_miflora.get("historiques_complets") or []
    if historiques_incomplets:
        lignes_detail.append(t("sync_history_missing_title"))
        for historique in historiques_incomplets:
            lignes_detail.append(
                t("sync_history_missing_line").format(
                    name=historique.get('nom'),
                    read=historique.get('historique_total_lues', 0),
                    total=historique.get('historique_total_annonce', '?'),
                    missing=historique.get('historique_manque', 0),
                    passes=historique.get('historique_passes', '?'),
                    max_passes=historique.get('historique_passes_max', '?'),
                )
            )
        lignes_detail.append(t("sync_history_missing_help"))
    elif historiques_complets:
        lignes_detail.append(t("sync_history_complete"))

    if controle_raspberry_a_programmer(resultat_miflora):
        programmer_controle_raspberry()
        lignes_detail.append(
            t("sync_raspberry_pending")
        )

    controles_zero = controles_humidite_zero_a_programmer(resultat_miflora)
    for controle in controles_zero:
        if controle.get("plante_id"):
            lancer_controle_humidite_zero(controle["plante_id"])
        lignes_detail.append(
            t("sync_zero_humidity_warning").format(name=controle.get('nom'))
        )

    if resultat_miflora.get('detail'):
        lignes_detail.append(resultat_miflora['detail'])
    if sources_en_echec:
        lignes_detail.append(t("sync_to_check").format(sources=", ".join(sources_en_echec)))

    sync_detail_var.set("\n".join(lignes_detail))

    sync_progress_var.set(
        t("sync_progress_percent").format(percent=100)
    )

    status_var.set(
        t("system_active")
    )

    global derniere_operation_bluetooth
    derniere_operation_bluetooth = datetime.now()

    sync_button.config(
        state="normal",
        text=t("sync_plain")
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



def git_revision_courte():
    try:
        resultat = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        if resultat.returncode == 0:
            return resultat.stdout.strip()
    except Exception:
        pass
    return "non disponible"


def etat_raspberry_a_propos():
    try:
        chemin = CONFIG_DIR / "raspberry.local.json"
        if not chemin.exists():
            return "Non configuré sur ce poste"
        config = lire_json(chemin)
        if not config.get("enabled", False):
            return "Configuration présente, mais Raspberry désactivé"
        capteurs = len(config.get("sensors", []) or [])
        return f"Activé · {capteurs} capteur(s) déclaré(s)"
    except Exception:
        return "Configuration présente, à vérifier"


def resume_mise_a_jour_a_propos(racine, verifier_distant=False):
    try:
        diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(racine, verifier_distant=verifier_distant)
        return texte_interface_utf8_sur(botaneo_update.formater_diagnostic_mise_a_jour(diagnostic))
    except Exception as erreur:
        return f"Mise à jour : diagnostic indisponible ({erreur})"


def texte_diagnostic_update_json_a_propos(verifier_distant=False):
    racine = Path(__file__).resolve().parent.parent
    try:
        diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(racine, verifier_distant=verifier_distant)
        return texte_interface_utf8_sur(botaneo_update.exporter_diagnostic_mise_a_jour_json(diagnostic))
    except Exception as erreur:
        return json.dumps(
            {
                t("sync_error_fallback"): "diagnostic mise à jour indisponible",
                "message": str(erreur),
                "application_autorisee": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )



def patch_note_update_a_propos(verifier_distant=True):
    racine = Path(__file__).resolve().parent.parent
    try:
        diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(racine, verifier_distant=verifier_distant)
    except Exception as erreur:
        return f"Patch note indisponible : {erreur}"
    version = diagnostic.get("version", {})
    version_distante = version.get("version_distante") or version.get("version") or "version non précisée"
    notes = str(version.get("notes") or "").strip()
    lignes = [
        "Patch note Gruterra",
        f"Version : {version_distante}",
    ]
    if notes:
        lignes.extend(["", notes])
    else:
        lignes.extend(["", "Aucune note de version détaillée n'est fournie par le manifeste."])
    return texte_interface_utf8_sur("\n".join(lignes))


def executer_assistant_update_a_propos(appliquer=False):
    racine = Path(__file__).resolve().parent.parent
    script = racine / "update_gruterra.py"
    if not script.exists():
        return "Assistant update introuvable : update_gruterra.py"
    commande = ["py", str(script), "--apply" if appliquer else "--dry-run"]
    environnement = os.environ.copy()
    environnement["PYTHONIOENCODING"] = "utf-8"
    environnement["PYTHONUTF8"] = "1"
    try:
        resultat = subprocess.run(
            commande,
            cwd=str(racine),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environnement,
            timeout=180,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        return "Assistant update interrompu : délai dépassé."
    except Exception as erreur:
        return f"Assistant update indisponible : {erreur}"

    sortie = (resultat.stdout or "").strip()
    erreur = (resultat.stderr or "").strip()
    lignes = [
        "Assistant update Gruterra",
        f"Mode : {'application' if appliquer else 'simulation'}",
        f"Code retour : {resultat.returncode}",
        "",
    ]
    if sortie:
        lignes.append(sortie)
    if erreur:
        lignes.extend(["", "Erreurs :", erreur])
    if appliquer:
        lignes.extend(["", patch_note_update_a_propos(verifier_distant=True)])
    return texte_interface_utf8_sur("\n".join(lignes)).strip()



def update_appliquee_depuis_resultat(contenu):
    texte = str(contenu or "")
    return "Code retour : 0" in texte and "Mise à jour appliquée" in texte


def script_lancement_courant(racine):
    if os.environ.get("BOTANEO_DEMO") == "1":
        return racine / "Lancer_Demo.py"
    return racine / "Lancer_Gruterra.py"


def redemarrer_gruterra(parent=None):
    racine = Path(__file__).resolve().parent.parent
    script = script_lancement_courant(racine)
    if not script.exists():
        messagebox.showwarning(
            t("update_restart_title"),
            t("update_restart_missing_launcher"),
            parent=parent,
        )
        return False
    environnement = os.environ.copy()
    environnement["PYTHONIOENCODING"] = "utf-8"
    environnement["PYTHONUTF8"] = "1"
    try:
        subprocess.Popen(
            [sys.executable, str(script)],
            cwd=str(racine),
            env=environnement,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    except Exception as erreur:
        messagebox.showwarning(
            t("update_restart_title"),
            f"{t('update_restart_failed')}\n\n{erreur}",
            parent=parent,
        )
        return False
    status_var.set(t("update_restarting"))
    root.after(500, root.destroy)
    return True


def proposer_redemarrage_apres_update(parent, contenu):
    if not update_appliquee_depuis_resultat(contenu):
        status_var.set(t("update_apply_done"))
        return
    status_var.set(t("update_restart_advised"))
    if messagebox.askyesno(
        t("update_restart_title"),
        t("update_restart_question"),
        parent=parent,
    ):
        redemarrer_gruterra(parent=parent)


def lancer_application_update(parent, afficher_resultat=None):
    if not messagebox.askyesno(
        t("update_apply_title"),
        t("update_apply_confirm"),
        parent=parent,
    ):
        return
    status_var.set(t("update_apply_running"))

    def tache():
        contenu = executer_assistant_update_a_propos(appliquer=True)

        def terminer():
            if afficher_resultat:
                afficher_resultat(contenu)
            else:
                messagebox.showinfo(
                    t("update_apply_result_title"),
                    contenu + "\n\n" + t("update_restart_hint"),
                    parent=parent,
                )
            proposer_redemarrage_apres_update(parent, contenu)

        root.after(0, terminer)

    threading.Thread(target=tache, daemon=True).start()


def update_installable_depuis_diagnostic(diagnostic):
    version = diagnostic.get("version", {}) if isinstance(diagnostic, dict) else {}
    statut_version = version.get("statut")
    archive_url = str(version.get("archive_url") or "").strip()
    sha256 = str(version.get("sha256") or "").strip()
    auto_update = bool(version.get("manifest_auto_update"))
    version_disponible = statut_version in {"mise_a_jour_disponible", "version_stable_disponible"}
    protections_ok = diagnostic.get("statut_global") != "bloque"
    return version_disponible and protections_ok and auto_update and archive_url and len(sha256) == 64


def verifier_update_au_demarrage():
    if os.environ.get("BOTANEO_DEMO") == "1":
        return

    racine = Path(__file__).resolve().parent.parent

    def tache():
        try:
            diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(racine, verifier_distant=True)
        except Exception:
            return
        if not update_installable_depuis_diagnostic(diagnostic):
            return

        version = diagnostic.get("version", {})
        version_distante = version.get("version_distante") or version.get("version") or "nouvelle version"
        notes = str(version.get("notes") or "").strip()

        def proposer():
            message = (
                f"Une mise à jour Gruterra est disponible : {version_distante}.\n\n"
                "Voulez-vous la télécharger et l'appliquer maintenant ?\n\n"
                "Vous pouvez répondre Non et continuer à utiliser Gruterra normalement, "
                "y compris synchroniser les capteurs."
            )
            if notes:
                message += f"\n\nNotes : {notes[:500]}"
            if not messagebox.askyesno(t("update_available_title"), message, parent=root):
                status_var.set(t("update_ignored"))
                return

            status_var.set(t("update_downloading"))

            def appliquer():
                resultat = executer_assistant_update_a_propos(appliquer=True)

                def terminer():
                    messagebox.showinfo(
                        t("update_apply_result_title"),
                        resultat + "\n\n" + t("update_restart_hint"),
                        parent=root,
                    )
                    proposer_redemarrage_apres_update(root, resultat)

                root.after(0, terminer)

            threading.Thread(target=appliquer, daemon=True).start()

        root.after(0, proposer)

    threading.Thread(target=tache, daemon=True).start()


def texte_a_propos(verifier_distant=False):
    racine = Path(__file__).resolve().parent.parent
    lignes = [
        "Gruterra",
        f"Version locale : {APP_VERSION}",
        f"Révision Git : {git_revision_courte()}",
        "",
        "Dossiers principaux :",
        f"- Projet : {racine}",
        f"- Application : {Path(__file__).resolve().parent}",
        f"- Base locale : {database.DB_PATH}",
        f"- Réglages personnels : {CONFIG_DIR}",
        "",
        "Fonctions principales :",
        "- suivi de plantes avec ou sans capteur",
        "- Mi Flora : mesure directe, historique et batterie",
        "- Raspberry optionnel : collecte et rattrapage",
        "- Netatmo privé/public et météo locale",
        "- arrosage manuel, rappels et alertes locales",
        "- historique graphique avec qualité des données",
        "",
        f"Raspberry : {etat_raspberry_a_propos()}",
        "",
        resume_mise_a_jour_a_propos(racine, verifier_distant=verifier_distant),
        "",
        "Sécurité :",
        "- les accès privés, bases réelles et sauvegardes restent sur ce PC",
        "- lancer py verifier_avant_github.py avant tout envoi GitHub",
        "- les documents privés de passation ne sont pas publiés",
    ]
    return texte_interface_utf8_sur("\n".join(lignes))


def ouvrir_a_propos():
    fenetre = tk.Toplevel(root)
    fenetre.title(t("about_title"))
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)

    tk.Label(
        fenetre,
        text="🌿 Gruterra",
        font=("Segoe UI", 18, "bold"),
        fg=GREEN,
        bg=CARD
    ).pack(anchor="w", padx=20, pady=(18, 4))

    tk.Label(
        fenetre,
        text=t("about_subtitle"),
        font=("Segoe UI", 10),
        fg=SECONDARY,
        bg=CARD
    ).pack(anchor="w", padx=20, pady=(0, 12))

    zone = tk.Text(
        fenetre,
        width=86,
        height=25,
        wrap="word",
        bg=BG,
        fg=TEXT,
        relief="flat",
        font=("Segoe UI", 9)
    )
    zone.pack(fill="both", expand=True, padx=20, pady=(0, 12))
    zone.insert("1.0", texte_a_propos(verifier_distant=False))
    zone.configure(state="disabled")

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", padx=20, pady=(0, 16))

    dernier_verifier_distant = {"valeur": False}

    def remplacer_texte_a_propos(contenu):
        zone.configure(state="normal")
        zone.delete("1.0", "end")
        zone.insert("1.0", contenu)
        zone.configure(state="disabled")

    def verifier_mise_a_jour():
        status_var.set(t("update_checking"))
        dernier_verifier_distant["valeur"] = True
        contenu = texte_a_propos(verifier_distant=True) + "\n\n" + patch_note_update_a_propos(verifier_distant=True)
        remplacer_texte_a_propos(contenu)
        status_var.set(t("update_check_done"))

    def lancer_update_simule():
        status_var.set(t("update_sim_running"))

        def tache():
            contenu = executer_assistant_update_a_propos(appliquer=False)
            root.after(0, lambda: remplacer_texte_a_propos(contenu))
            root.after(0, lambda: status_var.set(t("update_sim_done")))

        threading.Thread(target=tache, daemon=True).start()

    def appliquer_update():
        lancer_application_update(fenetre, afficher_resultat=remplacer_texte_a_propos)

    def copier():
        root.clipboard_clear()
        root.clipboard_append(texte_a_propos(verifier_distant=dernier_verifier_distant["valeur"]))
        status_var.set(t("about_copied"))

    def copier_diagnostic_update_json():
        root.clipboard_clear()
        root.clipboard_append(texte_diagnostic_update_json_a_propos(verifier_distant=dernier_verifier_distant["valeur"]))
        status_var.set(t("update_json_copied"))

    tk.Button(
        boutons,
        text=t("copy"),
        command=copier,
        bg=LIGHT_BLUE,
        fg=BLUE,
        activebackground=LIGHT_BLUE,
        relief="flat",
        cursor="hand2"
    ).pack(side="left")

    tk.Button(
        boutons,
        text=t("copy_update_json"),
        command=copier_diagnostic_update_json,
        bg=BG,
        fg=TEXT,
        activebackground=BG,
        relief="flat",
        cursor="hand2"
    ).pack(side="left", padx=(8, 0))

    tk.Button(
        boutons,
        text=t("check_updates"),
        command=verifier_mise_a_jour,
        bg=LIGHT_GREEN,
        fg=GREEN,
        activebackground=LIGHT_GREEN,
        relief="flat",
        cursor="hand2"
    ).pack(side="left", padx=(8, 0))

    tk.Button(
        boutons,
        text=t("update"),
        command=lancer_update_simule,
        bg=LIGHT_ORANGE,
        fg=ORANGE,
        activebackground=LIGHT_ORANGE,
        relief="flat",
        cursor="hand2"
    ).pack(side="left", padx=(8, 0))

    tk.Button(
        boutons,
        text=t("apply_update"),
        command=appliquer_update,
        bg=LIGHT_RED,
        fg=RED,
        activebackground=LIGHT_RED,
        relief="flat",
        cursor="hand2"
    ).pack(side="left", padx=(8, 0))

    tk.Button(
        boutons,
        text=t("close"),
        command=fenetre.destroy,
        bg=BG,
        fg=TEXT,
        relief="flat",
        cursor="hand2"
    ).pack(side="right")


def format_octets(nombre):
    try:
        valeur = float(nombre)
    except (TypeError, ValueError):
        valeur = 0
    unites = ["o", "Ko", "Mo", "Go", "To"]
    index = 0
    while valeur >= 1024 and index < len(unites) - 1:
        valeur /= 1024
        index += 1
    if index == 0:
        return f"{int(valeur)} {unites[index]}"
    return f"{valeur:.2f} {unites[index]}"


def format_valeur_synthese(valeur, suffixe="", decimales=0):
    if valeur is None:
        return "—"
    try:
        nombre = float(valeur)
    except (TypeError, ValueError):
        return "—"
    if decimales:
        texte = f"{nombre:.{decimales}f}"
    elif nombre.is_integer():
        texte = str(int(nombre))
    else:
        texte = f"{nombre:.1f}"
    return f"{texte}{suffixe}"


def format_plage_synthese(minimum, maximum, suffixe=""):
    if minimum is None and maximum is None:
        return "—"
    if minimum == maximum:
        return format_valeur_synthese(minimum, suffixe)
    return f"{format_valeur_synthese(minimum)}–{format_valeur_synthese(maximum, suffixe)}"


def texte_maintenance():
    diagnostic = database.diagnostic_compactage_mesures()
    try:
        nombre_mesures = database.get_nombre_mesures()
    except Exception:
        nombre_mesures = "indisponible"
    try:
        syntheses = database.lister_syntheses_journalieres(limite=8)
        toutes_syntheses = database.lister_syntheses_journalieres(limite=100000)
        syntheses_info = f"{len(toutes_syntheses)} synthèse(s) calculée(s)" if toutes_syntheses else "aucune synthèse calculée"
    except Exception:
        syntheses = []
        syntheses_info = "table non initialisée"

    etat = "allègement à envisager plus tard" if diagnostic.get("compactage_conseille") else "aucune action nécessaire"
    lignes = [
        "Données & résumés Gruterra",
        "",
        f"Fichier de données utilisé : {database.DB_PATH}",
        f"Volume actuel : {format_octets(diagnostic.get('taille_octets'))}",
        f"Seuil à partir duquel un allègement pourra être proposé : {format_octets(diagnostic.get('seuil_octets'))}",
        f"État : {etat}",
        f"Mesures conservées : {nombre_mesures}",
        f"Résumés par jour : {syntheses_info}",
        "",
        "Règles actuelles :",
        "- aucune suppression automatique de mesures brutes",
        "- aucun allègement automatique",
        "- les résumés par jour servent seulement à mieux lire l’historique",
        "- aucune opération qui supprime des mesures n’est autorisée automatiquement",
        "",
        "Prochaine étape future : afficher et valider les résumés avant d’envisager un allègement des très anciennes mesures.",
    ]

    return texte_interface_utf8_sur("\n".join(lignes))


def ouvrir_maintenance():
    fenetre = tk.Toplevel(root)
    fenetre.title(t("maintenance_title"))
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)

    tk.Label(fenetre, text=t("maintenance"), font=("Segoe UI", 18, "bold"), fg=GREEN, bg=CARD).pack(anchor="w", padx=20, pady=(18, 4))
    tk.Label(fenetre, text=t("maintenance_subtitle"), font=("Segoe UI", 10), fg=SECONDARY, bg=CARD).pack(anchor="w", padx=20, pady=(0, 12))

    zone = tk.Text(fenetre, width=86, height=14, wrap="word", bg=BG, fg=TEXT, relief="flat", font=("Segoe UI", 9))
    zone.pack(fill="both", expand=True, padx=20, pady=(0, 12))

    tk.Label(fenetre, text=t("latest_summaries"), font=("Segoe UI", 10, "bold"), fg=TEXT, bg=CARD).pack(anchor="w", padx=20, pady=(0, 6))
    tableau_frame = tk.Frame(fenetre, bg=CARD)
    tableau_frame.pack(fill="both", expand=False, padx=20, pady=(0, 12))
    colonnes = ("jour", "plante", "capteur", "mesures", "humidite", "lumiere", "sources")
    tableau_syntheses = ttk.Treeview(tableau_frame, columns=colonnes, show="headings", height=6)
    tableau_syntheses.heading("jour", text=t("day"))
    tableau_syntheses.heading("plante", text=t("plant"))
    tableau_syntheses.heading("capteur", text=t("sensor"))
    tableau_syntheses.heading("mesures", text=t("measurements"))
    tableau_syntheses.heading("humidite", text=t("humidity"))
    tableau_syntheses.heading("lumiere", text=t("max_light"))
    tableau_syntheses.heading("sources", text=t("sources"))
    tableau_syntheses.column("jour", width=95, anchor="center")
    tableau_syntheses.column("plante", width=130, anchor="w")
    tableau_syntheses.column("capteur", width=110, anchor="w")
    tableau_syntheses.column("mesures", width=80, anchor="center")
    tableau_syntheses.column("humidite", width=95, anchor="center")
    tableau_syntheses.column("lumiere", width=105, anchor="center")
    tableau_syntheses.column("sources", width=190, anchor="w")
    tableau_syntheses.pack(side="left", fill="both", expand=True)
    scrollbar_syntheses = ttk.Scrollbar(tableau_frame, orient="vertical", command=tableau_syntheses.yview)
    scrollbar_syntheses.pack(side="right", fill="y")
    tableau_syntheses.configure(yscrollcommand=scrollbar_syntheses.set)
    tableau_syntheses.bind("<Double-1>", lambda _event: ouvrir_detail_synthese())

    def rafraichir():
        zone.configure(state="normal")
        zone.delete("1.0", "end")
        zone.insert("1.0", texte_maintenance())
        zone.configure(state="disabled")
        for item in tableau_syntheses.get_children():
            tableau_syntheses.delete(item)
        try:
            syntheses = database.lister_syntheses_journalieres(limite=50)
        except Exception:
            syntheses = []
        for row in syntheses:
            if hasattr(database, "synthese_journaliere_exploitable") and not database.synthese_journaliere_exploitable(row):
                continue
            infos_capteur = database.get_infos_capteur_pour_synthese(row[1])
            tableau_syntheses.insert("", "end", values=(
                row[2],
                infos_capteur["plante_nom"],
                row[1],
                row[5],
                format_plage_synthese(row[9], row[10], " %"),
                format_valeur_synthese(row[13], " lux"),
                row[18] or "—",
            ))

    def copier():
        texte = texte_maintenance()
        root.clipboard_clear()
        root.clipboard_append(texte)
        status_var.set("Données & résumés copiés dans le presse-papiers")

    def ouvrir_detail_synthese():
        selection = tableau_syntheses.selection()
        if not selection:
            messagebox.showinfo("Synthèse", "Sélectionnez une synthèse dans le tableau.", parent=fenetre)
            return
        valeurs = tableau_syntheses.item(selection[0], "values")
        if not valeurs:
            return
        jour = valeurs[0]
        capteur_id = int(valeurs[2])
        syntheses = database.lister_syntheses_journalieres(capteur_id=capteur_id, limite=500)
        synthese = None
        for row in syntheses:
            if row[2] == jour:
                synthese = row
                break
        if synthese is None:
            messagebox.showwarning("Synthèse", "Synthèse introuvable ou déjà modifiée.", parent=fenetre)
            return

        detail = tk.Toplevel(fenetre)
        detail.title(f"Synthèse {jour}")
        detail.configure(bg=CARD)
        detail.resizable(False, False)
        detail.transient(fenetre)

        infos_capteur = database.get_infos_capteur_pour_synthese(capteur_id)
        lignes = [
            f"Jour : {synthese[2]}",
            f"Plante : {infos_capteur['plante_nom']}",
            f"Capteur : {infos_capteur['capteur_nom']} (ID {synthese[1]})",
            f"Adresse BLE : {infos_capteur['adresse_ble']}",
            f"Première mesure : {synthese[3]}",
            f"Dernière mesure : {synthese[4]}",
            f"Nombre de mesures : {synthese[5]}",
            "",
            f"Température : min {synthese[6]} °C · max {synthese[7]} °C · moyenne {synthese[8]:.2f} °C",
            f"Humidité : min {synthese[9]} % · max {synthese[10]} % · moyenne {synthese[11]:.2f} %",
            f"Luminosité : min {synthese[12]} lux · max {synthese[13]} lux · moyenne {synthese[14]:.2f} lux",
            f"Conductivité : min {synthese[15]} µS/cm · max {synthese[16]} µS/cm · moyenne {synthese[17]:.2f} µS/cm",
            "",
            f"Sources : {synthese[18]}",
            f"Créée le : {synthese[19]}",
            f"Statut : {synthese[20]}",
            "",
            "Cette synthèse est informative. Les mesures brutes sont conservées.",
        ]
        texte_detail = "\n".join(lignes)

        tk.Label(detail, text=t("summary_detail_title"), font=("Segoe UI", 16, "bold"), fg=GREEN, bg=CARD).pack(anchor="w", padx=18, pady=(16, 4))
        zone_detail = tk.Text(detail, width=82, height=21, wrap="word", bg=BG, fg=TEXT, relief="flat", font=("Segoe UI", 9))
        zone_detail.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        zone_detail.insert("1.0", texte_detail)
        zone_detail.configure(state="disabled")

        boutons_detail = tk.Frame(detail, bg=CARD)
        boutons_detail.pack(fill="x", padx=18, pady=(0, 14))

        def copier_detail():
            root.clipboard_clear()
            root.clipboard_append(texte_detail)
            status_var.set("Détail de synthèse copié dans le presse-papiers")

        tk.Button(boutons_detail, text=t("copy"), command=copier_detail, bg=LIGHT_BLUE, fg=BLUE, activebackground=LIGHT_BLUE, relief="flat", cursor="hand2").pack(side="left")
        tk.Button(boutons_detail, text=t("close"), command=detail.destroy, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="right")

    def preparer_syntheses():
        if not messagebox.askyesno(
            "Préparer les synthèses",
            "Préparer les synthèses journalières existantes ?\n\nAucune mesure brute ne sera supprimée.",
            parent=fenetre
        ):
            return
        resultat = database.preparer_syntheses_journalieres()
        rafraichir()
        messagebox.showinfo(
            "Synthèses préparées",
            f"{resultat['syntheses_preparees']} synthèse(s) préparée(s).\n"
            f"{resultat['jours_ignores']} jour(s) ignoré(s).\n\n"
            "Aucune mesure brute n'a été supprimée.",
            parent=fenetre
        )
        status_var.set("Synthèses journalières préparées sans suppression")

    def creer_sauvegarde(mode):
        if mode == "complete":
            if not messagebox.askyesno(
                t("private_full_backup"),
                sauvegarde_utilisateur.AVERTISSEMENT_SAUVEGARDE_PRIVEE
                + "\n\n" + t("create_private_backup_question"),
                parent=fenetre,
            ):
                return
        try:
            racine_gruterra = Path(__file__).resolve().parent.parent
            archive = sauvegarde_utilisateur.creer_sauvegarde_utilisateur(racine_gruterra, mode=mode)
            manifest = sauvegarde_utilisateur.construire_manifest_sauvegarde(racine_gruterra, mode=mode)
            rapport = sauvegarde_utilisateur.formater_rapport_sauvegarde(manifest)
        except Exception as erreur:
            messagebox.showerror(t("backup_error_title"), f"{t('backup_impossible')} : {erreur}", parent=fenetre)
            status_var.set(t("backup_status_impossible"))
            return

        root.clipboard_clear()
        root.clipboard_append(str(archive))
        messagebox.showinfo(
            t("backup_error_title"),
            f"{t('backup_created')} :\n{archive}\n\n{t('backup_path_copied')}\n\n{rapport}",
            parent=fenetre,
        )
        status_var.set(f"{t('backup_status_created')} : {archive.name}")

    rafraichir()

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", padx=20, pady=(0, 16))
    tk.Button(boutons, text=t("refresh_button"), command=rafraichir, bg=LIGHT_GREEN, fg=GREEN, activebackground=LIGHT_GREEN, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("copy"), command=copier, bg=LIGHT_BLUE, fg=BLUE, activebackground=LIGHT_BLUE, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("prepare_summaries"), command=preparer_syntheses, bg=LIGHT_ORANGE, fg=ORANGE, activebackground=LIGHT_ORANGE, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("export_my_data"), command=lambda: creer_sauvegarde("donnees"), bg=LIGHT_BLUE, fg=BLUE, activebackground=LIGHT_BLUE, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("private_full_backup"), command=lambda: creer_sauvegarde("complete"), bg=LIGHT_ORANGE, fg=ORANGE, activebackground=LIGHT_ORANGE, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("summary_detail"), command=ouvrir_detail_synthese, bg=BG, fg=TEXT, activebackground=BG, relief="flat", cursor="hand2").pack(side="left")
    tk.Button(boutons, text=t("close"), command=fenetre.destroy, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="right")

def format_duree_courte(secondes):
    if secondes is None:
        return "inconnue"
    try:
        secondes = int(secondes)
    except (TypeError, ValueError):
        return "inconnue"
    jours, reste = divmod(max(secondes, 0), 86400)
    heures, reste = divmod(reste, 3600)
    minutes = reste // 60
    if jours:
        return f"{jours} j {heures} h"
    if heures:
        return f"{heures} h {minutes} min"
    return f"{minutes} min"


def resume_sante_raspberry(etat=None):
    etat = etat if etat is not None else raspberry_sync.health_status()
    if not etat.get("ok"):
        return {
            "etat": etat,
            "texte": f"Raspberry indisponible · {etat.get('message', 'aucun détail')}",
            "couleur": RED,
            "fond": LIGHT_RED,
        }
    disque = etat.get("disk") or {}
    memoire = etat.get("memory") or {}
    statut = etat.get("status") or "ok"
    alertes = etat.get("warnings") or []
    libelle = "OK" if statut == "ok" and not alertes else "à surveiller"
    texte = (
        f"Raspberry {libelle} · {etat.get('hostname', 'Raspberry')} · "
        f"{etat.get('temperature_c', 'n/d')} °C · "
        f"disque libre {disque.get('free_percent', 'n/d')} % · "
        f"mémoire {memoire.get('available_percent', 'n/d')} %"
    )
    return {
        "etat": etat,
        "texte": texte,
        "couleur": GREEN if libelle == "OK" else ORANGE,
        "fond": LIGHT_GREEN if libelle == "OK" else LIGHT_ORANGE,
    }


def lignes_sante_raspberry(etat=None):
    etat = etat if etat is not None else raspberry_sync.health_status()
    lignes = ["Raspberry :"]
    if not etat.get("ok"):
        lignes.append(f"- Indisponible ou désactivé : {etat.get('message', 'aucun détail')}")
        return lignes

    disque = etat.get("disk") or {}
    memoire = etat.get("memory") or {}
    charge = etat.get("load_average") or {}
    statut = etat.get("status") or "ok"
    libelle_statut = "OK" if statut == "ok" else "à surveiller"
    lignes.extend([
        f"- État : {libelle_statut} · {etat.get('hostname', 'Raspberry')}",
        f"- Température : {etat.get('temperature_c', 'n/d')} °C",
        f"- Disque libre : {disque.get('free_percent', 'n/d')} % ({format_octets(disque.get('free_bytes'))} libres)",
        f"- Mémoire disponible : {memoire.get('available_percent', 'n/d')} % ({format_octets(memoire.get('available_bytes'))})",
        f"- Charge : {charge.get('1m', 'n/d')} / {charge.get('5m', 'n/d')} / {charge.get('15m', 'n/d')}",
        f"- Dossier Gruterra inscriptible : {'oui' if etat.get('writable') else 'non'}",
        f"- Sauvegardes locales Raspberry : {etat.get('backup_files', 0)} fichier(s)",
        f"- Fonctionne depuis : {format_duree_courte(etat.get('uptime_seconds'))}",
    ])
    alertes = etat.get("warnings") or []
    erreurs_disque = etat.get("disk_errors") or []
    if alertes:
        lignes.append("- Alertes : " + "; ".join(str(alerte) for alerte in alertes))
    if erreurs_disque:
        lignes.append(f"- Erreurs disque récentes détectées : {len(erreurs_disque)} ligne(s)")
    else:
        lignes.append("- Erreurs disque récentes : aucune détectée")
    return lignes


def texte_sante_systeme(etat_raspberry=None):
    diagnostic = database.get_diagnostic_global()
    base = diagnostic["base"]
    syntheses = diagnostic["syntheses"]
    lignes = [
        "État Gruterra & Raspberry",
        "",
        f"Base : {database.DB_PATH}",
        f"Taille base : {format_octets(base.get('taille_octets'))} / seuil {format_octets(base.get('seuil_octets'))}",
        f"Mesures brutes : {diagnostic['nombre_mesures']}",
        f"Mesures entièrement à zéro : {diagnostic.get('mesures_entierement_zero', 0)}",
        f"Synthèses : {syntheses['nombre']} ({syntheses['premier_jour']} → {syntheses['dernier_jour']})",
        f"Synthèses entièrement à zéro : {diagnostic.get('syntheses_entierement_zero', 0)}",
        f"Allègement conseillé plus tard : {'oui' if base.get('compactage_conseille') else 'non'}",
        "",
    ]
    lignes.extend(lignes_sante_raspberry(etat_raspberry))
    lignes.extend(["", "Capteurs :"])
    for capteur in diagnostic["capteurs"]:
        lignes.append(
            f"- {capteur[3] or 'Sans plante'} · {capteur[1] or 'Capteur'} · "
            f"{capteur[4]} mesure(s), dernière {capteur[5] or 'jamais'}, "
            f"passif {capteur[6] or 0}, historique {capteur[8] or 0}"
        )
    return texte_interface_utf8_sur("\n".join(lignes))


def ouvrir_sante_systeme():
    fenetre = tk.Toplevel(root)
    fenetre.title(t("health_title"))
    fenetre.configure(bg=CARD)
    fenetre.resizable(True, True)
    fenetre.transient(root)

    tk.Label(fenetre, text=t("health_header"), font=("Segoe UI", 18, "bold"), fg=GREEN, bg=CARD).pack(anchor="w", padx=20, pady=(18, 4))
    tk.Label(fenetre, text=t("health_subtitle"), font=("Segoe UI", 10), fg=SECONDARY, bg=CARD).pack(anchor="w", padx=20, pady=(0, 12))

    resume_raspberry_var = tk.StringVar(value="Raspberry : contrôle en cours…")
    resume_raspberry = tk.Label(
        fenetre,
        textvariable=resume_raspberry_var,
        font=("Segoe UI", 10, "bold"),
        fg=GREEN,
        bg=LIGHT_GREEN,
        anchor="w",
        padx=12,
        pady=8,
        relief="flat",
    )
    resume_raspberry.pack(fill="x", padx=20, pady=(0, 12))

    zone = tk.Text(fenetre, width=104, height=17, wrap="word", bg=BG, fg=TEXT, relief="flat", font=("Segoe UI", 9))
    zone.pack(fill="both", expand=True, padx=20, pady=(0, 12))

    tableau_frame = tk.Frame(fenetre, bg=CARD)
    tableau_frame.pack(fill="both", expand=False, padx=20, pady=(0, 12))
    colonnes = ("plante", "capteur", "mesures", "derniere", "passif", "historique")
    tableau_capteurs = ttk.Treeview(tableau_frame, columns=colonnes, show="headings", height=7)
    for colonne, titre, largeur, ancre in [
        ("plante", "Plante", 140, "w"),
        ("capteur", "Capteur", 130, "w"),
        ("mesures", "Mesures", 80, "center"),
        ("derniere", "Dernière mesure", 150, "center"),
        ("passif", "Passif", 70, "center"),
        ("historique", "Historique", 80, "center"),
    ]:
        tableau_capteurs.heading(colonne, text=titre)
        tableau_capteurs.column(colonne, width=largeur, anchor=ancre)
    tableau_capteurs.pack(side="left", fill="both", expand=True)
    scrollbar_capteurs = ttk.Scrollbar(tableau_frame, orient="vertical", command=tableau_capteurs.yview)
    scrollbar_capteurs.pack(side="right", fill="y")
    tableau_capteurs.configure(yscrollcommand=scrollbar_capteurs.set)

    def rafraichir():
        resume = resume_sante_raspberry()
        resume_raspberry_var.set(resume["texte"])
        resume_raspberry.configure(fg=resume["couleur"], bg=resume["fond"])
        zone.configure(state="normal")
        zone.delete("1.0", "end")
        zone.insert("1.0", texte_sante_systeme(resume["etat"]))
        zone.configure(state="disabled")
        for item in tableau_capteurs.get_children():
            tableau_capteurs.delete(item)
        diagnostic = database.get_diagnostic_global()
        for capteur in diagnostic["capteurs"]:
            tableau_capteurs.insert("", "end", values=(
                capteur[3] or "Sans plante",
                capteur[1] or f"Capteur {capteur[0]}",
                capteur[4] or 0,
                capteur[5] or "jamais",
                capteur[6] or 0,
                capteur[8] or 0,
            ))

    def copier():
        texte = texte_sante_systeme()
        root.clipboard_clear()
        root.clipboard_append(texte)
        status_var.set("État Gruterra & Raspberry copié dans le presse-papiers")

    rafraichir()

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", padx=20, pady=(0, 16))
    tk.Button(boutons, text=t("refresh_button"), command=rafraichir, bg=LIGHT_GREEN, fg=GREEN, activebackground=LIGHT_GREEN, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(boutons, text=t("copy"), command=copier, bg=LIGHT_BLUE, fg=BLUE, activebackground=LIGHT_BLUE, relief="flat", cursor="hand2").pack(side="left")
    tk.Button(boutons, text=t("close"), command=fenetre.destroy, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="right")

def ouvrir_parametres():
    fenetre = tk.Toplevel(root)
    fenetre.title(t("settings_title"))
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()

    tk.Label(
        fenetre,
        text=t("settings_header"),
        font=("Segoe UI", 16, "bold"),
        fg=TEXT,
        bg=CARD
    ).pack(anchor="w", padx=20, pady=(18, 8))

    affichage_bloc = tk.Frame(fenetre, bg=LIGHT_GREEN, highlightbackground=BORDER, highlightthickness=1)
    affichage_bloc.pack(fill="x", padx=20, pady=(0, 12))

    tk.Label(
        affichage_bloc,
        text=t("display"),
        font=("Segoe UI", 11, "bold"),
        fg=GREEN,
        bg=LIGHT_GREEN
    ).pack(anchor="w", padx=12, pady=(10, 4))

    options_langue = {"🇫🇷 Français": "fr", "🇬🇧 English": "en"}
    libelle_langue_courante = next((libelle for libelle, code in options_langue.items() if code == langue_interface), "🇫🇷 Français")
    langue_var = tk.StringVar(value=libelle_langue_courante)
    ligne_langue = tk.Frame(affichage_bloc, bg=LIGHT_GREEN)
    ligne_langue.pack(fill="x", padx=12, pady=(0, 8))
    tk.Label(ligne_langue, text=t("language"), bg=LIGHT_GREEN, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
    ttk.Combobox(
        ligne_langue,
        textvariable=langue_var,
        values=tuple(options_langue.keys()),
        width=16,
        state="readonly",
    ).pack(side="left", padx=(10, 8))
    tk.Label(
        affichage_bloc,
        text=t("language_note"),
        bg=LIGHT_GREEN,
        fg=SECONDARY,
        font=("Segoe UI", 8),
        wraplength=420,
        justify="left",
    ).pack(anchor="w", padx=12, pady=(0, 8))

    meteo_haut_var = tk.BooleanVar(value=meteo_affichee_en_haut())
    tk.Checkbutton(
        affichage_bloc,
        text=t("show_weather_top"),
        variable=meteo_haut_var,
        bg=LIGHT_GREEN,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        activeforeground=TEXT,
        selectcolor=CARD
    ).pack(anchor="w", padx=12, pady=(0, 10))

    plantes_accueil_var = tk.BooleanVar(value=plantes_affichees_sur_accueil())
    tk.Checkbutton(
        affichage_bloc,
        text=t("show_plants_home"),
        variable=plantes_accueil_var,
        bg=LIGHT_GREEN,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        activeforeground=TEXT,
        selectcolor=CARD
    ).pack(anchor="w", padx=12, pady=(0, 8))

    vue_compacte_var = tk.BooleanVar(value=vue_compacte_plantes_active())
    tk.Checkbutton(
        affichage_bloc,
        text=t("compact_plants"),
        variable=vue_compacte_var,
        bg=LIGHT_GREEN,
        fg=TEXT,
        activebackground=LIGHT_GREEN,
        activeforeground=TEXT,
        selectcolor=CARD
    ).pack(anchor="w", padx=12, pady=(0, 10))

    update_bloc = tk.Frame(fenetre, bg=LIGHT_ORANGE, highlightbackground=BORDER, highlightthickness=1)
    update_bloc.pack(fill="x", padx=20, pady=(0, 12))
    tk.Label(update_bloc, text=t("updates_section"), font=("Segoe UI", 11, "bold"), fg=ORANGE, bg=LIGHT_ORANGE).pack(anchor="w", padx=12, pady=(10, 4))

    update_texte_frame = tk.Frame(update_bloc, bg=LIGHT_ORANGE)
    update_texte_frame.pack(fill="x", padx=12, pady=(0, 8))
    update_info_zone = tk.Text(
        update_texte_frame,
        width=68,
        height=7,
        wrap="word",
        bg=BG,
        fg=SECONDARY,
        insertbackground=TEXT,
        relief="flat",
        font=("Segoe UI", 8),
    )
    update_info_scroll = ttk.Scrollbar(update_texte_frame, orient="vertical", command=update_info_zone.yview)
    update_info_zone.configure(yscrollcommand=update_info_scroll.set)
    update_info_zone.pack(side="left", fill="both", expand=True)
    update_info_scroll.pack(side="right", fill="y")

    def set_update_info(texte):
        update_info_zone.configure(state="normal")
        update_info_zone.delete("1.0", "end")
        update_info_zone.insert("1.0", texte_interface_utf8_sur(texte))
        update_info_zone.configure(state="normal")

    set_update_info(t("updates_settings_help"))

    def settings_verifier_update():
        status_var.set(t("update_checking"))
        try:
            diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(Path(__file__).resolve().parent.parent, verifier_distant=True)
            set_update_info(botaneo_update.formater_diagnostic_mise_a_jour(diagnostic) + "\n\n" + patch_note_update_a_propos(verifier_distant=True))
            status_var.set(t("update_check_done"))
        except Exception as erreur:
            set_update_info(f"Vérification impossible : {erreur}")

    def settings_tester_update():
        status_var.set(t("update_sim_running"))

        def tache():
            contenu = executer_assistant_update_a_propos(appliquer=False)
            root.after(0, lambda: set_update_info(contenu))
            root.after(0, lambda: status_var.set(t("update_sim_done")))

        threading.Thread(target=tache, daemon=True).start()

    update_actions = tk.Frame(update_bloc, bg=LIGHT_ORANGE)
    update_actions.pack(fill="x", padx=12, pady=(0, 10))
    tk.Button(update_actions, text=t("check_updates"), command=settings_verifier_update, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(update_actions, text=t("update"), command=settings_tester_update, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(update_actions, text=t("apply_update"), command=lambda: lancer_application_update(fenetre, afficher_resultat=set_update_info), bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left")

    bloc = tk.Frame(fenetre, bg=LIGHT_BLUE, highlightbackground=BORDER, highlightthickness=1)
    bloc.pack(fill="x", padx=20, pady=(0, 12))

    tk.Label(
        bloc,
        text=t("auto_sync"),
        font=("Segoe UI", 11, "bold"),
        fg=BLUE,
        bg=LIGHT_BLUE
    ).pack(anchor="w", padx=12, pady=(10, 4))

    active_var = tk.BooleanVar(value=bool(auto_sync_config.get("active", True)))
    tk.Checkbutton(
        bloc,
        text=t("enable_auto_sync"),
        variable=active_var,
        bg=LIGHT_BLUE,
        fg=TEXT,
        activebackground=LIGHT_BLUE,
        activeforeground=TEXT,
        selectcolor=CARD
    ).pack(anchor="w", padx=12, pady=(0, 8))

    ligne_heure = tk.Frame(bloc, bg=LIGHT_BLUE)
    ligne_heure.pack(fill="x", padx=12, pady=(0, 8))

    tk.Label(ligne_heure, text=t("time"), bg=LIGHT_BLUE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
    heure_var = tk.StringVar(value=auto_sync_config.get("heure", "18:00"))
    heure_entry = tk.Entry(ligne_heure, textvariable=heure_var, width=8, bg=BG, fg=TEXT, insertbackground=TEXT)
    heure_entry.pack(side="left", padx=(10, 4))
    tk.Label(ligne_heure, text=t("time_format_hint"), bg=LIGHT_BLUE, fg=SECONDARY, font=("Segoe UI", 8)).pack(side="left")

    tk.Label(
        bloc,
        text=t("allowed_days"),
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

    tk.Label(netatmo_bloc, text=t("netatmo"), font=("Segoe UI", 11, "bold"), fg=GREEN, bg=LIGHT_GREEN).pack(anchor="w", padx=12, pady=(10, 4))

    tk.Label(
        netatmo_bloc,
        text=t("add_public_favorite_station"),
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

    tk.Label(netatmo_bloc, text=t("netatmo_favorite_hint"),
             bg=LIGHT_GREEN, fg=SECONDARY, font=("Segoe UI", 8), wraplength=420,
             justify="left").pack(anchor="w", padx=12, pady=(0, 8))

    diagnostic_netatmo = diagnostiquer_config_netatmo()
    couleur_netatmo = GREEN if diagnostic_netatmo.get("ok") else ORANGE
    tk.Label(
        netatmo_bloc,
        text=t("netatmo_connection_prefix").format(message=diagnostic_netatmo.get("message", t("netatmo_unknown_status"))),
        bg=LIGHT_GREEN,
        fg=couleur_netatmo,
        font=("Segoe UI", 9, "bold"),
        wraplength=520,
        justify="left"
    ).pack(anchor="w", padx=12, pady=(0, 2))
    tk.Label(
        netatmo_bloc,
        text=diagnostic_netatmo.get("details", ""),
        bg=LIGHT_GREEN,
        fg=SECONDARY,
        font=("Segoe UI", 8),
        wraplength=520,
        justify="left"
    ).pack(anchor="w", padx=12, pady=(0, 6))

    def creer_fichier_netatmo_depuis_parametres():
        ok, message = creer_config_netatmo_exemple()
        if ok:
            erreur.set(message)
            status_var.set(message)
        else:
            erreur.set(message)

    actions_netatmo = tk.Frame(netatmo_bloc, bg=LIGHT_GREEN)
    actions_netatmo.pack(fill="x", padx=12, pady=(0, 8))
    tk.Button(
        actions_netatmo,
        text=t("create_netatmo_file"),
        command=creer_fichier_netatmo_depuis_parametres,
        bg=BG,
        fg=TEXT,
        relief="flat",
        cursor="hand2"
    ).pack(side="left")
    tk.Label(
        actions_netatmo,
        text=t("netatmo_file_next_step"),
        bg=LIGHT_GREEN,
        fg=SECONDARY,
        font=("Segoe UI", 8),
        wraplength=360,
        justify="left"
    ).pack(side="left", padx=(10, 0))

    tk.Label(
        netatmo_bloc,
        text=t("netatmo_help_settings"),
        bg=LIGHT_GREEN,
        fg=SECONDARY,
        font=("Segoe UI", 8),
        wraplength=520,
        justify="left"
    ).pack(anchor="w", padx=12, pady=(0, 8))

    alertes_bloc = tk.Frame(fenetre, bg=LIGHT_ORANGE, highlightbackground=BORDER, highlightthickness=1)
    alertes_bloc.pack(fill="x", padx=20, pady=(0, 12))

    tk.Label(alertes_bloc, text=t("alerts_section"), font=("Segoe UI", 11, "bold"), fg=ORANGE, bg=LIGHT_ORANGE).pack(anchor="w", padx=12, pady=(10, 4))

    email_var = tk.BooleanVar(value=bool(alertes_config.get("email_actif", False)))
    tk.Checkbutton(alertes_bloc, text=t("email_alerts_test_mode"), variable=email_var,
                  bg=LIGHT_ORANGE, fg=TEXT, activebackground=LIGHT_ORANGE,
                  activeforeground=TEXT, selectcolor=CARD).pack(anchor="w", padx=12, pady=(0, 6))

    ligne_email = tk.Frame(alertes_bloc, bg=LIGHT_ORANGE)
    ligne_email.pack(fill="x", padx=12, pady=(0, 6))
    tk.Label(ligne_email, text=t("recipient"), bg=LIGHT_ORANGE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
    email_destinataire_var = tk.StringVar(value=alertes_config.get("email_destinataire", ""))
    tk.Entry(ligne_email, textvariable=email_destinataire_var, width=32, bg=BG, fg=TEXT, insertbackground=TEXT).pack(side="left", padx=(10, 4))

    ligne_batterie = tk.Frame(alertes_bloc, bg=LIGHT_ORANGE)
    ligne_batterie.pack(fill="x", padx=12, pady=(0, 6))
    tk.Label(ligne_batterie, text=t("battery_threshold"), bg=LIGHT_ORANGE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
    seuil_batterie_var = tk.StringVar(value=str(alertes_config.get("seuil_batterie", 50)))
    tk.Entry(ligne_batterie, textvariable=seuil_batterie_var, width=6, bg=BG, fg=TEXT, insertbackground=TEXT).pack(side="left", padx=(10, 4))
    tk.Label(ligne_batterie, text="%", bg=LIGHT_ORANGE, fg=TEXT).pack(side="left")

    tk.Label(alertes_bloc, text=t("plants_with_email_reminder"), bg=LIGHT_ORANGE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(4, 3))
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

    tk.Label(alertes_bloc, text=t("email_alerts_test_help"),
             bg=LIGHT_ORANGE, fg=SECONDARY, font=("Segoe UI", 8), wraplength=520,
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

    tk.Button(raccourcis, text=t("every_day"), command=selectionner_tous, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left", padx=(0, 8))
    tk.Button(raccourcis, text=t("monday_to_friday"), command=jours_semaine, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left")

    def enregistrer():
        global langue_interface
        heure = heure_var.get().strip()
        try:
            heure_part, minute_part = heure.split(":", 1)
            heure_int = int(heure_part)
            minute_int = int(minute_part)
            if not (0 <= heure_int <= 23 and 0 <= minute_int <= 59):
                raise ValueError()
            heure = f"{heure_int:02d}:{minute_int:02d}"
        except Exception:
            erreur.set(t("invalid_time_example"))
            return

        jours = [index for index, var in enumerate(jours_vars) if var.get()]
        if not jours:
            erreur.set(t("select_day_or_disable_auto_sync"))
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
            erreur.set(t("invalid_battery_threshold_example"))
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
        interface_layout_config["plantes_sur_accueil"] = bool(plantes_accueil_var.get())
        interface_layout_config["vue_compacte_plantes"] = bool(vue_compacte_var.get())
        destinataire = email_destinataire_var.get().strip()
        if email_var.get() and not destinataire:
            erreur.set(t("email_recipient_required"))
            return

        alertes_config["email_actif"] = bool(email_var.get())
        alertes_config["email_mode"] = "preview"
        alertes_config["email_destinataire"] = destinataire
        alertes_config["seuil_batterie"] = seuil_batterie
        alertes_config["plantes_rappel_email"] = [pid for pid, var in plantes_alertes_vars if var.get()]

        nouvelle_langue = normaliser_langue(options_langue.get(langue_var.get(), langue_var.get()))

        sauvegarde_sync = sauvegarder_config_sync_auto()
        sauvegarde_layout = sauvegarder_layout_interface()
        sauvegarde_alertes = sauvegarder_config_alertes()
        sauvegarde_langue = sauvegarder_langue_interface(nouvelle_langue)

        if sauvegarde_sync and sauvegarde_layout and sauvegarde_alertes and sauvegarde_langue:
            langue_interface = nouvelle_langue
            actualiser_textes_interface()
            actualiser_affichage_sync_auto()
            fenetre.destroy()
            actualiser_interface()
            if station_favorite_saisie:
                status_var.set(favori_message)
            else:
                status_var.set(t("settings_saved"))
        else:
            erreur.set(t("settings_save_failed"))

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", padx=20, pady=(0, 15))

    tk.Button(boutons, text=t("save"), command=enregistrer, bg=LIGHT_GREEN, fg=TEXT, activebackground=LIGHT_GREEN, relief="flat", cursor="hand2").pack(side="right")
    tk.Button(boutons, text=t("cancel"), command=fenetre.destroy, bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="left")

    heure_entry.focus_set()


# ============================================================
# ACTIONS
# ============================================================

def ouvrir_ajout_plante():

    fenetre = tk.Toplevel(root)
    fenetre.title(t("add_plant_title"))
    fenetre.configure(bg=CARD)
    fenetre.resizable(False, False)
    fenetre.transient(root)
    fenetre.grab_set()

    champs = {}
    plante_selectionnee = tk.StringVar(value="")

    tk.Label(
        fenetre,
        text=t("plant_name"),
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
        text=t("known_needs"),
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
        text=t("location"),
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
        text=t("add"),
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
        text=t("cancel"),
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
    tk.Button(fenetre, text=t("add"), command=enregistrer, bg=LIGHT_GREEN, fg=TEXT,
              activebackground=LIGHT_GREEN, activeforeground=TEXT).pack(side='right', padx=20, pady=15)
    tk.Button(fenetre, text=t("cancel"), command=fenetre.destroy, bg=BG, fg=TEXT).pack(side='left', padx=20, pady=15)
    champs[0].focus_set()


def _date_locale_depuis_mesure(valeur):
    try:
        date = datetime.fromisoformat(valeur)
        if date.tzinfo:
            date = date.astimezone().replace(tzinfo=None)
        return date
    except Exception:
        return None


def _resume_mesures_export(mesures, debut):
    points = []
    for mesure in mesures:
        date = _date_locale_depuis_mesure(mesure[1])
        if date and date >= debut:
            points.append((date, mesure))
    points.sort(key=lambda item: item[0])
    if not points:
        return None
    resume = {"count": len(points), "first": points[0], "last": points[-1]}
    for nom, index in (("temperature", 2), ("humidite", 3), ("luminosite", 4), ("conductivite", 5)):
        valeurs = [item[1][index] for item in points if item[1][index] is not None]
        if valeurs:
            resume[nom] = {
                "min": min(valeurs),
                "max": max(valeurs),
                "moy": sum(valeurs) / len(valeurs),
                "dernier": valeurs[-1]
            }
    if len(points) > 1:
        ecarts = [(b[0] - a[0]).total_seconds() / 3600 for a, b in zip(points, points[1:])]
        resume["plus_grand_trou"] = max(ecarts)
        resume["trous_importants"] = sum(1 for ecart in ecarts if ecart > 1.8)
    else:
        resume["plus_grand_trou"] = 0
        resume["trous_importants"] = 0
    return resume


def _ligne_stat(label, data, unite=""):
    if not data:
        return None
    suffixe = f" {unite}" if unite else ""
    return f"- {label} : min {data['min']:.1f}{suffixe}, max {data['max']:.1f}{suffixe}, moyenne {data['moy']:.1f}{suffixe}, dernière {data['dernier']:.1f}{suffixe}."


def _format_export_valeur(valeur, unite="", decimales=0):
    if valeur is None:
        return "non disponible"
    try:
        nombre = float(valeur)
    except (TypeError, ValueError):
        return str(valeur)
    suffixe = f" {unite}" if unite else ""
    return f"{nombre:.{decimales}f}{suffixe}"


def _ajouter_resume_export(lignes, titre, resume):
    lignes.append(f"{titre} :")
    if not resume:
        lignes.append("- Aucune mesure disponible.")
        lignes.append("")
        return
    lignes.append(f"- {resume['count']} mesure(s).")
    for label, cle, unite in (
        ("Humidité", "humidite", "%"),
        ("Lumière", "luminosite", "lux"),
        ("Température", "temperature", "°C"),
        ("Conductivité", "conductivite", "µS/cm"),
    ):
        ligne = _ligne_stat(label, resume.get(cle), unite)
        if ligne:
            lignes.append(ligne)
    lignes.append(f"- Plus grand trou entre deux mesures : {resume.get('plus_grand_trou', 0):.1f} h.")
    if resume.get("trous_importants"):
        lignes.append(f"- Qualité : {resume['trous_importants']} trou(s) supérieur(s) à environ 1 h 48.")
    lignes.append("")


def _construire_expositions_export(evenements):
    points = []
    for evenement in evenements or []:
        date = _date_locale_depuis_mesure(evenement[2] if len(evenement) > 2 else None)
        type_evenement = (evenement[3] if len(evenement) > 3 and evenement[3] else "").strip().lower()
        titre = (evenement[4] if len(evenement) > 4 and evenement[4] else "").strip().lower()
        if not date or type_evenement != "exposition":
            continue
        if "sortie balcon" in titre:
            points.append((date, "sortie"))
        elif "retour intérieur" in titre or "retour interieur" in titre:
            points.append((date, "retour"))
    points.sort(key=lambda item: item[0])
    periodes = []
    sortie = None
    for date, action in points:
        if action == "sortie":
            sortie = date
        elif action == "retour" and sortie:
            if date > sortie:
                periodes.append((sortie, date))
            sortie = None
    if sortie:
        periodes.append((sortie, None))
    return periodes


def _mesure_dans_exposition(date, expositions, fin_defaut=None):
    for sortie, retour in expositions or []:
        fin = retour or fin_defaut or datetime.now()
        if sortie <= date <= fin:
            return True
    return False


def _resume_lumiere_contexte(mesures, expositions, debut):
    points = []
    fin_defaut = datetime.now()
    for mesure in mesures:
        date = _date_locale_depuis_mesure(mesure[1])
        if not date or date < debut or mesure[4] is None:
            continue
        try:
            lux = float(mesure[4])
        except (TypeError, ValueError):
            continue
        points.append((date, lux, _mesure_dans_exposition(date, expositions, fin_defaut)))
    if not points:
        return None

    valeurs = [lux for _, lux, _ in points]
    interieur = [lux for _, lux, dehors in points if not dehors]
    balcon = [lux for _, lux, dehors in points if dehors]
    return {
        "count": len(points),
        "moyenne": sum(valeurs) / len(valeurs),
        "maximum": max(valeurs),
        "interieur_count": len(interieur),
        "interieur_moyenne": (sum(interieur) / len(interieur)) if interieur else None,
        "interieur_maximum": max(interieur) if interieur else None,
        "balcon_count": len(balcon),
        "balcon_maximum": max(balcon) if balcon else None,
    }


def _ajouter_contexte_lumiere_export(lignes, mesures, evenements):
    expositions = _construire_expositions_export(evenements)
    maintenant = datetime.now()
    recentes = [
        (sortie, retour)
        for sortie, retour in expositions
        if sortie >= maintenant - timedelta(days=14)
    ]
    resume_7j = _resume_lumiere_contexte(mesures, expositions, maintenant - timedelta(days=7))
    resume_24h = _resume_lumiere_contexte(mesures, expositions, maintenant - timedelta(days=1))

    if not recentes and not resume_7j:
        return

    lignes.append("Contexte lumière :")
    if recentes:
        lignes.append(f"- {len(recentes)} exposition(s) balcon notée(s) sur les 14 derniers jours.")
        for sortie, retour in recentes[-4:]:
            if retour:
                duree = formater_duree_heures((retour - sortie).total_seconds() / 3600)
                lignes.append(f"- {sortie.strftime('%d/%m %H:%M')} → {retour.strftime('%H:%M')} : sortie balcon déclarée, durée {duree}.")
            else:
                lignes.append(f"- {sortie.strftime('%d/%m %H:%M')} : sortie balcon déclarée, retour non noté.")
    else:
        lignes.append("- Aucune exposition balcon récente notée dans le journal.")

    for titre, resume in (("24 h", resume_24h), ("7 jours", resume_7j)):
        if not resume:
            continue
        ligne = f"- Lumière {titre} : moyenne globale {resume['moyenne']:.0f} lux, maximum {resume['maximum']:.0f} lux"
        if resume["interieur_moyenne"] is not None:
            ligne += f", hors balcon {resume['interieur_moyenne']:.0f} lux de moyenne"
            if resume["interieur_maximum"] is not None:
                ligne += f" et {resume['interieur_maximum']:.0f} lux max"
        if resume["balcon_count"]:
            ligne += f", {resume['balcon_count']} mesure(s) pendant exposition balcon"
            if resume["balcon_maximum"] is not None:
                ligne += f" jusqu'à {resume['balcon_maximum']:.0f} lux"
        lignes.append(ligne + ".")

    if resume_7j and resume_7j.get("balcon_count") and resume_7j.get("interieur_moyenne") is not None:
        lignes.append("- Interprétation : les pics lumineux sont contextualisés par les sorties balcon ; ils ne doivent pas masquer la luminosité habituelle de l'emplacement intérieur.")
    lignes.append("")


def generer_texte_analyse_plante(plante_id):
    plante = database.get_plante(plante_id)
    if not plante:
        return "Plante introuvable dans Gruterra."
    _, nom, espece, emplacement, zone = plante
    capteur = obtenir_capteur_plante(plante_id)
    mesures = database.get_mesures(plante_id=plante_id, limite=-1)
    mesures = sorted(mesures, key=lambda item: item[1] or "")
    dernier_arrosage = database.get_dernier_arrosage(plante_id)
    arrosages = database.get_arrosages_plante(plante_id, limite=10)

    lignes = []
    details = []
    if espece:
        details.append(espece)
    if emplacement:
        details.append(emplacement)
    if zone:
        details.append(zone)
    lignes.append(f"Plante suivie : {nom}" + (f" / {' · '.join(details)}" if details else ""))
    if capteur:
        lignes.append(f"Capteur actif : {capteur[1]} `{capteur[2]}`.")
    else:
        lignes.append("Capteur actif : aucun.")
    lignes.append("")

    if dernier_arrosage:
        quantite = dernier_arrosage[3]
        quantite_txt = f"{quantite:g} ml" if quantite is not None else "quantité non renseignée"
        type_eau = dernier_arrosage[8] if len(dernier_arrosage) > 8 else None
        commentaire = dernier_arrosage[7] if len(dernier_arrosage) > 7 else None
        lignes.append("Dernier arrosage :")
        ligne = f"- {formater_date(dernier_arrosage[2])} : {quantite_txt}"
        if type_eau:
            ligne += f", eau : {type_eau}"
        if commentaire:
            ligne += f", commentaire : {commentaire}"
        lignes.append(ligne + ".")
        lignes.append("")

    if arrosages:
        lignes.append("Arrosages récents :")
        for arrosage in arrosages[:5]:
            quantite = arrosage[3]
            quantite_txt = f"{quantite:g} ml" if quantite is not None else "quantité non renseignée"
            type_eau = arrosage[8] if len(arrosage) > 8 else None
            commentaire = arrosage[7] if len(arrosage) > 7 else None
            morceaux = [quantite_txt]
            if type_eau:
                morceaux.append(f"eau : {type_eau}")
            if commentaire:
                morceaux.append(f"contexte : {commentaire}")
            lignes.append(f"- {formater_date(arrosage[2])} : " + ", ".join(morceaux) + ".")
        lignes.append("")

    try:
        evenements = database.get_journal_plante(plante_id, limite=50)
    except Exception:
        evenements = []
    if evenements:
        lignes.append("Événements / observations notés :")
        for evenement in evenements:
            type_evenement = evenement[3] if len(evenement) > 3 else "observation"
            titre = evenement[4] if len(evenement) > 4 and evenement[4] else "Observation"
            commentaire = evenement[5] if len(evenement) > 5 else None
            date = evenement[2] if len(evenement) > 2 else ""
            texte = f"- {formater_date(date)} : {titre}"
            if type_evenement and type_evenement != titre:
                texte += f" ({type_evenement})"
            if commentaire:
                texte += f" — {commentaire}"
            lignes.append(texte)
        lignes.append("")

    _ajouter_contexte_lumiere_export(lignes, mesures, evenements)

    maintenant = datetime.now()
    for titre, debut in (
        ("Résumé 24 h", maintenant - timedelta(days=1)),
        ("Résumé 48 h", maintenant - timedelta(days=2)),
        ("Résumé 7 jours", maintenant - timedelta(days=7)),
    ):
        _ajouter_resume_export(lignes, titre, _resume_mesures_export(mesures, debut))

    if dernier_arrosage:
        date_arrosage = _date_locale_depuis_mesure(dernier_arrosage[2])
        if date_arrosage:
            _ajouter_resume_export(lignes, "Résumé depuis le dernier arrosage", _resume_mesures_export(mesures, date_arrosage))
            autour = []
            for mesure in mesures:
                date = _date_locale_depuis_mesure(mesure[1])
                if date and date_arrosage - timedelta(hours=8) <= date <= date_arrosage + timedelta(hours=6):
                    autour.append((date, mesure))
            if autour:
                lignes.append("Mesures autour du dernier arrosage :")
                for date, mesure in autour[-18:]:
                    lignes.append(
                        f"- {date.strftime('%d/%m %H:%M')} : "
                        f"humidité {_format_export_valeur(mesure[3], '%')}, "
                        f"lumière {_format_export_valeur(mesure[4], 'lux')}, "
                        f"température {_format_export_valeur(mesure[2], '°C', 1)}, "
                        f"conductivité {_format_export_valeur(mesure[5], 'µS/cm')}."
                    )
                lignes.append("")

    suivi = analyser_apres_arrosage(plante_id)
    if suivi:
        lignes.append("Lecture Gruterra :")
        lignes.append(f"- {suivi['titre']} : {suivi['detail']}")
        lignes.append("")

    lignes.append("Point à discuter :")
    lignes.append("- Comparer l’évolution de l’humidité après arrosage avec l’état réel des feuilles et de la tige.")
    lignes.append("- Vérifier si la lumière moyenne hors balcon reste insuffisante pour une Crassula, même lorsque quelques pics lumineux apparaissent.")
    return texte_interface_utf8_sur("\n".join(lignes)).strip()


def copier_analyse_plante(plante_id):
    try:
        texte = generer_texte_analyse_plante(plante_id)
    except Exception as erreur:
        status_var.set(f"Analyse plante impossible : {erreur}")
        return
    root.clipboard_clear()
    root.clipboard_append(texte)
    status_var.set("Analyse plante copiée dans le presse-papiers")


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
            resultat = sync_miflora.importer_historique_capteur_sync(capteur[0], force_pc=False)
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
                action = resultat.get("historique_action")
                if action == "rien_de_nouveau":
                    status_var.set("Historique Mi Flora : rien de nouveau côté Raspberry.")
                    titre_message = "Historique Mi Flora · rien de nouveau"
                else:
                    status_var.set("Historique Mi Flora importé.")
                    titre_message = "Historique Mi Flora"
                sync_detail_var.set(resultat.get("message", "Historique importé."))
                actualiser_interface()
                messagebox.showinfo(
                    titre_message,
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


def plante_a_historique_mesures(plante_id):
    try:
        return bool(database.get_mesures(plante_id=plante_id, limite=1))
    except Exception:
        return False



def plantes_avec_historique_mesures(exclure_plante_id=None, limite=6):
    plantes = []
    try:
        for plante in database.get_plantes():
            if exclure_plante_id is not None and plante[0] == exclure_plante_id:
                continue
            if plante_a_historique_mesures(plante[0]):
                plantes.append(plante)
            if len(plantes) >= limite:
                break
    except Exception:
        pass
    return plantes



def afficher_raccourcis_historique(plante_id):
    plante = database.get_plante(plante_id)
    nom_plante = plante[1] if plante else "cette plante"
    raccourcis = plantes_avec_historique_mesures(
        exclure_plante_id=plante_id
    )

    fenetre = tk.Toplevel(root)
    fenetre.title("Historique")
    fenetre.configure(bg=CARD)
    fenetre.transient(root)
    fenetre.grab_set()
    fenetre.geometry("520x320")
    fenetre.minsize(480, 260)

    contenu = tk.Frame(fenetre, bg=CARD)
    contenu.pack(fill="both", expand=True, padx=22, pady=18)

    tk.Label(
        contenu,
        text="📈 Historique de mesures",
        font=("Segoe UI", 15, "bold"),
        fg=TEXT,
        bg=CARD,
        anchor="w"
    ).pack(fill="x")

    tk.Label(
        contenu,
        text=(
            f"{nom_plante} n'a pas encore de mesures capteur enregistrées. "
            "C'est normal pour une plante sans capteur actif."
        ),
        font=("Segoe UI", 10),
        fg=SECONDARY,
        bg=CARD,
        wraplength=460,
        justify="left",
        anchor="w"
    ).pack(fill="x", pady=(10, 12))

    if raccourcis:
        tk.Label(
            contenu,
            text="Ouvrir un historique disponible :",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT,
            bg=CARD,
            anchor="w"
        ).pack(fill="x", pady=(0, 6))

        for plante_historique in raccourcis:
            nom_historique = plante_historique[1]
            tk.Button(
                contenu,
                text=f"📈 {nom_historique}",
                font=("Segoe UI", 9, "bold"),
                bg=LIGHT_GREEN,
                fg=GREEN,
                activebackground=LIGHT_GREEN,
                activeforeground=GREEN,
                relief="flat",
                cursor="hand2",
                command=lambda pid=plante_historique[0]: (
                    fenetre.destroy(),
                    ouvrir_historique(root, pid, synchroniser)
                )
            ).pack(fill="x", pady=3)
    else:
        tk.Label(
            contenu,
            text=(
                "Aucune plante n'a encore d'historique de mesures. "
                "Après une synchronisation Mi Flora, le bouton ouvrira les graphiques."
            ),
            font=("Segoe UI", 10),
            fg=SECONDARY,
            bg=CARD,
            wraplength=460,
            justify="left",
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

    tk.Button(
        contenu,
        text=t("close"),
        font=("Segoe UI", 9, "bold"),
        bg=BG,
        fg=TEXT,
        activebackground=BG,
        activeforeground=TEXT,
        relief="flat",
        cursor="hand2",
        command=fenetre.destroy
    ).pack(anchor="e", pady=(12, 0))



def afficher_message_historique(plante_id):
    if plante_a_historique_mesures(plante_id):
        ouvrir_historique(root, plante_id, synchroniser)
    else:
        afficher_raccourcis_historique(plante_id)



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


def delai_rappel_arrosage(date_rappel, reference=None):
    reference = reference or datetime.now()
    try:
        if isinstance(date_rappel, str):
            date_rappel = datetime.fromisoformat(date_rappel)
        jours = (date_rappel.date() - reference.date()).days
    except Exception:
        return "date à vérifier"

    if jours < 0:
        return f"en retard de {abs(jours)} jour{'s' if abs(jours) != 1 else ''}"
    if jours == 0:
        return "aujourd'hui"
    if jours == 1:
        return "demain"
    return f"dans {jours} jours"


def rappel_mail_texte(plante_id, date_rappel, reference=None):
    if not plante_avec_rappel_email(plante_id):
        return None
    reference = reference or datetime.now()
    try:
        if isinstance(date_rappel, str):
            date_rappel = datetime.fromisoformat(date_rappel)
        date_mail = date_rappel - timedelta(days=7)
    except Exception:
        return "Mail de rappel prévu : une semaine avant, date à vérifier."
    if date_mail.date() <= reference.date():
        return "Mail de rappel : à préparer maintenant, car l’échéance est à moins d’une semaine."
    return f"Mail de rappel prévu environ le {formater_date(date_mail.isoformat(timespec='seconds'))}."


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

        suivi_arrosage = analyser_apres_arrosage(plante_id)
        if suivi_arrosage and suivi_arrosage["niveau"] in ("danger", "attention"):
            ajouter_alerte(
                alertes,
                suivi_arrosage["niveau"],
                f"{suivi_arrosage['titre']} · {nom}",
                suivi_arrosage["detail"]
            )

        try:
            rappel = database.get_rappel_arrosage_actif(plante_id)
        except Exception:
            rappel = None

        try:
            dernier_arrosage = database.get_dernier_arrosage(plante_id)
        except Exception:
            dernier_arrosage = None

        if not capteurs:
            details_sans_capteur = ["Suivi manuel actif : arrosage, notes et rappel."]
            niveau_sans_capteur = "info"
            titre_sans_capteur = f"🌱 {nom} sans capteur actif"

            if rappel and rappel[9]:
                try:
                    date_rappel = datetime.fromisoformat(rappel[9])
                    delai_txt = delai_rappel_arrosage(date_rappel, maintenant)
                    details_sans_capteur.append(f"Prochain arrosage : {delai_txt} · {formater_date(rappel[9])}.")
                    mail_txt = rappel_mail_texte(plante_id, date_rappel, maintenant)
                    if mail_txt:
                        details_sans_capteur.append(mail_txt)
                    if date_rappel.date() <= maintenant.date():
                        niveau_sans_capteur = "danger"
                        titre_sans_capteur = f"💧 Arrosage manuel à faire · {nom}"
                    elif (date_rappel - maintenant).days <= 2:
                        niveau_sans_capteur = "attention"
                        titre_sans_capteur = f"💧 Arrosage manuel bientôt · {nom}"
                except Exception:
                    details_sans_capteur.append(f"Prochain arrosage : {delai_rappel_arrosage(rappel[9], maintenant)} · {formater_date(rappel[9])}.")
                    mail_txt = rappel_mail_texte(plante_id, rappel[9], maintenant)
                    if mail_txt:
                        details_sans_capteur.append(mail_txt)

            if dernier_arrosage and dernier_arrosage[2]:
                quantite = dernier_arrosage[3]
                quantite_txt = f"{quantite:g} ml" if quantite is not None else "quantité non renseignée"
                details_sans_capteur.append(f"Dernier arrosage manuel : {formater_date(dernier_arrosage[2])} · {quantite_txt}.")

            if not rappel:
                details_sans_capteur.append("Aucun rappel programmé : utile pour les plantes hors domicile ou sans mesure d'humidité.")

            ajouter_alerte(alertes, niveau_sans_capteur, titre_sans_capteur, " ".join(details_sans_capteur))
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

        if capteurs and rappel and rappel[9]:
            try:
                date_rappel = datetime.fromisoformat(rappel[9])
                if date_rappel.date() <= maintenant.date():
                    detail = f"Rappel {delai_rappel_arrosage(date_rappel, maintenant)} · {formater_date(rappel[9])}."
                    mail_txt = rappel_mail_texte(plante_id, date_rappel, maintenant)
                    if mail_txt:
                        detail += " " + mail_txt
                    ajouter_alerte(alertes, "danger", f"💧 Arrosage à faire · {nom}", detail)
                elif (date_rappel - maintenant).days <= 2:
                    detail = f"Rappel {delai_rappel_arrosage(date_rappel, maintenant)} · {formater_date(rappel[9])}."
                    mail_txt = rappel_mail_texte(plante_id, date_rappel, maintenant)
                    if mail_txt:
                        detail += " " + mail_txt
                    ajouter_alerte(alertes, "attention", f"💧 Arrosage bientôt · {nom}", detail)
                elif plante_avec_rappel_email(plante_id) and (date_rappel - maintenant).days <= 7:
                    ajouter_alerte(alertes, "info", f"📧 Mail de rappel à prévoir · {nom}", f"Arrosage {delai_rappel_arrosage(date_rappel, maintenant)} · {formater_date(rappel[9])}. {rappel_mail_texte(plante_id, date_rappel, maintenant)}")
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


def lignes_email_depuis_alertes(alertes):
    lignes = [
        "Aperçu des alertes Gruterra.",
        "",
        "Aucun e-mail n'a été envoyé automatiquement.",
        "La mémoire locale sert seulement à éviter de reproposer trop souvent la même alerte.",
        "",
    ]
    if not alertes:
        lignes.append("Aucune alerte importante avec les données actuelles.")
        return lignes

    try:
        settings_email = botaneo_email.charger_parametres_email()
    except Exception:
        settings_email = None

    for alerte in alertes:
        niveau = alerte.get("niveau", "info")
        titre = alerte.get("titre", "Alerte Gruterra")
        detail = alerte.get("detail", "")
        try:
            statut_email = botaneo_email.resume_memoire_alerte(
                type_alerte=niveau,
                titre=titre,
                settings=settings_email,
            )
        except Exception:
            statut_email = "Alerte e-mail : statut mémoire indisponible, aucun envoi automatique."
        lignes.append(f"[{niveau.upper()}] {titre}")
        if detail:
            lignes.append(str(detail))
        lignes.append(statut_email)
        lignes.append("")
    return lignes


def ouvrir_apercu_email_alertes(alertes):
    fenetre = tk.Toplevel(root)
    fenetre.title("Aperçu e-mail alertes")
    fenetre.configure(bg=CARD)
    fenetre.geometry("760x560+90+70")
    fenetre.transient(root)

    tk.Label(
        fenetre,
        text="📧 Aperçu e-mail des alertes",
        font=("Segoe UI", 16, "bold"),
        fg=TEXT,
        bg=CARD
    ).pack(anchor="w", padx=18, pady=(16, 4))

    tk.Label(
        fenetre,
        text="Préparation uniquement : aucun e-mail n'est envoyé depuis cette fenêtre.",
        font=("Segoe UI", 9),
        fg=SECONDARY,
        bg=CARD
    ).pack(anchor="w", padx=18, pady=(0, 10))

    zone = tk.Text(
        fenetre,
        wrap="word",
        bg=BG,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        font=("Segoe UI", 9),
        padx=12,
        pady=12
    )
    zone.pack(fill="both", expand=True, padx=18, pady=(0, 12))

    try:
        apercu = botaneo_email.apercu_message_alerte(
            "Alertes Gruterra",
            lignes_email_depuis_alertes(alertes)
        )
    except Exception as erreur:
        lignes = [
            "Configuration e-mail locale absente ou incomplète.",
            "",
            "C'est normal tant que le compte dédié Gruterra n'est pas créé.",
            "Le futur fichier privé devra être placé ici :",
            str(CONFIG_DIR / "email.local.json"),
            "",
            f"Détail technique : {erreur}",
            "",
            "Aperçu du contenu qui serait préparé :",
            "",
            *lignes_email_depuis_alertes(alertes),
        ]
        apercu = "\n".join(lignes)

    zone.insert("1.0", apercu)
    zone.configure(state="disabled")

    boutons = tk.Frame(fenetre, bg=CARD)
    boutons.pack(fill="x", padx=18, pady=(0, 14))

    def copier():
        fenetre.clipboard_clear()
        fenetre.clipboard_append(apercu)
        status_var.set("Aperçu e-mail copié dans le presse-papiers")

    tk.Button(
        boutons,
        text="Copier l'aperçu",
        command=copier,
        bg=LIGHT_GREEN,
        fg=GREEN,
        relief="flat",
        cursor="hand2"
    ).pack(side="left")
    tk.Button(
        boutons,
        text=t("close"),
        command=fenetre.destroy,
        bg=BG,
        fg=TEXT,
        relief="flat",
        cursor="hand2"
    ).pack(side="right")


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
    tk.Button(
        entete,
        text="📧 Aperçu e-mail",
        font=("Segoe UI", 8, "bold"),
        bg=BG,
        fg=BLUE,
        activebackground=BG,
        activeforeground=BLUE,
        relief="flat",
        cursor="hand2",
        command=lambda a=alertes: ouvrir_apercu_email_alertes(a)
    ).pack(side="right", padx=(8, 0))
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

def afficher_titre_section(parent, titre, detail=None):
    bloc = tk.Frame(parent, bg=BG)
    bloc.pack(fill="x", padx=20, pady=(18, 6))

    ligne = tk.Frame(bloc, bg=BG)
    ligne.pack(fill="x")

    tk.Label(
        ligne,
        text=titre,
        font=("Segoe UI", 15, "bold"),
        fg=TEXT,
        bg=BG,
        anchor="w"
    ).pack(side="left")

    if detail:
        tk.Label(
            ligne,
            text=detail,
            font=("Segoe UI", 9),
            fg=SECONDARY,
            bg=BG,
            anchor="e"
        ).pack(side="right")

    tk.Frame(
        bloc,
        bg=BORDER,
        height=1
    ).pack(fill="x", pady=(6, 0))



def actualiser_interface():

    for widget in content_frame.winfo_children():
        if widget is not netatmo_frame:
            widget.destroy()
    netatmo_frame.pack_forget()

    plantes = database.get_plantes()
    meteo_en_haut = meteo_affichee_en_haut()

    if meteo_en_haut:
        afficher_titre_section(
            content_frame,
            "🌦️ Météo locale",
            "Netatmo et prévisions proches"
        )
        netatmo_frame.pack(fill="x", padx=20, pady=(4, 15))
        afficher_netatmo()

    afficher_titre_section(
        content_frame,
        "🔔 À surveiller",
        "alertes, rappels et points utiles"
    )
    afficher_centre_alertes(content_frame, plantes)

    afficher_titre_section(
        content_frame,
        "🖥️ Suivi système",
        "état local et contrôles automatiques"
    )
    suivi_raspberry.card(content_frame, globals())

    if not plantes:

        tk.Label(
            content_frame,
            text=t("no_plants"),
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

    if plantes_affichees_sur_accueil():
        plantes_filtrees = [plante for plante in plantes if plante_passe_filtres(plante)]
        afficher_titre_section(
            content_frame,
            "🌱 Plantes",
            f"{len(plantes_filtrees)} / {len(plantes)} affichée(s)"
        )
        afficher_filtres_plantes(content_frame, plantes, plantes_filtrees)

        if not plantes_filtrees:
            tk.Label(
                content_frame,
                text=t("no_plant_filters"),
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
    else:
        afficher_titre_section(
            content_frame,
            "🌱 Plantes",
            f"{len(plantes)} plante(s) masquée(s) sur l'accueil"
        )
        bloc_plantes_masquees = tk.Frame(content_frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        bloc_plantes_masquees.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(
            bloc_plantes_masquees,
            text=t("plants_hidden_home"),
            font=("Segoe UI", 10),
            fg=SECONDARY,
            bg=CARD,
            anchor="w",
            justify="left",
            wraplength=900
        ).pack(fill="x", padx=12, pady=(10, 6))
        tk.Button(
            bloc_plantes_masquees,
            text=t("open_plants_view"),
            command=ouvrir_vue_plantes,
            bg=LIGHT_GREEN,
            fg=GREEN,
            relief="flat",
            cursor="hand2"
        ).pack(anchor="w", padx=12, pady=(0, 10))

    if not meteo_en_haut:
        afficher_titre_section(
            content_frame,
            "🌦️ Météo locale",
            "Netatmo et prévisions proches"
        )
        netatmo_frame.pack(fill="x", padx=20, pady=(4, 15))
        afficher_netatmo()


def ouvrir_vue_plantes():
    fenetre = tk.Toplevel(root)
    fenetre.title(t("plants_view_title"))
    largeur = min(1040, max(860, fenetre.winfo_screenwidth() - 120))
    hauteur = min(760, max(620, fenetre.winfo_screenheight() - 140))
    fenetre.geometry(f"{largeur}x{hauteur}+60+45")
    fenetre.minsize(820, 560)
    fenetre.configure(bg=BG)

    entete = tk.Frame(fenetre, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    entete.pack(fill="x")
    tk.Label(entete, text=t("plants"), font=("Segoe UI", 18, "bold"), fg=GREEN, bg=CARD).pack(side="left", padx=18, pady=14)
    tk.Button(entete, text=t("refresh_plain"), command=lambda: remplir(), bg=BG, fg=TEXT, relief="flat", cursor="hand2").pack(side="right", padx=(0, 18), pady=12)

    conteneur = tk.Frame(fenetre, bg=BG)
    conteneur.pack(fill="both", expand=True)
    zone_canvas = tk.Canvas(conteneur, bg=BG, highlightthickness=0)
    barre = tk.Scrollbar(conteneur, orient="vertical", command=zone_canvas.yview)
    zone_canvas.configure(yscrollcommand=barre.set)
    barre.pack(side="right", fill="y")
    zone_canvas.pack(side="left", fill="both", expand=True)

    interieur = tk.Frame(zone_canvas, bg=BG)
    fenetre_canvas = zone_canvas.create_window((0, 0), window=interieur, anchor="nw")

    def ajuster_scroll(_event=None):
        zone_canvas.configure(scrollregion=zone_canvas.bbox("all"))

    def ajuster_largeur(event):
        zone_canvas.itemconfig(fenetre_canvas, width=event.width)

    interieur.bind("<Configure>", ajuster_scroll)
    zone_canvas.bind("<Configure>", ajuster_largeur)

    def defiler(event):
        if zone_canvas.yview() == (0.0, 1.0):
            return
        if getattr(event, "num", None) == 4:
            zone_canvas.yview_scroll(-3, "units")
        elif getattr(event, "num", None) == 5:
            zone_canvas.yview_scroll(3, "units")
        elif event.delta:
            zone_canvas.yview_scroll(-int(event.delta / 120) * 3, "units")

    fenetre.bind("<MouseWheel>", defiler)
    fenetre.bind("<Button-4>", defiler)
    fenetre.bind("<Button-5>", defiler)

    def remplir():
        for widget in interieur.winfo_children():
            widget.destroy()
        plantes = database.get_plantes()
        plantes_filtrees = [plante for plante in plantes if plante_passe_filtres(plante)]
        afficher_titre_section(
            interieur,
            "🌱 Toutes les plantes",
            f"{len(plantes_filtrees)} / {len(plantes)} affichée(s)"
        )
        afficher_filtres_plantes(interieur, plantes, plantes_filtrees, remplir)
        if not plantes_filtrees:
            tk.Label(
                interieur,
                text=t("no_plant_filters"),
                font=("Segoe UI", 11, "bold"),
                fg=SECONDARY,
                bg=BG
            ).pack(pady=25)
            return
        for plante in plantes_filtrees:
            if vue_compacte_plantes_active():
                creer_carte_plante_compacte(interieur, plante)
            else:
                creer_carte_plante(interieur, plante)

    remplir()


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
    text="GRUTERRA",
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
    text=t("refresh"),
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
    text=t("sync_plain"),
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
    text=t("add_plant"),
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


add_sensor_button = tk.Button(toolbar, text=t("add_sensor"), command=ouvrir_ajout_capteur,
                              font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT,
                              activebackground=CARD, activeforeground=TEXT, relief="flat", cursor="hand2")
add_sensor_button.pack(side="left", padx=8)

plants_view_button = tk.Button(toolbar, text=t("plants"), command=ouvrir_vue_plantes,
                               font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT,
                               activebackground=CARD, activeforeground=TEXT, relief="flat", cursor="hand2")
plants_view_button.pack(side="left", padx=(0, 8))


settings_button = tk.Button(
    toolbar,
    text=t("settings"),
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
    text=t("light_mode") if theme_sombre_actif else t("dark_mode"),
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


about_button = tk.Button(
    toolbar,
    text=t("about"),
    command=ouvrir_a_propos,
    font=("Segoe UI", 9, "bold"),
    bg=CARD,
    fg=TEXT,
    activebackground=CARD,
    activeforeground=TEXT,
    relief="flat",
    cursor="hand2"
)
about_button.pack(side="right", padx=(8, 0))

health_button = tk.Button(
    toolbar,
    text=t("health"),
    command=ouvrir_sante_systeme,
    font=("Segoe UI", 9, "bold"),
    bg=CARD,
    fg=TEXT,
    activebackground=CARD,
    activeforeground=TEXT,
    relief="flat",
    cursor="hand2"
)
health_button.pack(side="right", padx=(8, 0))
maintenance_button = tk.Button(
    toolbar,
    text=t("maintenance"),
    command=ouvrir_maintenance,
    font=("Segoe UI", 9, "bold"),
    bg=CARD,
    fg=TEXT,
    activebackground=CARD,
    activeforeground=TEXT,
    relief="flat",
    cursor="hand2"
)
maintenance_button.pack(side="right", padx=(8, 0))


def actualiser_textes_interface():
    root.title(t("app_title"))
    add_plant_button.config(text=t("add_plant"))
    add_sensor_button.config(text=t("add_sensor"))
    plants_view_button.config(text=t("plants"))
    settings_button.config(text=t("settings"))
    about_button.config(text=t("about"))
    health_button.config(text=t("health"))
    maintenance_button.config(text=t("maintenance"))
    theme_button.config(text=t("light_mode") if theme_sombre_actif else t("dark_mode"))


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
    text=t("sync_panel_title"),
    font=("Segoe UI", 10, "bold"),
    fg=BLUE,
    bg=LIGHT_BLUE,
    anchor="w"
).pack(
    fill="x",
    padx=15,
    pady=(10, 2)
)


sync_detail_header = tk.Frame(sync_frame, bg=LIGHT_BLUE)
sync_detail_header.pack(fill="x", padx=15)

tk.Button(
    sync_detail_header,
    text=t("copy_status"),
    font=("Segoe UI", 8, "bold"),
    bg=CARD,
    fg=BLUE,
    activebackground=CARD,
    relief="flat",
    cursor="hand2",
    command=copier_statut_synchronisation
).pack(side="right")

tk.Label(
    sync_detail_header,
    text=t("copyable_status"),
    font=("Segoe UI", 8, "bold"),
    fg=SECONDARY,
    bg=LIGHT_BLUE,
    anchor="w"
).pack(side="left")

sync_detail_text = tk.Text(
    sync_frame,
    height=3,
    wrap="word",
    font=("Segoe UI", 9),
    fg=TEXT,
    bg=LIGHT_BLUE,
    relief="flat",
    borderwidth=0,
    highlightthickness=0,
    cursor="xterm"
)
sync_detail_text.pack(fill="x", padx=15, pady=(2, 0))
sync_detail_text.configure(state="disabled")
sync_var.trace_add("write", rafraichir_texte_synchronisation)
sync_detail_var.trace_add("write", rafraichir_texte_synchronisation)
sync_progress_var.trace_add("write", rafraichir_texte_synchronisation)
rafraichir_texte_synchronisation()


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
    text="Gruterra",
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
if os.environ.get("BOTANEO_DEMO") != "1":
    root.after(1000, suivi_raspberry.start)
    root.after(500, actualiser_netatmo_seul)
    root.after(5000, verifier_sync_auto)
root.after(3000, verifier_update_au_demarrage)

root.mainloop()