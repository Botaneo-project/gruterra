
from i18n import traduire_courant as _tr
from datetime import datetime

import database


def analyser_plante(plante_id):
    """
    Analyse descriptive de l'évolution de l'humidité
    depuis le dernier arrosage enregistré.
    """

    plante = database.get_plante(plante_id)

    if plante is None:
        raise ValueError(_tr('analyse_text_15'))

    mesures = database.get_mesures()

    mesures = [
        mesure
        for mesure in mesures
        if mesure[7] is not None
    ]

    if not mesures:
        print(_tr('analyse_text_26'))
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
        print(_tr('analyse_text_46'))
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
    print(_tr('analyse_text_69'))
    print("=" * 60)

    print()
    print(_tr('analyse_text_71').format(v0=plante[1]))
    print(_tr('analyse_text_72').format(v0=plante[2]))
    print(_tr('analyse_text_75').format(v0=plante[3], v1=plante[4]))

    if dernier_arrosage is None:
        print()
        print(_tr('analyse_text_77'))
        print(_tr('analyse_text_78'))
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
    print(_tr('analyse_text_94'))
    print("-" * 30)
    print(
        _tr('analyse_text_97').format(v0=date_arrosage.strftime('%d/%m/%Y %H:%M:%S'))
    )
    print(_tr('analyse_text_98').format(v0=dernier_arrosage[1]))

    if dernier_arrosage[2]:
        print(_tr('analyse_text_103').format(v0=dernier_arrosage[2]))

    if dernier_arrosage[3]:
        print(_tr('analyse_text_106').format(v0=dernier_arrosage[3]))

    if dernier_arrosage[4]:
        print(_tr('analyse_text_109').format(v0=dernier_arrosage[4]))

    if not mesures_apres:
        print()
        print(_tr('analyse_text_111'))
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
    print(_tr('analyse_text_137'))
    print("-" * 30)
    print(_tr('analyse_text_139').format(v0=humidite_depart))
    print(_tr('analyse_text_140').format(v0=humidite_actuelle))

    if variation_humidite < 0:
        print(
            _tr('analyse_text_146').format(v0=variation_humidite)
        )
    elif variation_humidite > 0:
        print(
            _tr('analyse_text_151').format(v0=variation_humidite)
        )
    else:
        print(_tr('analyse_text_152'))

    if duree_heures > 0:
        vitesse = variation_humidite / duree_heures

        print(
            _tr('analyse_text_159').format(v0=duree_heures)
        )
        print(
            _tr('analyse_text_164').format(v0=vitesse)
        )

        vitesse_jour = vitesse * 24

        print(
            _tr('analyse_text_170').format(v0=vitesse_jour)
        )

    # Dernières conditions mesurées
    print()
    print(_tr('analyse_text_172'))
    print("-" * 30)
    print(_tr('synchronisation_text_70').format(v0=derniere[2]))
    print(_tr('analyse_text_179').format(v0=derniere[3]))
    print(_tr('analyse_text_180').format(v0=derniere[4]))
    print(_tr('analyse_text_181').format(v0=derniere[5]))

    print()
    print("=" * 60)
    print(_tr('analyse_text_185'))
    print(_tr('analyse_text_186'))
    print("=" * 60)


if __name__ == "__main__":
    analyser_plante(1)