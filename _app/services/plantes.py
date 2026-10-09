
from i18n import traduire_courant as _tr
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
        raise ValueError(_tr('plant_name_required'))

    if not espece:
        raise ValueError(_tr('plantes_text_35'))

    if emplacement:
        emplacement = emplacement.strip()

        if emplacement not in EMPLACEMENTS_VALIDES:
            raise ValueError(
                _tr('plantes_text_42')
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
        raise ValueError(_tr('plant_name_required'))

    if not espece:
        raise ValueError(_tr('plantes_text_35'))

    if emplacement:
        emplacement = emplacement.strip()

        if emplacement not in EMPLACEMENTS_VALIDES:
            raise ValueError(
                _tr('plantes_text_42')
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
        raise ValueError(_tr('analyse_text_15'))

    database.supprimer_plante(plante_id)