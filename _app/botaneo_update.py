"""Préparation des mises à jour Botaneo, sans application automatique.

Ce module ne télécharge rien et ne modifie pas le programme. Il sert à préparer
un futur auto-upgrade en listant clairement ce qui doit être préservé avant
toute mise à jour : base locale, configuration privée, secrets, préférences et
sauvegardes.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ELEMENTS_PERSONNELS = (
    "plantes.db",
    "_config",
    "_security_backups",
    "_historique",
    "_app/data",
)

FICHIERS_CONFIG_EXEMPLE = (
    "botaneo.local.example.json",
    "netatmo_config.example.json",
    "email.local.example.json",
)


@dataclass(frozen=True)
class ElementPersonnel:
    chemin: str
    existe: bool
    type: str
    raison: str


def detecter_element_personnel(racine, chemin_relatif) -> ElementPersonnel:
    racine = Path(racine)
    chemin = racine / chemin_relatif
    if chemin.is_dir():
        type_element = "dossier"
    elif chemin.is_file():
        type_element = "fichier"
    else:
        type_element = "absent"
    raisons = {
        "plantes.db": "base SQLite personnelle",
        "_config": "configuration privée, tokens et secrets locaux",
        "_security_backups": "sauvegardes locales de sécurité",
        "_historique": "anciens fichiers conservés localement",
        "_app/data": "suivis locaux, caches et états runtime",
    }
    return ElementPersonnel(
        chemin=chemin_relatif,
        existe=chemin.exists(),
        type=type_element,
        raison=raisons.get(chemin_relatif, "donnée locale à préserver"),
    )


def construire_plan_mise_a_jour(racine) -> dict:
    """Construit un plan de mise à jour en lecture seule."""

    racine = Path(racine)
    elements = [detecter_element_personnel(racine, item) for item in ELEMENTS_PERSONNELS]
    exemples = [str(item) for item in FICHIERS_CONFIG_EXEMPLE if (racine / item).exists()]
    return {
        "mode": "préparation uniquement",
        "racine": str(racine),
        "elements_personnels": elements,
        "fichiers_exemple": exemples,
        "actions_avant_update": [
            "fermer Botaneo",
            "lancer une sauvegarde locale",
            "vérifier que la base SQLite personnelle est sauvegardée",
            "préserver _config et les fichiers *.local.json",
            "appliquer la mise à jour seulement après validation explicite",
        ],
        "actions_interdites_sans_validation": [
            "supprimer la base réelle",
            "écraser _config",
            "supprimer les sauvegardes locales",
            "lancer un git reset ou un nettoyage destructeur",
        ],
    }


def formater_plan_mise_a_jour(plan) -> str:
    lignes = [
        "Plan de mise à jour Botaneo",
        f"Mode : {plan.get('mode', 'préparation')}",
        f"Racine : {plan.get('racine', 'inconnue')}",
        "",
        "Éléments personnels à préserver :",
    ]
    for element in plan.get("elements_personnels", []):
        etat = "présent" if element.existe else "absent"
        lignes.append(f"- {element.chemin} · {etat} · {element.raison}")
    lignes.extend(["", "Avant toute mise à jour :"])
    lignes.extend(f"- {action}" for action in plan.get("actions_avant_update", []))
    lignes.extend(["", "Interdit sans validation explicite :"])
    lignes.extend(f"- {action}" for action in plan.get("actions_interdites_sans_validation", []))
    return "\n".join(lignes)
