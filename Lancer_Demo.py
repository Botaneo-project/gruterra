"""Lance Gruterra en mode démonstration depuis la racine du projet.

Ce lanceur est prévu pour un double-clic ou une commande simple depuis le
répertoire décompressé. Il n'utilise aucun chemin fixe du PC.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "_app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

runpy.run_path(str(APP_DIR / "lancer_demo.py"), run_name="__main__")