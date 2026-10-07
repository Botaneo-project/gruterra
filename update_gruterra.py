"""Assistant de mise à jour Gruterra.

Par défaut, ce script vérifie seulement l'état de mise à jour. Avec ``--apply``,
il peut appliquer une archive officielle déclarée dans ``version_manifest.json``.
L'application réelle reste protégée : archive obligatoire, SHA256 obligatoire,
sauvegarde locale avant remplacement et conservation des données utilisateur.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

RACINE = Path(__file__).resolve().parent
APP_DIR = RACINE / "_app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import botaneo_update  # noqa: E402

DONNEES_A_PRESERVER = {
    "plantes.db",
    "_config",
    "_security_backups",
    "_historique",
    "_app/data",
    "discord_bot/.env",
    ".git",
}

FICHIERS_A_NE_PAS_REMPLACER = {
    "plantes.db",
    "netatmo_config.json",
}

DOSSIERS_IGNORES_ARCHIVE = {
    "__pycache__",
    ".git",
    ".github",
}

TIMEOUT_TELECHARGEMENT_SECONDES = 60


def configurer_sorties_utf8() -> None:
    """Évite les crashs UnicodeEncodeError dans les consoles Windows anciennes."""

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    for flux in (sys.stdout, sys.stderr):
        reconfigure = getattr(flux, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def safe_print(texte="") -> None:
    try:
        print(texte)
    except UnicodeEncodeError:
        print(str(texte).encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


def est_chemin_preserve(relatif: Path) -> bool:
    texte = relatif.as_posix()
    if texte in DONNEES_A_PRESERVER or texte in FICHIERS_A_NE_PAS_REMPLACER:
        return True
    return any(texte.startswith(prefix + "/") for prefix in DONNEES_A_PRESERVER)


def construire_message_validation(diagnostic: dict) -> str:
    version = diagnostic.get("version", {})
    lignes = [
        botaneo_update.formater_diagnostic_mise_a_jour(diagnostic),
        "",
        "Vérification avant installation :",
    ]

    archive_url = str(version.get("archive_url", "") or "").strip()
    sha256 = str(version.get("sha256", "") or "").strip()
    manifest_auto_update = bool(version.get("manifest_auto_update", False))

    if not manifest_auto_update:
        lignes.append("- installation depuis GitHub désactivée pour cette version")
    if not archive_url:
        lignes.append("- paquet de mise à jour absent des informations GitHub")
    if not sha256:
        lignes.append("- contrôle d’intégrité du paquet absent")

    statut_version = str(version.get("statut") or "").strip()
    if statut_version == "a_jour":
        lignes.append("- résultat : Gruterra est déjà à jour, aucune mise à jour normale à appliquer")
    elif statut_version == "version_locale_plus_recente":
        lignes.append("- résultat : la version locale est plus récente que la version distante, aucune mise à jour normale à appliquer")
    elif manifest_auto_update and archive_url and sha256 and diagnostic.get("statut_global") != "bloque":
        lignes.append("- tout est prêt ; l’installation peut être lancée après sauvegarde locale")
    else:
        lignes.append("- résultat : information seulement, aucune installation lancée")

    return "\n".join(lignes)


def valider_manifest_applicable(diagnostic: dict) -> tuple[bool, list[str]]:
    erreurs = []
    version = diagnostic.get("version", {})
    if diagnostic.get("statut_global") == "bloque":
        erreurs.append("installation bloquée : protections locales insuffisantes")
    statut_version = str(version.get("statut") or "").strip()
    if statut_version == "a_jour":
        erreurs.append("Gruterra est déjà à jour")
    elif statut_version == "version_locale_plus_recente":
        erreurs.append("version locale plus récente que la version distante")
    if not version.get("manifest_auto_update"):
        erreurs.append("installation depuis GitHub désactivée pour cette version")
    if not str(version.get("archive_url", "") or "").strip():
        erreurs.append("paquet de mise à jour absent des informations GitHub")
    sha256 = str(version.get("sha256", "") or "").strip().lower()
    if len(sha256) != 64 or any(car not in "0123456789abcdef" for car in sha256):
        erreurs.append("contrôle d’intégrité du paquet absent ou invalide")
    return not erreurs, erreurs


def telecharger_archive(url: str, destination: Path) -> None:
    requete = Request(str(url), headers={"User-Agent": "Gruterra-updater/1.0"})
    try:
        with urlopen(requete, timeout=TIMEOUT_TELECHARGEMENT_SECONDES) as reponse:
            with destination.open("wb") as fichier:
                shutil.copyfileobj(reponse, fichier)
    except (HTTPError, URLError, TimeoutError, OSError) as erreur:
        raise RuntimeError(f"Téléchargement impossible : {erreur}") from erreur


def calculer_sha256(chemin: Path) -> str:
    empreinte = hashlib.sha256()
    with chemin.open("rb") as fichier:
        for bloc in iter(lambda: fichier.read(1024 * 1024), b""):
            empreinte.update(bloc)
    return empreinte.hexdigest()


def verifier_sha256(chemin: Path, attendu: str) -> None:
    obtenu = calculer_sha256(chemin)
    if obtenu.lower() != attendu.lower():
        raise RuntimeError(f"SHA256 invalide : attendu {attendu}, obtenu {obtenu}")


def trouver_racine_archive(dossier_extrait: Path) -> Path:
    enfants = [item for item in dossier_extrait.iterdir() if item.name not in {"__MACOSX"}]
    if len(enfants) == 1 and enfants[0].is_dir():
        return enfants[0]
    return dossier_extrait


def lister_fichiers_programme(source: Path) -> list[Path]:
    fichiers = []
    for chemin in source.rglob("*"):
        if not chemin.is_file():
            continue
        relatif = chemin.relative_to(source)
        if any(part in DOSSIERS_IGNORES_ARCHIVE for part in relatif.parts):
            continue
        if est_chemin_preserve(relatif):
            continue
        fichiers.append(relatif)
    return sorted(fichiers)


def sauvegarder_programme(racine: Path, fichiers: list[Path]) -> Path:
    dossier_backup = racine / "_security_backups"
    dossier_backup.mkdir(exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = dossier_backup / f"gruterra-pre-update-{horodatage}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for relatif in fichiers:
            chemin = racine / relatif
            if chemin.exists() and chemin.is_file():
                zipf.write(chemin, relatif.as_posix())
    return archive


def appliquer_fichiers(source: Path, racine: Path, fichiers: list[Path]) -> int:
    compteur = 0
    for relatif in fichiers:
        destination = racine / relatif
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relatif, destination)
        compteur += 1
    return compteur


def appliquer_mise_a_jour(diagnostic: dict, racine: Path, dry_run: bool = True) -> dict:
    ok, erreurs = valider_manifest_applicable(diagnostic)
    if not ok:
        return {"ok": False, "applique": False, "erreurs": erreurs, "message": "Installation refusée."}

    version = diagnostic.get("version", {})
    archive_url = str(version.get("archive_url", "")).strip()
    sha256 = str(version.get("sha256", "")).strip()

    with tempfile.TemporaryDirectory(prefix="gruterra-update-") as tmp:
        tmp_path = Path(tmp)
        archive = tmp_path / "gruterra-update.zip"
        telecharger_archive(archive_url, archive)
        verifier_sha256(archive, sha256)
        extraction = tmp_path / "extracted"
        extraction.mkdir()
        with zipfile.ZipFile(archive) as zipf:
            zipf.extractall(extraction)
        source = trouver_racine_archive(extraction)
        fichiers = lister_fichiers_programme(source)
        if not fichiers:
            return {"ok": False, "applique": False, "erreurs": ["paquet téléchargé sans fichier Gruterra exploitable"], "message": "Installation refusée."}
        if dry_run:
            return {
                "ok": True,
                "applique": False,
                "fichiers": len(fichiers),
                "message": f"Vérification OK : {len(fichiers)} fichier(s) du programme seraient mis à jour.",
            }
        backup = sauvegarder_programme(racine, fichiers)
        copies = appliquer_fichiers(source, racine, fichiers)
        return {
            "ok": True,
            "applique": True,
            "fichiers": copies,
            "backup": str(backup),
            "message": f"Mise à jour appliquée : {copies} fichier(s) du programme remplacé(s). Sauvegarde créée : {backup}",
        }


def main(argv: list[str] | None = None) -> int:
    configurer_sorties_utf8()
    parser = argparse.ArgumentParser(description="Vérifie ou applique une mise à jour Gruterra en préservant les données locales.")
    parser.add_argument("--local", action="store_true", help="utilise seulement le manifeste local")
    parser.add_argument("--json", action="store_true", help="affiche le diagnostic JSON")
    parser.add_argument("--apply", action="store_true", help="applique l'archive officielle après contrôle SHA256 et sauvegarde locale")
    parser.add_argument("--dry-run", action="store_true", help="simule l'application de l'archive officielle sans remplacer les fichiers")
    args = parser.parse_args(argv)

    diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(
        RACINE,
        verifier_distant=not args.local,
    )

    if args.json:
        safe_print(botaneo_update.exporter_diagnostic_mise_a_jour_json(diagnostic))
        return 0 if diagnostic.get("statut_global") != "bloque" else 2

    safe_print(construire_message_validation(diagnostic))

    if args.apply or args.dry_run:
        safe_print("")
        safe_print("Installation demandée :" if args.apply else "Vérification sans installation demandée :")
        try:
            resultat = appliquer_mise_a_jour(diagnostic, RACINE, dry_run=not args.apply)
        except RuntimeError as erreur:
            safe_print(f"- échec : {erreur}")
            return 3
        safe_print(f"- {resultat.get('message')}")
        for erreur in resultat.get("erreurs", []):
            safe_print(f"- {erreur}")
        return 0 if resultat.get("ok") else 3

    return 0 if diagnostic.get("statut_global") != "bloque" else 2


if __name__ == "__main__":
    raise SystemExit(main())
