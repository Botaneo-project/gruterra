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
    print("🌿 ÉTAT DE BOTANEO")
    print("=" * 55)

    if not plantes:
        print("❌ Aucune plante enregistrée.")
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
            print(f"   Espèce      : {espece}")
            print(f"   Emplacement : {emplacement}")
            print(f"   Zone        : {zone}")

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
                        f"   📡 Capteur : {nom_capteur}"
                    )
                    print(
                        f"      Adresse : {adresse}"
                    )

            else:
                print("   📡 Aucun capteur actif")


def afficher_netatmo():
    """
    Actualise et affiche les données Netatmo.
    """

    print()
    print("=" * 55)
    print("🌦️ ACTUALISATION NETATMO")
    print("=" * 55)

    try:

        donnees = recuperer_netatmo()

        if not donnees:
            print("❌ Aucune donnée Netatmo.")
            return

        print()
        print("✅ Données Netatmo récupérées.")

        afficher_resultat(donnees)

    except Exception as e:

        print()
        message = str(e)

        if "503" in message:
            print("⚠️ Netatmo est temporairement indisponible.")
            print("   Les serveurs Netatmo ont refusé la requête.")
            print("   Réessayez dans quelques minutes.")
        else:
            print(
                f"❌ Erreur Netatmo : "
                f"{type(e).__name__}"
            )
            print(
                f"   Message : {message}"
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
        print("🌿 BOTANEO")
        print("=" * 55)
        print()
        print("1. 📊 Afficher l'état")
        print("2. 📡 Synchroniser les capteurs")
        print("3. 🌦️ Actualiser Netatmo")
        print("4. ❌ Quitter")
        print()

        choix = input("Votre choix : ").strip()

        if choix == "1":

            afficher_etat()

        elif choix == "2":

            synchroniser()

        elif choix == "3":

            afficher_netatmo()

        elif choix == "4":

            print()
            print("👋 Fermeture de Botaneo.")
            break

        else:

            print()
            print("❌ Choix invalide.")


if __name__ == "__main__":
    from instance_botaneo import exiger_instance_unique
    exiger_instance_unique()

    lancer_synchronisation_automatique()

    menu()
