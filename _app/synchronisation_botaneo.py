import asyncio

import database
from capteurs.miflora import lire_mesure
from capteurs.netatmo import recuperer_netatmo



async def synchroniser_miflora():
    print()
    print("=" * 60)
    print("🌿 BOTANEO - SYNCHRONISATION MI FLORA")
    print("=" * 60)

    capteurs = database.get_capteurs()

    if not capteurs:
        print("❌ Aucun capteur Mi Flora dans la base.")
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
        print(f"🌱 Plante    : {nom_plante}")
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
            print("✅ MESURE MI FLORA")
            print(f"   Température  : {temperature:.1f} °C")
            print(f"   Humidité     : {humidite} %")
            print(f"   Luminosité   : {luminosite} lux")
            print(f"   Conductivité : {conductivite} µS/cm")
            print("💾 Enregistrée dans plantes.db")

            succes = True

        except Exception as erreur:
            print()
            print(f"❌ Erreur Mi Flora : {erreur}")

    return succes


def synchroniser_netatmo():
    print()
    print("=" * 60)
    print("🏠 BOTANEO - SYNCHRONISATION NETATMO")
    print("=" * 60)

    try:
        stations = recuperer_netatmo()

        print()
        print(f"📡 {len(stations)} station(s) trouvée(s)")

        for station in stations:
            print()
            print(f"🏠 {station['nom']}")

            mesures = station["mesures"]

            if mesures["temperature"] is not None:
                print(
                    f"   🌡️ Température : "
                    f"{mesures['temperature']} °C"
                )

            if mesures["humidite"] is not None:
                print(
                    f"   💧 Humidité    : "
                    f"{mesures['humidite']} %"
                )

            for module in station["modules"]:
                print()
                print(f"   📦 Module : {module['nom']}")

                mesures = module["mesures"]

                if mesures["temperature"] is not None:
                    print(
                        f"      🌡️ Température : "
                        f"{mesures['temperature']} °C"
                    )

                if mesures["humidite"] is not None:
                    print(
                        f"      💧 Humidité    : "
                        f"{mesures['humidite']} %"
                    )

        print()
        print("✅ Netatmo synchronisé")
        return True

    except Exception as erreur:
        print()
        print(f"❌ Erreur Netatmo : {erreur}")
        return False


async def main():

    print()
    print("=" * 60)
    print("🌿 BOTANEO")
    print("SYNCHRONISATION GLOBALE")
    print("=" * 60)

    resultat_miflora = await synchroniser_miflora()

    # Petite pause avant Netatmo.
    await asyncio.sleep(1)

    resultat_netatmo = synchroniser_netatmo()

    print()
    print("=" * 60)
    print("📊 RÉSULTAT GLOBAL")
    print("=" * 60)

    print(
        "🌿 Mi Flora : "
        + ("✅ OK" if resultat_miflora else "❌ ÉCHEC")
    )

    print(
        "🏠 Netatmo  : "
        + ("✅ OK" if resultat_netatmo else "❌ ÉCHEC")
    )

    print("=" * 60)

    if resultat_miflora and resultat_netatmo:
        print("🎉 SYNCHRONISATION BOTANEO RÉUSSIE")
    else:
        print("⚠️ SYNCHRONISATION PARTIELLE")


if __name__ == "__main__":
    from instance_botaneo import exiger_instance_unique
    exiger_instance_unique()
    asyncio.run(main())
