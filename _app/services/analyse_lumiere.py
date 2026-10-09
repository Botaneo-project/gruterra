"""Analyse des expositions lumineuses et des sorties balcon."""
from __future__ import annotations

from i18n import traduire_courant as _tr, traduire_texte_courant as _texte

import math
from datetime import datetime, timedelta

from botaneo_dates import vers_local_naif


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


PLAGES_LUMIERE = (
    (0, 250, "très faible"),
    (250, 1000, "faible"),
    (1000, 10000, "correcte"),
    (10000, None, "forte"),
)


def extraire_points_lumiere(mesures):
    points = []
    for mesure in mesures or []:
        date = vers_local_naif(mesure[1] if len(mesure) > 1 else None)
        if not date or len(mesure) <= 4 or mesure[4] is None:
            continue
        try:
            lux = float(mesure[4])
        except (TypeError, ValueError):
            continue
        if math.isfinite(lux) and lux >= 0:
            points.append((date, lux))
    return sorted(points, key=lambda point: point[0])


def nom_plage_lumiere(lux):
    for minimum, maximum, nom in PLAGES_LUMIERE:
        if lux >= minimum and (maximum is None or lux < maximum):
            return nom
    return "inconnue"


def calculer_exposition_lumineuse(mesures):
    """Calcule des repères lumière entre mesures successives.

    Le cumul en lux·h reste une approximation : chaque intervalle conserve la
    valeur de la mesure précédente. C'est volontairement simple et lisible pour
    l'analyse plante.
    """

    points = extraire_points_lumiere(mesures)
    durees = {nom: 0.0 for _, _, nom in PLAGES_LUMIERE}
    cumul_lux_heures = 0.0
    duree_totale = 0.0

    for (date, lux), (date_suivante, _lux_suivant) in zip(points, points[1:]):
        heures = (date_suivante - date).total_seconds() / 3600
        if heures <= 0 or heures > 6:
            continue
        duree_totale += heures
        cumul_lux_heures += lux * heures
        durees[nom_plage_lumiere(lux)] += heures

    return {
        "points": len(points),
        "duree_totale_h": duree_totale,
        "cumul_lux_h": cumul_lux_heures,
        "durees_par_plage_h": durees,
    }


def resume_exposition_lumineuse(mesures):
    stats = calculer_exposition_lumineuse(mesures)
    if stats["points"] < 2 or stats["duree_totale_h"] <= 0:
        return _tr('analyse_lumiere_text_84')

    plages = []
    for _minimum, _maximum, nom in PLAGES_LUMIERE:
        duree = stats["durees_par_plage_h"].get(nom, 0)
        if duree > 0:
            plages.append(f"{_texte(nom)} {formater_nombre(duree)} h")
    return (
        _tr('analyse_lumiere_text_92').format(v0=formater_nombre(stats['cumul_lux_h']), v1=formater_nombre(stats['duree_totale_h']))
        + (" · " + " ; ".join(plages) if plages else "")
        + "."
    )


def construire_expositions_balcon(evenements):
    """Retourne les périodes Sortie balcon -> Retour intérieur du journal plante."""

    points = []
    for evenement in evenements or []:
        date = vers_local_naif(evenement[2] if len(evenement) > 2 else None)
        titre = (evenement[4] if len(evenement) > 4 and evenement[4] else "").strip().lower()
        type_evenement = (evenement[3] if len(evenement) > 3 and evenement[3] else "").strip().lower()
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


def filtrer_expositions_periode(expositions, debut, fin):
    resultat = []
    for sortie, retour in expositions or []:
        retour_effectif = retour or fin
        if retour_effectif >= debut and sortie <= fin:
            resultat.append((sortie, retour))
    return resultat


def filtrer_expositions_jour(expositions, jour):
    debut = datetime.combine(jour, datetime.min.time())
    fin = debut + timedelta(days=1)
    return filtrer_expositions_periode(expositions, debut, fin)


def mesure_dans_exposition(date, expositions):
    for sortie, retour in expositions or []:
        fin = retour or datetime.combine(date.date(), datetime.max.time())
        if sortie <= date <= fin:
            return True
    return False


def resume_expositions_jour(mesures, expositions):
    if not expositions:
        return _tr('analyse_lumiere_text_154')

    lignes = [_tr("light_balcony_header")]
    for sortie, retour in expositions:
        if retour:
            duree = (retour - sortie).total_seconds() / 3600
            lignes.append(_tr('analyse_lumiere_text_160').format(v0=sortie.strftime('%H:%M'), v1=retour.strftime('%H:%M'), v2=formater_nombre(duree)))
        else:
            lignes.append(_tr('analyse_lumiere_text_162').format(v0=sortie.strftime('%H:%M')))

    valeurs_globales = []
    valeurs_interieur = []
    valeurs_balcon = []
    for mesure in mesures or []:
        date = vers_local_naif(mesure[1])
        if not date or mesure[4] is None:
            continue
        try:
            lux = float(mesure[4])
        except (TypeError, ValueError):
            continue
        valeurs_globales.append(lux)
        if mesure_dans_exposition(date, expositions):
            valeurs_balcon.append(lux)
        else:
            valeurs_interieur.append(lux)

    if valeurs_globales:
        lignes.append(_tr('analyse_lumiere_text_182').format(v0=formater_nombre(sum(valeurs_globales) / len(valeurs_globales)), v1=formater_nombre(max(valeurs_globales))))
        lignes.append(f"- {resume_exposition_lumineuse(mesures)}")
    if valeurs_interieur:
        lignes.append(_tr('analyse_lumiere_text_186').format(v0=formater_nombre(sum(valeurs_interieur) / len(valeurs_interieur)), v1=formater_nombre(max(valeurs_interieur))))
    if valeurs_balcon:
        lignes.append(_tr('analyse_lumiere_text_187').format(v0=len(valeurs_balcon), v1=formater_nombre(max(valeurs_balcon))))
    if valeurs_interieur and valeurs_balcon:
        lignes.append(_tr('analyse_lumiere_text_189'))
    return "\n".join(lignes)
