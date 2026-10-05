"""Lance Gruterra en mode réel depuis la racine du projet.

Ce lanceur prépare seulement la configuration locale minimale si elle manque,
puis ouvre l'interface graphique. Les données personnelles restent locales et
hors GitHub.
"""

from __future__ import annotations

import runpy
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "_app"
CONFIG_DIR = ROOT / "_config"
LOCAL_CONFIG = CONFIG_DIR / "botaneo.local.json"
EXAMPLE_CONFIG = ROOT / "botaneo.local.example.json"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
if not LOCAL_CONFIG.exists() and EXAMPLE_CONFIG.exists():
    shutil.copyfile(EXAMPLE_CONFIG, LOCAL_CONFIG)

runpy.run_path(str(APP_DIR / "interface.py"), run_name="__main__")