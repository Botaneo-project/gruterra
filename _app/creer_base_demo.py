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
    rappel_fait INTEGER NOT NULL DEFAULT 0
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
        for i in range(96):
            date = now - timedelta(hours=95 - i)
            jour = i / 24
            lumiere_jour = max(25, 210 + 130 * math.sin((date.hour - 7) / 12 * math.pi)) if 7 <= date.hour <= 20 else 18
            humidite = max(16, 35 - jour * 3.4 + 2 * math.sin(i / 5))
            temperature = 22.4 + 1.8 * math.sin((date.hour - 8) / 24 * 2 * math.pi)
            conductivite = 118 - jour * 2 + math.sin(i / 7) * 4
            executer(conn, """
                INSERT INTO mesures (date_heure, temperature, humidite, luminosite, conductivite, donnees_brutes, capteur_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date.isoformat(timespec="seconds"), round(temperature, 1), round(humidite, 1), round(lumiere_jour, 0), round(conductivite, 0), "demo", capteur_crassula))

            humidite_m = 48 + 4 * math.sin(i / 9)
            lumiere_m = max(45, 520 + 260 * math.sin((date.hour - 7) / 12 * math.pi)) if 7 <= date.hour <= 20 else 35
            executer(conn, """
                INSERT INTO mesures (date_heure, temperature, humidite, luminosite, conductivite, donnees_brutes, capteur_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date.isoformat(timespec="seconds"), round(temperature + 0.4, 1), round(humidite_m, 1), round(lumiere_m, 0), round(210 + math.sin(i / 6) * 18, 0), "demo", capteur_monstera))

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
            (crassula, now - timedelta(days=5, hours=2), 80, "normal", None, None, "Arrosage de démonstration", None, 0),
            (monstera, now - timedelta(days=2, hours=4), 180, "normal", None, None, "Substrat maintenu légèrement humide", None, 0),
            (cactus, now - timedelta(days=18), 40, "normal", None, None, "Plante sans capteur, suivi manuel", (now + timedelta(days=10)).isoformat(timespec="seconds"), 0),
        ]
        conn.executemany("""
            INSERT INTO arrosages (plante_id, date_heure, quantite_ml, type, fertilisant, dosage, commentaire, rappel_date, rappel_fait)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(p, d.isoformat(timespec="seconds") if hasattr(d, 'isoformat') else d, q, t, f, dosage, c, r, fait) for p, d, q, t, f, dosage, c, r, fait in arrosages])

        conn.executemany("""
            INSERT INTO journal_plantes (plante_id, date_heure, type, titre, commentaire, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (crassula, (now - timedelta(days=4)).isoformat(timespec="seconds"), "observation", "Feuilles tombées", "Deux feuilles vertes et fermes tombées. Observation fictive pour tester le journal.", "demo"),
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
