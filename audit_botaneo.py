from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def trouver_git() -> str | None:
    git_path = shutil.which("git")
    if git_path:
        return git_path

    candidats = [
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "native" / "git" / "cmd" / "git.exe",
        Path.home() / "AppData" / "Local" / "GitHubDesktop" / "app" / "resources" / "app" / "git" / "cmd" / "git.exe",
    ]
    local_app = Path.home() / "AppData" / "Local" / "GitHubDesktop"
    if local_app.exists():
        candidats.extend(local_app.glob(r"app-*\resources\app\git\cmd\git.exe"))
        candidats.extend(local_app.glob(r"app-*\resources\app\git\mingw64\bin\git.exe"))

    for candidat in candidats:
        try:
            if candidat.exists():
                return str(candidat)
        except OSError:
            pass
    return None


def executer(titre: str, commande: list[str]) -> bool:
    print()
    print(f"=== {titre} ===")
    resultat = subprocess.run(
        commande,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if resultat.returncode == 0:
        print(f"OK : {titre}")
        return True
    print(f"ECHEC : {titre} (code {resultat.returncode})")
    return False


def afficher_status_git(git: str | None) -> None:
    if not git:
        return
    print()
    print("=== État Git après audit ===")
    resultat = subprocess.run(
        [git, "status", "--short"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    if resultat.returncode != 0:
        print("Impossible de lire l’état Git.")
        if resultat.stderr.strip():
            print(resultat.stderr.strip())
        return
    lignes = [ligne for ligne in resultat.stdout.splitlines() if ligne.strip()]
    if not lignes:
        print("Aucun fichier modifié.")
        return
    print("Fichiers modifiés ou non suivis :")
    for ligne in lignes:
        print(f"  {ligne}")
    print("Relire cette liste avant tout commit. Ne jamais utiliser git add .")


def main() -> int:
    print("Botaneo — audit local")
    print(f"Dossier : {ROOT}")

    etapes: list[tuple[str, list[str]]] = [
        ("Tests automatisés", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]),
        ("Vérification avant GitHub", [sys.executable, "verifier_avant_github.py"]),
    ]

    git = trouver_git()
    if git:
        etapes.append(("Contrôle du diff Git", [git, "diff", "--check"]))
    else:
        print("Git introuvable : le contrôle du diff Git sera ignoré.")

    ok = True
    for titre, commande in etapes:
        ok = executer(titre, commande) and ok

    afficher_status_git(git)

    print()
    if ok:
        print("AUDIT OK : les contrôles locaux sont passés.")
        return 0
    print("AUDIT EN ECHEC : corriger les erreurs ci-dessus avant commit/push.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
