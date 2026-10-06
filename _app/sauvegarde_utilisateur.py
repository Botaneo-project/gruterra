"""Sauvegardes utilisateur Gruterra.

Deux usages sont distingués :
- export partageable : données utiles sans secrets ;
- sauvegarde complète privée : récupération après sinistre, avec configuration locale
  et secrets éventuels. Cette archive ne doit jamais être publiée.

Le module prépare la base technique sans restauration automatique destructive.
"""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DOSSIER_SAUVEGARDES = "_user_backups"
AVERTISSEMENT_SAUVEGARDE_PRIVEE = (
    "Cette sauvegarde complète peut contenir des informations privées : base réelle, "
    "configuration locale, tokens, identifiants techniques et secrets. Ne la partagez "
    "pas et ne la publiez jamais sur GitHub."
)

ELEMENTS_EXPORT_DONNEES = (
    "plantes.db",
    "_historique",
    "_app/data",
)

ELEMENTS_SAUVEGARDE_COMPLETE = (
    "plantes.db",
    "_config",
    "_historique",
    "_app/data",
    "_security_backups",
)

FICHIERS_OPTIONNELS_COMPLETS = (
    "discord_bot/.env",
)


@dataclass(frozen=True)
class ElementSauvegarde:
    chemin: str
    existe: bool
    type: str
    prive: bool


def _type_chemin(path: Path) -> str:
    if path.is_dir():
        return "dossier"
    if path.is_file():
        return "fichier"
    return "absent"


def lister_elements_sauvegarde(racine, mode="complete") -> list[ElementSauvegarde]:
    racine = Path(racine)
    if mode == "donnees":
        elements = ELEMENTS_EXPORT_DONNEES
        prives = set()
    elif mode == "complete":
        elements = ELEMENTS_SAUVEGARDE_COMPLETE + FICHIERS_OPTIONNELS_COMPLETS
        prives = {"_config", "discord_bot/.env"}
    else:
        raise ValueError("mode de sauvegarde inconnu")

    resultat = []
    for relatif in elements:
        chemin = racine / relatif
        resultat.append(
            ElementSauvegarde(
                chemin=relatif,
                existe=chemin.exists(),
                type=_type_chemin(chemin),
                prive=relatif in prives or relatif.startswith("_config/"),
            )
        )
    return resultat


def construire_manifest_sauvegarde(racine, mode="complete") -> dict:
    elements = lister_elements_sauvegarde(racine, mode=mode)
    contient_prive = any(item.prive and item.existe for item in elements)
    return {
        "format": "gruterra-user-backup-v1",
        "mode": mode,
        "cree_le": datetime.now().isoformat(timespec="seconds"),
        "contient_elements_prives": contient_prive,
        "avertissement": AVERTISSEMENT_SAUVEGARDE_PRIVEE if mode == "complete" else "Export de données destiné au partage ou au diagnostic, sans configuration privée volontaire.",
        "elements": [item.__dict__ for item in elements],
        "restauration_automatique": False,
    }



def formater_rapport_sauvegarde(manifest: dict) -> str:
    """Retourne un rapport court et copiable pour l'utilisateur."""

    mode = manifest.get("mode", "inconnu")
    cree_le = manifest.get("cree_le", "horaire inconnu")
    elements = manifest.get("elements", [])
    presents = [item.get("chemin") for item in elements if item.get("existe")]
    absents = [item.get("chemin") for item in elements if not item.get("existe")]
    lignes = [
        "Rapport de sauvegarde Gruterra",
        f"Horaire : {cree_le}",
        f"Mode : {mode}",
        f"Contient des éléments privés : {'oui' if manifest.get('contient_elements_prives') else 'non'}",
        f"Éléments inclus : {', '.join(presents) if presents else 'aucun'}",
    ]
    if absents:
        lignes.append(f"Éléments absents : {', '.join(absents)}")
    avertissement = manifest.get("avertissement")
    if avertissement:
        lignes.append(f"Avertissement : {avertissement}")
    return "\n".join(lignes)


def _ajouter_fichier(zipf: zipfile.ZipFile, racine: Path, relatif: Path) -> None:
    chemin = racine / relatif
    if chemin.is_file():
        zipf.write(chemin, relatif.as_posix())


def _ajouter_dossier(zipf: zipfile.ZipFile, racine: Path, relatif: Path) -> None:
    dossier = racine / relatif
    if not dossier.is_dir():
        return
    for chemin in dossier.rglob("*"):
        if chemin.is_file():
            zipf.write(chemin, chemin.relative_to(racine).as_posix())


def creer_sauvegarde_utilisateur(racine, mode="complete", destination=None) -> Path:
    """Crée une archive ZIP locale.

    La restauration n'est pas effectuée ici. Pour le mode complet, l'archive peut
    contenir des secrets et doit rester locale. Aucun chiffrement n'est appliqué
    par cette première version.
    """

    racine = Path(racine)
    manifest = construire_manifest_sauvegarde(racine, mode=mode)
    dossier = Path(destination) if destination else racine / DOSSIER_SAUVEGARDES
    dossier.mkdir(parents=True, exist_ok=True)
    suffixe = "complete_privee" if mode == "complete" else "donnees"
    nom = f"Gruterra_Backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{suffixe}.zip"
    archive = dossier / nom

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        contenu_manifest = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        zipf.writestr("MANIFEST_GRUTERRA_BACKUP.json", contenu_manifest)
        for item in manifest["elements"]:
            if not item["existe"]:
                continue
            relatif = Path(item["chemin"])
            if item["type"] == "fichier":
                _ajouter_fichier(zipf, racine, relatif)
            elif item["type"] == "dossier":
                _ajouter_dossier(zipf, racine, relatif)
    return archive
