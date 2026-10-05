# Testing Gruterra on Windows

This guide lets you discover the interface with fake demo data, without a sensor, Raspberry Pi or Netatmo account.

## 1. Download the project

Open the GitHub repository:

```text
https://github.com/Botaneo-project/gruterra
```

Then use **Code → Download ZIP** and extract the folder.

## 2. Install Python

Install Python for Windows from:

```text
https://www.python.org/downloads/windows/
```

Use a standard installation with Tkinter and the `py` launcher.

## 3. Launch the demo

Open PowerShell in the extracted folder containing `requirements.txt`, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe Lancer_Demo.py
```

For later launches, use `Lancer_Demo.py` for the demo or `Lancer_Gruterra.py` for a blank real-use start.

No PowerShell activation script is required.

## 4. What the demo uses

**Demo**: opens Gruterra with fake plants and sample readings already present. **Real use**: opens Gruterra with your future local database, without fake data. The demo uses:

```text
_app/data/demo/plantes_demo.db
```

It also uses its own demo configuration. Automatic collection is disabled in demo mode. The synchronization buttons do not simulate physical sensors, so do not use them for the first demo test.

## 5. What to explore first

- **Crassula demo**: rich history over several days, watering cycles, 24 h / 48 h markers and a light peak related to a balcony exposure event.
- **History**: day selection, light graph, watering-cycle comparison and copyable summary for plant analysis.
- **Cactus balcony demo**: plant without an active sensor, with manual watering and a future reminder.
- **Pothos demo**: example of an old preserved sensor state.
- **Monstera demo**: more regular readings, useful for comparison.

## 6. Reset the demo database

You can modify the fake data. To start again with a clean demo database, close Gruterra and run:

```powershell
.\.venv\Scripts\python.exe _app\creer_base_demo.py
```

## 7. Feedback

Useful feedback includes:

- which screen you were using;
- what you clicked;
- what you expected;
- what happened instead;
- a screenshot without personal information if needed.

Do not send personal databases or configuration files containing credentials.

French version: [GUIDE_DEMO.md](GUIDE_DEMO.md).