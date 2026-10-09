"""Vue de l'historique d'une plante, en lecture seule, sans dependance externe."""
import math
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

import database
from services.analyse_arrosage import (
    analyser_cycles_arrosage,
    calculer_cycles_arrosage,
    comparer_conditions_cycles,
    date_debut_arrosage,
    formater_date_courte,
    mesurer_cycle_arrosage,
    quantite_arrosage_courte,
    quantite_arrosage_texte,
    resumer_cycles_arrosage,
)
from services.analyse_lumiere import (
    construire_expositions_balcon,
    filtrer_expositions_jour,
    filtrer_expositions_periode,
    mesure_dans_exposition as mesure_dans_exposition_historique,
    resume_expositions_jour,
)
from botaneo_dates import formater_local, maintenant_local, vers_local_naif
from ui_preferences import charger_theme_sombre, charger_langue_interface
from i18n import traduire, normaliser_langue, traduire_courant, traduire_texte_courant as _texte


def vh_t(cle):
    return traduire_courant(cle)


THEME_CLAIR = {
    "BG": "#F5F7F5",
    "CARD": "#FFFFFF",
    "TEXT": "#26332A",
    "SECONDARY": "#718078",
    "BORDER": "#E1E7E2",
    "GREEN": "#4F8A5B",
    "BLUE": "#4677A8",
    "ORANGE": "#D98C32",
    "PURPLE": "#6B55A3",
    "WATER": "#2C9FD6",
    "GRID": "#E1E7E2"
}

THEME_SOMBRE = {
    "BG": "#111816",
    "CARD": "#1B2521",
    "TEXT": "#E8F0EA",
    "SECONDARY": "#9FB0A6",
    "BORDER": "#30423A",
    "GREEN": "#82C990",
    "BLUE": "#8DBAF0",
    "ORANGE": "#F0B35D",
    "PURPLE": "#B8A7F4",
    "WATER": "#65C7FF",
    "GRID": "#30423A"
}

SERIES = {
    "Humidité": {"colonne": 3, "titre": "Humidité du sol", "unite": "%", "couleur": "GREEN", "minimum": 0, "maximum": 100},
    "Température": {"colonne": 2, "titre": "Température", "unite": "°C", "couleur": "ORANGE"},
    "Lumière": {"colonne": 4, "titre": "Luminosité", "unite": "lux", "couleur": "BLUE", "minimum": 0},
    "Conductivité": {"colonne": 5, "titre": "Conductivité", "unite": "µS/cm", "couleur": "PURPLE", "minimum": 0}
}



SERIES_LOCALES = {"Humidité": "series_moisture_choice", "Température": "series_temperature_title", "Lumière": "series_light_choice", "Conductivité": "series_conductivity_title"}


def nom_serie_affiche(nom):
    return vh_t(SERIES_LOCALES[nom]) if nom in SERIES_LOCALES else nom


class SerieLocaleVar(tk.StringVar):
    """Affiche une traduction, retourne aux calculs l'identifiant canonique de la série."""
    def __init__(self, master=None, value=None, name=None):
        super().__init__(master, nom_serie_affiche(value) if value else value, name)

    def get(self):
        valeur = super().get()
        return next((cle for cle in SERIES if nom_serie_affiche(cle) == valeur), valeur)

    def set(self, value):
        super().set(nom_serie_affiche(value))


def placer_etiquettes_evenements(etiquettes, gauche, droite, espacement=8):
    """Place des badges près de leur date sur des lignes sans chevauchement."""
    fins_lignes = []
    resultat = []
    for x, largeur, texte, couleur in sorted(etiquettes, key=lambda e: e[0]):
        largeur = min(largeur, max(droite - gauche, 1))
        debut = max(gauche, min(x + 6, droite - largeur))
        ligne = next((i for i, fin in enumerate(fins_lignes) if debut >= fin + espacement), len(fins_lignes))
        if ligne == len(fins_lignes):
            fins_lignes.append(debut + largeur)
        else:
            fins_lignes[ligne] = debut + largeur
        resultat.append((debut, largeur, ligne, texte, couleur, x))
    return resultat


def theme_actuel():
    return THEME_SOMBRE if charger_theme_sombre() else THEME_CLAIR


def formater_nombre(valeur):
    try:
        nombre = float(valeur)
        if not math.isfinite(nombre):
            return "—"
        if nombre.is_integer():
            return str(int(nombre))
        return f"{nombre:.1f}"
    except (ValueError, TypeError):
        return "—"


def extraire_points(mesures, nom_serie):
    config = SERIES[nom_serie]
    points = []

    for mesure in mesures:
        try:
            date = vers_local_naif(mesure[1])
            valeur = float(mesure[config["colonne"]])

            if date and math.isfinite(valeur):
                points.append((date, valeur))

        except (ValueError, TypeError):
            pass

    return sorted(points)


def limites_graphique(points, nom_serie):
    config = SERIES[nom_serie]
    valeurs = [valeur for _, valeur in points]
    minimum = min(valeurs)
    maximum = max(valeurs)

    if "minimum" in config:
        minimum = min(minimum, config["minimum"])

    if "maximum" in config:
        maximum = max(maximum, config["maximum"])

    if minimum == maximum:
        marge = max(1, abs(minimum) * 0.1)
        minimum -= marge
        maximum += marge

    marge = (maximum - minimum) * 0.08
    return minimum - marge, maximum + marge


def couleur_hex_vers_rgb(couleur):
    couleur = couleur.lstrip("#")
    return tuple(int(couleur[i:i + 2], 16) for i in (0, 2, 4))


def couleur_rgb_vers_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, int(valeur))):02x}" for valeur in rgb)


def melanger_couleurs(couleur_a, couleur_b, ratio=0.5):
    try:
        a = couleur_hex_vers_rgb(couleur_a)
        b = couleur_hex_vers_rgb(couleur_b)
        return couleur_rgb_vers_hex(
            a[i] * (1 - ratio) + b[i] * ratio
            for i in range(3)
        )
    except Exception:
        return couleur_a


def simplifier_coordonnees(coords, largeur_graphique):
    if len(coords) <= 240:
        return coords

    points = list(zip(coords[::2], coords[1::2]))
    cible = max(120, min(260, int(largeur_graphique / 4)))
    pas = max(1, len(points) // cible)
    retenus = points[::pas]
    if retenus[-1] != points[-1]:
        retenus.append(points[-1])

    resultat = []
    for x, y in retenus:
        resultat.extend((x, y))
    return resultat


def analyser_points(points, nom_serie):
    if not points:
        return {
            "tendance": "—",
            "lecture": vh_t("history_reading_no_usable_measure"),
            "couleur": "SECONDARY"
        }

    if len(points) == 1:
        return {
            "tendance": vh_t("trend_stable"),
            "lecture": vh_t("history_reading_single_measure"),
            "couleur": "SECONDARY"
        }

    debut_date, debut_valeur = points[0]
    fin_date, fin_valeur = points[-1]
    duree_heures = max((fin_date - debut_date).total_seconds() / 3600, 0.01)
    variation = fin_valeur - debut_valeur
    variation_jour = variation / duree_heures * 24
    unite = SERIES[nom_serie]["unite"]

    if abs(variation_jour) < 0.5:
        tendance = vh_t("trend_stable")
        couleur = "GREEN"
    elif variation_jour > 0:
        tendance = vh_t('vue_historique_text_190').format(v0=formater_nombre(variation_jour), v1=unite)
        couleur = "BLUE"
    else:
        tendance = vh_t('vue_historique_text_193').format(v0=formater_nombre(variation_jour), v1=unite)
        couleur = "ORANGE"

    if nom_serie == "Humidité":
        derniere = fin_valeur
        if derniere < 20 and variation_jour < -1:
            lecture = vh_t("history_reading_soil_low_down")
            couleur = "ORANGE"
        elif derniere > 35 and variation_jour > -0.5:
            lecture = vh_t("history_reading_soil_still_wet")
            couleur = "BLUE"
        else:
            lecture = vh_t("history_reading_soil_no_global_trend")
    elif nom_serie == "Lumière":
        valeurs = [valeur for _, valeur in points]
        moyenne = sum(valeurs) / len(valeurs)
        valeurs_eclairees = [valeur for valeur in valeurs if valeur >= 50]
        moyenne_eclairee = sum(valeurs_eclairees) / len(valeurs_eclairees) if valeurs_eclairees else 0
        if moyenne < 250 and moyenne_eclairee >= 250:
            lecture = (
                vh_t("history_reading_light_ok_when_lit")
            )
            couleur = "BLUE"
        elif moyenne < 250:
            lecture = vh_t("history_reading_light_low")
            couleur = "ORANGE"
        else:
            lecture = vh_t("history_reading_light_usable")
    elif nom_serie == "Température":
        if abs(variation_jour) >= 2:
            lecture = vh_t("history_reading_temp_change")
            couleur = "ORANGE"
        else:
            lecture = vh_t("history_reading_temp_stable")
    else:
        lecture = vh_t("history_reading_conductivity_prudent")

    return {
        "tendance": tendance,
        "lecture": lecture,
        "couleur": couleur
    }


def ids_humidite_zero_suspects(mesures):
    points = []
    for mesure in mesures:
        try:
            date = vers_local_naif(mesure[1])
            if not date:
                continue
            humidite = float(mesure[3])
            points.append((date, mesure, humidite))
        except (TypeError, ValueError):
            continue

    points.sort(key=lambda item: item[0])
    suspects = set()

    for index, (date, mesure, humidite) in enumerate(points):
        if humidite != 0:
            continue
        avant = next((item for item in reversed(points[:index]) if item[2] > 0), None)
        apres = next((item for item in points[index + 1:] if item[2] > 0), None)
        if not avant or not apres:
            continue
        ecart_avant_h = (date - avant[0]).total_seconds() / 3600
        ecart_apres_h = (apres[0] - date).total_seconds() / 3600
        if ecart_avant_h <= 3 and ecart_apres_h <= 3 and avant[2] >= 5 and apres[2] >= 5:
            suspects.add(mesure[0])

    return suspects


def filtrer_mesures_pour_serie(mesures, nom_serie):
    if nom_serie != "Humidité":
        return list(mesures), set()
    suspects = ids_humidite_zero_suspects(mesures)
    if not suspects:
        return list(mesures), suspects
    return [mesure for mesure in mesures if mesure[0] not in suspects], suspects


def date_locale_depuis_iso(valeur):
    return vers_local_naif(valeur)


def libelle_jour(date_jour):
    return date_jour.strftime("%d/%m/%Y")


def jours_disponibles_mesures(mesures):
    jours = set()
    for mesure in mesures:
        date = date_locale_depuis_iso(mesure[1])
        if date:
            jours.add(date.date())
    return sorted(jours, reverse=True)


def filtrer_mesures_jour(mesures, jour):
    resultat = []
    for mesure in mesures:
        date = date_locale_depuis_iso(mesure[1])
        if date and date.date() == jour:
            resultat.append(mesure)
    return resultat


def filtrer_arrosages_jour(arrosages, jour):
    resultat = []
    for arrosage in arrosages:
        date = date_locale_depuis_iso(arrosage[2])
        if date and date.date() == jour:
            resultat.append(arrosage)
    return resultat


def valeurs_colonne(mesures, index):
    valeurs = []
    for mesure in mesures:
        try:
            valeur = float(mesure[index])
            if math.isfinite(valeur):
                valeurs.append(valeur)
        except (TypeError, ValueError):
            pass
    return valeurs


def moyenne_colonne(mesures, index):
    valeurs = valeurs_colonne(mesures, index)
    if not valeurs:
        return None
    return sum(valeurs) / len(valeurs)


def statistiques_colonne(mesures, index):
    valeurs = valeurs_colonne(mesures, index)
    if not valeurs:
        return None
    return {
        "moyenne": sum(valeurs) / len(valeurs),
        "minimum": min(valeurs),
        "maximum": max(valeurs),
    }


def formater_statistique_jour(nom, stats, unite):
    if not stats:
        return f"- {nom} : —"
    return (
        vh_t('vue_historique_text_366').format(v0=nom, v1=formater_nombre(stats['moyenne']), v2=unite, v3=formater_nombre(stats['minimum']), v4=formater_nombre(stats['maximum']))
    )


def resume_stats_jour_dict(mesures, arrosages=None):
    arrosages = arrosages or []
    return {
        "mesures": len(mesures),
        "arrosages": len(arrosages),
        "humidite": statistiques_colonne(mesures, 3),
        "temperature": statistiques_colonne(mesures, 2),
        "lumiere": statistiques_colonne(mesures, 4),
        "conductivite": statistiques_colonne(mesures, 5),
    }


def formater_moyenne_stats(stats, unite):
    if not stats:
        return "—"
    return f"{formater_nombre(stats['moyenne'])} {unite}"


def libelle_cycle(cycle):
    arrosage = cycle.get("arrosage")
    quantite = quantite_arrosage_courte(arrosage)
    return f"{formater_date_courte(cycle.get('date'))} · {quantite}"


def valeur_cycle(cycle, cle):
    valeur = cycle.get(cle)
    if isinstance(valeur, (int, float)) and math.isfinite(valeur):
        return valeur
    return None


def points_cycle(cycle, nom_serie):
    debut = cycle.get("date")
    if not debut:
        return []
    config = SERIES.get(nom_serie, SERIES["Humidité"])
    index = config["colonne"]
    points = []
    for mesure in cycle.get("mesures") or []:
        date = date_locale_depuis_iso(mesure[1])
        if not date:
            continue
        try:
            valeur = float(mesure[index])
        except (TypeError, ValueError):
            continue
        if math.isfinite(valeur):
            heures = (date - debut).total_seconds() / 3600
            if heures >= 0:
                points.append((heures, valeur))
    return sorted(points)


def valeur_cycle_proche_repere(cycle, nom_serie, heures_cible, tolerance_h=3):
    points = points_cycle(cycle, nom_serie)
    if not points:
        return None
    meilleur = min(points, key=lambda point: abs(point[0] - heures_cible))
    ecart = abs(meilleur[0] - heures_cible)
    if ecart > tolerance_h:
        return None
    return {"heures": meilleur[0], "valeur": meilleur[1], "ecart_h": ecart}


def heures_depuis_debut_cycle(cycle, date):
    debut = cycle.get("date")
    if not debut or not date:
        return None
    try:
        heures = (date - debut).total_seconds() / 3600
    except TypeError:
        return None
    if not math.isfinite(heures) or heures < 0:
        return None
    return heures


def reperes_visuels_cycle(cycle):
    """Repères simples pour dessiner un cycle : arrosage, pic, 24 h, 48 h."""

    reperes = [{"cle": "arrosage", "heures": 0, "libelle": vh_t("watering"), "couleur": "WATER", "style": "plein"}]
    pic_heures = heures_depuis_debut_cycle(cycle, cycle.get("pic_date"))
    if pic_heures is not None:
        reperes.append({"cle": "pic", "heures": pic_heures, "libelle": vh_t('canonical_peak'), "couleur": "ORANGE", "style": "plein"})
    reperes.extend([
        {"cle": "24h", "heures": 24, "libelle": "24 h", "couleur": "PURPLE", "style": "pointille"},
        {"cle": "48h", "heures": 48, "libelle": "48 h", "couleur": "PURPLE", "style": "pointille"},
    ])
    return reperes


def comparer_deux_cycles(cycle_a, cycle_b):
    mesures_a = len(cycle_a.get("mesures") or [])
    mesures_b = len(cycle_b.get("mesures") or [])
    depart_a = valeur_cycle(cycle_a, "premiere_humidite")
    depart_b = valeur_cycle(cycle_b, "premiere_humidite")
    pic_a = valeur_cycle(cycle_a, "pic_humidite")
    pic_b = valeur_cycle(cycle_b, "pic_humidite")
    fin_a = valeur_cycle(cycle_a, "derniere_humidite")
    fin_b = valeur_cycle(cycle_b, "derniere_humidite")
    sechage_a = valeur_cycle(cycle_a, "sechage")
    sechage_b = valeur_cycle(cycle_b, "sechage")
    hausse_a = pic_a - depart_a if pic_a is not None and depart_a is not None else None
    hausse_b = pic_b - depart_b if pic_b is not None and depart_b is not None else None

    def fmt(valeur, unite=""):
        return "—" if valeur is None else f"{formater_nombre(valeur)}{(' ' + unite) if unite else ''}"

    vitesse_24h_a = valeur_cycle(cycle_a, "vitesse_24h")
    vitesse_24h_b = valeur_cycle(cycle_b, "vitesse_24h")
    trou_a = valeur_cycle(cycle_a, "plus_grand_trou_h")
    trou_b = valeur_cycle(cycle_b, "plus_grand_trou_h")

    repere_24_a = valeur_cycle_proche_repere(cycle_a, "Humidité", 24)
    repere_24_b = valeur_cycle_proche_repere(cycle_b, "Humidité", 24)
    repere_48_a = valeur_cycle_proche_repere(cycle_a, "Humidité", 48)
    repere_48_b = valeur_cycle_proche_repere(cycle_b, "Humidité", 48)

    def fmt_repere(repere):
        if not repere:
            return "—"
        return vh_t('comparison_report_1').format(v0=formater_nombre(repere['valeur']), v1=formater_nombre(repere['heures']))

    def valeur_repere(repere):
        return repere["valeur"] if repere else None

    comparabilite = comparer_conditions_cycles(cycle_a, cycle_b)

    lignes = [
        vh_t('comparison_report_2'),
        "",
        vh_t('comparison_report_3').format(v0=libelle_cycle(cycle_a)),
        vh_t('comparison_report_4').format(v0=libelle_cycle(cycle_b)),
        "",
        vh_t('comparison_report_5').format(v0=mesures_a, v1=mesures_b, v2=mesures_a - mesures_b),
        vh_t('comparison_report_6').format(v0=fmt(depart_a, '%'), v1=fmt(depart_b, '%')),
        vh_t('comparison_report_7').format(v0=fmt(pic_a, '%'), v1=fmt(pic_b, '%')),
        vh_t('comparison_report_8').format(v0=fmt_repere(repere_24_a), v1=fmt_repere(repere_24_b)),
        vh_t('comparison_report_9').format(v0=fmt_repere(repere_48_a), v1=fmt_repere(repere_48_b)),
        vh_t('comparison_report_10').format(v0=fmt(fin_a, '%'), v1=fmt(fin_b, '%')),
        vh_t('comparison_report_11').format(v0=fmt(hausse_a, vh_t('comparison_report_34')), v1=fmt(hausse_b, vh_t('comparison_report_34'))),
        vh_t('comparison_report_12').format(v0=fmt(sechage_a, vh_t('comparison_report_35')), v1=fmt(sechage_b, vh_t('comparison_report_35'))),
        vh_t('comparison_report_13').format(v0=fmt(vitesse_24h_a, vh_t('comparison_report_35')), v1=fmt(vitesse_24h_b, vh_t('comparison_report_35'))),
        vh_t('comparison_report_14').format(v0=cycle_a.get('qualite') or '—', v1=cycle_b.get('qualite') or '—'),
        comparabilite["texte"],
    ]
    if sechage_a is not None and sechage_b is not None:
        diff = sechage_a - sechage_b
        if abs(diff) < 0.4:
            lecture = vh_t('comparison_report_16')
        elif diff < 0:
            lecture = vh_t('comparison_report_18')
        else:
            lecture = vh_t('comparison_report_19')
        lignes.append(vh_t('comparison_report_17').format(v0=lecture, v1=formater_nombre(diff)))
    lignes.append(vh_t('comparison_report_15'))
    return {
        "texte": "\n".join(lignes),
        "lignes_tableau": [
            (vh_t('comparison_report_20'), str(mesures_a), str(mesures_b), str(mesures_a - mesures_b)),
            (vh_t('comparison_report_21'), fmt(depart_a, "%"), fmt(depart_b, "%"), fmt((depart_a - depart_b) if depart_a is not None and depart_b is not None else None, vh_t('comparison_report_34'))),
            (vh_t('comparison_report_22'), fmt(pic_a, "%"), fmt(pic_b, "%"), fmt((pic_a - pic_b) if pic_a is not None and pic_b is not None else None, vh_t('comparison_report_34'))),
            (vh_t('comparison_report_23'), fmt_repere(repere_24_a), fmt_repere(repere_24_b), fmt((valeur_repere(repere_24_a) - valeur_repere(repere_24_b)) if valeur_repere(repere_24_a) is not None and valeur_repere(repere_24_b) is not None else None, vh_t('comparison_report_34'))),
            (vh_t('comparison_report_24'), fmt_repere(repere_48_a), fmt_repere(repere_48_b), fmt((valeur_repere(repere_48_a) - valeur_repere(repere_48_b)) if valeur_repere(repere_48_a) is not None and valeur_repere(repere_48_b) is not None else None, vh_t('comparison_report_34'))),
            (vh_t('comparison_report_25'), fmt(fin_a, "%"), fmt(fin_b, "%"), fmt((fin_a - fin_b) if fin_a is not None and fin_b is not None else None, vh_t('comparison_report_34'))),
            (vh_t('comparison_report_26'), fmt(hausse_a, vh_t('comparison_report_34')), fmt(hausse_b, vh_t('comparison_report_34')), fmt((hausse_a - hausse_b) if hausse_a is not None and hausse_b is not None else None, vh_t('comparison_report_34'))),
            (vh_t('comparison_report_27'), fmt(sechage_a, vh_t('comparison_report_35')), fmt(sechage_b, vh_t('comparison_report_35')), fmt((sechage_a - sechage_b) if sechage_a is not None and sechage_b is not None else None, vh_t('comparison_report_35'))),
            (vh_t('comparison_report_28'), fmt(vitesse_24h_a, vh_t('comparison_report_35')), fmt(vitesse_24h_b, vh_t('comparison_report_35')), fmt((vitesse_24h_a - vitesse_24h_b) if vitesse_24h_a is not None and vitesse_24h_b is not None else None, vh_t('comparison_report_35'))),
            (vh_t('comparison_report_29'), cycle_a.get("lecture_sechage") or "—", "", ""),
            (vh_t('comparison_report_30'), cycle_b.get("lecture_sechage") or "—", "", ""),
            (vh_t('comparison_report_31'), fmt(trou_a, "h"), fmt(trou_b, "h"), fmt((trou_a - trou_b) if trou_a is not None and trou_b is not None else None, "h")),
            (vh_t('comparison_report_32'), cycle_a.get("qualite") or "—", cycle_b.get("qualite") or "—", "—"),
            (vh_t('comparison_report_33'), _texte(comparabilite["niveau"]), "", "; ".join(comparabilite["alertes"])),
        ],
    }


def comparer_deux_jours(mesures, arrosages, jour_a, jour_b):
    mesures_a = filtrer_mesures_jour(mesures, jour_a)
    mesures_b = filtrer_mesures_jour(mesures, jour_b)
    arrosages_a = filtrer_arrosages_jour(arrosages, jour_a)
    arrosages_b = filtrer_arrosages_jour(arrosages, jour_b)
    stats_a = resume_stats_jour_dict(mesures_a, arrosages_a)
    stats_b = resume_stats_jour_dict(mesures_b, arrosages_b)
    lignes = [
        vh_t('comparison_report_36').format(v0=libelle_jour(jour_a), v1=libelle_jour(jour_b)),
        "",
        vh_t('comparison_report_37').format(v0=stats_a['mesures'], v1=stats_b['mesures']),
        vh_t('comparison_report_38').format(v0=stats_a['arrosages'], v1=stats_b['arrosages']),
        vh_t('comparison_report_39').format(v0=formater_moyenne_stats(stats_a['humidite'], '%'), v1=formater_moyenne_stats(stats_b['humidite'], '%')),
        vh_t('comparison_report_40').format(v0=formater_moyenne_stats(stats_a['temperature'], '°C'), v1=formater_moyenne_stats(stats_b['temperature'], '°C')),
        vh_t('comparison_report_41').format(v0=formater_moyenne_stats(stats_a['lumiere'], 'lux'), v1=formater_moyenne_stats(stats_b['lumiere'], 'lux')),
        vh_t('comparison_report_42').format(v0=formater_moyenne_stats(stats_a['conductivite'], 'µS/cm'), v1=formater_moyenne_stats(stats_b['conductivite'], 'µS/cm')),
    ]
    if stats_a['humidite'] and stats_b['humidite']:
        ecart = stats_a['humidite']['moyenne'] - stats_b['humidite']['moyenne']
        lignes.append(vh_t('comparison_report_43').format(v0=formater_nombre(ecart)))
    if stats_a['lumiere'] and stats_b['lumiere']:
        ecart_lumiere = stats_a['lumiere']['moyenne'] - stats_b['lumiere']['moyenne']
        lignes.append(vh_t('comparison_report_44').format(v0=formater_nombre(ecart_lumiere)))
    return {
        "texte": "\n".join(lignes),
        "stats_a": stats_a,
        "stats_b": stats_b,
        "mesures_a": mesures_a,
        "mesures_b": mesures_b,
        "arrosages_a": arrosages_a,
        "arrosages_b": arrosages_b,
    }


def resume_moyennes_jour(mesures, jour, arrosages=None):
    if not jour:
        return vh_t("history_day_no_date")
    arrosages = arrosages or []
    if not mesures:
        if arrosages:
            details = []
            for arrosage in arrosages:
                quantite = f"{formater_nombre(arrosage[3])} ml" if arrosage[3] is not None else vh_t("quantity_not_noted")
                details.append(quantite)
            return vh_t("history_day_no_measure_with_watering").format(day=libelle_jour(jour), details=', '.join(details))
        return vh_t("history_day_no_measure").format(day=libelle_jour(jour))

    mesures_ordonnees = sorted(mesures, key=lambda mesure: mesure[1] or "")
    premiere = date_locale_depuis_iso(mesures_ordonnees[0][1])
    derniere = date_locale_depuis_iso(mesures_ordonnees[-1][1])
    humidite = statistiques_colonne(mesures, 3)
    temperature = statistiques_colonne(mesures, 2)
    lumiere = statistiques_colonne(mesures, 4)
    conductivite = statistiques_colonne(mesures, 5)

    lignes = [vh_t("history_day_measure_count").format(day=libelle_jour(jour), count=len(mesures))]
    if premiere and derniere:
        lignes.append(vh_t("history_day_measured_range").format(start=premiere.strftime('%H:%M'), end=derniere.strftime('%H:%M')))
    if arrosages:
        details = []
        for arrosage in arrosages:
            heure = date_locale_depuis_iso(arrosage[2])
            heure_txt = heure.strftime('%H:%M') if heure else vh_t("unknown_time")
            quantite = f"{formater_nombre(arrosage[3])} ml" if arrosage[3] is not None else vh_t("quantity_not_noted")
            eau = f" · {arrosage[8]}" if len(arrosage) > 8 and arrosage[8] else ""
            details.append(f"{heure_txt} : {quantite}{eau}")
        lignes.append(vh_t("history_day_watering_list").format(details=" ; ".join(details)))
    else:
        lignes.append(vh_t("history_day_no_watering"))

    lignes.extend([
        formater_statistique_jour(vh_t("series_soil_humidity_short"), humidite, "%"),
        formater_statistique_jour(vh_t("series_temperature_short"), temperature, "°C"),
        formater_statistique_jour(vh_t("series_light_short"), lumiere, "lux"),
        formater_statistique_jour(vh_t("series_conductivity_short"), conductivite, "µS/cm"),
    ])

    if len(mesures) < 6:
        lignes.append(vh_t("history_day_few_measurements"))
    return "\n".join(lignes)


def ouvrir_historique(parent, plante_id, action_synchroniser=None):
    couleurs = theme_actuel()
    plante = database.get_plante(plante_id)

    fenetre = tk.Toplevel(parent)
    fenetre.title(vh_t("history_window_title").format(plant=(plante[1] if plante else vh_t("plant_missing"))))
    largeur_fenetre = min(1080, max(900, fenetre.winfo_screenwidth() - 90))
    hauteur_fenetre = min(740, max(620, fenetre.winfo_screenheight() - 120))
    fenetre.geometry(f"{largeur_fenetre}x{hauteur_fenetre}+40+30")
    fenetre.minsize(860, 600)
    fenetre.configure(bg=couleurs["BG"])

    tk.Label(fenetre, text=plante[1] if plante else vh_t("plant_missing"),
             bg=couleurs["BG"], fg=couleurs["TEXT"],
             font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=24, pady=(18, 2))
    tk.Label(fenetre, text=vh_t("history_subtitle"),
             bg=couleurs["BG"], fg=couleurs["SECONDARY"],
             font=("Segoe UI", 10)).pack(anchor="w", padx=24)

    barre = tk.Frame(fenetre, bg=couleurs["BG"])
    barre.pack(fill="x", padx=24, pady=12)

    periode = tk.StringVar(value=vh_t("period_all"))
    serie = SerieLocaleVar(value="Humidité")
    jour_selectionne = tk.StringVar(value="")
    bilan = tk.StringVar()
    tri_table = {"colonne": None}
    jours_par_libelle = {}

    tk.Label(barre, text=vh_t("period"), bg=couleurs["BG"],
             fg=couleurs["TEXT"]).pack(side="left", padx=(0, 8))
    choix_periode = ttk.Combobox(barre, textvariable=periode,
                                 values=(vh_t("period_day"), vh_t("period_24h"), vh_t("period_7d"), vh_t("period_all")),
                                 state="readonly", width=14)
    choix_periode.pack(side="left")

    tk.Label(barre, text=vh_t("day"), bg=couleurs["BG"],
             fg=couleurs["TEXT"]).pack(side="left", padx=(18, 8))
    choix_jour = ttk.Combobox(barre, textvariable=jour_selectionne,
                              values=(), state="disabled", width=12, height=12)
    choix_jour.pack(side="left")

    tk.Label(barre, text=vh_t("measurement"), bg=couleurs["BG"],
             fg=couleurs["TEXT"]).pack(side="left", padx=(18, 8))
    choix_serie = ttk.Combobox(barre, textvariable=serie,
                               values=tuple(nom_serie_affiche(nom) for nom in SERIES),
                               state="readonly", width=16)
    choix_serie.pack(side="left")

    if action_synchroniser:
        ttk.Button(
            barre,
            text=vh_t("resync"),
            command=action_synchroniser
        ).pack(side="left", padx=(14, 0))

    tk.Label(barre, textvariable=bilan, bg=couleurs["BG"],
             fg=couleurs["TEXT"]).pack(side="left", padx=18)

    resume_frame = tk.Frame(fenetre, bg=couleurs["CARD"],
                            highlightbackground=couleurs["BORDER"],
                            highlightthickness=1)
    resume_frame.pack(fill="x", padx=24, pady=(0, 10))

    resume_vars = {
        "dernier": tk.StringVar(value="—"),
        "moyenne": tk.StringVar(value="—"),
        "minimum": tk.StringVar(value="—"),
        "maximum": tk.StringVar(value="—"),
        "tendance": tk.StringVar(value="—")
    }

    for titre, variable in ((vh_t("latest"), resume_vars["dernier"]),
                            (vh_t("average"), resume_vars["moyenne"]),
                            (vh_t("minimum"), resume_vars["minimum"]),
                            (vh_t("maximum"), resume_vars["maximum"]),
                            (vh_t("trend"), resume_vars["tendance"])):
        bloc = tk.Frame(resume_frame, bg=couleurs["CARD"])
        bloc.pack(side="left", expand=True, fill="x", padx=8, pady=8)
        tk.Label(bloc, textvariable=variable, bg=couleurs["CARD"],
                 fg=couleurs["TEXT"], font=("Segoe UI", 14, "bold")).pack()
        tk.Label(bloc, text=titre, bg=couleurs["CARD"],
                 fg=couleurs["SECONDARY"], font=("Segoe UI", 8)).pack()

    jour_resume_var = tk.StringVar(value=vh_t("history_day_help"))
    jour_resume_label = tk.Label(
        fenetre,
        textvariable=jour_resume_var,
        bg=couleurs["CARD"],
        fg=couleurs["TEXT"],
        font=("Segoe UI", 9),
        anchor="w",
        justify="left",
        wraplength=980,
        highlightbackground=couleurs["BORDER"],
        highlightthickness=1
    )
    qualite_var = tk.StringVar(value=vh_t("data_quality_waiting"))
    qualite_label = tk.Label(
        fenetre,
        textvariable=qualite_var,
        bg=couleurs["CARD"],
        fg=couleurs["SECONDARY"],
        font=("Segoe UI", 9, "bold"),
        anchor="w",
        justify="left",
        wraplength=980,
        highlightbackground=couleurs["BORDER"],
        highlightthickness=1
    )
    qualite_label.pack(fill="x", padx=24, pady=(0, 8), ipady=6)

    lecture_var = tk.StringVar(value=vh_t("history_select_measure"))
    lecture_label = tk.Label(
        fenetre,
        textvariable=lecture_var,
        bg=couleurs["CARD"],
        fg=couleurs["TEXT"],
        font=("Segoe UI", 10, "bold"),
        anchor="w",
        justify="left",
        wraplength=980,
        highlightbackground=couleurs["BORDER"],
        highlightthickness=1
    )
    lecture_label.pack(fill="x", padx=24, pady=(0, 10), ipady=8)

    canvas = tk.Canvas(fenetre, bg=couleurs["CARD"],
                       highlightbackground=couleurs["BORDER"],
                       highlightthickness=1, height=240)
    canvas.pack(fill="both", expand=True, padx=24)

    outils_table = tk.Frame(fenetre, bg=couleurs["BG"])
    outils_table.pack(fill="x", padx=24, pady=(6, 8))

    tk.Label(
        outils_table,
        text=vh_t("history_quick_markers"),
        bg=couleurs["BG"],
        fg=couleurs["SECONDARY"],
        font=("Segoe UI", 9, "bold")
    ).pack(side="left", padx=(0, 10))

    outils_post_arrosage = tk.Frame(fenetre, bg=couleurs["BG"])

    tk.Label(
        outils_post_arrosage,
        text=vh_t("after_watering"),
        bg=couleurs["BG"],
        fg=couleurs["WATER"],
        font=("Segoe UI", 9, "bold")
    ).pack(side="left", padx=(0, 10))

    cadre = tk.Frame(fenetre, bg=couleurs["BG"])
    cadre.pack(fill="both", expand=True, padx=24, pady=(0, 18))

    colonnes = ("date", "humidite", "temperature", "lumiere", "conductivite", "_mesure_id")
    table = ttk.Treeview(cadre, columns=colonnes, show="headings", height=7)
    titres = (vh_t("date_time"), vh_t("humidity_percent"), vh_t("temperature_c"), vh_t("light_lux"), vh_t("conductivity_us"))

    for nom, titre, largeur in zip(colonnes[:5], titres, (185, 110, 130, 120, 165)):
        table.heading(nom, text=titre, command=lambda col=nom: trier_table(col))
        table.column(nom, width=largeur, minwidth=80, anchor="center")
    table.heading("_mesure_id", text="")
    table.column("_mesure_id", width=0, minwidth=0, stretch=False)

    scroll = ttk.Scrollbar(cadre, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    table.pack(side="left", fill="both", expand=True)

    points = []
    mesures_courantes = []
    arrosages_courants = []
    expositions_courantes = []
    points_graphique_courants = []
    repere_graphique = {"index": None}
    bilan_jour_courant = {"texte": "", "jour": ""}

    def analyser_qualite_donnees(mesures, periode_affichee):
        dates = []
        for mesure in mesures:
            date = vers_local_naif(mesure[1])
            if date:
                dates.append(date)
        dates.sort()
        if not dates:
            return vh_t('vue_historique_text_796'), "SECONDARY"
        debut = dates[0]
        fin = dates[-1]
        if periode_affichee == vh_t("period_all"):
            return (
                vh_t('vue_historique_text_801').format(v0=len(dates), v1=debut.strftime('%d/%m %H:%M'), v2=fin.strftime('%d/%m %H:%M')),
                "SECONDARY"
            )
        duree_heures = max((fin - debut).total_seconds() / 3600, 0)
        ecarts = []
        for avant, apres in zip(dates, dates[1:]):
            ecarts.append((apres - avant).total_seconds() / 3600)
        plus_grand_trou = max(ecarts) if ecarts else 0
        trous_importants = sum(1 for ecart in ecarts if ecart > 1.8)
        attendu = int(duree_heures) + 1 if duree_heures >= 1 else len(dates)
        manque_estime = max(attendu - len(dates), 0)
        couverture = f"{len(dates)}/{attendu}" if attendu else str(len(dates))
        texte = (
            vh_t('vue_historique_text_816').format(v0=couverture, v1=debut.strftime('%d/%m %H:%M'), v2=fin.strftime('%d/%m %H:%M'), v3=plus_grand_trou)
        )
        if manque_estime or trous_importants:
            texte += vh_t('vue_historique_text_821').format(v0=manque_estime, v1=trous_importants)
            return texte, "ORANGE"
        texte += vh_t('vue_historique_text_823')
        return texte, "GREEN"

    def valeur_tri_mesure(mesure, colonne):
        index_par_colonne = {
            "date": 1,
            "temperature": 2,
            "humidite": 3,
            "lumiere": 4,
            "conductivite": 5
        }
        index = index_par_colonne.get(colonne)
        if index is None:
            return float("-inf")
        valeur = mesure[index]
        if colonne == "date":
            try:
                date = vers_local_naif(valeur)
                return date.timestamp() if date else float("-inf")
            except (ValueError, TypeError):
                return float("-inf")
        try:
            nombre = float(valeur)
            return nombre if math.isfinite(nombre) else float("-inf")
        except (ValueError, TypeError):
            return float("-inf")


    def libelle_tri(colonne):
        return {
            "date": vh_t('vue_historique_text_853'),
            "humidite": vh_t('vue_historique_text_854'),
            "temperature": vh_t('vue_historique_text_855'),
            "lumiere": vh_t('vue_historique_text_856'),
            "conductivite": vh_t('vue_historique_text_857')
        }.get(colonne, vh_t('vue_historique_text_874'))


    def afficher_mesures_table(mesures, colonne_tri=None):
        for item in table.get_children():
            table.delete(item)

        for mesure in mesures:
            try:
                date = formater_local(mesure[1], str(mesure[1] or "—"))
            except (ValueError, TypeError):
                date = str(mesure[1] or "—")

            item_id = table.insert("", "end", values=(date, formater_nombre(mesure[3]),
                                                       formater_nombre(mesure[2]),
                                                       formater_nombre(mesure[4]),
                                                       formater_nombre(mesure[5])))
            try:
                table.set(item_id, "_mesure_id", mesure[0])
            except Exception:
                pass

        if mesures and colonne_tri:
            enfants = table.get_children()
            if enfants:
                table.selection_set(enfants[0])
                table.focus(enfants[0])
                table.see(enfants[0])


    def trier_table(colonne):
        tri_table["colonne"] = colonne
        mesures_triees = sorted(
            mesures_courantes,
            key=lambda mesure: valeur_tri_mesure(mesure, colonne),
            reverse=True
        )
        afficher_mesures_table(mesures_triees, colonne)
        if mesures_triees:
            meilleure = mesures_triees[0]
            valeur = valeur_tri_mesure(meilleure, colonne)
            if colonne == "date":
                try:
                    date = formater_local(meilleure[1], str(meilleure[1] or "—"))
                except (ValueError, TypeError):
                    date = str(meilleure[1] or "—")
                bilan.set(vh_t('vue_historique_text_904').format(v0=len(mesures_courantes), v1=libelle_tri(colonne), v2=date))
            elif math.isfinite(valeur):
                unite = {
                    "humidite": "%",
                    "temperature": "°C",
                    "lumiere": "lux",
                    "conductivite": "µS/cm"
                }.get(colonne, "")
                bilan.set(vh_t('vue_historique_text_912').format(v0=len(mesures_courantes), v1=libelle_tri(colonne), v2=formater_nombre(valeur), v3=unite))
            else:
                bilan.set(vh_t('vue_historique_text_914').format(v0=len(mesures_courantes), v1=libelle_tri(colonne)))


    def colonne_serie_actuelle():
        return {
            "Humidité": "humidite",
            "Température": "temperature",
            "Lumière": "lumiere",
            "Conductivité": "conductivite"
        }.get(serie.get(), "humidite")


    def selectionner_mesure(mesure, libelle, valeur=None, unite=""):
        if not mesure:
            bilan.set(vh_t('vue_historique_text_928').format(v0=len(mesures_courantes)))
            return
        mesure_id = str(mesure[0])
        for item in table.get_children():
            if str(table.set(item, "_mesure_id")) == mesure_id:
                table.selection_set(item)
                table.focus(item)
                table.see(item)
                break
        detail = f" · {formater_nombre(valeur)} {unite}" if valeur is not None and math.isfinite(valeur) else ""
        bilan.set(vh_t('vue_historique_text_938').format(v0=len(mesures_courantes), v1=libelle, v2=detail))


    def selectionner_repere(type_repere):
        colonne = colonne_serie_actuelle()
        valeurs = []
        for mesure in mesures_courantes:
            valeur = valeur_tri_mesure(mesure, colonne)
            if math.isfinite(valeur):
                valeurs.append((mesure, valeur))
        if not valeurs:
            selectionner_mesure(None, vh_t('vue_historique_text_965'))
            return

        unite = SERIES[serie.get()]["unite"]
        if type_repere == "max":
            mesure, valeur = max(valeurs, key=lambda item: item[1])
            selectionner_mesure(mesure, f"maximum {nom_serie_affiche(serie.get()).lower()}", valeur, unite)
        elif type_repere == "min":
            mesure, valeur = min(valeurs, key=lambda item: item[1])
            selectionner_mesure(mesure, f"minimum {nom_serie_affiche(serie.get()).lower()}", valeur, unite)
        elif type_repere == "moyenne":
            moyenne = sum(valeur for _, valeur in valeurs) / len(valeurs)
            mesure, valeur = min(valeurs, key=lambda item: abs(item[1] - moyenne))
            selectionner_mesure(mesure, vh_t('vue_historique_text_962').format(v0=formater_nombre(moyenne), v1=unite), valeur, unite)
        elif type_repere == "derniere":
            mesure = max(mesures_courantes, key=lambda item: valeur_tri_mesure(item, "date"))
            valeur = valeur_tri_mesure(mesure, colonne)
            selectionner_mesure(mesure, vh_t('vue_historique_text_966').format(v0=nom_serie_affiche(serie.get()).lower()), valeur, unite)


    def minutes_repere(repere):
        valeur = repere[4]
        unite = repere[5]
        if unite == "minutes":
            return valeur
        if unite == "heures":
            return valeur * 60
        if unite == "jours":
            return valeur * 24 * 60
        return valeur


    def selectionner_apres_arrosage(repere):
        if not arrosages_courants:
            selectionner_mesure(None, vh_t('vue_historique_text_983'))
            return
        if not mesures_courantes:
            selectionner_mesure(None, vh_t('vue_historique_text_986'))
            return

        dernier_arrosage = max(
            arrosages_courants,
            key=lambda item: valeur_tri_mesure((None, item[2], None, None, None, None), "date")
        )
        date_arrosage = date_locale_depuis_iso(dernier_arrosage[2])
        if not date_arrosage:
            selectionner_mesure(None, vh_t('vue_historique_text_995'))
            return

        cible = date_arrosage + timedelta(minutes=minutes_repere(repere))
        mesures_apres = []
        for mesure in mesures_courantes:
            date_mesure = date_locale_depuis_iso(mesure[1])
            if not date_mesure:
                continue
            if date_mesure >= date_arrosage:
                mesures_apres.append((mesure, date_mesure))

        if not mesures_apres:
            selectionner_mesure(None, vh_t('vue_historique_text_1008').format(v0=repere[2]))
            return

        mesure, date_mesure = min(mesures_apres, key=lambda item: abs((item[1] - cible).total_seconds()))
        colonne = colonne_serie_actuelle()
        valeur = valeur_tri_mesure(mesure, colonne)
        unite = SERIES[serie.get()]["unite"]
        ecart_min = abs((date_mesure - cible).total_seconds()) / 60
        selectionner_mesure(
            mesure,
            vh_t('vue_historique_text_1018').format(v0=repere[2], v1=ecart_min),
            valeur,
            unite
        )


    def remettre_ordre_normal():
        tri_table["colonne"] = None
        afficher_mesures_table(mesures_courantes)
        bilan.set(vh_t('vue_historique_text_1027').format(v0=len(mesures_courantes)))


    def graduations_temps(start, end):
        duree_heures = max((end - start).total_seconds() / 3600, 0)
        if duree_heures <= 8:
            pas_heures = 1
        elif duree_heures <= 30:
            pas_heures = 3
        elif duree_heures <= 72:
            pas_heures = 6
        elif duree_heures <= 24 * 10:
            pas_heures = 24
        else:
            pas_heures = 24 * 7

        base = start.replace(minute=0, second=0, microsecond=0)
        while base < start:
            base += timedelta(hours=pas_heures)
        graduations = []
        courant = base
        while courant <= end:
            graduations.append(courant)
            courant += timedelta(hours=pas_heures)
        return graduations


    def libelle_graduation(date, start, end):
        duree_heures = max((end - start).total_seconds() / 3600, 0)
        if duree_heures <= 36:
            return date.strftime("%H:%M")
        if date.hour == 0 or duree_heures > 72:
            return date.strftime("%d/%m")
        return date.strftime("%Hh")


    def selectionner_point_graphique_depuis_x(x_souris):
        if not points_graphique_courants:
            return
        index, date, valeur, x, y = min(
            points_graphique_courants,
            key=lambda item: abs(item[3] - x_souris)
        )
        repere_graphique["index"] = index
        unite = SERIES[serie.get()]["unite"]
        bilan.set(
            vh_t('vue_historique_text_1073').format(v0=len(mesures_courantes), v1=date.strftime('%d/%m/%Y %H:%M'), v2=formater_nombre(valeur), v3=unite)
        )
        dessiner()


    def dessiner(event=None):
        nonlocal points_graphique_courants
        canvas.delete("all")
        w = max(canvas.winfo_width(), 240)
        h = max(canvas.winfo_height(), 180)
        x0, x1, y0, y1 = 72, w - 38, 48, h - 54
        config = SERIES[serie.get()]
        couleur_ligne = couleurs[config["couleur"]]
        couleur_secondaire = couleurs["SECONDARY"]
        couleur_grille = melanger_couleurs(couleurs["GRID"], couleurs["CARD"], 0.35)
        couleur_zone = melanger_couleurs(couleur_ligne, couleurs["CARD"], 0.82)

        canvas.create_text(x0, 22, text=f"{_texte(config['titre'])} ({config['unite']})",
                           anchor="w", fill=couleurs["TEXT"],
                           font=("Segoe UI", 12, "bold"))
        if serie.get() == "Lumière":
            aide_graphique = vh_t("history_light_graph_help")
        else:
            aide_graphique = vh_t("history_graph_help")
        canvas.create_text(
            x0,
            39,
            text=aide_graphique,
            anchor="w",
            fill=couleur_secondaire,
            font=("Segoe UI", 8)
        )
        canvas.create_text(x1, 22, text=vh_t('vue_historique_text_1101').format(v0=len(points)),
                           anchor="e", fill=couleur_secondaire,
                           font=("Segoe UI", 9))

        if not points:
            canvas.create_text(w / 2, h / 2, text=vh_t("history_no_measure_period"),
                               fill=couleur_secondaire, font=("Segoe UI", 11))
            return

        low, high = limites_graphique(points, serie.get())

        canvas.create_rectangle(x0, y0, x1, y1, outline=couleurs["BORDER"], fill="")

        for i in range(5):
            value = low + (high - low) * i / 4
            y = y1 - (y1 - y0) * i / 4
            canvas.create_line(x0, y, x1, y, fill=couleur_grille)
            canvas.create_text(x0 - 14, y, text=formater_nombre(value),
                               anchor="e", fill=couleur_secondaire,
                               font=("Segoe UI", 8))

        start, end = points[0][0], points[-1][0]
        dates_arrosage_visibles = []
        for arrosage in arrosages_courants:
            date_arrosage = date_locale_depuis_iso(arrosage[2])
            if date_arrosage:
                dates_arrosage_visibles.append(date_arrosage)
        if dates_arrosage_visibles:
            start = min(start, min(dates_arrosage_visibles))
            end = max(end, max(dates_arrosage_visibles))
        dates_exposition_visibles = []
        for sortie_balcon, retour_balcon in expositions_courantes:
            dates_exposition_visibles.append(sortie_balcon)
            if retour_balcon:
                dates_exposition_visibles.append(retour_balcon)
        if dates_exposition_visibles:
            start = min(start, min(dates_exposition_visibles))
            end = max(end, max(dates_exposition_visibles))
        span = (end - start).total_seconds()
        coords = []
        etiquettes_evenements = []

        def ajouter_etiquette(x, texte, couleur):
            from tkinter.font import Font
            largeur = Font(family="Segoe UI", size=9, weight="bold").measure(texte) + 12
            etiquettes_evenements.append((x, largeur, texte, couleur))

        for sortie_balcon, retour_balcon in expositions_courantes:
            retour_effectif = retour_balcon or end
            if retour_effectif < start or sortie_balcon > end:
                continue
            debut_zone = max(sortie_balcon, start)
            fin_zone = min(retour_effectif, end)
            if fin_zone < debut_zone:
                continue
            x_debut = x0 + (x1 - x0) * (debut_zone - start).total_seconds() / span if span else (x0 + x1) / 2
            x_fin = x0 + (x1 - x0) * (fin_zone - start).total_seconds() / span if span else x_debut
            couleur_balcon = melanger_couleurs(couleurs["ORANGE"], couleurs["CARD"], 0.80)
            canvas.create_rectangle(x_debut, y0, x_fin, y1, fill=couleur_balcon, outline="")
            canvas.create_line(x_debut, y0, x_debut, y1, fill=couleurs["ORANGE"], dash=(2, 4))
            ajouter_etiquette(x_debut, vh_t("balcony_out_short"), couleurs["ORANGE"])
            if retour_balcon:
                canvas.create_line(x_fin, y0, x_fin, y1, fill=couleurs["BLUE"], dash=(2, 4))
                ajouter_etiquette(x_fin, vh_t("back_inside_short"), couleurs["BLUE"])
            elif x_fin - x_debut > 46:
                canvas.create_text(
                    (x_debut + x_fin) / 2,
                    y0 + 28,
                    text=vh_t("return_not_recorded"),
                    fill=couleurs["SECONDARY"],
                    font=("Segoe UI", 8)
                )

        for arrosage in arrosages_courants:
            date_arrosage = date_locale_depuis_iso(arrosage[2])
            if not date_arrosage:
                continue
            if not (start <= date_arrosage <= end):
                continue
            x_arrosage = x0 + (x1 - x0) * (date_arrosage - start).total_seconds() / span if span else (x0 + x1) / 2
            quantite = arrosage[3]
            quantite_txt = f"{quantite:g} ml" if quantite is not None else vh_t("watering_short")
            canvas.create_line(
                x_arrosage, y0, x_arrosage, y1,
                fill=couleurs["WATER"],
                width=2,
                dash=(5, 4)
            )
            canvas.create_oval(
                x_arrosage - 6, y0 - 2, x_arrosage + 6, y0 + 10,
                fill=couleurs["WATER"],
                outline=couleurs["CARD"],
                width=2
            )
            ajouter_etiquette(x_arrosage, f"💧 {quantite_txt}", couleurs["WATER"])

        for debut_badge, largeur_badge, ligne_badge, texte_badge, couleur_badge, x_evenement in placer_etiquettes_evenements(etiquettes_evenements, x0, x1):
            haut_badge = y0 + 5 + ligne_badge * 23
            canvas.create_rectangle(debut_badge, haut_badge, debut_badge + largeur_badge, haut_badge + 20,
                                    fill=couleurs["CARD"], outline=couleur_badge, tags="event_labels")
            canvas.create_text(debut_badge + 6, haut_badge + 10, text=texte_badge, anchor="w",
                               fill=couleur_badge, font=("Segoe UI", 9, "bold"), tags="event_labels")

        points_graphique_courants = []
        for index_point, (date, valeur) in enumerate(points):
            x = x0 + (x1 - x0) * (date - start).total_seconds() / span if span else (x0 + x1) / 2
            y = y1 - (y1 - y0) * (valeur - low) / (high - low)
            coords.extend((x, y))
            points_graphique_courants.append((index_point, date, valeur, x, y))

        coords_ligne = simplifier_coordonnees(coords, x1 - x0)

        if len(coords_ligne) >= 4:
            zone = [coords_ligne[0], y1] + coords_ligne + [coords_ligne[-2], y1]
            canvas.create_polygon(*zone, fill=couleur_zone, outline="")
            canvas.create_line(*coords_ligne, fill=melanger_couleurs(couleur_ligne, couleurs["CARD"], 0.55), width=7, smooth=True)
            canvas.create_line(*coords_ligne, fill=couleur_ligne, width=3, smooth=True)
        elif coords_ligne:
            x, y = coords_ligne[0], coords_ligne[1]
            canvas.create_oval(x - 5, y - 5, x + 5, y + 5,
                               fill=couleur_ligne, outline=couleurs["CARD"])

        points_marqueurs = list(zip(coords[::2], coords[1::2]))
        if len(points_marqueurs) <= 28:
            marqueurs = points_marqueurs
        else:
            pas = max(1, len(points_marqueurs) // 10)
            marqueurs = points_marqueurs[::pas]
            if marqueurs[-1] != points_marqueurs[-1]:
                marqueurs.append(points_marqueurs[-1])

        rayon = 3 if len(points_marqueurs) <= 28 else 4
        for x, y in marqueurs:
            canvas.create_oval(x - rayon, y - rayon, x + rayon, y + rayon,
                               fill=couleurs["CARD"], outline=couleur_ligne, width=2)

        index_selection = repere_graphique.get("index")
        if isinstance(index_selection, int) and 0 <= index_selection < len(points_graphique_courants):
            _index, date_selection, valeur_selection, x_selection, y_selection = points_graphique_courants[index_selection]
            canvas.create_line(x_selection, y0, x_selection, y1, fill=couleurs["ORANGE"], width=2, dash=(4, 3))
            canvas.create_oval(x_selection - 7, y_selection - 7, x_selection + 7, y_selection + 7,
                               fill=couleurs["ORANGE"], outline=couleurs["CARD"], width=2)
            texte_repere = f"{date_selection.strftime('%H:%M')} · {formater_nombre(valeur_selection)} {config['unite']}"
            largeur_etiquette = max(130, len(texte_repere) * 7)
            x_texte = min(max(x_selection, x0 + largeur_etiquette / 2), x1 - largeur_etiquette / 2)
            y_texte = max(y0 + 18, y_selection - 24)
            canvas.create_rectangle(
                x_texte - largeur_etiquette / 2,
                y_texte - 13,
                x_texte + largeur_etiquette / 2,
                y_texte + 13,
                fill=couleurs["CARD"],
                outline=couleurs["ORANGE"]
            )
            canvas.create_text(x_texte, y_texte, text=texte_repere, fill=couleurs["TEXT"], font=("Segoe UI", 9, "bold"))

        dernier_x, dernier_y = points_marqueurs[-1]
        canvas.create_oval(dernier_x - 6, dernier_y - 6, dernier_x + 6, dernier_y + 6,
                           fill=couleur_ligne, outline=couleurs["CARD"], width=2)
        canvas.create_text(dernier_x, max(y0 + 14, dernier_y - 16),
                           text=f"{formater_nombre(points[-1][1])} {config['unite']}",
                           anchor="s", fill=couleurs["TEXT"],
                           font=("Segoe UI", 9, "bold"))

        if span:
            for graduation in graduations_temps(start, end):
                x_tick = x0 + (x1 - x0) * (graduation - start).total_seconds() / span
                canvas.create_line(x_tick, y1, x_tick, y1 + 5, fill=couleur_secondaire)
                canvas.create_line(x_tick, y0, x_tick, y1, fill=melanger_couleurs(couleur_grille, couleurs["CARD"], 0.35))
                canvas.create_text(
                    x_tick,
                    y1 + 20,
                    text=libelle_graduation(graduation, start, end),
                    anchor="center",
                    fill=couleur_secondaire,
                    font=("Segoe UI", 8)
                )
        canvas.create_text(x0, y1 + 38, text=start.strftime("%d/%m %H:%M"),
                           anchor="w", fill=couleur_secondaire,
                           font=("Segoe UI", 8))
        canvas.create_text(x1, y1 + 38, text=end.strftime("%d/%m %H:%M"),
                           anchor="e", fill=couleur_secondaire,
                           font=("Segoe UI", 8))
        canvas.tag_raise("event_labels")

    def ouvrir_comparaison_jours():
        try:
            toutes_mesures = database.get_mesures(plante_id=plante_id, limite=-1)
        except Exception:
            toutes_mesures = []
        try:
            tous_arrosages = database.get_arrosages_plante(plante_id, limite=200)
        except Exception:
            tous_arrosages = []
        jours = jours_disponibles_mesures(toutes_mesures)
        if len(jours) < 2:
            messagebox.showinfo(vh_t('compare_days_dialog'), vh_t('compare_days_minimum'), parent=fenetre)
            return
        libelles = [libelle_jour(jour) for jour in jours]
        jours_lookup = dict(zip(libelles, jours))
        detail = tk.Toplevel(fenetre)
        detail.title(vh_t('compare_days_window'))
        detail.configure(bg=couleurs["CARD"])
        detail.transient(fenetre)
        detail.geometry("820x520+90+90")
        tk.Label(detail, text=vh_t('compare_days_header'), bg=couleurs["CARD"], fg=couleurs["GREEN"], font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 4))
        choix = tk.Frame(detail, bg=couleurs["CARD"])
        choix.pack(fill="x", padx=18, pady=(6, 10))
        jour_a_var = tk.StringVar(value=libelles[0])
        jour_b_var = tk.StringVar(value=libelles[1])
        tk.Label(choix, text=vh_t('compare_day_a'), bg=couleurs["CARD"], fg=couleurs["TEXT"]).pack(side="left", padx=(0, 6))
        combo_a = ttk.Combobox(choix, textvariable=jour_a_var, values=libelles, state="readonly", width=12)
        combo_a.pack(side="left", padx=(0, 16))
        tk.Label(choix, text=vh_t('compare_day_b'), bg=couleurs["CARD"], fg=couleurs["TEXT"]).pack(side="left", padx=(0, 6))
        combo_b = ttk.Combobox(choix, textvariable=jour_b_var, values=libelles, state="readonly", width=12)
        combo_b.pack(side="left")

        colonnes_cmp = ("mesure", "jour_a", "jour_b", "ecart")
        tableau = ttk.Treeview(detail, columns=colonnes_cmp, show="headings", height=8)
        for colonne, titre, largeur in (("mesure", vh_t('compare_measurement'), 180), ("jour_a", vh_t('compare_day_a'), 150), ("jour_b", vh_t('compare_day_b'), 150), ("ecart", vh_t('compare_difference'), 150)):
            tableau.heading(colonne, text=titre)
            tableau.column(colonne, width=largeur, anchor="center")
        tableau.pack(fill="x", padx=18, pady=(0, 10))

        zone = tk.Text(detail, height=9, wrap="word", bg=couleurs["BG"], fg=couleurs["TEXT"], relief="flat", font=("Segoe UI", 9))
        zone.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        resultat_courant = {"texte": ""}

        def valeur_stat(stats, cle, unite):
            bloc = stats.get(cle)
            if not bloc:
                return "—", None
            return f"{formater_nombre(bloc['moyenne'])} {unite}", bloc['moyenne']

        def rafraichir_comparaison(_event=None):
            jour_a = jours_lookup.get(jour_a_var.get())
            jour_b = jours_lookup.get(jour_b_var.get())
            if not jour_a or not jour_b:
                return
            resultat = comparer_deux_jours(toutes_mesures, tous_arrosages, jour_a, jour_b)
            resultat_courant["texte"] = resultat["texte"]
            for item in tableau.get_children():
                tableau.delete(item)
            lignes = [
                (vh_t('compare_measurement_count'), str(resultat['stats_a']['mesures']), str(resultat['stats_b']['mesures']), str(resultat['stats_a']['mesures'] - resultat['stats_b']['mesures'])),
                (vh_t('compare_watering_count'), str(resultat['stats_a']['arrosages']), str(resultat['stats_b']['arrosages']), str(resultat['stats_a']['arrosages'] - resultat['stats_b']['arrosages'])),
            ]
            for titre, cle, unite in ((vh_t('compare_average_moisture'), "humidite", "%"), (vh_t('compare_average_temperature'), "temperature", "°C"), (vh_t('compare_average_light'), "lumiere", "lux"), (vh_t('compare_average_conductivity'), "conductivite", "µS/cm")):
                texte_a, valeur_a = valeur_stat(resultat['stats_a'], cle, unite)
                texte_b, valeur_b = valeur_stat(resultat['stats_b'], cle, unite)
                ecart = "—" if valeur_a is None or valeur_b is None else f"{formater_nombre(valeur_a - valeur_b)} {unite}"
                lignes.append((titre, texte_a, texte_b, ecart))
            for ligne in lignes:
                tableau.insert("", "end", values=ligne)
            zone.configure(state="normal")
            zone.delete("1.0", "end")
            zone.insert("1.0", resultat["texte"])
            zone.configure(state="disabled")

        combo_a.bind("<<ComboboxSelected>>", rafraichir_comparaison)
        combo_b.bind("<<ComboboxSelected>>", rafraichir_comparaison)
        boutons = tk.Frame(detail, bg=couleurs["CARD"])
        boutons.pack(fill="x", padx=18, pady=(0, 14))
        def copier_comparaison():
            detail.clipboard_clear()
            detail.clipboard_append(resultat_courant.get("texte") or "")
            bilan.set(vh_t("compare_copied_status").format(status=bilan.get()))
        ttk.Button(boutons, text=vh_t('compare_copy'), command=copier_comparaison).pack(side="left")
        ttk.Button(boutons, text=vh_t('compare_close'), command=detail.destroy).pack(side="right")
        rafraichir_comparaison()


    def ouvrir_cycles_arrosage():
        try:
            toutes_mesures = database.get_mesures(plante_id=plante_id, limite=-1)
        except Exception:
            toutes_mesures = []
        try:
            tous_arrosages = database.get_arrosages_plante(plante_id, limite=200)
        except Exception:
            tous_arrosages = []
        cycles = calculer_cycles_arrosage(toutes_mesures, tous_arrosages)
        texte = resumer_cycles_arrosage(toutes_mesures, tous_arrosages)
        if not cycles:
            messagebox.showinfo(vh_t('vue_historique_text_1400'), vh_t('vue_historique_text_1397'), parent=fenetre)
            return
        detail = tk.Toplevel(fenetre)
        detail.title(vh_t('vue_historique_text_1400'))
        detail.configure(bg=couleurs["CARD"])
        detail.transient(fenetre)
        detail.geometry("980x690+70+50")
        tk.Label(detail, text=vh_t('vue_historique_text_1404'), bg=couleurs["CARD"], fg=couleurs["WATER"], font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 4))
        tk.Label(detail, text=vh_t('vue_historique_text_1405'), bg=couleurs["CARD"], fg=couleurs["SECONDARY"], font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 6))
        analyse_cycles_var = tk.StringVar(value=analyser_cycles_arrosage(cycles))
        fond_analyse = melanger_couleurs(couleurs["BLUE"], couleurs["CARD"], 0.88)
        tk.Label(detail, textvariable=analyse_cycles_var, bg=fond_analyse, fg=couleurs["BLUE"], font=("Segoe UI", 9, "bold"), anchor="w", justify="left", wraplength=860, padx=10, pady=7).pack(fill="x", padx=18, pady=(0, 10))

        colonnes_cycles = ("date", "quantite", "mesures", "avant", "depart", "pic", "fin", "sechage", "vitesse24", "trou", "qualite", "suivi")
        tableau = ttk.Treeview(detail, columns=colonnes_cycles, show="headings", height=6)
        titres_cycles = {
            "date": vh_t('watering_title'),
            "quantite": vh_t('vue_historique_text_1414'),
            "mesures": vh_t('comparison_report_20'),
            "avant": vh_t('canonical_before'),
            "depart": vh_t('vue_historique_text_1417'),
            "pic": vh_t('canonical_peak'),
            "fin": vh_t('canonical_end'),
            "sechage": vh_t('vue_historique_text_1420'),
            "vitesse24": "24 h",
            "trou": vh_t('vue_historique_text_1437'),
            "qualite": vh_t('comparison_report_32'),
            "suivi": vh_t('canonical_tracking'),
        }
        largeurs_cycles = {
            "date": 135,
            "quantite": 80,
            "mesures": 75,
            "avant": 70,
            "depart": 70,
            "pic": 70,
            "fin": 70,
            "sechage": 95,
            "vitesse24": 75,
            "trou": 80,
            "qualite": 145,
            "suivi": 125,
        }
        for colonne in colonnes_cycles:
            tableau.heading(colonne, text=titres_cycles[colonne])
            tableau.column(colonne, width=largeurs_cycles[colonne], anchor="center")
        tableau.pack(fill="x", padx=18, pady=(0, 10))

        cycles_affiches = list(reversed(cycles))
        for cycle in cycles_affiches:
            arrosage = cycle.get("arrosage")
            quantite = quantite_arrosage_courte(arrosage)
            suivi = f"→ {formater_date_courte(cycle.get('fin'))}" if cycle.get("fin") else vh_t('vue_historique_text_1464')
            tableau.insert("", "end", values=(
                formater_date_courte(cycle.get("date")),
                quantite,
                len(cycle.get("mesures") or []),
                formater_nombre(cycle.get("humidite_avant")) if cycle.get("humidite_avant") is not None else "—",
                formater_nombre(cycle.get("premiere_humidite")) if cycle.get("premiere_humidite") is not None else "—",
                formater_nombre(cycle.get("pic_humidite")) if cycle.get("pic_humidite") is not None else "—",
                formater_nombre(cycle.get("derniere_humidite")) if cycle.get("derniere_humidite") is not None else "—",
                f"{formater_nombre(cycle.get('sechage'))} pt/j" if cycle.get("sechage") is not None else "—",
                f"{formater_nombre(cycle.get('vitesse_24h'))} pt/j" if cycle.get("vitesse_24h") is not None else "—",
                f"{formater_nombre(cycle.get('plus_grand_trou_h'))} h" if cycle.get("plus_grand_trou_h") is not None else "—",
                cycle.get("qualite") or "—",
                suivi,
            ))

        comparaison_frame = tk.Frame(detail, bg=couleurs["CARD"])
        comparaison_frame.pack(fill="x", padx=18, pady=(0, 8))
        tk.Label(comparaison_frame, text=vh_t('vue_historique_text_1462'), bg=couleurs["CARD"], fg=couleurs["TEXT"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        choix_cycles = tk.Frame(comparaison_frame, bg=couleurs["CARD"])
        choix_cycles.pack(fill="x", pady=(6, 6))
        libelles_cycles = [libelle_cycle(cycle) for cycle in cycles_affiches]
        cycles_lookup = dict(zip(libelles_cycles, cycles_affiches))
        cycle_a_var = tk.StringVar(value=libelles_cycles[0] if libelles_cycles else "")
        cycle_b_var = tk.StringVar(value=libelles_cycles[1] if len(libelles_cycles) > 1 else (libelles_cycles[0] if libelles_cycles else ""))
        tk.Label(choix_cycles, text=vh_t('vue_historique_text_1469'), bg=couleurs["CARD"], fg=couleurs["TEXT"]).pack(side="left", padx=(0, 6))
        combo_cycle_a = ttk.Combobox(choix_cycles, textvariable=cycle_a_var, values=libelles_cycles, state="readonly", width=28)
        combo_cycle_a.pack(side="left", padx=(0, 12))
        tk.Label(choix_cycles, text=vh_t('vue_historique_text_1472'), bg=couleurs["CARD"], fg=couleurs["TEXT"]).pack(side="left", padx=(0, 6))
        combo_cycle_b = ttk.Combobox(choix_cycles, textvariable=cycle_b_var, values=libelles_cycles, state="readonly", width=28)
        combo_cycle_b.pack(side="left", padx=(0, 12))
        serie_cycle_var = SerieLocaleVar(value="Humidité")
        tk.Label(choix_cycles, text=vh_t('vue_historique_text_1476'), bg=couleurs["CARD"], fg=couleurs["TEXT"]).pack(side="left", padx=(0, 6))
        combo_serie_cycle = ttk.Combobox(choix_cycles, textvariable=serie_cycle_var, values=tuple(nom_serie_affiche(nom) for nom in SERIES), state="readonly", width=13)
        combo_serie_cycle.pack(side="left")

        colonnes_cmp_cycles = ("indicateur", "cycle_a", "cycle_b", "ecart")
        tableau_cmp = ttk.Treeview(comparaison_frame, columns=colonnes_cmp_cycles, show="headings", height=8)
        for colonne, titre, largeur in (("indicateur", vh_t('canonical_indicator'), 155), ("cycle_a", vh_t('vue_historique_text_1469'), 130), ("cycle_b", vh_t('vue_historique_text_1472'), 130), ("ecart", vh_t('compare_difference'), 130)):
            tableau_cmp.heading(colonne, text=titre)
            tableau_cmp.column(colonne, width=largeur, anchor="center")
        tableau_cmp.pack(fill="x")

        graphique_cycles = tk.Canvas(comparaison_frame, height=250, bg=couleurs["BG"], highlightbackground=couleurs["BORDER"], highlightthickness=1)
        graphique_cycles.pack(fill="x", pady=(8, 0))

        def dessiner_comparaison_cycles(cycle_a, cycle_b):
            graphique_cycles.delete("all")
            largeur = max(graphique_cycles.winfo_width(), 520)
            hauteur = max(graphique_cycles.winfo_height(), 230)
            x0, x1, y0, y1 = 64, largeur - 34, 54, hauteur - 46
            nom_serie = serie_cycle_var.get() or "Humidité"
            config_serie = SERIES.get(nom_serie, SERIES["Humidité"])
            points_a = points_cycle(cycle_a, nom_serie)
            points_b = points_cycle(cycle_b, nom_serie)
            tous_points = points_a + points_b
            if not tous_points:
                graphique_cycles.create_text(largeur / 2, hauteur / 2, text=vh_t('vue_historique_text_1506').format(v0=nom_serie.lower()), fill=couleurs["SECONDARY"], font=("Segoe UI", 10))
                return
            reperes_a = reperes_visuels_cycle(cycle_a)
            reperes_b = reperes_visuels_cycle(cycle_b)
            max_repere = max((repere["heures"] for repere in reperes_a + reperes_b if repere["cle"] in {"24h", "48h"}), default=0)
            max_heures = max(1, max(point[0] for point in tous_points), min(48, max_repere))
            if max(point[0] for point in tous_points) >= 24:
                max_heures = max(max_heures, 24)
            if max(point[0] for point in tous_points) >= 48:
                max_heures = max(max_heures, 48)
            valeurs = [point[1] for point in tous_points]
            marge = max(1, (max(valeurs) - min(valeurs)) * 0.10)
            bas = min(valeurs) - marge
            haut = max(valeurs) + marge
            if "minimum" in config_serie:
                bas = min(bas, config_serie["minimum"])
            if "maximum" in config_serie:
                haut = max(haut, config_serie["maximum"])
            if bas == haut:
                bas -= 1
                haut += 1

            def x_depuis_heures(heures):
                return x0 + (x1 - x0) * heures / max_heures

            def y_depuis_valeur(valeur):
                return y1 - (y1 - y0) * (valeur - bas) / (haut - bas)

            graphique_cycles.create_text(x0, 17, text=vh_t('vue_historique_text_1534').format(v0=_texte(config_serie['titre']), v1=config_serie['unite']), anchor="w", fill=couleurs["TEXT"], font=("Segoe UI", 10, "bold"))
            graphique_cycles.create_rectangle(x0, y0, x1, y1, outline=couleurs["BORDER"])

            legendes = [
                (couleurs["GREEN"], vh_t('vue_historique_text_1469')),
                (couleurs["BLUE"], vh_t('vue_historique_text_1472')),
                (couleurs["WATER"], vh_t('watering_title')),
                (couleurs["ORANGE"], vh_t('canonical_peak')),
                (couleurs["PURPLE"], "24 h / 48 h"),
            ]
            x_legende = x0
            for couleur, libelle in legendes:
                graphique_cycles.create_oval(x_legende, 34, x_legende + 9, 43, fill=couleur, outline=couleur)
                graphique_cycles.create_text(x_legende + 14, 38, text=libelle, anchor="w", fill=couleurs["SECONDARY"], font=("Segoe UI", 8, "bold"))
                x_legende += max(76, len(libelle) * 7 + 24)

            couleur_grille = melanger_couleurs(couleurs["GRID"], couleurs["CARD"], 0.25)
            for i in range(4):
                valeur = bas + (haut - bas) * i / 3
                y = y_depuis_valeur(valeur)
                graphique_cycles.create_line(x0, y, x1, y, fill=couleur_grille)
                graphique_cycles.create_text(x0 - 8, y, text=formater_nombre(valeur), anchor="e", fill=couleurs["SECONDARY"], font=("Segoe UI", 8))
            graduations = [0]
            if max_heures > 24:
                graduations.append(24)
            if max_heures > 48:
                graduations.append(48)
            graduations.extend([max_heures / 2, max_heures])
            for heures in sorted({round(item, 2) for item in graduations if 0 <= item <= max_heures}):
                x = x_depuis_heures(heures)
                graphique_cycles.create_line(x, y1, x, y1 + 4, fill=couleurs["SECONDARY"])
                graphique_cycles.create_text(x, y1 + 16, text=f"{formater_nombre(heures)} h", fill=couleurs["SECONDARY"], font=("Segoe UI", 8))

            def dessiner_repere(repere):
                heures = repere["heures"]
                if heures > max_heures:
                    return
                couleur = couleurs.get(repere["couleur"], couleurs["SECONDARY"])
                x = x_depuis_heures(heures)
                dash = (4, 4) if repere.get("style") == "pointille" else None
                graphique_cycles.create_line(x, y0, x, y1, fill=couleur, dash=dash, width=2 if repere["cle"] in {"arrosage", "pic"} else 1)
                texte_y = y0 + 13 if repere["cle"] in {"arrosage", "24h"} else y0 + 29
                graphique_cycles.create_text(x + 5, texte_y, text=repere["libelle"], anchor="w", fill=couleur, font=("Segoe UI", 8, "bold"))

            for repere in reperes_a:
                if repere["cle"] != "pic":
                    dessiner_repere(repere)
            for cycle, suffixe in ((cycle_a, "A"), (cycle_b, "B")):
                pic_heures = heures_depuis_debut_cycle(cycle, cycle.get("pic_date"))
                if pic_heures is not None:
                    dessiner_repere({
                        "cle": "pic",
                        "heures": pic_heures,
                        "libelle": vh_t('vue_historique_text_1603').format(v0=suffixe),
                        "couleur": "ORANGE",
                        "style": "plein",
                    })

            def dessiner_ligne(points, couleur, etiquette, cycle):
                if not points:
                    return
                coords = []
                for heures, valeur in points:
                    x = x_depuis_heures(heures)
                    y = y_depuis_valeur(valeur)
                    coords.extend((x, y))
                if len(coords) >= 4:
                    graphique_cycles.create_line(*coords, fill=couleur, width=3, smooth=True)
                for heures, valeur in points:
                    x = x_depuis_heures(heures)
                    y = y_depuis_valeur(valeur)
                    rayon = 2
                    graphique_cycles.create_oval(x - rayon, y - rayon, x + rayon, y + rayon, fill=couleur, outline="")
                pic_heures = heures_depuis_debut_cycle(cycle, cycle.get("pic_date"))
                if pic_heures is not None and pic_heures <= max_heures:
                    pic_valeur = valeur_cycle(cycle, "pic_humidite")
                    if pic_valeur is not None:
                        x_pic = x_depuis_heures(pic_heures)
                        y_pic = y_depuis_valeur(pic_valeur)
                        graphique_cycles.create_oval(x_pic - 6, y_pic - 6, x_pic + 6, y_pic + 6, fill=couleurs["ORANGE"], outline=couleurs["CARD"], width=2)
                x_fin, y_fin = coords[-2], coords[-1]
                graphique_cycles.create_oval(x_fin - 5, y_fin - 5, x_fin + 5, y_fin + 5, fill=couleur, outline=couleurs["CARD"], width=1)
                graphique_cycles.create_text(x_fin + 7, y_fin, text=etiquette, anchor="w", fill=couleur, font=("Segoe UI", 8, "bold"))

            dessiner_ligne(points_a, couleurs["GREEN"], "A", cycle_a)
            dessiner_ligne(points_b, couleurs["BLUE"], "B", cycle_b)

        zone = tk.Text(detail, height=6, wrap="word", bg=couleurs["BG"], fg=couleurs["TEXT"], relief="flat", font=("Segoe UI", 9))
        zone.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        zone.insert("1.0", texte)
        zone.configure(state="disabled")
        comparaison_texte = {"texte": ""}

        def rafraichir_comparaison_cycles(_event=None):
            cycle_a = cycles_lookup.get(cycle_a_var.get())
            cycle_b = cycles_lookup.get(cycle_b_var.get())
            for item in tableau_cmp.get_children():
                tableau_cmp.delete(item)
            if not cycle_a or not cycle_b:
                comparaison_texte["texte"] = ""
                return
            resultat = comparer_deux_cycles(cycle_a, cycle_b)
            comparaison_texte["texte"] = resultat["texte"]
            dessiner_comparaison_cycles(cycle_a, cycle_b)
            for ligne in resultat["lignes_tableau"]:
                tableau_cmp.insert("", "end", values=ligne)
            zone.configure(state="normal")
            zone.delete("1.0", "end")
            zone.insert("1.0", texte + "\n\n" + resultat["texte"])
            zone.configure(state="disabled")

        combo_cycle_a.bind("<<ComboboxSelected>>", rafraichir_comparaison_cycles)
        combo_cycle_b.bind("<<ComboboxSelected>>", rafraichir_comparaison_cycles)
        combo_serie_cycle.bind("<<ComboboxSelected>>", rafraichir_comparaison_cycles)
        graphique_cycles.bind("<Configure>", lambda _event: rafraichir_comparaison_cycles())
        rafraichir_comparaison_cycles()

        boutons = tk.Frame(detail, bg=couleurs["CARD"])
        boutons.pack(fill="x", padx=18, pady=(0, 14))
        def copier_cycles():
            detail.clipboard_clear()
            detail.clipboard_append((texte + "\n\n" + comparaison_texte.get("texte", "")).strip())
            bilan.set(vh_t('vue_historique_text_1656').format(v0=bilan.get()))
        ttk.Button(boutons, text=vh_t('compare_copy'), command=copier_cycles).pack(side="left")
        ttk.Button(boutons, text=vh_t('compare_close'), command=detail.destroy).pack(side="right")


    def copier_journee():
        nom_plante = plante[1] if plante else vh_t('plant')
        texte_jour = bilan_jour_courant.get("texte") or ""
        if periode.get() != vh_t("period_day") or not texte_jour:
            bilan.set(vh_t('vue_historique_text_1665').format(v0=bilan.get()))
            return
        texte_expositions = bilan_jour_courant.get("expositions") or ""
        lignes = [
            vh_t('vue_historique_text_1685').format(v0=nom_plante),
            "",
            texte_jour,
        ]
        if texte_expositions:
            lignes.extend(["", texte_expositions])
        lignes.extend([
            "",
            qualite_var.get(),
        ])
        fenetre.clipboard_clear()
        fenetre.clipboard_append("\n".join(lignes).strip())
        bilan.set(vh_t('vue_historique_text_1681').format(v0=bilan.get()))


    def copier_resume_historique():
        nom_plante = plante[1] if plante else vh_t('plant')
        lignes = [
            vh_t('vue_historique_text_1703').format(v0=nom_plante),
            vh_t('vue_historique_text_1688').format(v0=periode.get()),
            vh_t('vue_historique_text_1689').format(v0=nom_serie_affiche(serie.get())),
            "",
            vh_t('vue_historique_text_1691'),
            vh_t('vue_historique_text_1692').format(v0=resume_vars['dernier'].get()),
            vh_t('vue_historique_text_1709').format(v0=resume_vars['moyenne'].get()),
            vh_t('vue_historique_text_1710_more').format(v0=resume_vars['minimum'].get()),
            vh_t('vue_historique_text_1711').format(v0=resume_vars['maximum'].get()),
            vh_t('vue_historique_text_1712_more').format(v0=resume_vars['tendance'].get()),
            "",
            jour_resume_var.get(),
            qualite_var.get(),
            lecture_var.get(),
            vh_t('vue_historique_text_1717').format(v0=bilan.get()),
        ]

        selection = table.selection()
        if selection:
            valeurs = table.item(selection[0], "values")
            if valeurs:
                lignes.extend([
                    "",
                    vh_t('vue_historique_text_1710'),
                    vh_t('vue_historique_text_1727').format(v0=valeurs[0]),
                    vh_t('vue_historique_text_1712').format(v0=valeurs[1]),
                    vh_t('interface_text_5921').format(v0=valeurs[2]),
                    vh_t('vue_historique_text_1714').format(v0=valeurs[3]),
                    vh_t('vue_historique_text_1715').format(v0=valeurs[4]),
                ])

        fenetre.clipboard_clear()
        fenetre.clipboard_append("\n".join(lignes).strip())
        bilan.set(vh_t('vue_historique_text_1720').format(v0=bilan.get()))


    def actualiser(event=None):
        nonlocal points, mesures_courantes, arrosages_courants, expositions_courantes, jours_par_libelle

        try:
            mesures = database.get_mesures(plante_id=plante_id, limite=-1)
        except Exception:
            bilan.set(vh_t('vue_historique_text_1729'))
            return

        try:
            arrosages = database.get_arrosages_plante(plante_id, limite=200)
        except Exception:
            arrosages = []

        try:
            evenements = database.get_journal_plante(plante_id, limite=500)
        except Exception:
            evenements = []
        expositions = construire_expositions_balcon(evenements)

        jours_disponibles = jours_disponibles_mesures(mesures)
        jours_par_libelle = {libelle_jour(jour): jour for jour in jours_disponibles}
        libelles_jours = tuple(jours_par_libelle.keys())
        choix_jour.configure(values=libelles_jours)

        if periode.get() == vh_t("period_day"):
            if libelles_jours and jour_selectionne.get() not in jours_par_libelle:
                jour_selectionne.set(libelles_jours[0])
            if not jour_resume_label.winfo_ismapped():
                jour_resume_label.pack(fill="x", padx=24, pady=(0, 8), ipady=8, before=qualite_label)
            choix_jour.configure(state="readonly" if libelles_jours else "disabled")
            jour = jours_par_libelle.get(jour_selectionne.get())
            if jour:
                mesures = filtrer_mesures_jour(mesures, jour)
                arrosages = filtrer_arrosages_jour(arrosages, jour)
                expositions = filtrer_expositions_jour(expositions, jour)
                texte_jour = resume_moyennes_jour(mesures, jour, arrosages)
                texte_exposition_jour = resume_expositions_jour(mesures, expositions)
                jour_resume_var.set(texte_jour)
                bilan_jour_courant["texte"] = texte_jour
                bilan_jour_courant["expositions"] = texte_exposition_jour
                bilan_jour_courant["jour"] = libelle_jour(jour)
                jour_resume_label.configure(fg=couleurs["TEXT"])
            else:
                mesures = []
                arrosages = []
                expositions = []
                jour_resume_var.set(vh_t('vue_historique_text_1770'))
                bilan_jour_courant["texte"] = ""
                bilan_jour_courant["expositions"] = ""
                bilan_jour_courant["jour"] = ""
                jour_resume_label.configure(fg=couleurs["SECONDARY"])
        else:
            choix_jour.configure(state="readonly" if libelles_jours else "disabled")
            bilan_jour_courant["texte"] = ""
            bilan_jour_courant["jour"] = ""
            jour_resume_label.pack_forget()

        jours = {vh_t("period_24h"): 1, vh_t("period_7d"): 7}.get(periode.get())

        if jours:
            maintenant = maintenant_local().replace(tzinfo=None)
            limite = maintenant - timedelta(days=jours)
            filtre = []
            for mesure in mesures:
                date = date_locale_depuis_iso(mesure[1])
                if date and limite <= date <= maintenant:
                    filtre.append(mesure)
            mesures = filtre

            arrosages_filtres = []
            for arrosage in arrosages:
                date = date_locale_depuis_iso(arrosage[2])
                if date and limite <= date <= maintenant:
                    arrosages_filtres.append(arrosage)
            arrosages = arrosages_filtres
            expositions = filtrer_expositions_periode(expositions, limite, maintenant)

        arrosages_courants = list(arrosages)
        expositions_courantes = list(expositions)

        mesures_courantes = list(mesures)
        if tri_table["colonne"]:
            afficher_mesures_table(
                sorted(
                    mesures_courantes,
                    key=lambda mesure: valeur_tri_mesure(mesure, tri_table["colonne"]),
                    reverse=True
                ),
                tri_table["colonne"]
            )
        else:
            afficher_mesures_table(mesures_courantes)

        mesures_stats, mesures_suspectes_ids = filtrer_mesures_pour_serie(mesures, serie.get())
        points = extraire_points(mesures_stats, serie.get())
        if repere_graphique.get("index") is not None and repere_graphique["index"] >= len(points):
            repere_graphique["index"] = None
        config = SERIES[serie.get()]

        analyse = analyser_points(points, serie.get())
        if points:
            valeurs = [valeur for _, valeur in points]
            resume_vars["dernier"].set(f"{formater_nombre(points[-1][1])} {config['unite']}")
            resume_vars["moyenne"].set(f"{formater_nombre(sum(valeurs) / len(valeurs))} {config['unite']}")
            resume_vars["minimum"].set(f"{formater_nombre(min(valeurs))} {config['unite']}")
            resume_vars["maximum"].set(f"{formater_nombre(max(valeurs))} {config['unite']}")
            resume_vars["tendance"].set(analyse["tendance"])
        else:
            for variable in resume_vars.values():
                variable.set("—")

        qualite_texte, qualite_couleur = analyser_qualite_donnees(mesures, periode.get())
        if mesures_suspectes_ids:
            qualite_texte += (
                vh_t('vue_historique_text_1838').format(v0=len(mesures_suspectes_ids))
            )
            qualite_couleur = "ORANGE"
        qualite_var.set(qualite_texte)
        qualite_label.configure(fg=couleurs.get(qualite_couleur, couleurs["SECONDARY"]))

        lecture_var.set(analyse["lecture"])
        lecture_label.configure(fg=couleurs.get(analyse["couleur"], couleurs["TEXT"]))
        suffixe_arrosage = vh_t('vue_historique_text_1847').format(v0=len(arrosages_courants)) if arrosages_courants else ""
        suffixe_exposition = vh_t('vue_historique_text_1863').format(v0=len(expositions_courantes)) if expositions_courantes else ""
        if periode.get() == vh_t("period_day"):
            if outils_post_arrosage.winfo_ismapped():
                outils_post_arrosage.pack_forget()
        else:
            if not outils_post_arrosage.winfo_ismapped():
                outils_post_arrosage.pack(fill="x", padx=24, pady=(0, 8), before=cadre)

        if tri_table["colonne"]:
            bilan.set(vh_t('vue_historique_text_1857').format(v0=len(mesures), v1=suffixe_arrosage, v2=suffixe_exposition, v3=libelle_tri(tri_table['colonne'])))
        else:
            bilan.set(vh_t('vue_historique_text_1859').format(v0=len(mesures), v1=suffixe_arrosage, v2=suffixe_exposition))
        dessiner()

    for texte, repere in (
            (vh_t("history_marker_max"), "max"),
            (vh_t("history_marker_min"), "min"),
            (vh_t("history_marker_average"), "moyenne"),
            (vh_t("history_marker_latest"), "derniere")):
        ttk.Button(
            outils_table,
            text=texte,
            command=lambda r=repere: selectionner_repere(r)
        ).pack(side="left", padx=(0, 6))

    try:
        reperes_analyse = database.get_reperes_analyse_actifs()
    except Exception:
        reperes_analyse = []

    for repere in reperes_analyse:
        if repere[3] != "apres_arrosage":
            continue
        ttk.Button(
            outils_post_arrosage,
            text=repere[2],
            command=lambda r=repere: selectionner_apres_arrosage(r)
        ).pack(side="left", padx=(0, 6))

    ttk.Button(barre, text=vh_t("normal_order"), command=remettre_ordre_normal).pack(side="right", padx=(8, 0))
    ttk.Button(barre, text=vh_t("copy_summary"), command=copier_resume_historique).pack(side="right", padx=(8, 0))
    ttk.Button(barre, text=vh_t("compare_days"), command=ouvrir_comparaison_jours).pack(side="right", padx=(8, 0))
    ttk.Button(barre, text=vh_t("cycles"), command=ouvrir_cycles_arrosage).pack(side="right", padx=(8, 0))
    ttk.Button(barre, text=vh_t("copy_day"), command=copier_journee).pack(side="right", padx=(8, 0))
    ttk.Button(barre, text=vh_t("refresh_plain"), command=actualiser).pack(side="right")
    def selectionner_periode(_event=None):
        if periode.get() == vh_t("period_day"):
            serie.set("Lumière")
            if not jour_selectionne.get():
                try:
                    mesures = database.get_mesures(plante_id=plante_id, limite=-1)
                    jours = jours_disponibles_mesures(mesures)
                    if jours:
                        jour_selectionne.set(libelle_jour(jours[0]))
                except Exception:
                    pass
        actualiser()

    def selectionner_jour(_event=None):
        if jour_selectionne.get():
            periode.set(vh_t("period_day"))
            serie.set("Lumière")
        actualiser()

    choix_periode.bind("<<ComboboxSelected>>", selectionner_periode)
    choix_jour.bind("<<ComboboxSelected>>", selectionner_jour)
    choix_serie.bind("<<ComboboxSelected>>", actualiser)
    canvas.bind("<Configure>", dessiner)
    canvas.bind("<Button-1>", lambda event: selectionner_point_graphique_depuis_x(event.x))
    canvas.bind("<B1-Motion>", lambda event: selectionner_point_graphique_depuis_x(event.x))
    actualiser()

    return fenetre
