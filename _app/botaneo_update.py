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
        "statut_version": construire_statut_version("0.1.0-dev"),
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
        plan.get("statut_version", {}).get("message", "Vérification de version non configurée."),
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


def normaliser_version(version):
    texte = str(version or "").strip().lower()
    if texte.startswith("v"):
        texte = texte[1:]
    suffixe_dev = "dev" in texte or "alpha" in texte or "beta" in texte or "rc" in texte
    principal = texte.split("-")[0]
    morceaux = []
    for part in principal.split("."):
        try:
            morceaux.append(int(part))
        except ValueError:
            chiffres = "".join(car for car in part if car.isdigit())
            morceaux.append(int(chiffres) if chiffres else 0)
    while len(morceaux) < 3:
        morceaux.append(0)
    return tuple(morceaux[:3]), suffixe_dev


def comparer_versions(version_locale, version_distante):
    locale, locale_dev = normaliser_version(version_locale)
    distante, distante_dev = normaliser_version(version_distante)
    if distante > locale:
        statut = "mise_a_jour_disponible"
    elif distante == locale and locale_dev and not distante_dev:
        statut = "version_stable_disponible"
    elif distante == locale:
        statut = "a_jour"
    else:
        statut = "locale_plus_recente"
    return {
        "version_locale": str(version_locale),
        "version_distante": str(version_distante),
        "statut": statut,
        "application_autorisee": False,
        "message": message_version(statut, version_locale, version_distante),
    }


def message_version(statut, version_locale, version_distante):
    if statut == "mise_a_jour_disponible":
        return f"Version distante {version_distante} disponible ; sauvegarde et validation nécessaires avant application."
    if statut == "version_stable_disponible":
        return f"Version stable {version_distante} disponible pour remplacer la version locale {version_locale}."
    if statut == "a_jour":
        return f"Version locale {version_locale} à jour."
    return f"Version locale {version_locale} plus récente que la version distante {version_distante}."


def construire_statut_version(version_locale, version_distante=None):
    if not version_distante:
        return {
            "version_locale": str(version_locale),
            "version_distante": None,
            "statut": "verification_non_configuree",
            "application_autorisee": False,
            "message": "Vérification distante non configurée ; aucune mise à jour automatique active.",
        }
    return comparer_versions(version_locale, version_distante)
