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
    "WATER": "#2C9FD6",
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
    "WATER": "#65C7FF",
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


def couleur_hex_vers_rgb(couleur):
    couleur = couleur.lstrip("#")
    return tuple(int(couleur[i:i + 2], 16) for i in (0, 2, 4))


def couleur_rgb_vers_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, int(valeur))):02x}" for valeur in rgb)


def melanger_couleurs(couleur_a, couleur_b, ratio=0.5):
    try:
        a = couleur_hex_vers_rgb(couleur_a)
        b = couleur_hex_vers_rgb(couleur_b)
        return couleur_rgb_vers_hex(
            a[i] * (1 - ratio) + b[i] * ratio
            for i in range(3)
        )
    except Exception:
        return couleur_a


def simplifier_coordonnees(coords, largeur_graphique):
    if len(coords) <= 240:
        return coords

    points = list(zip(coords[::2], coords[1::2]))
    cible = max(120, min(260, int(largeur_graphique / 4)))
    pas = max(1, len(points) // cible)
    retenus = points[::pas]
    if retenus[-1] != points[-1]:
        retenus.append(points[-1])

    resultat = []
    for x, y in retenus:
        resultat.extend((x, y))
    return resultat


def analyser_points(points, nom_serie):
    if not points:
        return {
            "tendance": "—",
            "lecture": "Aucune mesure exploitable sur cette période.",
            "couleur": "SECONDARY"
        }

    if len(points) == 1:
        return {
            "tendance": "stable",
            "lecture": "Une seule mesure disponible : tendance non interprétable.",
            "couleur": "SECONDARY"
        }

    debut_date, debut_valeur = points[0]
    fin_date, fin_valeur = points[-1]
    duree_heures = max((fin_date - debut_date).total_seconds() / 3600, 0.01)
    variation = fin_valeur - debut_valeur
    variation_jour = variation / duree_heures * 24
    unite = SERIES[nom_serie]["unite"]

    if abs(variation_jour) < 0.5:
        tendance = "stable"
        couleur = "GREEN"
    elif variation_jour > 0:
        tendance = f"+{formater_nombre(variation_jour)} {unite}/jour"
        couleur = "BLUE"
    else:
        tendance = f"{formater_nombre(variation_jour)} {unite}/jour"
        couleur = "ORANGE"

    if nom_serie == "Humidité":
        derniere = fin_valeur
        if derniere < 20 and variation_jour < -1:
            lecture = "Humidité basse et en baisse : arrosage à surveiller."
            couleur = "ORANGE"
        elif derniere > 35 and variation_jour > -0.5:
            lecture = "Substrat encore humide : éviter d'arroser trop vite."
            couleur = "BLUE"
        else:
            lecture = "Aucune tendance globale suffisamment fiable sur la période affichée. Les réponses aux arrosages doivent être comparées séparément."
    elif nom_serie == "Lumière":
        valeurs = [valeur for _, valeur in points]
        moyenne = sum(valeurs) / len(valeurs)
        if moyenne < 250:
            lecture = "Lumière moyenne faible : emplacement ou éclairage à surveiller."
            couleur = "ORANGE"
        else:
            lecture = "Lumière exploitable sur la période affichée."
    elif nom_serie == "Température":
        if abs(variation_jour) >= 2:
            lecture = "Température en évolution nette : surveiller les écarts."
            couleur = "ORANGE"
        else:
            lecture = "Température globalement stable."
    else:
        lecture = "Conductivité affichée comme indicateur de suivi, à interpréter prudemment."

    return {
        "tendance": tendance,
        "lecture": lecture,
        "couleur": couleur
    }


def ids_humidite_zero_suspects(mesures):
    points = []
    for mesure in mesures:
        try:
            date = datetime.fromisoformat(mesure[1])
            if date.tzinfo:
                date = date.astimezone().replace(tzinfo=None)
            humidite = float(mesure[3])
            points.append((date, mesure, humidite))
        except (TypeError, ValueError):
            continue

    points.sort(key=lambda item: item[0])
    suspects = set()

    for index, (date, mesure, humidite) in enumerate(points):
        if humidite != 0:
            continue
        avant = next((item for item in reversed(points[:index]) if item[2] > 0), None)
        apres = next((item for item in points[index + 1:] if item[2] > 0), None)
        if not avant or not apres:
            continue
        ecart_avant_h = (date - avant[0]).total_seconds() / 3600
        ecart_apres_h = (apres[0] - date).total_seconds() / 3600
        if ecart_avant_h <= 3 and ecart_apres_h <= 3 and avant[2] >= 5 and apres[2] >= 5:
            suspects.add(mesure[0])

    return suspects


def filtrer_mesures_pour_serie(mesures, nom_serie):
    if nom_serie != "Humidité":
        return list(mesures), set()
    suspects = ids_humidite_zero_suspects(mesures)
    if not suspects:
        return list(mesures), suspects
    return [mesure for mesure in mesures if mesure[0] not in suspects], suspects


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
    tri_table = {"colonne": None}

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
        "maximum": tk.StringVar(value="—"),
        "tendance": tk.StringVar(value="—")
    }

    for titre, variable in (("Dernière", resume_vars["dernier"]),
                            ("Moyenne", resume_vars["moyenne"]),
                            ("Minimum", resume_vars["minimum"]),
                            ("Maximum", resume_vars["maximum"]),
                            ("Tendance", resume_vars["tendance"])):
        bloc = tk.Frame(resume_frame, bg=couleurs["CARD"])
        bloc.pack(side="left", expand=True, fill="x", padx=8, pady=8)
        tk.Label(bloc, textvariable=variable, bg=couleurs["CARD"],
                 fg=couleurs["TEXT"], font=("Segoe UI", 14, "bold")).pack()
        tk.Label(bloc, text=titre, bg=couleurs["CARD"],
                 fg=couleurs["SECONDARY"], font=("Segoe UI", 8)).pack()

    qualite_var = tk.StringVar(value="Qualité des données : en attente")
    qualite_label = tk.Label(
        fenetre,
        textvariable=qualite_var,
        bg=couleurs["CARD"],
        fg=couleurs["SECONDARY"],
        font=("Segoe UI", 9, "bold"),
        anchor="w",
        justify="left",
        wraplength=980,
        highlightbackground=couleurs["BORDER"],
        highlightthickness=1
    )
    qualite_label.pack(fill="x", padx=24, pady=(0, 8), ipady=6)

    lecture_var = tk.StringVar(value="Sélectionnez une mesure pour lire la tendance.")
    lecture_label = tk.Label(
        fenetre,
        textvariable=lecture_var,
        bg=couleurs["CARD"],
        fg=couleurs["TEXT"],
        font=("Segoe UI", 10, "bold"),
        anchor="w",
        justify="left",
        wraplength=980,
        highlightbackground=couleurs["BORDER"],
        highlightthickness=1
    )
    lecture_label.pack(fill="x", padx=24, pady=(0, 10), ipady=8)

    canvas = tk.Canvas(fenetre, bg=couleurs["CARD"],
                       highlightbackground=couleurs["BORDER"],
                       highlightthickness=1, height=300)
    canvas.pack(fill="both", expand=True, padx=24)

    outils_table = tk.Frame(fenetre, bg=couleurs["BG"])
    outils_table.pack(fill="x", padx=24, pady=(6, 8))

    tk.Label(
        outils_table,
        text="Repères rapides du tableau",
        bg=couleurs["BG"],
        fg=couleurs["SECONDARY"],
        font=("Segoe UI", 9, "bold")
    ).pack(side="left", padx=(0, 10))

    outils_post_arrosage = tk.Frame(fenetre, bg=couleurs["BG"])
    outils_post_arrosage.pack(fill="x", padx=24, pady=(0, 8))

    tk.Label(
        outils_post_arrosage,
        text="Après arrosage",
        bg=couleurs["BG"],
        fg=couleurs["WATER"],
        font=("Segoe UI", 9, "bold")
    ).pack(side="left", padx=(0, 10))

    cadre = tk.Frame(fenetre, bg=couleurs["BG"])
    cadre.pack(fill="both", expand=True, padx=24, pady=(0, 18))

    colonnes = ("date", "humidite", "temperature", "lumiere", "conductivite", "_mesure_id")
    table = ttk.Treeview(cadre, columns=colonnes, show="headings", height=8)
    titres = ("Date et heure", "Humidité (%)", "Température (°C)", "Lumière (lux)", "Conductivité (µS/cm)")

    for nom, titre, largeur in zip(colonnes[:5], titres, (185, 110, 130, 120, 165)):
        table.heading(nom, text=titre, command=lambda col=nom: trier_table(col))
        table.column(nom, width=largeur, minwidth=80, anchor="center")
    table.heading("_mesure_id", text="")
    table.column("_mesure_id", width=0, minwidth=0, stretch=False)

    scroll = ttk.Scrollbar(cadre, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    table.pack(side="left", fill="both", expand=True)

    points = []
    mesures_courantes = []
    arrosages_courants = []

    def analyser_qualite_donnees(mesures):
        dates = []
        for mesure in mesures:
            try:
                date = datetime.fromisoformat(mesure[1])
                if date.tzinfo:
                    date = date.astimezone().replace(tzinfo=None)
                dates.append(date)
            except (TypeError, ValueError):
                pass
        dates.sort()
        if not dates:
            return "Qualité des données : aucune mesure sur cette période.", "SECONDARY"
        debut = dates[0]
        fin = dates[-1]
        duree_heures = max((fin - debut).total_seconds() / 3600, 0)
        ecarts = []
        for avant, apres in zip(dates, dates[1:]):
            ecarts.append((apres - avant).total_seconds() / 3600)
        plus_grand_trou = max(ecarts) if ecarts else 0
        trous_importants = sum(1 for ecart in ecarts if ecart > 1.8)
        attendu = int(duree_heures) + 1 if duree_heures >= 1 else len(dates)
        manque_estime = max(attendu - len(dates), 0)
        couverture = f"{len(dates)}/{attendu}" if attendu else str(len(dates))
        texte = (
            f"Qualité des données : {couverture} mesure(s) attendues environ · "
            f"période {debut.strftime('%d/%m %H:%M')} → {fin.strftime('%d/%m %H:%M')} · "
            f"plus grand trou {plus_grand_trou:.1f} h"
        )
        if manque_estime or trous_importants:
            texte += f" · ⚠ données probablement incomplètes ({manque_estime} manquante(s) estimée(s), {trous_importants} trou(s) > 1h48). Relancer Synchroniser ou Importer historique peut compléter."
            return texte, "ORANGE"
        texte += " · suivi régulier sur cette période."
        return texte, "GREEN"

    def valeur_tri_mesure(mesure, colonne):
        index_par_colonne = {
            "date": 1,
            "temperature": 2,
            "humidite": 3,
            "lumiere": 4,
            "conductivite": 5
        }
        index = index_par_colonne.get(colonne)
        if index is None:
            return float("-inf")
        valeur = mesure[index]
        if colonne == "date":
            try:
                date = datetime.fromisoformat(valeur)
                if date.tzinfo:
                    date = date.astimezone().replace(tzinfo=None)
                return date.timestamp()
            except (ValueError, TypeError):
                return float("-inf")
        try:
            nombre = float(valeur)
            return nombre if math.isfinite(nombre) else float("-inf")
        except (ValueError, TypeError):
            return float("-inf")


    def libelle_tri(colonne):
        return {
            "date": "date la plus récente",
            "humidite": "humidité la plus haute",
            "temperature": "température la plus haute",
            "lumiere": "lumière la plus forte",
            "conductivite": "conductivité la plus haute"
        }.get(colonne, "ordre normal")


    def afficher_mesures_table(mesures, colonne_tri=None):
        for item in table.get_children():
            table.delete(item)

        for mesure in mesures:
            try:
                date = datetime.fromisoformat(mesure[1]).strftime("%d/%m/%Y %H:%M:%S")
            except (ValueError, TypeError):
                date = str(mesure[1] or "—")

            item_id = table.insert("", "end", values=(date, formater_nombre(mesure[3]),
                                                       formater_nombre(mesure[2]),
                                                       formater_nombre(mesure[4]),
                                                       formater_nombre(mesure[5])))
            try:
                table.set(item_id, "_mesure_id", mesure[0])
            except Exception:
                pass

        if mesures and colonne_tri:
            enfants = table.get_children()
            if enfants:
                table.selection_set(enfants[0])
                table.focus(enfants[0])
                table.see(enfants[0])


    def trier_table(colonne):
        tri_table["colonne"] = colonne
        mesures_triees = sorted(
            mesures_courantes,
            key=lambda mesure: valeur_tri_mesure(mesure, colonne),
            reverse=True
        )
        afficher_mesures_table(mesures_triees, colonne)
        if mesures_triees:
            meilleure = mesures_triees[0]
            valeur = valeur_tri_mesure(meilleure, colonne)
            if colonne == "date":
                try:
                    date = datetime.fromisoformat(meilleure[1]).strftime("%d/%m/%Y %H:%M:%S")
                except (ValueError, TypeError):
                    date = str(meilleure[1] or "—")
                bilan.set(f"{len(mesures_courantes)} mesure(s) · tri : {libelle_tri(colonne)} · {date}")
            elif math.isfinite(valeur):
                unite = {
                    "humidite": "%",
                    "temperature": "°C",
                    "lumiere": "lux",
                    "conductivite": "µS/cm"
                }.get(colonne, "")
                bilan.set(f"{len(mesures_courantes)} mesure(s) · tri : {libelle_tri(colonne)} · {formater_nombre(valeur)} {unite}")
            else:
                bilan.set(f"{len(mesures_courantes)} mesure(s) · tri : {libelle_tri(colonne)}")


    def colonne_serie_actuelle():
        return {
            "Humidité": "humidite",
            "Température": "temperature",
            "Lumière": "lumiere",
            "Conductivité": "conductivite"
        }.get(serie.get(), "humidite")


    def selectionner_mesure(mesure, libelle, valeur=None, unite=""):
        if not mesure:
            bilan.set(f"{len(mesures_courantes)} mesure(s) · aucun repère disponible")
            return
        mesure_id = str(mesure[0])
        for item in table.get_children():
            if str(table.set(item, "_mesure_id")) == mesure_id:
                table.selection_set(item)
                table.focus(item)
                table.see(item)
                break
        detail = f" · {formater_nombre(valeur)} {unite}" if valeur is not None and math.isfinite(valeur) else ""
        bilan.set(f"{len(mesures_courantes)} mesure(s) · {libelle}{detail}")


    def selectionner_repere(type_repere):
        colonne = colonne_serie_actuelle()
        valeurs = []
        for mesure in mesures_courantes:
            valeur = valeur_tri_mesure(mesure, colonne)
            if math.isfinite(valeur):
                valeurs.append((mesure, valeur))
        if not valeurs:
            selectionner_mesure(None, "aucune valeur exploitable")
            return

        unite = SERIES[serie.get()]["unite"]
        if type_repere == "max":
            mesure, valeur = max(valeurs, key=lambda item: item[1])
            selectionner_mesure(mesure, f"maximum {serie.get().lower()}", valeur, unite)
        elif type_repere == "min":
            mesure, valeur = min(valeurs, key=lambda item: item[1])
            selectionner_mesure(mesure, f"minimum {serie.get().lower()}", valeur, unite)
        elif type_repere == "moyenne":
            moyenne = sum(valeur for _, valeur in valeurs) / len(valeurs)
            mesure, valeur = min(valeurs, key=lambda item: abs(item[1] - moyenne))
            selectionner_mesure(mesure, f"plus proche de la moyenne {formater_nombre(moyenne)} {unite}", valeur, unite)
        elif type_repere == "derniere":
            mesure = max(mesures_courantes, key=lambda item: valeur_tri_mesure(item, "date"))
            valeur = valeur_tri_mesure(mesure, colonne)
            selectionner_mesure(mesure, f"dernière mesure {serie.get().lower()}", valeur, unite)


    def minutes_repere(repere):
        valeur = repere[4]
        unite = repere[5]
        if unite == "minutes":
            return valeur
        if unite == "heures":
            return valeur * 60
        if unite == "jours":
            return valeur * 24 * 60
        return valeur


    def selectionner_apres_arrosage(repere):
        if not arrosages_courants:
            selectionner_mesure(None, "aucun arrosage visible sur cette période")
            return
        if not mesures_courantes:
            selectionner_mesure(None, "aucune mesure visible sur cette période")
            return

        dernier_arrosage = max(
            arrosages_courants,
            key=lambda item: valeur_tri_mesure((None, item[2], None, None, None, None), "date")
        )
        try:
            date_arrosage = datetime.fromisoformat(dernier_arrosage[2])
            if date_arrosage.tzinfo:
                date_arrosage = date_arrosage.astimezone().replace(tzinfo=None)
        except (TypeError, ValueError):
            selectionner_mesure(None, "date d'arrosage inexploitable")
            return

        cible = date_arrosage + timedelta(minutes=minutes_repere(repere))
        mesures_apres = []
        for mesure in mesures_courantes:
            try:
                date_mesure = datetime.fromisoformat(mesure[1])
                if date_mesure.tzinfo:
                    date_mesure = date_mesure.astimezone().replace(tzinfo=None)
            except (TypeError, ValueError):
                continue
            if date_mesure >= date_arrosage:
                mesures_apres.append((mesure, date_mesure))

        if not mesures_apres:
            selectionner_mesure(None, f"aucune mesure après {repere[2]}")
            return

        mesure, date_mesure = min(mesures_apres, key=lambda item: abs((item[1] - cible).total_seconds()))
        colonne = colonne_serie_actuelle()
        valeur = valeur_tri_mesure(mesure, colonne)
        unite = SERIES[serie.get()]["unite"]
        ecart_min = abs((date_mesure - cible).total_seconds()) / 60
        selectionner_mesure(
            mesure,
            f"{repere[2]} · mesure la plus proche, écart {ecart_min:.0f} min",
            valeur,
            unite
        )


    def remettre_ordre_normal():
        tri_table["colonne"] = None
        afficher_mesures_table(mesures_courantes)
        bilan.set(f"{len(mesures_courantes)} mesure(s) · ordre normal")


    def dessiner(event=None):
        canvas.delete("all")
        w = max(canvas.winfo_width(), 240)
        h = max(canvas.winfo_height(), 180)
        x0, x1, y0, y1 = 72, w - 38, 48, h - 54
        config = SERIES[serie.get()]
        couleur_ligne = couleurs[config["couleur"]]
        couleur_secondaire = couleurs["SECONDARY"]
        couleur_grille = melanger_couleurs(couleurs["GRID"], couleurs["CARD"], 0.35)
        couleur_zone = melanger_couleurs(couleur_ligne, couleurs["CARD"], 0.82)

        canvas.create_text(x0, 22, text=f"{config['titre']} ({config['unite']})",
                           anchor="w", fill=couleurs["TEXT"],
                           font=("Segoe UI", 12, "bold"))
        canvas.create_text(x1, 22, text=f"{len(points)} point(s)",
                           anchor="e", fill=couleur_secondaire,
                           font=("Segoe UI", 9))

        if not points:
            canvas.create_text(w / 2, h / 2, text="Aucune mesure pour cette période.",
                               fill=couleur_secondaire, font=("Segoe UI", 11))
            return

        low, high = limites_graphique(points, serie.get())

        canvas.create_rectangle(x0, y0, x1, y1, outline=couleurs["BORDER"], fill="")

        for i in range(5):
            value = low + (high - low) * i / 4
            y = y1 - (y1 - y0) * i / 4
            canvas.create_line(x0, y, x1, y, fill=couleur_grille)
            canvas.create_text(x0 - 14, y, text=formater_nombre(value),
                               anchor="e", fill=couleur_secondaire,
                               font=("Segoe UI", 8))

        start, end = points[0][0], points[-1][0]
        dates_arrosage_visibles = []
        for arrosage in arrosages_courants:
            try:
                date_arrosage = datetime.fromisoformat(arrosage[2])
                if date_arrosage.tzinfo:
                    date_arrosage = date_arrosage.astimezone().replace(tzinfo=None)
                dates_arrosage_visibles.append(date_arrosage)
            except (TypeError, ValueError):
                pass
        if dates_arrosage_visibles:
            start = min(start, min(dates_arrosage_visibles))
            end = max(end, max(dates_arrosage_visibles))
        span = (end - start).total_seconds()
        coords = []

        for arrosage in arrosages_courants:
            try:
                date_arrosage = datetime.fromisoformat(arrosage[2])
                if date_arrosage.tzinfo:
                    date_arrosage = date_arrosage.astimezone().replace(tzinfo=None)
            except (TypeError, ValueError):
                continue
            if not (start <= date_arrosage <= end):
                continue
            x_arrosage = x0 + (x1 - x0) * (date_arrosage - start).total_seconds() / span if span else (x0 + x1) / 2
            quantite = arrosage[3]
            quantite_txt = f"{quantite:g} ml" if quantite is not None else "arrosage"
            canvas.create_line(
                x_arrosage, y0, x_arrosage, y1,
                fill=couleurs["WATER"],
                width=2,
                dash=(5, 4)
            )
            canvas.create_oval(
                x_arrosage - 6, y0 - 2, x_arrosage + 6, y0 + 10,
                fill=couleurs["WATER"],
                outline=couleurs["CARD"],
                width=2
            )
            canvas.create_text(
                x_arrosage + 8,
                y0 + 14,
                text=f"💧 {quantite_txt}",
                anchor="w",
                fill=couleurs["WATER"],
                font=("Segoe UI", 8, "bold")
            )

        for date, valeur in points:
            x = x0 + (x1 - x0) * (date - start).total_seconds() / span if span else (x0 + x1) / 2
            y = y1 - (y1 - y0) * (valeur - low) / (high - low)
            coords.extend((x, y))

        coords_ligne = simplifier_coordonnees(coords, x1 - x0)

        if len(coords_ligne) >= 4:
            zone = [coords_ligne[0], y1] + coords_ligne + [coords_ligne[-2], y1]
            canvas.create_polygon(*zone, fill=couleur_zone, outline="")
            canvas.create_line(*coords_ligne, fill=melanger_couleurs(couleur_ligne, couleurs["CARD"], 0.55), width=7, smooth=True)
            canvas.create_line(*coords_ligne, fill=couleur_ligne, width=3, smooth=True)
        elif coords_ligne:
            x, y = coords_ligne[0], coords_ligne[1]
            canvas.create_oval(x - 5, y - 5, x + 5, y + 5,
                               fill=couleur_ligne, outline=couleurs["CARD"])

        points_marqueurs = list(zip(coords[::2], coords[1::2]))
        if len(points_marqueurs) <= 28:
            marqueurs = points_marqueurs
        else:
            pas = max(1, len(points_marqueurs) // 10)
            marqueurs = points_marqueurs[::pas]
            if marqueurs[-1] != points_marqueurs[-1]:
                marqueurs.append(points_marqueurs[-1])

        rayon = 3 if len(points_marqueurs) <= 28 else 4
        for x, y in marqueurs:
            canvas.create_oval(x - rayon, y - rayon, x + rayon, y + rayon,
                               fill=couleurs["CARD"], outline=couleur_ligne, width=2)

        dernier_x, dernier_y = points_marqueurs[-1]
        canvas.create_oval(dernier_x - 6, dernier_y - 6, dernier_x + 6, dernier_y + 6,
                           fill=couleur_ligne, outline=couleurs["CARD"], width=2)
        canvas.create_text(dernier_x, max(y0 + 14, dernier_y - 16),
                           text=f"{formater_nombre(points[-1][1])} {config['unite']}",
                           anchor="s", fill=couleurs["TEXT"],
                           font=("Segoe UI", 9, "bold"))

        canvas.create_text(x0, y1 + 28, text=start.strftime("%d/%m %H:%M"),
                           anchor="w", fill=couleur_secondaire,
                           font=("Segoe UI", 8))
        if span:
            milieu = start + (end - start) / 2
            canvas.create_text((x0 + x1) / 2, y1 + 28, text=milieu.strftime("%d/%m %H:%M"),
                               anchor="center", fill=couleur_secondaire,
                               font=("Segoe UI", 8))
            canvas.create_text(x1, y1 + 28, text=end.strftime("%d/%m %H:%M"),
                               anchor="e", fill=couleur_secondaire,
                               font=("Segoe UI", 8))

    def copier_resume_historique():
        nom_plante = plante[1] if plante else "Plante"
        lignes = [
            f"Historique Botaneo — {nom_plante}",
            f"Période affichée : {periode.get()}",
            f"Mesure affichée : {serie.get()}",
            "",
            "Résumé visible :",
            f"- Dernière : {resume_vars['dernier'].get()}",
            f"- Moyenne : {resume_vars['moyenne'].get()}",
            f"- Minimum : {resume_vars['minimum'].get()}",
            f"- Maximum : {resume_vars['maximum'].get()}",
            f"- Tendance : {resume_vars['tendance'].get()}",
            "",
            qualite_var.get(),
            lecture_var.get(),
            f"Tableau : {bilan.get()}",
        ]

        selection = table.selection()
        if selection:
            valeurs = table.item(selection[0], "values")
            if valeurs:
                lignes.extend([
                    "",
                    "Ligne sélectionnée :",
                    f"- Date : {valeurs[0]}",
                    f"- Humidité : {valeurs[1]} %",
                    f"- Température : {valeurs[2]} °C",
                    f"- Lumière : {valeurs[3]} lux",
                    f"- Conductivité : {valeurs[4]} µS/cm",
                ])

        fenetre.clipboard_clear()
        fenetre.clipboard_append("\n".join(lignes).strip())
        bilan.set(f"{bilan.get()} · résumé copié")


    def actualiser(event=None):
        nonlocal points, mesures_courantes, arrosages_courants

        try:
            mesures = database.get_mesures(plante_id=plante_id, limite=-1)
        except Exception:
            bilan.set("Impossible de lire les mesures. Réessayez.")
            return

        try:
            arrosages = database.get_arrosages_plante(plante_id, limite=200)
        except Exception:
            arrosages = []

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

            arrosages_filtres = []
            for arrosage in arrosages:
                try:
                    date = datetime.fromisoformat(arrosage[2])
                    if date.tzinfo:
                        date = date.astimezone().replace(tzinfo=None)
                    if limite <= date <= datetime.now():
                        arrosages_filtres.append(arrosage)
                except (ValueError, TypeError):
                    pass
            arrosages = arrosages_filtres

        arrosages_courants = list(arrosages)

        mesures_courantes = list(mesures)
        if tri_table["colonne"]:
            afficher_mesures_table(
                sorted(
                    mesures_courantes,
                    key=lambda mesure: valeur_tri_mesure(mesure, tri_table["colonne"]),
                    reverse=True
                ),
                tri_table["colonne"]
            )
        else:
            afficher_mesures_table(mesures_courantes)

        mesures_stats, mesures_suspectes_ids = filtrer_mesures_pour_serie(mesures, serie.get())
        points = extraire_points(mesures_stats, serie.get())
        config = SERIES[serie.get()]

        analyse = analyser_points(points, serie.get())
        if points:
            valeurs = [valeur for _, valeur in points]
            resume_vars["dernier"].set(f"{formater_nombre(points[-1][1])} {config['unite']}")
            resume_vars["moyenne"].set(f"{formater_nombre(sum(valeurs) / len(valeurs))} {config['unite']}")
            resume_vars["minimum"].set(f"{formater_nombre(min(valeurs))} {config['unite']}")
            resume_vars["maximum"].set(f"{formater_nombre(max(valeurs))} {config['unite']}")
            resume_vars["tendance"].set(analyse["tendance"])
        else:
            for variable in resume_vars.values():
                variable.set("—")

        qualite_texte, qualite_couleur = analyser_qualite_donnees(mesures)
        if mesures_suspectes_ids:
            qualite_texte += (
                f" · ⚠ {len(mesures_suspectes_ids)} humidité à 0 % isolée(s) conservée(s) "
                "dans le tableau, exclue(s) du graphique et des statistiques."
            )
            qualite_couleur = "ORANGE"
        qualite_var.set(qualite_texte)
        qualite_label.configure(fg=couleurs.get(qualite_couleur, couleurs["SECONDARY"]))

        lecture_var.set(analyse["lecture"])
        lecture_label.configure(fg=couleurs.get(analyse["couleur"], couleurs["TEXT"]))
        suffixe_arrosage = f" · {len(arrosages_courants)} arrosage(s)" if arrosages_courants else ""
        if tri_table["colonne"]:
            bilan.set(f"{len(mesures)} mesure(s){suffixe_arrosage} · tri : {libelle_tri(tri_table['colonne'])}")
        else:
            bilan.set(f"{len(mesures)} mesure(s){suffixe_arrosage}")
        dessiner()

    for texte, repere in (
            ("Max", "max"),
            ("Min", "min"),
            ("Moyenne proche", "moyenne"),
            ("Dernière", "derniere")):
        ttk.Button(
            outils_table,
            text=texte,
            command=lambda r=repere: selectionner_repere(r)
        ).pack(side="left", padx=(0, 6))

    try:
        reperes_analyse = database.get_reperes_analyse_actifs()
    except Exception:
        reperes_analyse = []

    for repere in reperes_analyse:
        if repere[3] != "apres_arrosage":
            continue
        ttk.Button(
            outils_post_arrosage,
            text=repere[2],
            command=lambda r=repere: selectionner_apres_arrosage(r)
        ).pack(side="left", padx=(0, 6))

    ttk.Button(barre, text="Ordre normal", command=remettre_ordre_normal).pack(side="right", padx=(8, 0))
    ttk.Button(barre, text="Copier résumé", command=copier_resume_historique).pack(side="right", padx=(8, 0))
    ttk.Button(barre, text="Actualiser", command=actualiser).pack(side="right")
    choix_periode.bind("<<ComboboxSelected>>", actualiser)
    choix_serie.bind("<<ComboboxSelected>>", actualiser)
    canvas.bind("<Configure>", dessiner)
    actualiser()

    return fenetre
