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
            "message": "Sol actuellement très sec."
        }

    if humidite < 30:
        return {
            "etat": "en_dessechement",
            "niveau": "orange",
            "message": "Le sol commence à être sec."
        }

    if humidite < 40:
        return {
            "etat": "a_surveille",
            "niveau": "jaune",
            "message": "Humidité à surveiller."
        }

    return {
        "etat": "humide",
        "niveau": "vert",
        "message": "Humidité du sol actuellement correcte."
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
            "Historique encore trop court pour une prévision fiable."
        )
    elif len(mesures) < 20:
        confiance = "moyenne"
        explication_confiance = (
            "Historique en cours de constitution."
        )
    else:
        confiance = "bonne"
        explication_confiance = (
            "Historique suffisant pour commencer à identifier "
            "les tendances."
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
        print("❌ Aucune donnée disponible pour l'analyse.")
        return

    mesure = analyse["mesure"]
    humidite = analyse["humidite"]

    print()
    print("=" * 60)
    print("🌿 GRUTERRA - ANALYSE DE LA PLANTE")
    print("=" * 60)

    print()
    print("💧 HUMIDITÉ DU SOL")
    print("-" * 30)
    print(f"   {mesure['humidite']} %")
    print(f"   {humidite['message']}")

    print()
    print("🌡️ TEMPÉRATURE")
    print("-" * 30)
    print(f"   {mesure['temperature']:.1f} °C")

    print()
    print("☀️ LUMINOSITÉ")
    print("-" * 30)
    print(f"   {mesure['luminosite']} lux")

    print()
    print("🧪 CONDUCTIVITÉ")
    print("-" * 30)
    print(f"   {mesure['conductivite']} µS/cm")

    print()
    print("📈 TENDANCE")
    print("-" * 30)

    if analyse["tendance_humidite"] == "baisse":
        print("   💧 Humidité : ↓ baisse")

    elif analyse["tendance_humidite"] == "hausse":
        print("   💧 Humidité : ↑ hausse")

    elif analyse["tendance_humidite"] == "stable":
        print("   💧 Humidité : → stable")

    else:
        print("   💧 Humidité : ? inconnue")

    vitesse = analyse["vitesse_humidite_par_heure"]

    if vitesse is not None:
        print(
            f"   Variation : "
            f"{vitesse:+.2f} point(s) / heure"
        )

    print()
    print("🎯 FIABILITÉ DE L'ANALYSE")
    print("-" * 30)
    print(f"   Confiance : {analyse['confiance']}")
    print(f"   {analyse['explication_confiance']}")
    print(
        f"   {analyse['nombre_mesures']} mesure(s) analysée(s)"
    )

    print()
    print("💡 ACTION")
    print("-" * 30)

    if humidite["etat"] == "sec":
        print("   🔴 Le sol est actuellement très sec.")
        print("   ⚠️ Arrosage à envisager.")
        print("   ℹ️ Gruterra ne donne pas encore de délai")
        print("      précis : l'historique doit encore s'enrichir.")

    elif humidite["etat"] == "en_dessechement":
        print("   🟠 Le sol est en phase de dessèchement.")
        print("   👀 Surveillance recommandée.")

    elif humidite["etat"] == "a_surveille":
        print("   🟡 Humidité à surveiller.")
        print("   👀 Gruterra observe actuellement l'évolution.")

    else:
        print("   🟢 Pas d'action immédiate sur l'humidité.")

    print()
    print("=" * 60)


def afficher_evolution(capteur_id, heures=24):
    """Affiche l'historique récent d'un capteur."""

    mesures = obtenir_evolution_capteur(
        capteur_id,
        heures
    )

    if mesures is None:
        print("❌ Aucune mesure disponible sur cette période.")
        return

    print()
    print("📊 ÉVOLUTION DU SOL")
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
        f"📈 {len(mesures)} mesure(s) "
        f"sur les dernières {heures} h"
    )


if __name__ == "__main__":
    afficher_analyse(1)