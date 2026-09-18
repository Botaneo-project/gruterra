import asyncio
from datetime import datetime

import database
import raspberry_sync
from capteurs.miflora import lire_mesure


async def synchroniser_capteur(capteur, silencieux=False):
    """
    Synchronise un capteur Mi Flora actif et enregistre sa mesure.

    silencieux=True :
        aucun affichage pendant la synchronisation automatique.

    silencieux=False :
        affichage détaillé pour une synchronisation manuelle.
    """

    (
        capteur_id,
        nom_capteur,
        adresse,
        plante_id,
        nom_plante,
        espece,
        emplacement,
        zone,
        actif,
        date_fin
    ) = capteur

    if not actif:
        if not silencieux:
            print(f"⏭️ Capteur ID {capteur_id} inactif — ignoré.")
        return None

    if raspberry_sync.owned(adresse):
        result = await asyncio.to_thread(raspberry_sync.synchronize)
        if not silencieux:
            print(result['message'])
        return result['ok']

    if not silencieux:
        print()
        print("=" * 45)
        print(f"🌿 Plante  : {nom_plante} ({espece})")
        print(f"📍 Lieu    : {emplacement} - {zone}")
        print(f"📡 Capteur : {nom_capteur}")
        print(f"🔗 Adresse : {adresse}")
        print("=" * 45)
        print("🔌 Connexion...")

    try:
        temperature, humidite, luminosite, conductivite, donnees_brutes = (
            await lire_mesure(
                adresse,
                silencieux=silencieux
            )
        )

        heure_mesure = datetime.now()

        if not silencieux:
            print("✅ Connecté !")
            print("📡 Lecture des mesures...")
            print()
            print("🌱 MESURES")
            print("-" * 30)
            print(f"🌡️ Température : {temperature:.1f} °C")
            print(f"💧 Humidité    : {humidite} %")
            print(f"☀️ Luminosité  : {luminosite} lux")
            print(f"🧪 Conductivité : {conductivite} µS/cm")
            print(
                f"🕐 Heure de mesure : "
                f"{heure_mesure.strftime('%d/%m/%Y %H:%M:%S')}"
            )

        database.enregistrer_mesure(
            capteur_id,
            heure_mesure.isoformat(timespec="seconds"),
            temperature,
            humidite,
            luminosite,
            conductivite,
            donnees_brutes
        )

        if not silencieux:
            print()
            print(
                f"💾 Mesure enregistrée — capteur ID {capteur_id}"
            )
            print("🔌 Déconnexion.")

        return True

    except Exception as e:
        if not silencieux:
            print()
            print(
                f"❌ Erreur avec ce capteur : "
                f"{type(e).__name__}"
            )
            print(f"   Message : {repr(e)}")

        return False


async def synchroniser_tous_les_capteurs(silencieux=False):
    """
    Synchronise tous les capteurs enregistrés.

    silencieux=True :
        utilisé par la synchronisation automatique.

    silencieux=False :
        utilisé par la synchronisation manuelle.
    """

    capteurs = database.get_capteurs()

    if not capteurs:
        if not silencieux:
            print("❌ Aucun capteur dans la base.")
        return

    if not silencieux:
        print()
        print("🌱 SYNCHRONISATION DES CAPTEURS")
        print("=" * 45)
        print(f"📊 {len(capteurs)} capteur(s) enregistré(s)")

    succes = 0
    echecs = 0
    ignores = 0

    for capteur in capteurs:

        resultat = await synchroniser_capteur(
            capteur,
            silencieux=silencieux
        )

        if resultat is True:
            succes += 1

        elif resultat is False:
            echecs += 1

        else:
            ignores += 1

        await asyncio.sleep(2)

    if not silencieux:
        print()
        print("=" * 45)
        print("📊 RÉSULTAT DE LA SYNCHRONISATION")
        print("=" * 45)
        print(f"✅ Réussites : {succes}")
        print(f"❌ Échecs    : {echecs}")
        print(f"⏭️ Ignorés   : {ignores}")
        print(f"📡 Total     : {len(capteurs)}")
        print("=" * 45)


async def main():
    await synchroniser_tous_les_capteurs()


if __name__ == "__main__":
    asyncio.run(main())