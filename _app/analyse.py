from datetime import datetime

import database


def analyser_plante(plante_id):
    """
    Analyse descriptive de l'évolution de l'humidité
    depuis le dernier arrosage enregistré.
    """

    plante = database.get_plante(plante_id)

    if plante is None:
        raise ValueError("La plante n'existe pas.")

    mesures = database.get_mesures()

    mesures = [
        mesure
        for mesure in mesures
        if mesure[7] is not None
    ]

    if not mesures:
        print("❌ Aucune mesure disponible.")
        return

    # Recherche des mesures associées aux capteurs
    # actuellement ou historiquement liés à cette plante.
    capteurs = database.get_capteurs()

    capteur_ids = [
        capteur[0]
        for capteur in capteurs
        if capteur[3] == plante_id
    ]

    mesures_plante = [
        mesure
        for mesure in mesures
        if mesure[7] in capteur_ids
    ]

    if not mesures_plante:
        print("❌ Aucune mesure disponible pour cette plante.")
        return

    # Dernier arrosage
    conn = database.get_connection()

    dernier_arrosage = conn.execute(
        """
        SELECT date_heure, quantite_ml, type, fertilisant, dosage
        FROM arrosages
        WHERE plante_id = ?
        ORDER BY date_heure DESC
        LIMIT 1
        """,
        (plante_id,)
    ).fetchone()

    conn.close()

    print()
    print("=" * 60)
    print("🧠 ANALYSE BOTANEO")
    print("=" * 60)

    print()
    print(f"🌿 Plante : {plante[1]}")
    print(f"   Espèce : {plante[2]}")
    print(f"   Lieu   : {plante[3]} - {plante[4]}")

    if dernier_arrosage is None:
        print()
        print("💧 Aucun arrosage enregistré.")
        print("ℹ️ Impossible d'analyser un cycle de séchage.")
        return

    date_arrosage = datetime.fromisoformat(
        dernier_arrosage[0]
    )

    mesures_apres = [
        mesure
        for mesure in mesures_plante
        if datetime.fromisoformat(mesure[1]) >= date_arrosage
    ]

    print()
    print("💧 DERNIER ARROSAGE")
    print("-" * 30)
    print(
        f"🕐 Date : "
        f"{date_arrosage.strftime('%d/%m/%Y %H:%M:%S')}"
    )
    print(f"💦 Quantité : {dernier_arrosage[1]} ml")

    if dernier_arrosage[2]:
        print(f"   Type : {dernier_arrosage[2]}")

    if dernier_arrosage[3]:
        print(f"   Fertilisant : {dernier_arrosage[3]}")

    if dernier_arrosage[4]:
        print(f"   Dosage : {dernier_arrosage[4]}")

    if not mesures_apres:
        print()
        print("ℹ️ Aucune mesure après cet arrosage.")
        return

    # Tri chronologique
    mesures_apres.sort(
        key=lambda mesure: datetime.fromisoformat(mesure[1])
    )

    premiere = mesures_apres[0]
    derniere = mesures_apres[-1]

    humidite_depart = premiere[3]
    humidite_actuelle = derniere[3]

    date_depart = datetime.fromisoformat(premiere[1])
    date_actuelle = datetime.fromisoformat(derniere[1])

    duree_heures = (
        date_actuelle - date_depart
    ).total_seconds() / 3600

    variation_humidite = (
        humidite_actuelle - humidite_depart
    )

    print()
    print("💧 ÉVOLUTION DE L'HUMIDITÉ")
    print("-" * 30)
    print(f"Première mesure : {humidite_depart:.1f} %")
    print(f"Dernière mesure : {humidite_actuelle:.1f} %")

    if variation_humidite < 0:
        print(
            f"📉 Variation : "
            f"{variation_humidite:.1f} point(s)"
        )
    elif variation_humidite > 0:
        print(
            f"📈 Variation : "
            f"+{variation_humidite:.1f} point(s)"
        )
    else:
        print("➡️ Variation : stable")

    if duree_heures > 0:
        vitesse = variation_humidite / duree_heures

        print(
            f"⏱️ Durée observée : "
            f"{duree_heures:.1f} h"
        )
        print(
            f"📊 Variation moyenne : "
            f"{vitesse:.3f} point/h"
        )

        vitesse_jour = vitesse * 24

        print(
            f"📅 Variation moyenne : "
            f"{vitesse_jour:.2f} point(s)/jour"
        )

    # Dernières conditions mesurées
    print()
    print("🌡️ DERNIÈRES CONDITIONS")
    print("-" * 30)
    print(f"🌡️ Température : {derniere[2]:.1f} °C")
    print(f"💧 Humidité sol : {derniere[3]:.1f} %")
    print(f"☀️ Luminosité : {derniere[4]:.1f} lux")
    print(f"🧪 Conductivité : {derniere[5]:.1f} µS/cm")

    print()
    print("=" * 60)
    print("ℹ️ Cette analyse est descriptive.")
    print("Aucune recommandation d'arrosage n'est encore générée.")
    print("=" * 60)


if __name__ == "__main__":
    analyser_plante(1)