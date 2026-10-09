
from i18n import traduire_courant as _tr
import asyncio

import database
from capteurs.miflora import lire_mesure
from capteurs.netatmo import recuperer_netatmo



async def synchroniser_miflora():
    print()
    print("=" * 60)
    print(_tr('synchronisation_botaneo_text_14'))
    print("=" * 60)

    capteurs = database.get_capteurs()

    if not capteurs:
        print(_tr('synchronisation_botaneo_text_18'))
        return False

    succes = False

    for capteur in capteurs:
        (
            capteur_id,
            nom_capteur,
            adresse,
            plante_id,
            nom_plante,
            espece,
            emplacement,
            zone
        ) = capteur

        print()
        print(_tr('synchronisation_botaneo_text_36').format(v0=nom_plante))
        print(f"📍 Emplacement : {emplacement} - {zone}")
        print(f"📡 Capteur   : {nom_capteur}")
        print(f"🔗 Adresse   : {adresse}")

        try:
            (
                temperature,
                humidite,
                luminosite,
                conductivite,
                donnees_brutes
            ) = await lire_mesure(adresse)

            database.enregistrer_mesure(
                capteur_id,
                __import__("datetime").datetime.now().isoformat(
                    timespec="seconds"
                ),
                temperature,
                humidite,
                luminosite,
                conductivite,
                donnees_brutes
            )

            print()
            print(_tr('synchronisation_botaneo_text_65_more'))
            print(_tr('synchronisation_botaneo_text_64').format(v0=temperature))
            print(_tr('synchronisation_botaneo_text_65').format(v0=humidite))
            print(_tr('synchronisation_botaneo_text_66').format(v0=luminosite))
            print(_tr('synchronisation_botaneo_text_67').format(v0=conductivite))
            print(_tr('synchronisation_botaneo_text_68'))

            succes = True

        except Exception as erreur:
            print()
            print(_tr('synchronisation_botaneo_text_74').format(v0=erreur))

    return succes


def synchroniser_netatmo():
    print()
    print("=" * 60)
    print(_tr('synchronisation_botaneo_text_84'))
    print("=" * 60)

    try:
        stations = recuperer_netatmo()

        print()
        print(_tr('synchronisation_botaneo_text_89').format(v0=len(stations)))

        for station in stations:
            print()
            print(f"🏠 {station['nom']}")

            mesures = station["mesures"]

            if mesures["temperature"] is not None:
                print(
                    _tr('synchronisation_botaneo_text_99').format(v0=mesures['temperature'])
                )

            if mesures["humidite"] is not None:
                print(
                    _tr('synchronisation_botaneo_text_105').format(v0=mesures['humidite'])
                )

            for module in station["modules"]:
                print()
                print(f"   📦 Module : {module['nom']}")

                mesures = module["mesures"]

                if mesures["temperature"] is not None:
                    print(
                        _tr('synchronisation_botaneo_text_117').format(v0=mesures['temperature'])
                    )

                if mesures["humidite"] is not None:
                    print(
                        _tr('synchronisation_botaneo_text_123').format(v0=mesures['humidite'])
                    )

        print()
        print(_tr('synchronisation_botaneo_text_128'))
        return True

    except Exception as erreur:
        print()
        print(_tr('app_text_146').format(v0=erreur))
        return False


async def main():

    print()
    print("=" * 60)
    print("🌿 GRUTERRA")
    print(_tr('synchronisation_botaneo_text_140'))
    print("=" * 60)

    resultat_miflora = await synchroniser_miflora()

    # Petite pause avant Netatmo.
    await asyncio.sleep(1)

    resultat_netatmo = synchroniser_netatmo()

    print()
    print("=" * 60)
    print(_tr('synchronisation_botaneo_text_154'))
    print("=" * 60)

    print(
        "🌿 Mi Flora : "
        + ("✅ OK" if resultat_miflora else _tr('synchronisation_botaneo_text_159'))
    )

    print(
        "🏠 Netatmo  : "
        + ("✅ OK" if resultat_netatmo else _tr('synchronisation_botaneo_text_159'))
    )

    print("=" * 60)

    if resultat_miflora and resultat_netatmo:
        print(_tr('synchronisation_botaneo_text_170'))
    else:
        print(_tr('synchronisation_botaneo_text_170_more'))


if __name__ == "__main__":
    from instance_botaneo import exiger_instance_unique
    exiger_instance_unique()
    asyncio.run(main())
