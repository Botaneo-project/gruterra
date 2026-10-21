"""Lance Gruterra en mode démonstration depuis la racine du projet.

Ce lanceur est prévu pour un double-clic ou une commande simple depuis le
répertoire décompressé. Il n'utilise aucun chemin fixe du PC.
"""

from __future__ import annotations

import runpy
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "_app"


# Recovery runs before imports from a possibly interrupted program installation.
try:
    marker = ROOT / "_security_backups" / "update-pending.json"
    if marker.exists():
        runner = ROOT / "_security_backups" / "update-recovery.py"
    else:
        runner = ROOT / "update_recovery.py"
    if runner.resolve() != runner:
        raise RuntimeError("linked recovery runner")
    recovery = runpy.run_path(str(runner), run_name="gruterra_frozen_recovery")
    recovery_result = recovery["recover_pending"](ROOT)
    if recovery_result["status"] == "restored":
        os.environ["GRUTERRA_RECOVERED_UPDATE"] = "1"
        print("Gruterra : mise a jour interrompue, version precedente restauree.")
        print("Gruterra: interrupted update, previous version restored.")
except Exception:
    print("Gruterra : mise a jour en cours ou recuperation bloquee. Conservez les sauvegardes.")
    print("Gruterra: update in progress or recovery blocked. Keep the backups; application not started.")
    raise SystemExit(3) from None

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

runpy.run_path(str(APP_DIR / "lancer_demo.py"), run_name="__main__")