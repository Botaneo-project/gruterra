"""Lance Botaneo avec une base fictive de démonstration."""

from __future__ import annotations

import os
from pathlib import Path

from creer_base_demo import DEMO_DB, creer_base_demo

if not DEMO_DB.exists():
    creer_base_demo(force=True)

os.environ["BOTANEO_DB_PATH"] = str(DEMO_DB)
os.environ["BOTANEO_DEMO"] = "1"
os.environ["BOTANEO_CONFIG_DIR"] = str(DEMO_DB.parent / "config")

demo_config = DEMO_DB.parent / "config"
demo_config.mkdir(parents=True, exist_ok=True)
local_config = demo_config / "botaneo.local.json"
if not local_config.exists():
    import shutil
    shutil.copyfile(Path(__file__).resolve().parent.parent / "botaneo.local.example.json", local_config)

import interface  # noqa: E402,F401 - ouvre l'interface Tkinter
