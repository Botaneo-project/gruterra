import database


def lister_capteurs():
    """Retourne tous les capteurs avec leur plante associée."""
    return database.get_capteurs()


def obtenir_capteurs_plante(plante_id):
    """Retourne les capteurs associés à une plante."""

    capteurs = database.get_capteurs()

    return [
        capteur
        for capteur in capteurs
        if capteur[3] == plante_id
    ]


def ajouter_capteur(
    nom,
    adresse_ble,
    plante_id
):
    """Ajoute un capteur."""

    nom = nom.strip()

    if not nom:
        raise ValueError("Le nom du capteur est obligatoire.")

    return database.ajouter_capteur(
        nom,
        adresse_ble,
        plante_id
    )