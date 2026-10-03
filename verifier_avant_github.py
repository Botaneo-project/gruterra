from __future__ import annotations

import fnmatch
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def trouver_git() -> str:
    git_path = shutil.which("git")
    if git_path:
        return git_path

    candidats = [
        Path(os.environ.get("ProgramFiles", "")) / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("LocalAppData", "")) / "GitHubDesktop" / "app" / "resources" / "app" / "git" / "cmd" / "git.exe",
        Path(os.environ.get("UserProfile", "")) / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "native" / "git" / "cmd" / "git.exe",
    ]

    local_app = Path(os.environ.get("LocalAppData", ""))
    github_desktop = local_app / "GitHubDesktop"
    if github_desktop.exists():
        candidats.extend(github_desktop.glob(r"app-*\resources\app\git\cmd\git.exe"))
        candidats.extend(github_desktop.glob(r"app-*\resources\app\git\mingw64\bin\git.exe"))

    for candidat in candidats:
        try:
            if candidat and candidat.exists():
                return str(candidat)
        except OSError:
            pass

    raise SystemExit(
        "Git est introuvable depuis Python. Installe Git pour Windows ou GitHub Desktop, "
        "ou ajoute git.exe au PATH Windows."
    )


GIT = trouver_git()

SENSITIVE_PATH_PARTS = [
    "_config/",
    "_security_backups/",
    "_historique/",
    "_app/data/",
    "archive_conservee_",
]

SENSITIVE_FILE_PATTERNS = [
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.bak",
    "*.tmp",
    "*.lock",
    "*.zip",
    "*.7z",
    "*.rar",
    "*.local.json",
    "*token*",
    "*secret*",
    "*password*",
    "*credential*",
    "*auth*",
]

TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".toml", ".yml", ".yaml",
    ".ps1", ".bat", ".cmd", ".ini", ".cfg", ".gitignore"
}

SECRET_PATTERNS = [
    re.compile(r"access[_-]?token", re.IGNORECASE),
    re.compile(r"refresh[_-]?token", re.IGNORECASE),
    re.compile(r"client[_-]?secret", re.IGNORECASE),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"authorization\s*[:=]", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9._\-]{20,}", re.IGNORECASE),
    re.compile(r"password\s*[:=]", re.IGNORECASE),
]

ALLOWLIST_CONTENT = {
    "README.md",
    "GITHUB_PREPARATION.md",
    "SECURITE_CONFIGURATION.md",
    "botaneo.local.example.json",
    "netatmo_config.example.json",
    "verifier_avant_github.py",
    "_app/SECURITE_CONFIGURATION.md",
    "_app/capteurs/netatmo.py",
    "GUIDE_NETATMO.md",
}

ALLOWLIST_PATHS = {
    "_app/creer_base_demo.py",
    "_app/lancer_demo.py",
    "backup_botaneo.py",
    "raspberry/backup_daily.py",
    "raspberry/backup_manifest.py",
}


def run_git(args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        [GIT, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout


def normaliser(path: str) -> str:
    return path.replace("\\", "/").strip()


def est_sensible(path: str) -> bool:
    p = normaliser(path).lower()
    for part in SENSITIVE_PATH_PARTS:
        if part.lower() in p:
            return True
    name = Path(p).name
    for pattern in SENSITIVE_FILE_PATTERNS:
        if fnmatch.fnmatch(name, pattern.lower()):
            return True
    return False


def fichiers_suivis() -> list[str]:
    return [normaliser(line) for line in run_git(["ls-files"]).splitlines() if line.strip()]


def status_porcelain(include_ignored: bool = False) -> list[tuple[str, str]]:
    args = ["status", "--short"]
    if include_ignored:
        args.append("--ignored")
    lignes = run_git(args).splitlines()
    items = []
    for ligne in lignes:
        if not ligne.strip():
            continue
        statut = ligne[:2]
        path = ligne[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        items.append((statut, normaliser(path)))
    return items


def lire_fichier_texte(path: str) -> str | None:
    local = ROOT / path
    if not local.exists() or not local.is_file():
        return None
    if local.suffix.lower() not in TEXT_EXTENSIONS and local.name != ".gitignore":
        return None
    try:
        if local.stat().st_size > 500_000:
            return None
        return local.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def verifier_fichiers_sensibles_suivis(tracked: list[str]) -> list[str]:
    problemes = []
    for path in tracked:
        if path in ALLOWLIST_PATHS:
            continue
        if est_sensible(path):
            problemes.append(path)
    return problemes


def verifier_fichiers_sensibles_non_ignores(status: list[tuple[str, str]]) -> list[str]:
    problemes = []
    for statut, path in status:
        if statut == "!!":
            continue
        if path in ALLOWLIST_PATHS:
            continue
        if est_sensible(path):
            problemes.append(f"{statut} {path}")
    return problemes


def verifier_contenu_secret(tracked: list[str]) -> list[str]:
    problemes = []
    for path in tracked:
        if path in ALLOWLIST_CONTENT:
            continue
        contenu = lire_fichier_texte(path)
        if contenu is None:
            continue
        for regex in SECRET_PATTERNS:
            if regex.search(contenu):
                problemes.append(f"{path} : motif suspect `{regex.pattern}`")
                break
    return problemes


def verifier_python() -> list[str]:
    fichiers = [p for p in fichiers_suivis() if p.endswith(".py")]
    if not fichiers:
        return []
    cmd = [sys.executable, "-m", "py_compile", *fichiers]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode == 0:
        return []
    return [result.stderr.strip() or result.stdout.strip() or "Erreur py_compile inconnue"]


def afficher_liste(titre: str, lignes: list[str]) -> None:
    print(f"\n{titre}")
    if not lignes:
        print("  rien à signaler")
        return
    for ligne in lignes:
        print(f"  - {ligne}")


def main() -> int:
    os.chdir(ROOT)
    print("Gruterra — vérification avant GitHub")
    print(f"Dossier : {ROOT}")

    status = status_porcelain()
    status_ignored = status_porcelain(include_ignored=True)
    tracked = fichiers_suivis()

    afficher_liste("Fichiers modifiés / ajoutés / supprimés", [f"{s} {p}" for s, p in status])

    problemes = []

    sensibles_suivis = verifier_fichiers_sensibles_suivis(tracked)
    afficher_liste("Contrôle fichiers sensibles déjà suivis par Git", sensibles_suivis)
    problemes.extend(f"Fichier sensible suivi : {p}" for p in sensibles_suivis)

    sensibles_non_ignores = verifier_fichiers_sensibles_non_ignores(status_ignored)
    afficher_liste("Contrôle fichiers sensibles non ignorés ou prêts à partir", sensibles_non_ignores)
    problemes.extend(f"Fichier sensible non ignoré : {p}" for p in sensibles_non_ignores)

    secrets = verifier_contenu_secret(tracked)
    afficher_liste("Contrôle mots-clés de secrets dans les fichiers suivis", secrets)
    problemes.extend(f"Contenu suspect : {p}" for p in secrets)

    erreurs_python = verifier_python()
    afficher_liste("Contrôle Python", erreurs_python)
    problemes.extend(f"Erreur Python : {p}" for p in erreurs_python)

    branche = run_git(["branch", "--show-current"]).strip() or "inconnue"
    print(f"\nBranche Git : {branche}")

    if problemes:
        print("\nERREUR : vérification bloquée. Rien ne devrait être envoyé sur GitHub avant correction.")
        print("Problèmes à corriger :")
        for probleme in problemes:
            print(f"  - {probleme}")
        return 1

    print("\nOK : vérification réussie. Aucun risque évident détecté.")
    print("Tu peux ensuite faire :")
    print("  git add <fichiers voulus>")
    print('  git commit -m "Message clair"')
    print("  git push origin main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
