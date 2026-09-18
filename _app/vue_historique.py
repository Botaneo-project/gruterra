"""Vue de l'historique d'une plante, en lecture seule, sans dependance externe."""
import math
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

import database
from ui_preferences import charger_theme_sombre


THEME_CLAIR = {
    "BG": "#F5F7F5",
    "CARD": "#FFFFFF",
    "TEXT": "#26332A",
    "SECONDARY": "#718078",
    "BORDER": "#E1E7E2",
    "GREEN": "#4F8A5B",
    "BLUE": "#4677A8",
    "ORANGE": "#D98C32",
    "PURPLE": "#6B55A3",
    "GRID": "#E1E7E2"
}

THEME_SOMBRE = {
    "BG": "#111816",
    "CARD": "#1B2521",
    "TEXT": "#E8F0EA",
    "SECONDARY": "#9FB0A6",
    "BORDER": "#30423A",
    "GREEN": "#82C990",
    "BLUE": "#8DBAF0",
    "ORANGE": "#F0B35D",
    "PURPLE": "#B8A7F4",
    "GRID": "#30423A"
}

SERIES = {
    "Humidité": {"colonne": 3, "titre": "Humidité du sol", "unite": "%", "couleur": "GREEN", "minimum": 0, "maximum": 100},
    "Température": {"colonne": 2, "titre": "Température", "unite": "°C", "couleur": "ORANGE"},
    "Lumière": {"colonne": 4, "titre": "Luminosité", "unite": "lux", "couleur": "BLUE", "minimum": 0},
    "Conductivité": {"colonne": 5, "titre": "Conductivité", "unite": "µS/cm", "couleur": "PURPLE", "minimum": 0}
}


def theme_actuel():
    return THEME_SOMBRE if charger_theme_sombre() else THEME_CLAIR


def formater_nombre(valeur):
    try:
        nombre = float(valeur)
        if not math.isfinite(nombre):
            return "—"
        if nombre.is_integer():
            return str(int(nombre))
        return f"{nombre:.1f}"
    except (ValueError, TypeError):
        return "—"


def extraire_points(mesures, nom_serie):
    config = SERIES[nom_serie]
    points = []

    for mesure in mesures:
        try:
            date = datetime.fromisoformat(mesure[1])
            valeur = float(mesure[config["colonne"]])

            if date.tzinfo:
                date = date.astimezone().replace(tzinfo=None)

            if math.isfinite(valeur):
                points.append((date, valeur))

        except (ValueError, TypeError):
            pass

    return sorted(points)


def limites_graphique(points, nom_serie):
    config = SERIES[nom_serie]
    valeurs = [valeur for _, valeur in points]
    minimum = min(valeurs)
    maximum = max(valeurs)

    if "minimum" in config:
        minimum = min(minimum, config["minimum"])

    if "maximum" in config:
        maximum = max(maximum, config["maximum"])

    if minimum == maximum:
        marge = max(1, abs(minimum) * 0.1)
        minimum -= marge
        maximum += marge

    marge = (maximum - minimum) * 0.08
    return minimum - marge, maximum + marge


def ouvrir_historique(parent, plante_id):
    couleurs = theme_actuel()
    plante = database.get_plante(plante_id)

    fenetre = tk.Toplevel(parent)
    fenetre.title("Historique — " + (plante[1] if plante else "Plante"))
    fenetre.geometry("1080x760")
    fenetre.minsize(820, 580)
    fenetre.configure(bg=couleurs["BG"])

    tk.Label(fenetre, text=plante[1] if plante else "Plante introuvable",
             bg=couleurs["BG"], fg=couleurs["TEXT"],
             font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=24, pady=(18, 2))
    tk.Label(fenetre, text="Historique des mesures · heures locales",
             bg=couleurs["BG"], fg=couleurs["SECONDARY"],
             font=("Segoe UI", 10)).pack(anchor="w", padx=24)

    barre = tk.Frame(fenetre, bg=couleurs["BG"])
    barre.pack(fill="x", padx=24, pady=12)

    periode = tk.StringVar(value="Tout")
    serie = tk.StringVar(value="Humidité")
    bilan = tk.StringVar()

    tk.Label(barre, text="Période", bg=couleurs["BG"],
             fg=couleurs["TEXT"]).pack(side="left", padx=(0, 8))
    choix_periode = ttk.Combobox(barre, textvariable=periode,
                                 values=("24 heures", "7 jours", "Tout"),
                                 state="readonly", width=14)
    choix_periode.pack(side="left")

    tk.Label(barre, text="Mesure", bg=couleurs["BG"],
             fg=couleurs["TEXT"]).pack(side="left", padx=(18, 8))
    choix_serie = ttk.Combobox(barre, textvariable=serie,
                               values=tuple(SERIES.keys()),
                               state="readonly", width=16)
    choix_serie.pack(side="left")
    tk.Label(barre, textvariable=bilan, bg=couleurs["BG"],
             fg=couleurs["TEXT"]).pack(side="left", padx=18)

    resume_frame = tk.Frame(fenetre, bg=couleurs["CARD"],
                            highlightbackground=couleurs["BORDER"],
                            highlightthickness=1)
    resume_frame.pack(fill="x", padx=24, pady=(0, 10))

    resume_vars = {
        "dernier": tk.StringVar(value="—"),
        "moyenne": tk.StringVar(value="—"),
        "minimum": tk.StringVar(value="—"),
        "maximum": tk.StringVar(value="—")
    }

    for titre, variable in (("Dernière", resume_vars["dernier"]),
                            ("Moyenne", resume_vars["moyenne"]),
                            ("Minimum", resume_vars["minimum"]),
                            ("Maximum", resume_vars["maximum"])):
        bloc = tk.Frame(resume_frame, bg=couleurs["CARD"])
        bloc.pack(side="left", expand=True, fill="x", padx=8, pady=8)
        tk.Label(bloc, textvariable=variable, bg=couleurs["CARD"],
                 fg=couleurs["TEXT"], font=("Segoe UI", 14, "bold")).pack()
        tk.Label(bloc, text=titre, bg=couleurs["CARD"],
                 fg=couleurs["SECONDARY"], font=("Segoe UI", 8)).pack()

    canvas = tk.Canvas(fenetre, bg=couleurs["CARD"],
                       highlightbackground=couleurs["BORDER"],
                       highlightthickness=1, height=300)
    canvas.pack(fill="both", expand=True, padx=24)

    tk.Label(fenetre, text="Choisissez la mesure à afficher. Le tableau conserve toutes les valeurs.",
             bg=couleurs["BG"], fg=couleurs["SECONDARY"],
             font=("Segoe UI", 9)).pack(anchor="w", padx=24, pady=(5, 10))

    cadre = tk.Frame(fenetre, bg=couleurs["BG"])
    cadre.pack(fill="both", expand=True, padx=24, pady=(0, 18))

    colonnes = ("date", "humidite", "temperature", "lumiere", "conductivite")
    table = ttk.Treeview(cadre, columns=colonnes, show="headings", height=8)
    titres = ("Date et heure", "Humidité (%)", "Température (°C)", "Lumière (lux)", "Conductivité (µS/cm)")

    for nom, titre, largeur in zip(colonnes, titres, (185, 110, 130, 120, 165)):
        table.heading(nom, text=titre)
        table.column(nom, width=largeur, minwidth=80, anchor="center")

    scroll = ttk.Scrollbar(cadre, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    table.pack(side="left", fill="both", expand=True)

    points = []

    def dessiner(event=None):
        canvas.delete("all")
        w = max(canvas.winfo_width(), 240)
        h = max(canvas.winfo_height(), 180)
        x0, x1, y0, y1 = 68, w - 34, 42, h - 48
        config = SERIES[serie.get()]
        couleur_ligne = couleurs[config["couleur"]]

        canvas.create_text(x0, 20, text=f"{config['titre']} ({config['unite']})",
                           anchor="w", fill=couleurs["TEXT"],
                           font=("Segoe UI", 11, "bold"))

        if not points:
            canvas.create_text(w / 2, h / 2, text="Aucune mesure pour cette période.",
                               fill=couleurs["SECONDARY"], font=("Segoe UI", 11))
            return

        low, high = limites_graphique(points, serie.get())

        for i in range(6):
            value = low + (high - low) * i / 5
            y = y1 - (y1 - y0) * i / 5
            canvas.create_line(x0, y, x1, y, fill=couleurs["GRID"])
            canvas.create_text(x0 - 12, y, text=formater_nombre(value),
                               anchor="e", fill=couleurs["SECONDARY"])

        start, end = points[0][0], points[-1][0]
        span = (end - start).total_seconds()
        coords = []

        for date, valeur in points:
            x = x0 + (x1 - x0) * (date - start).total_seconds() / span if span else (x0 + x1) / 2
            y = y1 - (y1 - y0) * (valeur - low) / (high - low)
            coords.extend((x, y))

        if len(points) > 1:
            canvas.create_line(*coords, fill=couleur_ligne, width=3, smooth=True)

        for x, y in zip(coords[::2], coords[1::2]):
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4,
                               fill=couleur_ligne, outline=couleurs["CARD"])

        canvas.create_text(x0, y1 + 24, text=start.strftime("%d/%m %H:%M"),
                           anchor="w", fill=couleurs["SECONDARY"])
        if span:
            canvas.create_text(x1, y1 + 24, text=end.strftime("%d/%m %H:%M"),
                               anchor="e", fill=couleurs["SECONDARY"])

    def actualiser(event=None):
        nonlocal points

        try:
            mesures = database.get_mesures(plante_id=plante_id, limite=-1)
        except Exception:
            bilan.set("Impossible de lire les mesures. Réessayez.")
            return

        jours = {"24 heures": 1, "7 jours": 7}.get(periode.get())

        if jours:
            limite = datetime.now() - timedelta(days=jours)
            filtre = []
            for mesure in mesures:
                try:
                    date = datetime.fromisoformat(mesure[1])
                    if date.tzinfo:
                        date = date.astimezone().replace(tzinfo=None)
                    if limite <= date <= datetime.now():
                        filtre.append(mesure)
                except (ValueError, TypeError):
                    pass
            mesures = filtre

        for item in table.get_children():
            table.delete(item)

        for mesure in mesures:
            try:
                date = datetime.fromisoformat(mesure[1]).strftime("%d/%m/%Y %H:%M:%S")
            except (ValueError, TypeError):
                date = str(mesure[1] or "—")

            table.insert("", "end", values=(date, formater_nombre(mesure[3]),
                                            formater_nombre(mesure[2]),
                                            formater_nombre(mesure[4]),
                                            formater_nombre(mesure[5])))

        points = extraire_points(mesures, serie.get())
        config = SERIES[serie.get()]

        if points:
            valeurs = [valeur for _, valeur in points]
            resume_vars["dernier"].set(f"{formater_nombre(points[-1][1])} {config['unite']}")
            resume_vars["moyenne"].set(f"{formater_nombre(sum(valeurs) / len(valeurs))} {config['unite']}")
            resume_vars["minimum"].set(f"{formater_nombre(min(valeurs))} {config['unite']}")
            resume_vars["maximum"].set(f"{formater_nombre(max(valeurs))} {config['unite']}")
        else:
            for variable in resume_vars.values():
                variable.set("—")

        bilan.set(f"{len(mesures)} mesure(s)")
        dessiner()

    ttk.Button(barre, text="Actualiser", command=actualiser).pack(side="right")
    choix_periode.bind("<<ComboboxSelected>>", actualiser)
    choix_serie.bind("<<ComboboxSelected>>", actualiser)
    canvas.bind("<Configure>", dessiner)
    actualiser()

    return fenetre
