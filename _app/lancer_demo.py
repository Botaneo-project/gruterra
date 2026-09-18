"""Lance Botaneo avec une base fictive de démonstration."""

from __future__ import annotations

import os
from pathlib import Path

from creer_base_demo import DEMO_DB, creer_base_demo

if not DEMO_DB.exists():
    creer_base_demo(force=True)

os.environ["BOTANEO_DB_PATH"] = str(DEMO_DB)
os.environ.setdefault("BOTANEO_DEMO", "1")

import interface  # noqa: E402,F401 - ouvre l'interface Tkinter
