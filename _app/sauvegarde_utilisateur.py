"""Sauvegardes utilisateur Gruterra.

Deux usages sont distingués :
- export partageable : données utiles sans secrets ;
- sauvegarde complète privée : récupération après sinistre, avec configuration locale
  et secrets éventuels. Cette archive ne doit jamais être publiée.

Le module prépare la base technique sans restauration automatique destructive.
"""
from __future__ import annotations

from i18n import traduire, traduire_courant as _tr

import json
import os
import sqlite3
import tempfile
import time
from contextlib import closing
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DOSSIER_SAUVEGARDES = "_user_backups"
AVERTISSEMENT_SAUVEGARDE_PRIVEE = (
    traduire('sauvegarde_utilisateur_text_20', 'fr')
)

ELEMENTS_EXPORT_DONNEES = (
    "_app/plantes.db",
    "_historique",
    "_app/data",
)

ELEMENTS_SAUVEGARDE_COMPLETE = (
    "_app/plantes.db",
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


def lister_elements_sauvegarde(racine, mode="complete", *, db_path=None, config_dir=None, data_dir=None) -> list[ElementSauvegarde]:
    racine = Path(racine)
    if mode == "donnees":
        elements = ELEMENTS_EXPORT_DONNEES
        prives = set()
    elif mode == "complete":
        elements = ELEMENTS_SAUVEGARDE_COMPLETE + FICHIERS_OPTIONNELS_COMPLETS
        prives = {"_config", "discord_bot/.env"}
    else:
        raise ValueError(_tr('sauvegarde_utilisateur_text_69'))

    resultat = []
    for relatif in elements:
        chemin = _source(racine, relatif, db_path, config_dir, data_dir)
        resultat.append(
            ElementSauvegarde(
                chemin=relatif,
                existe=chemin.exists(),
                type=_type_chemin(chemin),
                prive=relatif in prives or relatif.startswith("_config/"),
            )
        )
    return resultat


def construire_manifest_sauvegarde(racine, mode="complete", *, db_path=None, config_dir=None, data_dir=None) -> dict:
    elements = lister_elements_sauvegarde(racine, mode=mode, db_path=db_path, config_dir=config_dir, data_dir=data_dir)
    contient_prive = any(item.prive and item.existe for item in elements)
    return {
        "format": "gruterra-user-backup-v1",
        "mode": mode,
        "base_active_archive": "_app/plantes.db",
        "methode_sqlite": "sqlite-backup",
        "cree_le": datetime.now().isoformat(timespec="seconds"),
        "contient_elements_prives": contient_prive,
        "avertissement": _tr('sauvegarde_utilisateur_text_20') if mode == "complete" else _tr('sauvegarde_utilisateur_text_93'),
        "elements": [item.__dict__ for item in elements],
        "restauration_automatique": False,
    }



def formater_rapport_sauvegarde(manifest: dict) -> str:
    """Retourne un rapport court et copiable pour l'utilisateur."""

    mode = manifest.get("mode", _tr('interface_text_1854'))
    cree_le = manifest.get("cree_le", _tr('sauvegarde_utilisateur_text_104'))
    elements = manifest.get("elements", [])
    presents = [item.get("chemin") for item in elements if item.get("existe")]
    absents = [item.get("chemin") for item in elements if not item.get("existe")]
    lignes = [
        _tr('sauvegarde_utilisateur_text_109'),
        _tr('sauvegarde_utilisateur_text_110').format(v0=cree_le),
        _tr('sauvegarde_utilisateur_text_111').format(v0=_tr('sauvegarde_utilisateur_text_111_more') if mode == 'complete' else _tr('sauvegarde_utilisateur_text_111_more_more')),
        _tr('sauvegarde_utilisateur_text_112').format(v0=_tr('botaneo_update_text_346') if manifest.get('contient_elements_prives') else _tr('botaneo_update_text_346_more')),
        _tr('sauvegarde_utilisateur_text_113_more').format(v0=', '.join(presents) if presents else _tr('sauvegarde_utilisateur_text_113')),
    ]
    if absents:
        lignes.append(_tr('sauvegarde_utilisateur_text_116').format(v0=', '.join(absents)))
    avertissement = manifest.get("avertissement")
    if avertissement:
        lignes.append(_tr('sauvegarde_utilisateur_text_119').format(v0=avertissement))
    return "\n".join(lignes)


def _base_active(racine, db_path=None):
    return Path(db_path if db_path is not None else
                os.environ.get("BOTANEO_DB_PATH", Path(racine) / "_app" / "plantes.db"))


def _source(racine, relatif, db_path, config_dir, data_dir):
    if relatif == "_app/plantes.db":
        return _base_active(racine, db_path)
    if relatif == "_config":
        return Path(config_dir) if config_dir is not None else Path(os.environ.get("BOTANEO_CONFIG_DIR", Path(racine) / "_config"))
    if relatif == "_app/data":
        return Path(data_dir) if data_dir is not None else Path(os.environ.get("BOTANEO_DATA_DIR", Path(racine) / "_app/data"))
    return Path(racine) / relatif


def _ajouter_source(zipf, source, nom, temporaire, *, force_sqlite=False):
    # SQLite backup includes committed WAL pages without copying live sidecars.
    if not force_sqlite and source.name.endswith(("-wal", "-shm", "-journal")):
        return
    if force_sqlite or source.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        copie = temporaire / "snapshot.sqlite3"
        if copie.exists():
            copie.unlink()
        with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as entree:
            with closing(sqlite3.connect(copie)) as sortie:
                deadline = time.monotonic() + 30
                def progress(status, remaining, total):
                    if time.monotonic() > deadline:
                        raise TimeoutError("SQLite snapshot timed out")
                entree.backup(sortie, pages=256, progress=progress)
                if sortie.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise sqlite3.DatabaseError("SQLite integrity check failed")
        zipf.write(copie, nom)
    else:
        zipf.write(source, nom)


def creer_sauvegarde_utilisateur(racine, mode="complete", destination=None, *, db_path=None, config_dir=None, data_dir=None):
    """Private, unencrypted ZIP; SQLite files are consistent snapshots.

    No restoration or changes to the source databases are performed.
    A missing active database is an error, even if a legacy root DB exists.
    """
    racine = Path(racine)
    base = _base_active(racine, db_path)
    if not base.is_file():
        raise FileNotFoundError("Active Gruterra database is missing")
    manifest = construire_manifest_sauvegarde(racine, mode=mode, db_path=base, config_dir=config_dir, data_dir=data_dir)
    dossier = Path(destination) if destination else racine / DOSSIER_SAUVEGARDES
    dossier.mkdir(parents=True, exist_ok=True)
    suffixe = "complete_privee" if mode == "complete" else "donnees"
    nom = f"Gruterra_Backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}_{suffixe}.zip"
    archive = dossier / nom
    with tempfile.TemporaryDirectory(prefix="gruterra-backup-", dir=dossier) as temp:
        temp = Path(temp)
        brouillon = temp / "archive.partial"
        with zipfile.ZipFile(brouillon, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("MANIFEST_GRUTERRA_BACKUP.json",
                          json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            for item in manifest["elements"]:
                if not item["existe"]:
                    continue
                relatif = item["chemin"]
                source = _source(racine, relatif, base, config_dir, data_dir)
                if source.is_file():
                    _ajouter_source(zipf, source, relatif, temp, force_sqlite=relatif == "_app/plantes.db")
                elif source.is_dir():
                    for fichier in source.rglob("*"):
                        if fichier.is_file() and fichier.resolve() != base.resolve():
                            parts = fichier.relative_to(source).parts
                            if DOSSIER_SAUVEGARDES in parts:
                                continue
                            if mode == "donnees" and relatif == "_app/data" and any(part in {"config", "_config"} for part in parts[:-1]):
                                continue
                            # Never recursively include the archive being built.
                            if fichier.resolve().is_relative_to(dossier.resolve()):
                                continue
                            private_config = _source(racine, "_config", base, config_dir, data_dir).resolve()
                            if relatif != "_config" and fichier.resolve().is_relative_to(private_config):
                                continue
                            archive_name = (Path(relatif) / fichier.relative_to(source)).as_posix()
                            _ajouter_source(zipf, fichier, archive_name, temp)
        with brouillon.open('r+b') as stream:
            os.fsync(stream.fileno())
        brouillon.replace(archive)
    return archive
