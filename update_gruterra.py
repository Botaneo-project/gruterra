"""Vérification guidée des mises à jour Gruterra.

Ce script est volontairement non destructif : il ne télécharge pas d'archive,
ne remplace aucun fichier et ne modifie pas les données utilisateur. Il sert à
valider les protections avant une future mise à jour automatique.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
APP_DIR = RACINE / "_app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import botaneo_update  # noqa: E402


def construire_message_validation(diagnostic: dict) -> str:
    version = diagnostic.get("version", {})
    lignes = [
        botaneo_update.formater_diagnostic_mise_a_jour(diagnostic),
        "",
        "Validation auto-update :",
    ]

    archive_url = str(version.get("archive_url", "") or "").strip()
    sha256 = str(version.get("sha256", "") or "").strip()
    manifest_auto_update = bool(version.get("manifest_auto_update", False))

    if not manifest_auto_update:
        lignes.append("- application automatique désactivée dans le manifeste public")
    if not archive_url:
        lignes.append("- archive de mise à jour absente du manifeste")
    if not sha256:
        lignes.append("- empreinte SHA256 absente du manifeste")

    if manifest_auto_update and archive_url and sha256 and diagnostic.get("statut_global") != "bloque":
        lignes.append("- prérequis applicatifs détectés, mais application automatique encore volontairement non implémentée")
    else:
        lignes.append("- résultat : vérification informative uniquement, aucune mise à jour appliquée")

    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vérifie l'état de mise à jour Gruterra sans modifier le programme.")
    parser.add_argument("--local", action="store_true", help="utilise seulement le manifeste local")
    parser.add_argument("--json", action="store_true", help="affiche le diagnostic JSON")
    args = parser.parse_args(argv)

    diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(
        RACINE,
        verifier_distant=not args.local,
    )

    if args.json:
        print(botaneo_update.exporter_diagnostic_mise_a_jour_json(diagnostic))
    else:
        print(construire_message_validation(diagnostic))

    return 0 if diagnostic.get("statut_global") != "bloque" else 2


if __name__ == "__main__":
    raise SystemExit(main())
