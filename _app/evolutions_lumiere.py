"""Évolutions observées, sans déduire un déplacement ou une durée d'exposition."""

from i18n import traduire_courant as _tr
from collections import defaultdict
from datetime import datetime, timedelta
from math import isfinite
from statistics import median


def analyser_evolutions(mesures, maintenant=None):
    maintenant = maintenant or datetime.now()
    if maintenant.tzinfo:
        maintenant = maintenant.astimezone().replace(tzinfo=None)
    aujourd_hui = maintenant.date()
    heures = defaultdict(lambda: defaultdict(list))
    for mesure in mesures:
        try:
            date = datetime.fromisoformat(mesure[1])
            if date.tzinfo:
                date = date.astimezone().replace(tzinfo=None)
            lux = float(mesure[4])
        except (ValueError, TypeError, IndexError):
            continue
        if (isfinite(lux) and lux >= 0 and 8 <= date.hour < 20
                and aujourd_hui - timedelta(days=8) <= date.date() < aujourd_hui):
            heures[date.date()][date.hour].append(lux)
    jours = {jour: {h: median(v) for h, v in valeurs.items()}
             for jour, valeurs in heures.items()}
    evenements = []
    noms = (_tr('evolutions_lumiere_text_30'), _tr('evolutions_lumiere_text_30_more'), _tr('evolutions_lumiere_text_30_more_more'), _tr('evolutions_lumiere_text_30_more_more_more'), _tr('evolutions_lumiere_text_30_more_more_more_more'), _tr('evolutions_lumiere_text_30_more_more_more_more_more'), _tr('evolutions_lumiere_text_30_more_more_more_more_more_more'))
    for jour in sorted(jours, reverse=True):
        precedent = jour - timedelta(days=1)
        commun = sorted(set(jours[jour]) & set(jours.get(precedent, {})))
        # Des créneaux comparables, répartis sur la journée ; pas de journée en cours.
        if len(commun) < 4 or commun[-1] - commun[0] < 4:
            continue
        avant = sum(jours[precedent][h] for h in commun) / len(commun)
        apres = sum(jours[jour][h] for h in commun) / len(commun)
        hausse = apres - avant >= 250 and apres >= 2 * avant
        baisse = avant - apres >= 250 and avant >= 2 * apres
        if not (hausse or baisse):
            continue
        pic = max(v for valeurs in heures[jour].values() for v in valeurs)
        evenements.append({
            'date': jour.isoformat(),
            'sens': 'hausse' if hausse else 'baisse',
            'titre': f"{noms[jour.weekday()]} {jour:%d/%m} · " + (
                _tr('evolutions_lumiere_text_46') if hausse else _tr('evolutions_lumiere_text_46_more')),
            'detail': _tr('evolutions_lumiere_text_47').format(v0=len(commun), v1=avant, v2=apres, v3=pic),
        })
    return evenements


def lire_evolutions(database, plante_id, maintenant=None):
    maintenant = maintenant or datetime.now()
    # Filtrage par date, sans plafond de relevés qui masquerait les anciens jours.
    debut = (maintenant - timedelta(days=9)).date().isoformat()
    connexion = database.get_connection()
    try:
        mesures = connexion.execute('''
            SELECT m.id, m.date_heure, m.temperature, m.humidite, m.luminosite
            FROM mesures m JOIN capteurs c ON c.id = m.capteur_id
            WHERE c.plante_id = ? AND m.date_heure >= ?
        ''', (plante_id, debut)).fetchall()
    finally:
        connexion.close()
    return analyser_evolutions(mesures, maintenant)
