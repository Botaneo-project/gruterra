# Gruterra

> **Source code and downloads:** changes on `main` may be newer than the latest published archive, currently **0.1.6-dev**. Recent restart, database protection and interface fixes will be included in a future release; pushing source changes does not update the downloadable archive automatically.

Gruterra is a local plant monitoring app. It brings together plants, Mi Flora / Flower Care readings, sensor history, watering logs, reminders, local weather context and early watering-cycle analysis.

The project started from a practical need: not only seeing sensor values, but understanding what happens to a plant over time. For example: did watering actually increase moisture near the sensor? How long did it take to return to the starting level? Was a bright day a real exposure period or only a short light spike?

> Official project name: **Gruterra**. Some files, environment variables, Raspberry services and paths still keep the historical technical name `botaneo` for compatibility with existing installations.

## Language status

Gruterra started as a French-first project. The main screens now support French and English, selected in Settings. Detailed documentation is partly French; personal notes and older release notes keep their original language.

English is welcome for GitHub, Reddit and Discord feedback, but the app is not fully translated yet. This document is an English entry point, not a promise that the full application is already bilingual.

## Quick demo without hardware

The easiest way to discover Gruterra is the demo mode. It does not require a Mi Flora sensor, Raspberry Pi, Netatmo account or personal database.

Download and extract the official release archive, double-click `Installer_Gruterra.bat`, then `Lancer_Demo.bat`. If Python is missing, the installer attempts to install Python 3.12.10 and continues with the local `.venv`. No Git or hardware is required.

Detailed demo guide: [GUIDE_DEMO_EN.md](GUIDE_DEMO_EN.md). ZIP release installation guide: [GUIDE_INSTALLATION.md](GUIDE_INSTALLATION.md).

French README: [README.md](README.md).

## What Gruterra can already do

- Track plants with or without an active sensor.
- Associate a Mi Flora / Flower Care sensor with a plant.
- Read Mi Flora values: soil moisture, temperature, light, conductivity and battery.
- Import the internal Mi Flora history without deleting sensor data.
- Display historical graphs with data-quality information, watering markers and day selection.
- Record manual watering events, reminders and observations.
- Analyze watering cycles: moisture before watering, peak, 24 h, 48 h, return toward the starting level and measurement quality.
- Distinguish balcony/outdoor exposure events from indoor periods for light analysis.
- Display basic plant needs from a small local plant database.
- Display private/public Netatmo data and a local weather summary when configured.
- Optionally synchronize with a Raspberry Pi for more regular data collection.
- Check update information from GitHub while protecting local data.

## Current project state

Gruterra is under active development. It already works locally for personal use, but installation and public distribution are still being stabilized.

Current priorities:

- improve history and watering-cycle readability;
- make the demo mode useful for people without hardware;
- provide a safer guided update path;
- document Raspberry Pi setup more clearly;
- keep secrets, real databases and private configuration out of the repository;
- keep improving the English documentation and the in-app French / English translation.

Roadmap: [ROADMAP.md](ROADMAP.md). Detailed development history: [TODO.md](TODO.md).

## Personal data and safety

Gruterra is designed to run locally. Do not publish:

- real SQLite databases;
- the `_config/` folder;
- Netatmo, weather, e-mail or other API tokens;
- local favorites and settings;
- backups;
- runtime caches and collected personal data.

The repository only contains anonymous example files.

## Installation

The Windows installer uses Python 3.12.10 when no suitable Python installation is detected. Tkinter is required.

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

If the `py` launcher is not available, use the installed Python executable.

Tkinter and SQLite are included with a standard Python installation on Windows.

## Launch

Graphical interface:

```powershell
.\.venv\Scripts\python.exe Lancer_Gruterra.py
```

Console interface:

```powershell
cd C:\Plantes\_app
py app.py
```

## Demo mode

Demo mode creates a fake local SQLite database in `_app/data/demo/plantes_demo.db`. It is safe to explore and does not use real sensors or real credentials.

```powershell
.\.venv\Scripts\python.exe Lancer_Demo.py
```

To recreate a clean demo database:

```powershell
.\.venv\Scripts\python.exe _app\creer_base_demo.py
```

## Update assistant

In Settings, use Check for updates → Prepare update → Apply update. When already up to date, no installation action is offered. Updates check the official archive and SHA-256, create a local backup and preserve user data. The demo supports manual update testing too. Command-line diagnostics are also available:

```powershell
py update_gruterra.py
py update_gruterra.py --dry-run
py update_gruterra.py --apply
```

The `--apply` mode refuses to run unless the public manifest explicitly enables automatic update and provides both an official archive URL and a valid SHA256 hash. Before replacing program files, it creates a local backup and preserves personal data such as `plantes.db`, `_config/`, `_historique/`, `_app/data/`, the local Discord bot `.env` and the Git repository.

The assistant is intentionally strict: real updates require an official release archive, a matching SHA256 hash and an explicit update flag in the manifest. It never replaces local files silently in the background.

## Netatmo and Raspberry Pi

- Netatmo setup guide: [GUIDE_NETATMO.md](GUIDE_NETATMO.md) — still mostly French.
- Raspberry Pi status and setup notes: [RASPBERRY.md](RASPBERRY.md) — still mostly French.

## Contributing

The project is still young. Useful feedback includes installation issues, demo-mode feedback, Mi Flora / Flower Care behavior, Raspberry Pi collection ideas, Netatmo setup clarity, wording improvements and translation suggestions.

Please never share private tokens, passwords, refresh tokens, real configuration files or real personal databases.


### Contribution identity preparation on main

New contribution identities use Ed25519. Separate key backups are password-encrypted and restoration verifies the identity. Legacy identities are preserved pending explicit migration. The local working file and full ZIP backups remain private; full ZIP backups are not encrypted. No contribution network sharing is enabled.
