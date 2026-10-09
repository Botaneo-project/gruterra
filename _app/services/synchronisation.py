
from i18n import traduire_courant as _tr
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
            print(_tr('synchronisation_text_35').format(v0=capteur_id))
        return None

    if raspberry_sync.owned(adresse):
        result = await asyncio.to_thread(raspberry_sync.synchronize)
        if not silencieux:
            print(result['message'])
        return result['ok']

    if not silencieux:
        print()
        print("=" * 45)
        print(_tr('synchronisation_text_47').format(v0=nom_plante, v1=espece))
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
            print(_tr('synchronisation_text_65'))
            print(_tr('synchronisation_text_66'))
            print()
            print(_tr('synchronisation_text_70_more'))
            print("-" * 30)
            print(_tr('synchronisation_text_70').format(v0=temperature))
            print(_tr('netatmo_text_946').format(v0=humidite))
            print(_tr('synchronisation_text_72').format(v0=luminosite))
            print(_tr('synchronisation_text_73').format(v0=conductivite))
            print(
                _tr('synchronisation_text_75').format(v0=heure_mesure.strftime('%d/%m/%Y %H:%M:%S'))
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
                _tr('synchronisation_text_92').format(v0=capteur_id)
            )
            print(_tr('synchronisation_text_94'))

        return True

    except Exception as e:
        if not silencieux:
            print()
            print(
                _tr('synchronisation_text_102').format(v0=type(e).__name__)
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
            print(_tr('synchronisation_text_125'))
        return

    if not silencieux:
        print()
        print(_tr('synchronisation_text_130'))
        print("=" * 45)
        print(_tr('synchronisation_text_132').format(v0=len(capteurs)))

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
        print(_tr('synchronisation_text_159'))
        print("=" * 45)
        print(_tr('synchronisation_text_161').format(v0=succes))
        print(_tr('synchronisation_text_162').format(v0=echecs))
        print(_tr('synchronisation_text_163').format(v0=ignores))
        print(f"📡 Total     : {len(capteurs)}")
        print("=" * 45)


async def main():
    await synchroniser_tous_les_capteurs()


if __name__ == "__main__":
    asyncio.run(main())