"""Crée une base de démonstration Gruterra avec des données fictives.

Cette base sert aux captures, essais et démonstrations GitHub.
Elle ne copie aucune donnée personnelle de l'utilisateur.
"""

from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DEMO_DIR = APP_DIR / "data" / "demo"
DEMO_DB = DEMO_DIR / "plantes_demo.db"
SOURCE_DB = APP_DIR / "plantes.db"


SCHEMA_FALLBACK = """
CREATE TABLE IF NOT EXISTS plantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    espece TEXT,
    emplacement TEXT,
    zone TEXT
);

CREATE TABLE IF NOT EXISTS capteurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    adresse_ble TEXT NOT NULL,
    plante_id INTEGER,
    actif INTEGER NOT NULL DEFAULT 1,
    date_fin TEXT
);

CREATE TABLE IF NOT EXISTS mesures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_heure TEXT NOT NULL,
    temperature REAL,
    humidite REAL,
    luminosite REAL,
    conductivite REAL,
    donnees_brutes TEXT,
    capteur_id INTEGER
);

CREATE TABLE IF NOT EXISTS besoins_plantes (
    plante_id INTEGER PRIMARY KEY,
    type_plante TEXT,
    lumiere TEXT,
    arrosage TEXT,
    humidite_sol TEXT,
    temperature TEXT,
    notes TEXT,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS arrosages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plante_id INTEGER NOT NULL,
    date_heure TEXT NOT NULL,
    quantite_ml REAL,
    commentaire TEXT,
    type TEXT NOT NULL DEFAULT 'normal',
    fertilisant TEXT,
    dosage TEXT,
    rappel_date TEXT,
    rappel_fait INTEGER NOT NULL DEFAULT 0,
    type_eau TEXT
);

CREATE TABLE IF NOT EXISTS journal_plantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plante_id INTEGER,
    date_heure TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'observation',
    titre TEXT,
    commentaire TEXT NOT NULL,
    source TEXT DEFAULT 'manuel'
);

CREATE TABLE IF NOT EXISTS historique_miflora_brut (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    capteur_id INTEGER NOT NULL,
    index_capteur INTEGER NOT NULL,
    timestamp_capteur INTEGER,
    date_heure_utc TEXT,
    temperature REAL,
    humidite REAL,
    luminosite REAL,
    conductivite REAL,
    raw_hex TEXT NOT NULL,
    import_date TEXT NOT NULL,
    statut TEXT NOT NULL DEFAULT 'importe'
);
"""


def charger_schema_depuis_base_locale() -> str | None:
    if not SOURCE_DB.exists():
        return None
    conn = sqlite3.connect(SOURCE_DB)
    try:
        lignes = conn.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type='table'
              AND name NOT LIKE 'sqlite_%'
              AND sql IS NOT NULL
            ORDER BY name
            """
        ).fetchall()
    finally:
        conn.close()
    schema = ";\n".join(sql for (sql,) in lignes)
    return schema + ";" if schema else None


def executer(conn: sqlite3.Connection, sql: str, params=()) -> int:
    cur = conn.execute(sql, params)
    return int(cur.lastrowid)


def creer_base_demo(force: bool = True) -> Path:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    if force and DEMO_DB.exists():
        DEMO_DB.unlink()

    conn = sqlite3.connect(DEMO_DB)
    try:
        conn.executescript(charger_schema_depuis_base_locale() or SCHEMA_FALLBACK)

        crassula = executer(conn, "INSERT INTO plantes (nom, espece, emplacement, zone) VALUES (?, ?, ?, ?)", (
            "Crassula démo", "Crassula ovata", "Salon", "Intérieur"
        ))
        monstera = executer(conn, "INSERT INTO plantes (nom, espece, emplacement, zone) VALUES (?, ?, ?, ?)", (
            "Monstera démo", "Monstera deliciosa", "Bureau", "Intérieur"
        ))
        cactus = executer(conn, "INSERT INTO plantes (nom, espece, emplacement, zone) VALUES (?, ?, ?, ?)", (
            "Cactus balcon démo", "Mammillaria", "Balcon", "Extérieur"
        ))
        pothos = executer(conn, "INSERT INTO plantes (nom, espece, emplacement, zone) VALUES (?, ?, ?, ?)", (
            "Pothos démo", "Epipremnum aureum", "Cuisine", "Intérieur"
        ))

        capteur_crassula = executer(conn, "INSERT INTO capteurs (nom, adresse_ble, plante_id, actif, date_fin) VALUES (?, ?, ?, ?, ?)", (
            "Mi Flora Démo 1", "AA:BB:CC:DD:EE:01", crassula, 1, None
        ))
        capteur_monstera = executer(conn, "INSERT INTO capteurs (nom, adresse_ble, plante_id, actif, date_fin) VALUES (?, ?, ?, ?, ?)", (
            "Mi Flora Démo 2", "AA:BB:CC:DD:EE:02", monstera, 1, None
        ))
        executer(conn, "INSERT INTO capteurs (nom, adresse_ble, plante_id, actif, date_fin) VALUES (?, ?, ?, ?, ?)", (
            "Ancien capteur Démo", "AA:BB:CC:DD:EE:99", pothos, 0, (datetime.now() - timedelta(days=12)).isoformat(timespec="seconds")
        ))

        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        debut_historique = now - timedelta(days=10)
        ancien_arrosage = now - timedelta(days=8, hours=2)
        arrosage_recent_1 = now - timedelta(days=3, hours=2)
        arrosage_recent_2 = arrosage_recent_1 + timedelta(minutes=35)
        sortie_balcon = now - timedelta(days=1, hours=5)
        retour_balcon = sortie_balcon + timedelta(hours=2, minutes=15)

        def lumiere_interieure(date: datetime, base: float = 220) -> float:
            if not 7 <= date.hour <= 20:
                return 14
            courbe = math.sin((date.hour - 7) / 13 * math.pi)
            return max(35, base + 165 * courbe + 22 * math.sin(date.timestamp() / 18000))

        def lumiere_crassula(date: datetime) -> float:
            if sortie_balcon <= date <= retour_balcon:
                progression = (date - sortie_balcon).total_seconds() / max(1, (retour_balcon - sortie_balcon).total_seconds())
                return 8200 + 9400 * math.sin(progression * math.pi)
            return lumiere_interieure(date, 160)

        def reponse_arrosage(date: datetime, debut: datetime, pic: float, duree_h: float) -> float:
            h = (date - debut).total_seconds() / 3600
            if h < 0 or h > duree_h:
                return 0
            if h <= 5:
                return pic * (h / 5)
            return max(0, pic * (1 - (h - 5) / (duree_h - 5)))

        for i in range(10 * 24 + 1):
            date = debut_historique + timedelta(hours=i)
            temperature = 22.0 + 1.8 * math.sin((date.hour - 8) / 24 * 2 * math.pi)
            if sortie_balcon <= date <= retour_balcon:
                temperature += 1.1

            humidite = 18.5 + 0.6 * math.sin(i / 9)
            humidite += reponse_arrosage(date, ancien_arrosage, 13.5, 92)
            humidite += reponse_arrosage(date, arrosage_recent_1, 7.2, 54)
            humidite += reponse_arrosage(date, arrosage_recent_2, 4.1, 42)
            humidite = min(34, max(16, humidite))
            conductivite = 82 + 6 * math.sin(i / 17) - max(0, (date - ancien_arrosage).total_seconds() / 86400) * 0.45

            executer(conn, """
                INSERT INTO mesures (date_heure, temperature, humidite, luminosite, conductivite, donnees_brutes, capteur_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date.isoformat(timespec="seconds"), round(temperature, 1), round(humidite, 1), round(lumiere_crassula(date), 0), round(conductivite, 0), "demo", capteur_crassula))

            humidite_m = 48 + 4 * math.sin(i / 18)
            lumiere_m = lumiere_interieure(date, 520)
            executer(conn, """
                INSERT INTO mesures (date_heure, temperature, humidite, luminosite, conductivite, donnees_brutes, capteur_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date.isoformat(timespec="seconds"), round(temperature + 0.4, 1), round(humidite_m, 1), round(lumiere_m, 0), round(210 + math.sin(i / 13) * 18, 0), "demo", capteur_monstera))

        besoins = [
            (crassula, "Succulente", "Très lumineux, soleil doux possible", "Espacé, laisser sécher", "Plutôt sec", "15 à 26 °C", "Données fictives pour démonstration.", None),
            (monstera, "Tropicale", "Lumière vive indirecte", "Modéré", "Légèrement humide", "18 à 27 °C", "Surveiller l'humidité et éviter le plein soleil.", None),
            (cactus, "Cactus", "Très lumineux", "Très espacé", "Sec", "12 à 30 °C", "Plante sans capteur pour tester les rappels manuels.", None),
            (pothos, "Tropicale facile", "Lumière moyenne à vive", "Modéré", "Léger séchage entre deux arrosages", "18 à 28 °C", "Exemple avec ancien capteur conservé.", None),
        ]
        conn.executemany("""
            INSERT INTO besoins_plantes (plante_id, type_plante, lumiere, arrosage, humidite_sol, temperature, notes, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, besoins)

        arrosages = [
            (crassula, ancien_arrosage, 80, "normal", None, None, "Premier cycle démo : hausse nette puis séchage progressif", None, 0, "eau filtrée démo"),
            (crassula, arrosage_recent_1, 40, "normal", None, None, "Session fractionnée démo : premier apport", None, 0, "Volvic démo"),
            (crassula, arrosage_recent_2, 55, "normal", None, None, "Session fractionnée démo : complément, total logique 95 ml", None, 0, "Volvic démo"),
            (monstera, now - timedelta(days=2, hours=4), 180, "normal", None, None, "Substrat maintenu légèrement humide", None, 0, "eau du robinet reposée démo"),
            (cactus, now - timedelta(days=18), 40, "normal", None, None, "Plante sans capteur, suivi manuel", (now + timedelta(days=10)).isoformat(timespec="seconds"), 0, "eau minérale démo"),
        ]
        conn.executemany("""
            INSERT INTO arrosages (plante_id, date_heure, quantite_ml, type, fertilisant, dosage, commentaire, rappel_date, rappel_fait, type_eau)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(p, d.isoformat(timespec="seconds") if hasattr(d, 'isoformat') else d, q, t, f, dosage, c, r, fait, eau) for p, d, q, t, f, dosage, c, r, fait, eau in arrosages])

        conn.executemany("""
            INSERT INTO journal_plantes (plante_id, date_heure, type, titre, commentaire, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (crassula, (now - timedelta(days=9)).isoformat(timespec="seconds"), "observation", "Feuilles tombées", "Deux feuilles vertes et fermes tombées. Observation fictive pour tester le journal.", "demo"),
            (crassula, sortie_balcon.isoformat(timespec="seconds"), "exposition", "Sortie balcon", "Plante sortie avec son capteur pour tester la lumière extérieure.", "demo"),
            (crassula, retour_balcon.isoformat(timespec="seconds"), "exposition", "Retour intérieur", "Retour au salon après exposition naturelle.", "demo"),
            (monstera, (now - timedelta(days=1)).isoformat(timespec="seconds"), "observation", "Croissance", "Nouvelle feuille visible.", "demo"),
            (cactus, (now - timedelta(days=3)).isoformat(timespec="seconds"), "rappel", "Contrôle balcon", "Vérifier visuellement le substrat et l'exposition.", "demo"),
        ])

        conn.commit()
    finally:
        conn.close()
    return DEMO_DB


if __name__ == "__main__":
    chemin = creer_base_demo(force=True)
    print(f"Base de démonstration créée : {chemin}")
