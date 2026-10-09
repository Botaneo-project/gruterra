
from i18n import traduire_courant as _tr
import asyncio
import threading

from database import get_plantes
from services.capteurs import lister_capteurs
from services.synchronisation import synchroniser_tous_les_capteurs
from capteurs.netatmo import recuperer_netatmo, afficher_resultat


def synchronisation_automatique():
    """
    Lance la synchronisation automatique en arrière-plan.

    La synchronisation est silencieuse afin de ne pas perturber
    l'affichage du menu principal.
    """

    try:
        asyncio.run(
            synchroniser_tous_les_capteurs(
                silencieux=True
            )
        )

    except Exception:
        # Une erreur de synchronisation automatique ne doit pas
        # arrêter l'application principale.
        pass


def lancer_synchronisation_automatique():
    """
    Lance la synchronisation automatique dans un thread séparé.
    """

    thread = threading.Thread(
        target=synchronisation_automatique,
        daemon=True
    )

    thread.start()


def afficher_etat():
    """
    Affiche l'état actuel des plantes et des capteurs.
    """

    plantes = get_plantes()
    capteurs = lister_capteurs()

    print()
    print("=" * 55)
    print(_tr('app_text_54'))
    print("=" * 55)

    if not plantes:
        print(_tr('app_text_58'))
    else:

        for plante in plantes:

            (
                plante_id,
                nom,
                espece,
                emplacement,
                zone
            ) = plante

            print()
            print(f"🌱 {nom}")
            print(_tr('app_text_73').format(v0=espece))
            print(_tr('app_text_76').format(v0=emplacement))
            print(_tr('app_text_77').format(v0=zone))

            capteurs_plante = [
                capteur
                for capteur in capteurs
                if capteur[3] == plante_id
                and capteur[8]
            ]

            if capteurs_plante:

                for capteur in capteurs_plante:

                    (
                        capteur_id,
                        nom_capteur,
                        adresse,
                        plante_id_capteur,
                        nom_plante,
                        espece_capteur,
                        emplacement_capteur,
                        zone_capteur,
                        actif,
                        date_fin
                    ) = capteur

                    print(
                        _tr('app_text_104').format(v0=nom_capteur)
                    )
                    print(
                        _tr('app_text_107').format(v0=adresse)
                    )

            else:
                print(_tr('app_text_109'))


def afficher_netatmo():
    """
    Actualise et affiche les données Netatmo.
    """

    print()
    print("=" * 55)
    print(_tr('app_text_121'))
    print("=" * 55)

    try:

        donnees = recuperer_netatmo()

        if not donnees:
            print(_tr('app_text_127'))
            return

        print()
        print(_tr('app_text_131'))

        afficher_resultat(donnees)

    except Exception as e:

        print()
        message = str(e)

        if "503" in message:
            print(_tr('app_text_141'))
            print(_tr('app_text_142'))
            print(_tr('app_text_143'))
        else:
            print(
                _tr('app_text_146').format(v0=type(e).__name__)
            )
            print(
                _tr('app_text_151').format(v0=message)
            )


def synchroniser():
    """
    Synchronisation manuelle avec affichage détaillé.
    """

    asyncio.run(
        synchroniser_tous_les_capteurs(
            silencieux=False
        )
    )


def menu():

    while True:

        print()
        print("=" * 55)
        print("🌿 GRUTERRA")
        print("=" * 55)
        print()
        print(_tr('app_text_175'))
        print(_tr('app_text_176'))
        print(_tr('cli_refresh_netatmo'))
        print(_tr('cli_quit'))
        print()

        choix = input(_tr('app_text_182')).strip()

        if choix == "1":

            afficher_etat()

        elif choix == "2":

            synchroniser()

        elif choix == "3":

            afficher_netatmo()

        elif choix == "4":

            print()
            print(_tr('app_text_198'))
            break

        else:

            print()
            print(_tr('cli_invalid_choice'))


if __name__ == "__main__":
    from instance_botaneo import exiger_instance_unique
    exiger_instance_unique()

    lancer_synchronisation_automatique()

    menu()
