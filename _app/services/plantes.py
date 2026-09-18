import database


EMPLACEMENTS_VALIDES = (
    "Intérieur",
    "Extérieur"
)


def lister_plantes():
    """Retourne la liste des plantes."""
    return database.get_plantes()


def obtenir_plante(plante_id):
    """Retourne une plante à partir de son identifiant."""
    return database.get_plante(plante_id)


def ajouter_plante(
    nom,
    espece,
    emplacement=None,
    zone=None
):
    """Ajoute une plante après validation des données."""

    nom = nom.strip()
    espece = espece.strip()

    if not nom:
        raise ValueError("Le nom de la plante est obligatoire.")

    if not espece:
        raise ValueError("L'espèce de la plante est obligatoire.")

    if emplacement:
        emplacement = emplacement.strip()

        if emplacement not in EMPLACEMENTS_VALIDES:
            raise ValueError(
                "L'emplacement doit être 'Intérieur' ou 'Extérieur'."
            )

    if zone:
        zone = zone.strip()

    return database.ajouter_plante(
        nom,
        espece,
        emplacement,
        zone
    )


def modifier_plante(
    plante_id,
    nom,
    espece,
    emplacement=None,
    zone=None
):
    """Modifie une plante après validation des données."""

    nom = nom.strip()
    espece = espece.strip()

    if not nom:
        raise ValueError("Le nom de la plante est obligatoire.")

    if not espece:
        raise ValueError("L'espèce de la plante est obligatoire.")

    if emplacement:
        emplacement = emplacement.strip()

        if emplacement not in EMPLACEMENTS_VALIDES:
            raise ValueError(
                "L'emplacement doit être 'Intérieur' ou 'Extérieur'."
            )

    if zone:
        zone = zone.strip()

    database.modifier_plante(
        plante_id,
        nom,
        espece,
        emplacement,
        zone
    )


def supprimer_plante(plante_id):
    """Supprime une plante."""

    plante = database.get_plante(plante_id)

    if plante is None:
        raise ValueError("La plante n'existe pas.")

    database.supprimer_plante(plante_id)