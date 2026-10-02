"""Analyse des arrosages et des cycles d'humidité.

Ce module contient la logique pure utilisée par l'historique graphique.
Il ne dépend pas de Tkinter et peut être testé sans interface.
"""

import math

import database
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


def formater_date_courte(date):
    if not date:
        return "date inconnue"
    return date.strftime("%d/%m/%Y %H:%M")


def date_debut_arrosage(arrosage):
    if isinstance(arrosage, dict):
        return arrosage.get("date_debut")
    return vers_local_naif(arrosage[2])


def quantite_arrosage_texte(arrosage):
    if isinstance(arrosage, dict):
        total = arrosage.get("quantite_totale_ml")
        total_txt = f"{formater_nombre(total)} ml" if total is not None else "quantité non notée"
        apports = arrosage.get("apports") or []
        if len(apports) > 1:
            details = []
            for apport in apports:
                date = vers_local_naif(apport[2])
                heure = date.strftime("%H:%M") if date else "heure inconnue"
                quantite = f"{formater_nombre(apport[3])} ml" if apport[3] is not None else "quantité non notée"
                details.append(f"{quantite} à {heure}")
            return f"session {total_txt} ({' + '.join(details)})"
        return total_txt
    return f"{formater_nombre(arrosage[3])} ml" if arrosage and arrosage[3] is not None else "quantité non notée"


def quantite_arrosage_courte(arrosage):
    if isinstance(arrosage, dict):
        total = arrosage.get("quantite_totale_ml")
        total_txt = f"{formater_nombre(total)} ml" if total is not None else "—"
        if arrosage.get("fractionnee"):
            return f"session {total_txt}"
        return total_txt
    return f"{formater_nombre(arrosage[3])} ml" if arrosage and arrosage[3] is not None else "—"


def mesurer_cycle_arrosage(arrosage, prochain_arrosage, mesures):
    date_arrosage = date_debut_arrosage(arrosage)
    if not date_arrosage:
        return None
    date_fin = date_debut_arrosage(prochain_arrosage) if prochain_arrosage else None
    mesures_cycle = []
    humidites_avant = []
    for mesure in mesures:
        date_mesure = vers_local_naif(mesure[1])
        if not date_mesure:
            continue
        try:
            humidite = float(mesure[3]) if mesure[3] is not None else None
        except (TypeError, ValueError):
            humidite = None
        if date_mesure < date_arrosage:
            if humidite is not None and math.isfinite(humidite):
                humidites_avant.append((date_mesure, humidite))
            continue
        if date_fin and date_mesure >= date_fin:
            continue
        mesures_cycle.append(mesure)
    mesures_cycle.sort(key=lambda mesure: mesure[1] or "")
    humidites_avant.sort(key=lambda item: item[0])
    avant_date, avant_humidite = humidites_avant[-1] if humidites_avant else (None, None)
    delai_avant_h = (date_arrosage - avant_date).total_seconds() / 3600 if avant_date else None
    if not mesures_cycle:
        return {
            "date": date_arrosage,
            "fin": date_fin,
            "arrosage": arrosage,
            "mesures": [],
            "humidite_avant": avant_humidite,
            "delai_avant_h": delai_avant_h,
            "qualite": "aucune mesure après",
            "texte": f"{formater_date_courte(date_arrosage)} · aucune mesure après arrosage",
        }

    humidites = [(vers_local_naif(m[1]), float(m[3])) for m in mesures_cycle if m[3] is not None]
    humidites = [(date, valeur) for date, valeur in humidites if date is not None and math.isfinite(valeur)]
    if not humidites:
        return {
            "date": date_arrosage,
            "fin": date_fin,
            "arrosage": arrosage,
            "mesures": mesures_cycle,
            "humidite_avant": avant_humidite,
            "delai_avant_h": delai_avant_h,
            "qualite": "humidité inexploitable",
            "texte": f"{formater_date_courte(date_arrosage)} · {len(mesures_cycle)} mesure(s), humidité inexploitable",
        }

    premiere_date, premiere_humidite = humidites[0]
    pic_date, pic_humidite = max(humidites, key=lambda item: item[1])
    derniere_date, derniere_humidite = humidites[-1]
    duree_heures = max((derniere_date - premiere_date).total_seconds() / 3600, 0)
    ecarts = [(b[0] - a[0]).total_seconds() / 3600 for a, b in zip(humidites, humidites[1:])]
    plus_grand_trou = max(ecarts) if ecarts else 0
    if len(humidites) < 4:
        qualite = "prudence : peu de mesures"
    elif plus_grand_trou > 8:
        qualite = f"prudence : trou {formater_nombre(plus_grand_trou)} h"
    elif plus_grand_trou > 3:
        qualite = f"correct avec trou {formater_nombre(plus_grand_trou)} h"
    else:
        qualite = "bonne"
    sechage = None
    baisse_apres_pic = None
    if derniere_date > pic_date and pic_humidite != derniere_humidite:
        heures_depuis_pic = (derniere_date - pic_date).total_seconds() / 3600
        if heures_depuis_pic > 0:
            baisse_apres_pic = pic_humidite - derniere_humidite
            sechage = (derniere_humidite - pic_humidite) / heures_depuis_pic * 24
    quantite = quantite_arrosage_texte(arrosage)
    avant_txt = formater_nombre(avant_humidite) if avant_humidite is not None else "—"
    texte = (
        f"{formater_date_courte(date_arrosage)} · {quantite} · {len(mesures_cycle)} mesure(s) · "
        f"avant {avant_txt} → après {formater_nombre(premiere_humidite)} → pic {formater_nombre(pic_humidite)} → fin {formater_nombre(derniere_humidite)} % · qualité {qualite}"
    )
    if sechage is not None:
        texte += f" · baisse après pic {formater_nombre(baisse_apres_pic)} pt ({formater_nombre(sechage)} pt/j)"
    else:
        texte += " · baisse après pic non calculable"
    if date_fin:
        texte += f" · prochain arrosage {formater_date_courte(date_fin)}"
    elif duree_heures:
        texte += f" · suivi {formater_nombre(duree_heures / 24)} jour(s)"
    return {
        "date": date_arrosage,
        "fin": date_fin,
        "arrosage": arrosage,
        "mesures": mesures_cycle,
        "texte": texte,
        "sechage": sechage,
        "baisse_apres_pic": baisse_apres_pic,
        "humidite_avant": avant_humidite,
        "delai_avant_h": delai_avant_h,
        "premiere_humidite": premiere_humidite,
        "pic_humidite": pic_humidite,
        "derniere_humidite": derniere_humidite,
        "qualite": qualite,
    }


def calculer_cycles_arrosage(mesures, arrosages, limite=6):
    sessions = database.construire_sessions_arrosage(arrosages)
    cycles = []
    for index, arrosage in enumerate(sessions):
        prochain = sessions[index + 1] if index + 1 < len(sessions) else None
        cycle = mesurer_cycle_arrosage(arrosage, prochain, mesures)
        if cycle:
            cycles.append(cycle)
    return cycles[-limite:]


def analyser_cycles_arrosage(cycles):
    cycles_humidite = [
        cycle for cycle in cycles
        if cycle.get("premiere_humidite") is not None
        and cycle.get("pic_humidite") is not None
        and cycle.get("derniere_humidite") is not None
    ]
    if not cycles_humidite:
        return "Analyse cycles : pas encore assez de mesures d'humidité après arrosage pour interpréter."

    recent = cycles_humidite[-1]
    reference_depart = recent.get("humidite_avant")
    if reference_depart is None:
        reference_depart = recent["premiere_humidite"]
    hausse = recent["pic_humidite"] - reference_depart
    baisse = recent.get("baisse_apres_pic")
    retour = recent["derniere_humidite"] - reference_depart
    qualite = recent.get("qualite") or "à vérifier"
    morceaux = [
        "Analyse cycles : lecture simple du dernier cycle",
        f"avant {formater_nombre(reference_depart)} %",
        f"pic {formater_nombre(recent['pic_humidite'])} %",
        f"hausse observée +{formater_nombre(hausse)} point(s)",
        f"fin {formater_nombre(retour)} point(s) par rapport à l'avant-arrosage",
        f"qualité {qualite}",
    ]
    if baisse is not None:
        morceaux.append(f"baisse après pic {formater_nombre(baisse)} point(s)")
    else:
        morceaux.append("baisse après pic non calculable")
    if recent.get("sechage") is not None:
        morceaux.append(f"vitesse après pic {formater_nombre(recent['sechage'])} pt/j")

    if len(cycles_humidite) >= 2:
        precedent = cycles_humidite[-2]
        depart_precedent = precedent.get("humidite_avant")
        if depart_precedent is None:
            depart_precedent = precedent["premiere_humidite"]
        hausse_precedente = precedent["pic_humidite"] - depart_precedent
        morceaux.append(f"cycle précédent : hausse +{formater_nombre(hausse_precedente)} point(s)")

    return "; ".join(morceaux) + ". Interprétation prudente : zone du capteur uniquement."


def resumer_cycles_arrosage(mesures, arrosages, limite=6):
    cycles = calculer_cycles_arrosage(mesures, arrosages, limite=limite)
    if not cycles:
        return "Cycles d’arrosage : aucun arrosage exploitable avec les données actuelles."
    lignes = ["Cycles d’arrosage détectés", "", analyser_cycles_arrosage(cycles), ""]
    for cycle in reversed(cycles):
        lignes.append("- " + cycle["texte"])
    lignes.extend([
        "",
        "Lecture prudente : le Mi Flora mesure une zone du pot. La vitesse de séchage décrit la zone du capteur, pas forcément toute la motte.",
    ])
    return "\n".join(lignes)


