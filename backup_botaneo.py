import zipfile
from datetime import datetime
from pathlib import Path


SOURCE = Path(r"C:\Plantes")
BACKUP_DIRS = [
    Path(r"E:\Backups_Plantes"),
    Path(r"J:\Backups_Plantes"),
]

EXCLUDED_SUFFIXES = {".tmp", ".pyc", ".lock"}
EXCLUDED_DIR_NAMES = {"__pycache__"}


def destination_available(path):
    return path.drive and Path(path.drive + "\\").exists()


def state_file(backup_dir):
    return backup_dir / ".botaneo_backup_state"


def get_files():
    """Retourne tous les fichiers du projet à sauvegarder."""
    files = []

    for path in SOURCE.rglob("*"):
        if not path.is_file():
            continue

        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue

        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue

        files.append(path)

    return sorted(files)


def get_state(files):
    """
    Crée une signature de l'état actuel du projet.
    On utilise le chemin, la taille et la date de modification.
    """
    lines = []

    for path in files:
        try:
            stat = path.stat()
            relative = path.relative_to(SOURCE)
        except OSError:
            continue

        lines.append(
            f"{relative}|{stat.st_size}|{stat.st_mtime_ns}"
        )

    return "\n".join(lines)


def has_changed(backup_dir, current_state):
    """Vérifie si le projet a changé depuis la dernière sauvegarde sur ce disque."""

    marker = state_file(backup_dir)

    if not marker.exists():
        return True

    previous_state = marker.read_text(
        encoding="utf-8"
    )

    return previous_state != current_state


def create_backup(files, backup_dir, timestamp):
    """Crée l'archive ZIP dans le dossier demandé."""

    backup_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    backup_file = (
        backup_dir /
        f"Botaneo_{timestamp}.zip"
    )

    ignored = []

    with zipfile.ZipFile(
        backup_file,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6
    ) as archive:

        for path in files:
            try:
                archive.write(
                    path,
                    arcname=path.relative_to(SOURCE)
                )
            except OSError as erreur:
                ignored.append(
                    f"{path.relative_to(SOURCE)} | {type(erreur).__name__}: {erreur}"
                )

        if ignored:
            archive.writestr(
                "rapport_fichiers_ignores.txt",
                "Fichiers ignores pendant la sauvegarde Botaneo:\n\n" + "\n".join(ignored)
            )

    return backup_file, ignored


def main():

    print()
    print("=" * 60)
    print("BOTANEO - SAUVEGARDE")
    print("=" * 60)
    print()

    files = get_files()

    if not files:
        print("ATTENTION: Aucun fichier trouvé.")
        print("=" * 60)
        return

    current_state = get_state(files)
    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    created = []
    skipped = []
    unavailable = []
    warnings = []

    for backup_dir in BACKUP_DIRS:
        if not destination_available(backup_dir):
            unavailable.append(backup_dir)
            continue

        if not has_changed(backup_dir, current_state):
            skipped.append(backup_dir)
            continue

        backup_file, ignored = create_backup(files, backup_dir, timestamp)

        state_file(backup_dir).write_text(
            current_state,
            encoding="utf-8"
        )

        created.append(backup_file)
        if ignored:
            warnings.append((backup_file, ignored))

    print(f"Dossier source : {SOURCE}")
    print(f"Fichiers analysés : {len(files)}")
    print()

    if created:
        print("OK: Sauvegarde terminée")
        print()
        for backup_file in created:
            print(f"Archive : {backup_file}")
            print(
                f"   Taille  : "
                f"{backup_file.stat().st_size / 1024 / 1024:.2f} Mo"
            )
    else:
        print("Aucun nouveau ZIP créé.")

    if skipped:
        print()
        print("OK: Aucun changement sur :")
        for backup_dir in skipped:
            print(f"- {backup_dir}")

    if unavailable:
        print()
        print("ATTENTION: Disque ou dossier indisponible :")
        for backup_dir in unavailable:
            print(f"- {backup_dir}")

    if warnings:
        print()
        print("ATTENTION: Certains fichiers ont été ignorés. Voir rapport_fichiers_ignores.txt dans l'archive :")
        for backup_file, ignored in warnings:
            print(f"- {backup_file} : {len(ignored)} fichier(s)")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()

