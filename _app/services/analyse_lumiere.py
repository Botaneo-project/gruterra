"""Analyse des expositions lumineuses et des sorties balcon."""
from __future__ import annotations

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
        return "Exposition balcon : aucune notée ce jour."

    lignes = ["Exposition balcon :"]
    for sortie, retour in expositions:
        if retour:
            duree = (retour - sortie).total_seconds() / 3600
            lignes.append(f"- {sortie.strftime('%H:%M')} → {retour.strftime('%H:%M')} · durée {formater_nombre(duree)} h.")
        else:
            lignes.append(f"- {sortie.strftime('%H:%M')} → retour non noté.")

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
        lignes.append(f"- Lumière globale : moyenne {formater_nombre(sum(valeurs_globales) / len(valeurs_globales))} lux, max {formater_nombre(max(valeurs_globales))} lux.")
    if valeurs_interieur:
        lignes.append(f"- Hors balcon : moyenne {formater_nombre(sum(valeurs_interieur) / len(valeurs_interieur))} lux, max {formater_nombre(max(valeurs_interieur))} lux.")
    if valeurs_balcon:
        lignes.append(f"- Pendant balcon : {len(valeurs_balcon)} mesure(s), max {formater_nombre(max(valeurs_balcon))} lux.")
    if valeurs_interieur and valeurs_balcon:
        lignes.append("- Lecture : les pics lumineux de cette journée sont expliqués par l'exposition balcon ; interpréter séparément l'emplacement intérieur.")
    return "\n".join(lignes)
