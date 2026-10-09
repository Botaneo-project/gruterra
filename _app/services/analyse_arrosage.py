"""Analyse des arrosages et des cycles d'humidité.

Ce module contient la logique pure utilisée par l'historique graphique.
Il ne dépend pas de Tkinter et peut être testé sans interface.
"""

from i18n import traduire_courant as _tr, traduire_texte_courant as _texte

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
        return _tr('botaneo_email_text_192')
    return date.strftime("%d/%m/%Y %H:%M")


def date_debut_arrosage(arrosage):
    if isinstance(arrosage, dict):
        return arrosage.get("date_debut")
    return vers_local_naif(arrosage[2])


def quantite_arrosage_texte(arrosage):
    if isinstance(arrosage, dict):
        total = arrosage.get("quantite_totale_ml")
        total_txt = f"{formater_nombre(total)} ml" if total is not None else _tr('quantity_not_noted')
        apports = arrosage.get("apports") or []
        if len(apports) > 1:
            details = []
            for apport in apports:
                date = vers_local_naif(apport[2])
                heure = date.strftime("%H:%M") if date else _tr('unknown_time')
                quantite = f"{formater_nombre(apport[3])} ml" if apport[3] is not None else _tr('quantity_not_noted')
                details.append(_tr('analyse_arrosage_text_48').format(v0=quantite, v1=heure))
            return _tr('analyse_arrosage_text_51').format(v0=total_txt, v1=' + '.join(details))
        return total_txt
    return f"{formater_nombre(arrosage[3])} ml" if arrosage and arrosage[3] is not None else _tr('quantity_not_noted')


def quantite_arrosage_courte(arrosage):
    if isinstance(arrosage, dict):
        total = arrosage.get("quantite_totale_ml")
        total_txt = f"{formater_nombre(total)} ml" if total is not None else "—"
        if arrosage.get("fractionnee"):
            return _tr('analyse_arrosage_text_61').format(v0=total_txt)
        return total_txt
    return f"{formater_nombre(arrosage[3])} ml" if arrosage and arrosage[3] is not None else "—"


def valeur_arrosage(arrosage, index, cle_session=None):
    if isinstance(arrosage, dict):
        if cle_session and arrosage.get(cle_session) is not None:
            return arrosage.get(cle_session)
        apports = arrosage.get("apports") or []
        if not apports:
            return None
        valeurs = []
        for apport in apports:
            try:
                valeur = apport[index]
            except IndexError:
                valeur = None
            if valeur not in (None, ""):
                valeurs.append(valeur)
        if not valeurs:
            return None
        return valeurs[0] if len(set(map(str, valeurs))) == 1 else "mixte"
    try:
        return arrosage[index]
    except (TypeError, IndexError):
        return None


def quantite_arrosage_valeur(arrosage):
    valeur = valeur_arrosage(arrosage, 3, "quantite_totale_ml")
    try:
        return float(valeur) if valeur is not None else None
    except (TypeError, ValueError):
        return None


def type_eau_arrosage(arrosage):
    valeur = valeur_arrosage(arrosage, 8)
    return str(valeur).strip().lower() if valeur not in (None, "") else None


def comparer_conditions_cycles(cycle_a, cycle_b):
    """Compare les conditions disponibles avant de rapprocher deux cycles."""

    alertes = []
    niveau = "proche"

    quantite_a = quantite_arrosage_valeur(cycle_a.get("arrosage"))
    quantite_b = quantite_arrosage_valeur(cycle_b.get("arrosage"))
    if quantite_a is not None and quantite_b is not None:
        ecart_quantite = abs(quantite_a - quantite_b)
        reference = max(quantite_a, quantite_b, 1)
        if ecart_quantite > 20 and ecart_quantite / reference > 0.2:
            niveau = "à éviter"
            alertes.append(_tr('analyse_arrosage_text_114').format(v0=formater_nombre(quantite_a), v1=formater_nombre(quantite_b)))
        elif ecart_quantite > 10:
            niveau = "prudence"
            alertes.append(_tr('analyse_arrosage_text_117').format(v0=formater_nombre(quantite_a), v1=formater_nombre(quantite_b)))

    eau_a = type_eau_arrosage(cycle_a.get("arrosage"))
    eau_b = type_eau_arrosage(cycle_b.get("arrosage"))
    if eau_a and eau_b and eau_a != eau_b:
        niveau = "à éviter" if niveau == "à éviter" else "prudence"
        alertes.append(_tr('analyse_arrosage_text_123').format(v0=eau_a, v1=eau_b))

    niveaux_qualite = {"bonne": 0, "correcte": 1, "prudence": 2, "interruption longue": 3}
    qa = niveaux_qualite.get(cycle_a.get("qualite_niveau"), 2)
    qb = niveaux_qualite.get(cycle_b.get("qualite_niveau"), 2)
    if max(qa, qb) >= 3:
        niveau = "à éviter"
        alertes.append(_tr('analyse_arrosage_text_130'))
    elif max(qa, qb) >= 2 and niveau == "proche":
        niveau = "prudence"
        alertes.append(_tr('analyse_arrosage_text_133'))

    if not alertes:
        alertes.append(_tr('analyse_arrosage_text_138'))

    return {
        "niveau": niveau,
        "alertes": alertes,
        "texte": _tr('analyse_arrosage_text_141').format(v0=_texte(niveau)) + "; ".join(alertes),
    }


def analyser_qualite_cycle(humidites, pic_date=None, derniere_date=None):
    """Retourne une qualité stable pour un cycle et ses principaux trous de mesure."""

    ecarts = []
    for avant, apres in zip(humidites, humidites[1:]):
        heures = (apres[0] - avant[0]).total_seconds() / 3600
        if heures > 0:
            ecarts.append({"debut": avant[0], "fin": apres[0], "heures": heures})
    plus_grand_trou = max((ecart["heures"] for ecart in ecarts), default=0)

    if len(humidites) < 4:
        niveau = "prudence"
        libelle = _tr('analyse_arrosage_text_157')
    elif plus_grand_trou > 24:
        niveau = "interruption longue"
        libelle = _tr("quality_gap_long").format(hours=formater_nombre(plus_grand_trou))
    elif plus_grand_trou > 8:
        niveau = "prudence"
        libelle = _tr('analyse_arrosage_text_165').format(v0=formater_nombre(plus_grand_trou))
    elif plus_grand_trou > 3:
        niveau = "correcte"
        libelle = _tr('analyse_arrosage_text_166').format(v0=formater_nombre(plus_grand_trou))
    else:
        niveau = "bonne"
        libelle = _tr('analyse_arrosage_text_171')

    avertissements = []
    for cible, nom in ((pic_date, "pic"), (derniere_date, _tr('analyse_arrosage_text_172'))):
        if not cible:
            continue
        for ecart in ecarts:
            if ecart["heures"] > 8 and ecart["fin"] == cible:
                avertissements.append(_tr('analyse_arrosage_text_177').format(v0=nom, v1=formater_nombre(ecart['heures'])))
                break

    if avertissements and niveau == "bonne":
        niveau = "correcte"
    elif avertissements and niveau == "correcte":
        niveau = "prudence"

    return {
        "niveau": niveau,
        "libelle": _texte(libelle),
        "plus_grand_trou_h": plus_grand_trou,
        "avertissements": avertissements,
    }


def vitesse_sechage_apres_pic(pic_date, pic_humidite, derniere_date, derniere_humidite):
    if not pic_date or not derniere_date or derniere_date <= pic_date:
        return None
    if pic_humidite is None or derniere_humidite is None or pic_humidite == derniere_humidite:
        return None
    heures_depuis_pic = (derniere_date - pic_date).total_seconds() / 3600
    if heures_depuis_pic <= 0:
        return None
    return (derniere_humidite - pic_humidite) / heures_depuis_pic * 24


def vitesse_humidite_sur_24h(humidites):
    if len(humidites) < 2:
        return None
    derniere_date, derniere_humidite = humidites[-1]
    cible = derniere_date.timestamp() - 24 * 3600
    candidates = [item for item in humidites[:-1] if item[0].timestamp() <= cible]
    if not candidates:
        return None
    date_ref, humidite_ref = candidates[-1]
    heures = (derniere_date - date_ref).total_seconds() / 3600
    if heures <= 0:
        return None
    return (derniere_humidite - humidite_ref) / heures * 24


def qualifier_vitesse_sechage(sechage):
    if sechage is None:
        return _tr('analyse_arrosage_text_221')
    if sechage < -8:
        return _tr('analyse_arrosage_text_223')
    if sechage < -3:
        return _tr('analyse_arrosage_text_225')
    if sechage < -0.5:
        return _tr('analyse_arrosage_text_227')
    if sechage <= 0.5:
        return _tr('analyse_arrosage_text_229')
    return _tr('analyse_arrosage_text_230')


def resumer_indicateurs_cycle(cycle):
    return {
        "reponse_arrosage": cycle.get("lecture_courte") or _tr('analyse_arrosage_text_235'),
        "sechage_apres_pic": qualifier_vitesse_sechage(cycle.get("sechage")),
        "tendance_24h": (
            _tr('analyse_arrosage_text_238').format(v0=formater_nombre(cycle.get('vitesse_24h')))
            if cycle.get("vitesse_24h") is not None
            else _tr('analyse_arrosage_text_240')
        ),
    }


def interpreter_reponse_cycle(reference_depart, premiere_humidite, pic_humidite, derniere_humidite, qualite_niveau):
    if premiere_humidite is None or pic_humidite is None or derniere_humidite is None:
        return {
            "hausse_apres_arrosage": None,
            "ecart_final_depart": None,
            "lecture_courte": _tr('analyse_arrosage_text_250'),
        }
    if reference_depart is None:
        reference_depart = premiere_humidite
    hausse = pic_humidite - reference_depart
    ecart_final = derniere_humidite - reference_depart
    prudence = _tr('analyse_arrosage_text_256') if qualite_niveau in {"prudence", "interruption longue"} else ""
    if hausse < 2:
        lecture = _tr('analyse_arrosage_text_258')
    elif ecart_final <= 2:
        lecture = _tr('analyse_arrosage_text_260')
    elif ecart_final >= 8:
        lecture = _tr('analyse_arrosage_text_262')
    else:
        lecture = _tr('analyse_arrosage_text_264')
    return {
        "hausse_apres_arrosage": hausse,
        "ecart_final_depart": ecart_final,
        "lecture_courte": lecture + prudence,
    }


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
            "qualite": _tr('analyse_arrosage_text_306'),
            "texte": _tr('analyse_arrosage_text_307').format(v0=formater_date_courte(date_arrosage)),
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
            "qualite": _tr('analyse_arrosage_text_320'),
            "texte": _tr('analyse_arrosage_text_321').format(v0=formater_date_courte(date_arrosage), v1=len(mesures_cycle)),
        }

    premiere_date, premiere_humidite = humidites[0]
    pic_date, pic_humidite = max(humidites, key=lambda item: item[1])
    derniere_date, derniere_humidite = humidites[-1]
    duree_heures = max((derniere_date - premiere_date).total_seconds() / 3600, 0)
    qualite_detail = analyser_qualite_cycle(humidites, pic_date=pic_date, derniere_date=derniere_date)
    qualite = qualite_detail["libelle"]
    sechage = vitesse_sechage_apres_pic(pic_date, pic_humidite, derniere_date, derniere_humidite)
    vitesse_24h = vitesse_humidite_sur_24h(humidites)
    baisse_apres_pic = None
    if sechage is not None:
        baisse_apres_pic = pic_humidite - derniere_humidite
    reference_depart = avant_humidite if avant_humidite is not None else premiere_humidite
    interpretation = interpreter_reponse_cycle(reference_depart, premiere_humidite, pic_humidite, derniere_humidite, qualite_detail["niveau"])
    quantite = quantite_arrosage_texte(arrosage)
    avant_txt = formater_nombre(avant_humidite) if avant_humidite is not None else "—"
    texte = (
        _tr('analyse_arrosage_text_340').format(v0=formater_date_courte(date_arrosage), v1=quantite, v2=len(mesures_cycle), v3=avant_txt, v4=formater_nombre(premiere_humidite), v5=formater_nombre(pic_humidite), v6=formater_nombre(derniere_humidite), v7=formater_nombre(interpretation['hausse_apres_arrosage']), v8=formater_nombre(interpretation['ecart_final_depart']), v9=qualite)
    )
    lecture_sechage = qualifier_vitesse_sechage(sechage)
    if sechage is not None:
        texte += _tr('analyse_arrosage_text_346').format(v0=formater_nombre(baisse_apres_pic), v1=formater_nombre(sechage), v2=lecture_sechage)
    else:
        texte += f" · {lecture_sechage}"
    if vitesse_24h is not None:
        texte += _tr('analyse_arrosage_text_350').format(v0=formater_nombre(vitesse_24h))
    if qualite_detail["avertissements"]:
        texte += " · " + "; ".join(qualite_detail["avertissements"])
    if date_fin:
        texte += _tr('analyse_arrosage_text_354').format(v0=formater_date_courte(date_fin))
    elif duree_heures:
        texte += _tr('analyse_arrosage_text_356').format(v0=formater_nombre(duree_heures / 24))
    return {
        "date": date_arrosage,
        "fin": date_fin,
        "arrosage": arrosage,
        "mesures": mesures_cycle,
        "texte": texte,
        "sechage": sechage,
        "vitesse_24h": vitesse_24h,
        "baisse_apres_pic": baisse_apres_pic,
        "qualite_niveau": qualite_detail["niveau"],
        "plus_grand_trou_h": qualite_detail["plus_grand_trou_h"],
        "avertissements_qualite": qualite_detail["avertissements"],
        "humidite_avant": avant_humidite,
        "delai_avant_h": delai_avant_h,
        "premiere_date": premiere_date,
        "pic_date": pic_date,
        "derniere_date": derniere_date,
        "premiere_humidite": premiere_humidite,
        "pic_humidite": pic_humidite,
        "derniere_humidite": derniere_humidite,
        "hausse_apres_arrosage": interpretation["hausse_apres_arrosage"],
        "ecart_final_depart": interpretation["ecart_final_depart"],
        "lecture_courte": interpretation["lecture_courte"],
        "lecture_sechage": lecture_sechage,
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
        return _tr('analyse_arrosage_text_404')

    recent = cycles_humidite[-1]
    reference_depart = recent.get("humidite_avant")
    if reference_depart is None:
        reference_depart = recent["premiere_humidite"]
    hausse = recent["pic_humidite"] - reference_depart
    baisse = recent.get("baisse_apres_pic")
    retour = recent["derniere_humidite"] - reference_depart
    qualite = recent.get("qualite") or _tr('analyse_arrosage_text_413')
    indicateurs = resumer_indicateurs_cycle(recent)
    morceaux = [
        _tr('analyse_arrosage_text_416'),
        _tr('analyse_arrosage_text_417') + indicateurs["reponse_arrosage"],
        _tr('analyse_arrosage_text_418').format(v0=formater_nombre(reference_depart)),
        f"{_texte('pic')} {formater_nombre(recent['pic_humidite'])} %",
        _tr('analyse_arrosage_text_420').format(v0=formater_nombre(hausse)),
        _tr('analyse_arrosage_text_421').format(v0=formater_nombre(retour)),
        _tr('analyse_arrosage_text_422') + indicateurs["sechage_apres_pic"],
        _tr('analyse_arrosage_text_423') + indicateurs["tendance_24h"],
        _tr('analyse_arrosage_text_424').format(v0=qualite),
    ]
    if baisse is not None:
        morceaux.append(_tr('analyse_arrosage_text_427').format(v0=formater_nombre(baisse)))
    else:
        morceaux.append(_tr('analyse_arrosage_text_429'))
    if recent.get("sechage") is not None:
        morceaux.append(_tr('analyse_arrosage_text_431').format(v0=formater_nombre(recent['sechage'])))
    if recent.get("vitesse_24h") is not None:
        morceaux.append(_tr('analyse_arrosage_text_433').format(v0=formater_nombre(recent['vitesse_24h'])))
    if recent.get("avertissements_qualite"):
        morceaux.append(_tr('analyse_arrosage_text_435') + ", ".join(recent["avertissements_qualite"]))

    if len(cycles_humidite) >= 2:
        precedent = cycles_humidite[-2]
        depart_precedent = precedent.get("humidite_avant")
        if depart_precedent is None:
            depart_precedent = precedent["premiere_humidite"]
        hausse_precedente = precedent["pic_humidite"] - depart_precedent
        morceaux.append(_tr('analyse_arrosage_text_443').format(v0=formater_nombre(hausse_precedente)))

    return "; ".join(morceaux) + _tr('analyse_arrosage_text_445')


def resumer_cycles_arrosage(mesures, arrosages, limite=6):
    cycles = calculer_cycles_arrosage(mesures, arrosages, limite=limite)
    if not cycles:
        return _tr('analyse_arrosage_text_451')
    lignes = [_tr('analyse_arrosage_text_452'), "", analyser_cycles_arrosage(cycles), ""]
    for cycle in reversed(cycles):
        lignes.append("- " + cycle["texte"])
    lignes.extend([
        "",
        _tr('analyse_arrosage_text_457'),
    ])
    return "\n".join(lignes)


