"""Prépare une archive de release Gruterra sans données privées.

Le script utilise uniquement les fichiers suivis par Git. Il crée une archive ZIP
locale et calcule son SHA256 pour renseigner ensuite ``version_manifest.json``
lors de la publication d'une release GitHub.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent
DIST_DIR = RACINE / "_dist"
MANIFEST = RACINE / "version_manifest.json"

FICHIERS_EXCLUS = {
    "version_manifest.json",
}

DOSSIERS_EXCLUS = {
    ".git",
    "__pycache__",
    "_dist",
}


def lancer_git(args: list[str]) -> str:
    resultat = subprocess.run(
        ["git", *args],
        cwd=RACINE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return resultat.stdout.strip()


def verifier_arbre_propre() -> None:
    statut = lancer_git(["status", "--short"])
    if statut:
        raise RuntimeError(
            "Le dossier Git contient des changements non validés. "
            "Commit ou annule les changements avant de préparer une archive officielle."
        )


def lire_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def lire_version() -> str:
    donnees = lire_manifest()
    version = str(donnees.get("version") or "").strip()
    if not version:
        raise RuntimeError("version_manifest.json ne contient pas de version exploitable.")
    return version


def lister_fichiers_suivis() -> list[Path]:
    sortie = lancer_git(["ls-files"])
    fichiers = []
    for ligne in sortie.splitlines():
        relatif = Path(ligne.strip())
        if not relatif.as_posix():
            continue
        if relatif.as_posix() in FICHIERS_EXCLUS:
            continue
        if any(part in DOSSIERS_EXCLUS for part in relatif.parts):
            continue
        chemin = RACINE / relatif
        if chemin.is_file():
            fichiers.append(relatif)
    return sorted(fichiers, key=lambda item: item.as_posix().lower())


def calculer_sha256(chemin: Path) -> str:
    empreinte = hashlib.sha256()
    with chemin.open("rb") as fichier:
        for bloc in iter(lambda: fichier.read(1024 * 1024), b""):
            empreinte.update(bloc)
    return empreinte.hexdigest()


def construire_archive(version: str, fichiers: list[Path]) -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    nom = f"gruterra-{version}.zip"
    archive = DIST_DIR / nom
    racine_archive = f"gruterra-{version}"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for relatif in fichiers:
            zipf.write(RACINE / relatif, f"{racine_archive}/{relatif.as_posix()}")
    return archive


def construire_release_url(version: str) -> str:
    return f"https://github.com/Botaneo-project/gruterra/releases/download/v{version}/gruterra-{version}.zip"


def ecrire_manifest_pret(version: str, sha256: str) -> Path:
    donnees = lire_manifest()
    donnees["archive_url"] = construire_release_url(version)
    donnees["sha256"] = sha256
    donnees["mise_a_jour_automatique"] = True
    chemin = DIST_DIR / f"version_manifest-{version}-ready.json"
    chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return chemin



MOTS_CLES_IMPORTANTS = (
    "update",
    "release",
    "raspberry",
    "historique",
    "analyse",
    "cycle",
    "discord",
    "netatmo",
    "secur",
    "schema",
    "base",
)

MOTS_CLES_TECHNIQUES = (
    "todo",
    "readme",
    "guide",
    "documenter",
    "doc",
    "typo",
)


def commits_depuis_dernier_tag() -> list[str]:
    try:
        dernier_tag = lancer_git(["describe", "--tags", "--abbrev=0"])
        plage = f"{dernier_tag}..HEAD"
        sortie = lancer_git(["log", "--pretty=format:%s", plage])
    except subprocess.CalledProcessError:
        sortie = lancer_git(["log", "--pretty=format:%s", "--max-count=40"])
    return [ligne.strip() for ligne in sortie.splitlines() if ligne.strip()]


def classer_commits(commits: list[str]) -> tuple[list[str], list[str]]:
    importants = []
    autres = []
    for commit in commits:
        normalise = commit.lower()
        cible = importants if any(mot in normalise for mot in MOTS_CLES_IMPORTANTS) else autres
        if any(mot in normalise for mot in MOTS_CLES_TECHNIQUES) and not any(mot in normalise for mot in MOTS_CLES_IMPORTANTS):
            cible = autres
        cible.append(commit)
    return importants, autres


def ecrire_changelog_release(version: str) -> Path:
    commits = commits_depuis_dernier_tag()
    importants, autres = classer_commits(commits)
    chemin = DIST_DIR / f"gruterra-{version}-changelog.md"
    lignes = [f"# Gruterra {version}", "", "## Changements importants"]
    lignes.extend(f"- {item}" for item in importants[:12])
    if not importants:
        lignes.append("- Préparation de la release Gruterra.")
    lignes.extend(["", "## Autres changements inclus"])
    lignes.extend(f"- {item}" for item in autres[:20])
    if not autres:
        lignes.append("- Aucun autre changement listé.")
    lignes.extend([
        "",
        "## Sécurité de mise à jour",
        "- Archive officielle vérifiée par SHA256.",
        "- Données locales et configuration privée préservées.",
        "- Redémarrage manuel conseillé après application.",
    ])
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return chemin


def ecrire_note_release(version: str, archive: Path, sha256: str, fichiers: list[Path], manifest_ready: Path, changelog: Path) -> Path:
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    note = DIST_DIR / f"gruterra-{version}-release-info.txt"
    url = construire_release_url(version)
    lignes = [
        "Gruterra - préparation release",
        f"Date locale : {horodatage}",
        f"Version : {version}",
        f"Archive : {archive.name}",
        f"SHA256 : {sha256}",
        f"Fichiers inclus : {len(fichiers)}",
        f"Manifeste prêt : {manifest_ready.name}",
        f"Changelog prêt : {changelog.name}",
        "",
        "Après publication GitHub Release, vous pouvez copier le changelog prêt dans la description :",
        f"  {changelog}",
        "",
        "Puis copier le contenu du manifeste prêt :",
        f"  {manifest_ready}",
        "",
        "Ou renseigner version_manifest.json ainsi :",
        f'  "archive_url": "{url}",',
        f'  "sha256": "{sha256}",',
        '  "mise_a_jour_automatique": true',
        "",
        "Contrôle : l'archive est construite uniquement depuis les fichiers suivis par Git.",
        "Les bases locales, tokens, configs privées, captures brutes et docs privées ne sont pas inclus.",
    ]
    note.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return note




def valider_sortie_release(version: str, archive: Path, sha256: str, manifest_ready: Path, changelog: Path) -> list[str]:
    erreurs = []
    if not archive.exists():
        erreurs.append(f"archive absente : {archive}")
    elif calculer_sha256(archive) != sha256:
        erreurs.append("SHA256 recalculé différent du SHA256 annoncé")
    if not manifest_ready.exists():
        erreurs.append(f"manifeste prêt absent : {manifest_ready}")
    else:
        try:
            manifest = json.loads(manifest_ready.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as erreur:
            erreurs.append(f"manifeste prêt illisible : {erreur}")
        else:
            if manifest.get("version") != version:
                erreurs.append("version du manifeste prêt différente de la version préparée")
            if manifest.get("sha256") != sha256:
                erreurs.append("SHA256 du manifeste prêt différent du SHA256 de l'archive")
            attendu = construire_release_url(version)
            if manifest.get("archive_url") != attendu:
                erreurs.append("URL d'archive du manifeste prêt différente de l'URL attendue")
            if manifest.get("mise_a_jour_automatique") is not True:
                erreurs.append("mise_a_jour_automatique n'est pas activé dans le manifeste prêt")
    if not changelog.exists():
        erreurs.append(f"changelog absent : {changelog}")
    elif "## Changements importants" not in changelog.read_text(encoding="utf-8"):
        erreurs.append("changelog sans section Changements importants")
    return erreurs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prépare une archive officielle Gruterra et son SHA256.")
    parser.add_argument("--allow-dirty", action="store_true", help="autorise une archive malgré des changements Git non validés")
    args = parser.parse_args(argv)

    if not args.allow_dirty:
        verifier_arbre_propre()
    version = lire_version()
    fichiers = lister_fichiers_suivis()
    if not fichiers:
        raise RuntimeError("Aucun fichier suivi par Git à archiver.")
    archive = construire_archive(version, fichiers)
    sha256 = calculer_sha256(archive)
    manifest_ready = ecrire_manifest_pret(version, sha256)
    changelog = ecrire_changelog_release(version)
    note = ecrire_note_release(version, archive, sha256, fichiers, manifest_ready, changelog)
    erreurs_release = valider_sortie_release(version, archive, sha256, manifest_ready, changelog)
    if erreurs_release:
        raise RuntimeError("Release locale incohérente : " + "; ".join(erreurs_release))

    print("Archive Gruterra préparée")
    print(f"Version : {version}")
    print(f"Archive : {archive}")
    print(f"SHA256 : {sha256}")
    print(f"Fichiers inclus : {len(fichiers)}")
    print(f"Manifeste prêt : {manifest_ready}")
    print(f"Changelog prêt : {changelog}")
    print(f"Note release : {note}")
    print("Validation release : OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        raise SystemExit(1)
