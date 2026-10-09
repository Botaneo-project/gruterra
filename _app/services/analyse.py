
from i18n import traduire_courant as _tr
import database
from datetime import datetime, timedelta


def obtenir_evolution_capteur(capteur_id, heures=24):
    """Retourne les mesures récentes d'un capteur."""

    mesures = database.get_mesures_capteur(capteur_id, 500)

    if not mesures:
        return None

    limite = datetime.now() - timedelta(hours=heures)

    mesures_recentes = []

    for mesure in mesures:
        date_mesure = datetime.fromisoformat(mesure[1])

        if date_mesure >= limite:
            mesures_recentes.append(mesure)

    if not mesures_recentes:
        return None

    mesures_recentes.sort(key=lambda mesure: mesure[1])

    return mesures_recentes


def analyser_humidite(humidite):
    """
    Première interprétation de l'humidité du sol.

    Ces catégories sont volontairement prudentes.
    Elles ne constituent pas encore une règle d'arrosage définitive.
    """

    if humidite < 20:
        return {
            "etat": "sec",
            "niveau": "rouge",
            "message": _tr('analyse_text_43')
        }

    if humidite < 30:
        return {
            "etat": "en_dessechement",
            "niveau": "orange",
            "message": _tr('analyse_text_50')
        }

    if humidite < 40:
        return {
            "etat": "a_surveille",
            "niveau": "jaune",
            "message": _tr('analyse_text_57')
        }

    return {
        "etat": "humide",
        "niveau": "vert",
        "message": _tr('analyse_text_63')
    }


def calculer_tendance(mesures):
    """
    Compare la première et la dernière mesure disponibles.

    Retourne une tendance simple :
    - hausse
    - baisse
    - stable
    - inconnue
    """

    if not mesures or len(mesures) < 2:
        return "inconnue"

    premiere = mesures[0]
    derniere = mesures[-1]

    humidite_depart = premiere[3]
    humidite_fin = derniere[3]

    difference = humidite_fin - humidite_depart

    if difference <= -2:
        return "baisse"

    if difference >= 2:
        return "hausse"

    return "stable"


def calculer_vitesse_dessechement(mesures):
    """
    Estime la vitesse de variation de l'humidité du sol.

    Cette valeur est informative uniquement.
    Elle servira plus tard à établir une véritable prévision.
    """

    if not mesures or len(mesures) < 2:
        return None

    premiere = mesures[0]
    derniere = mesures[-1]

    date_depart = datetime.fromisoformat(premiere[1])
    date_fin = datetime.fromisoformat(derniere[1])

    duree_heures = (
        date_fin - date_depart
    ).total_seconds() / 3600

    if duree_heures <= 0:
        return None

    humidite_depart = premiere[3]
    humidite_fin = derniere[3]

    variation = humidite_fin - humidite_depart

    return variation / duree_heures


def analyser_capteur(capteur_id, heures=24):
    """
    Analyse l'état actuel d'un capteur Mi Flora.
    """

    mesures = obtenir_evolution_capteur(
        capteur_id,
        heures
    )

    if not mesures:
        return None

    derniere = mesures[-1]

    temperature = derniere[2]
    humidite = derniere[3]
    luminosite = derniere[4]
    conductivite = derniere[5]

    analyse_humidite_resultat = analyser_humidite(humidite)
    tendance = calculer_tendance(mesures)
    vitesse = calculer_vitesse_dessechement(mesures)

    if len(mesures) < 5:
        confiance = "faible"
        explication_confiance = (
            _tr('analyse_text_157')
        )
    elif len(mesures) < 20:
        confiance = "moyenne"
        explication_confiance = (
            _tr('analyse_text_162')
        )
    else:
        confiance = "bonne"
        explication_confiance = (
            _tr('analyse_text_167')
        )

    return {
        "mesure": {
            "date_heure": derniere[1],
            "temperature": temperature,
            "humidite": humidite,
            "luminosite": luminosite,
            "conductivite": conductivite
        },
        "humidite": analyse_humidite_resultat,
        "tendance_humidite": tendance,
        "vitesse_humidite_par_heure": vitesse,
        "nombre_mesures": len(mesures),
        "confiance": confiance,
        "explication_confiance": explication_confiance
    }


def afficher_analyse(capteur_id, heures=24):
    """Affiche une analyse lisible de l'état actuel du sol."""

    analyse = analyser_capteur(
        capteur_id,
        heures
    )

    if analyse is None:
        print()
        print(_tr('analyse_text_198'))
        return

    mesure = analyse["mesure"]
    humidite = analyse["humidite"]

    print()
    print("=" * 60)
    print(_tr('analyse_text_207'))
    print("=" * 60)

    print()
    print(_tr('analyse_text_210'))
    print("-" * 30)
    print(f"   {mesure['humidite']} %")
    print(f"   {humidite['message']}")

    print()
    print(_tr('analyse_text_216'))
    print("-" * 30)
    print(f"   {mesure['temperature']:.1f} °C")

    print()
    print(_tr('analyse_text_221'))
    print("-" * 30)
    print(f"   {mesure['luminosite']} lux")

    print()
    print(_tr('analyse_text_226'))
    print("-" * 30)
    print(f"   {mesure['conductivite']} µS/cm")

    print()
    print(_tr('analyse_text_232'))
    print("-" * 30)

    if analyse["tendance_humidite"] == "baisse":
        print(_tr('analyse_text_235'))

    elif analyse["tendance_humidite"] == "hausse":
        print(_tr('analyse_text_238'))

    elif analyse["tendance_humidite"] == "stable":
        print(_tr('analyse_text_241'))

    else:
        print(_tr('analyse_text_244'))

    vitesse = analyse["vitesse_humidite_par_heure"]

    if vitesse is not None:
        print(
            _tr('analyse_text_251').format(v0=vitesse)
        )

    print()
    print(_tr('analyse_text_255'))
    print("-" * 30)
    print(_tr('analyse_text_258').format(v0=analyse['confiance']))
    print(f"   {analyse['explication_confiance']}")
    print(
        _tr('analyse_text_260').format(v0=analyse['nombre_mesures'])
    )

    print()
    print(_tr('analyse_text_264'))
    print("-" * 30)

    if humidite["etat"] == "sec":
        print(_tr('analyse_text_268'))
        print(_tr('analyse_text_269'))
        print(_tr('analyse_text_270'))
        print(_tr('analyse_text_271'))

    elif humidite["etat"] == "en_dessechement":
        print(_tr('analyse_text_274'))
        print(_tr('analyse_text_275'))

    elif humidite["etat"] == "a_surveille":
        print(_tr('analyse_text_278'))
        print(_tr('analyse_text_279'))

    else:
        print(_tr('analyse_text_282'))

    print()
    print("=" * 60)


def afficher_evolution(capteur_id, heures=24):
    """Affiche l'historique récent d'un capteur."""

    mesures = obtenir_evolution_capteur(
        capteur_id,
        heures
    )

    if mesures is None:
        print(_tr('analyse_text_297'))
        return

    print()
    print(_tr('analyse_text_301'))
    print("=" * 50)

    for mesure in mesures:
        date_heure = datetime.fromisoformat(mesure[1])
        temperature = mesure[2]
        humidite = mesure[3]
        luminosite = mesure[4]
        conductivite = mesure[5]

        print(
            f"{date_heure.strftime('%d/%m %H:%M')}  "
            f"💧 {humidite:>3} %  "
            f"🌡️ {temperature:>4} °C  "
            f"☀️ {luminosite:>4} lux  "
            f"🧪 {conductivite:>4} µS/cm"
        )

    print("=" * 50)
    print(
        _tr('analyse_text_321').format(v0=len(mesures), v1=heures)
    )


if __name__ == "__main__":
    afficher_analyse(1)