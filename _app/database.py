import os
import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("BOTANEO_DB_PATH", BASE_DIR / "plantes.db"))


_SCHEMA_INITIALISE = False


def get_connection():
    """Ouvre une connexion à la base de données avec les clés étrangères actives."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialiser_schema():
    """Crée le schéma principal minimal pour une installation neuve.

    Cette initialisation est additive : elle crée les tables et index absents,
    sans supprimer ni fusionner les données existantes.
    """
    global _SCHEMA_INITIALISE
    if _SCHEMA_INITIALISE:
        return

    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                espece TEXT,
                emplacement TEXT,
                zone TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS capteurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                adresse_ble TEXT NOT NULL,
                plante_id INTEGER,
                actif INTEGER NOT NULL DEFAULT 1,
                date_fin TEXT,
                FOREIGN KEY (plante_id) REFERENCES plantes(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS mesures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_heure TEXT NOT NULL,
                temperature REAL,
                humidite REAL,
                luminosite REAL,
                conductivite REAL,
                donnees_brutes TEXT,
                capteur_id INTEGER,
                FOREIGN KEY (capteur_id) REFERENCES capteurs(id)
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_capteurs_plante ON capteurs(plante_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_capteurs_adresse_active ON capteurs(adresse_ble, actif)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mesures_capteur_date ON mesures(capteur_id, date_heure)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mesures_date ON mesures(date_heure)")
        conn.commit()
        _SCHEMA_INITIALISE = True
    finally:
        conn.close()


def date_heure_valide(valeur):
    """Valide une date ISO exploitable avant insertion ou analyse."""
    if not isinstance(valeur, str) or not valeur.strip():
        return False
    texte = valeur.strip()
    try:
        datetime.fromisoformat(texte.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def supprimer_mesures_sans_date():
    """Supprime les mesures et archives Mi Flora sans date fiable.

    Règle Gruterra : une mesure sans date exploitable ne doit pas participer
    aux statistiques, même si elle contient des valeurs plausibles.
    """
    conn = get_connection()
    supprimees_mesures = 0
    supprimees_archives = 0
    try:
        rows = conn.execute("SELECT id, date_heure FROM mesures").fetchall()
        ids_mesures = [row[0] for row in rows if not date_heure_valide(row[1])]
        if ids_mesures:
            conn.executemany("DELETE FROM mesures WHERE id = ?", [(row_id,) for row_id in ids_mesures])
            supprimees_mesures = len(ids_mesures)

        table = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='historique_miflora_brut'
        """).fetchone()
        if table:
            rows = conn.execute("SELECT id, date_heure_utc FROM historique_miflora_brut").fetchall()
            ids_archives = [row[0] for row in rows if not date_heure_valide(row[1])]
            if ids_archives:
                conn.executemany("DELETE FROM historique_miflora_brut WHERE id = ?", [(row_id,) for row_id in ids_archives])
                supprimees_archives = len(ids_archives)
        conn.commit()
    finally:
        conn.close()
    return {"mesures": supprimees_mesures, "archives": supprimees_archives}


# ============================================================
# PLANTES
# ============================================================

def get_plantes():
    """Retourne toutes les plantes."""

    initialiser_schema()

    conn = get_connection()

    plantes = conn.execute("""
        SELECT
            id,
            nom,
            espece,
            emplacement,
            zone
        FROM plantes
        ORDER BY id
    """).fetchall()

    conn.close()

    return plantes


def get_plante(plante_id):
    """Retourne une plante à partir de son identifiant."""

    initialiser_schema()

    conn = get_connection()

    plante = conn.execute("""
        SELECT
            id,
            nom,
            espece,
            emplacement,
            zone
        FROM plantes
        WHERE id = ?
    """, (plante_id,)).fetchone()

    conn.close()

    return plante


def ajouter_plante(
    nom,
    espece,
    emplacement=None,
    zone=None
):
    """Ajoute une nouvelle plante."""

    initialiser_schema()

    conn = get_connection()

    curseur = conn.execute("""
        INSERT INTO plantes
        (nom, espece, emplacement, zone)
        VALUES (?, ?, ?, ?)
    """, (
        nom,
        espece,
        emplacement,
        zone
    ))

    plante_id = curseur.lastrowid

    conn.commit()
    conn.close()

    return plante_id


def modifier_plante(
    plante_id,
    nom,
    espece,
    emplacement=None,
    zone=None
):
    """Modifie une plante existante."""

    initialiser_schema()

    conn = get_connection()

    conn.execute("""
        UPDATE plantes
        SET
            nom = ?,
            espece = ?,
            emplacement = ?,
            zone = ?
        WHERE id = ?
    """, (
        nom,
        espece,
        emplacement,
        zone,
        plante_id
    ))

    conn.commit()
    conn.close()


def supprimer_plante(plante_id):
    """Supprime une plante."""

    initialiser_schema()

    conn = get_connection()

    conn.execute("""
        DELETE FROM plantes
        WHERE id = ?
    """, (plante_id,))

    conn.commit()
    conn.close()


# ============================================================
# BESOINS PLANTES
# ============================================================

def initialiser_besoins_plantes():
    """Crée la table complémentaire des besoins de plantes si besoin."""

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS besoins_plantes (
            plante_id INTEGER PRIMARY KEY,
            type_plante TEXT,
            lumiere TEXT,
            arrosage TEXT,
            humidite_sol TEXT,
            temperature TEXT,
            notes TEXT,
            image_url TEXT,
            FOREIGN KEY (plante_id) REFERENCES plantes(id)
        )
    """)

    conn.commit()
    conn.close()


def get_besoins_plante(plante_id):
    """Retourne les besoins connus d'une plante, ou None."""

    initialiser_besoins_plantes()
    conn = get_connection()

    besoins = conn.execute("""
        SELECT
            plante_id,
            type_plante,
            lumiere,
            arrosage,
            humidite_sol,
            temperature,
            notes,
            image_url
        FROM besoins_plantes
        WHERE plante_id = ?
    """, (plante_id,)).fetchone()

    conn.close()
    return besoins


def enregistrer_besoins_plante(
    plante_id,
    type_plante=None,
    lumiere=None,
    arrosage=None,
    humidite_sol=None,
    temperature=None,
    notes=None,
    image_url=None
):
    """Ajoute ou met à jour les besoins connus d'une plante."""

    initialiser_besoins_plantes()
    conn = get_connection()

    conn.execute("""
        INSERT INTO besoins_plantes
        (plante_id, type_plante, lumiere, arrosage, humidite_sol, temperature, notes, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(plante_id) DO UPDATE SET
            type_plante = excluded.type_plante,
            lumiere = excluded.lumiere,
            arrosage = excluded.arrosage,
            humidite_sol = excluded.humidite_sol,
            temperature = excluded.temperature,
            notes = excluded.notes,
            image_url = excluded.image_url
    """, (
        plante_id,
        type_plante,
        lumiere,
        arrosage,
        humidite_sol,
        temperature,
        notes,
        image_url
    ))

    conn.commit()
    conn.close()


# ============================================================
# JOURNAL PLANTES
# ============================================================

def initialiser_journal_plantes():
    """Crée la table du journal des observations si besoin."""

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS journal_plantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plante_id INTEGER,
            date_heure TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'observation',
            titre TEXT,
            commentaire TEXT NOT NULL,
            source TEXT DEFAULT 'manuel',
            FOREIGN KEY (plante_id) REFERENCES plantes(id)
        )
    """)

    conn.commit()
    conn.close()


def ajouter_observation_plante(
    plante_id,
    date_heure,
    commentaire,
    titre=None,
    type_evenement="observation",
    source="manuel"
):
    """Ajoute une observation ou un événement au journal d'une plante."""

    initialiser_journal_plantes()
    conn = get_connection()

    curseur = conn.execute("""
        INSERT INTO journal_plantes
        (plante_id, date_heure, type, titre, commentaire, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        plante_id,
        date_heure,
        type_evenement,
        titre,
        commentaire,
        source
    ))

    evenement_id = curseur.lastrowid
    conn.commit()
    conn.close()

    return evenement_id


def get_journal_plante(plante_id, limite=20):
    """Retourne les derniers événements d'une plante."""

    initialiser_journal_plantes()
    conn = get_connection()

    evenements = conn.execute("""
        SELECT
            id,
            plante_id,
            date_heure,
            type,
            titre,
            commentaire,
            source
        FROM journal_plantes
        WHERE plante_id = ?
        ORDER BY date_heure DESC, id DESC
        LIMIT ?
    """, (plante_id, limite)).fetchall()

    conn.close()
    return evenements


# ============================================================
# REPÈRES D'ANALYSE PLANTES
# ============================================================

REPERES_ANALYSE_DEFAUT = [
    ("apres_arrosage_10min", "10 min après arrosage", "apres_arrosage", 10, "minutes", 1),
    ("apres_arrosage_1h", "1 h après arrosage", "apres_arrosage", 1, "heures", 2),
    ("apres_arrosage_24h", "24 h après arrosage", "apres_arrosage", 24, "heures", 3),
    ("apres_arrosage_48h", "48 h après arrosage", "apres_arrosage", 48, "heures", 4),
]


def initialiser_reperes_analyse_plantes():
    """Crée et initialise les repères d'analyse utiles dans l'historique."""

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reperes_analyse_plantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            libelle TEXT NOT NULL,
            type TEXT NOT NULL,
            valeur INTEGER NOT NULL,
            unite TEXT NOT NULL,
            actif INTEGER NOT NULL DEFAULT 1,
            ordre INTEGER NOT NULL DEFAULT 0
        )
    """)

    for code, libelle, type_repere, valeur, unite, ordre in REPERES_ANALYSE_DEFAUT:
        conn.execute("""
            INSERT INTO reperes_analyse_plantes
            (code, libelle, type, valeur, unite, actif, ordre)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(code) DO UPDATE SET
                libelle = excluded.libelle,
                type = excluded.type,
                valeur = excluded.valeur,
                unite = excluded.unite,
                ordre = excluded.ordre
        """, (code, libelle, type_repere, valeur, unite, ordre))

    conn.commit()
    conn.close()


def get_reperes_analyse_actifs():
    """Retourne les repères d'analyse actifs, dans l'ordre d'affichage."""

    initialiser_reperes_analyse_plantes()
    conn = get_connection()

    reperes = conn.execute("""
        SELECT
            id,
            code,
            libelle,
            type,
            valeur,
            unite,
            actif,
            ordre
        FROM reperes_analyse_plantes
        WHERE actif = 1
        ORDER BY ordre ASC, id ASC
    """).fetchall()

    conn.close()
    return reperes


# ============================================================
# CAPTEURS
# ============================================================

def get_capteurs():
    """
    Retourne tous les capteurs avec leur plante associée.

    Retourne également leur état actif/inactif
    et leur date de fin éventuelle.
    """

    initialiser_schema()

    conn = get_connection()

    capteurs = conn.execute("""
        SELECT
            c.id,
            c.nom,
            c.adresse_ble,
            c.plante_id,
            p.nom,
            p.espece,
            p.emplacement,
            p.zone,
            c.actif,
            c.date_fin
        FROM capteurs c
        LEFT JOIN plantes p
            ON c.plante_id = p.id
        ORDER BY c.id
    """).fetchall()

    conn.close()

    return capteurs


def get_capteur(capteur_id):
    """Retourne un capteur avec sa plante associée."""

    initialiser_schema()

    conn = get_connection()

    capteur = conn.execute("""
        SELECT
            c.id,
            c.nom,
            c.adresse_ble,
            c.plante_id,
            p.nom,
            p.espece,
            p.emplacement,
            p.zone,
            c.actif,
            c.date_fin
        FROM capteurs c
        LEFT JOIN plantes p
            ON c.plante_id = p.id
        WHERE c.id = ?
    """, (capteur_id,)).fetchone()

    conn.close()

    return capteur


def get_capteur_par_adresse(adresse_ble):
    """
    Retourne le capteur correspondant à une adresse BLE.

    Le capteur actif est prioritaire.
    À défaut, retourne le dernier capteur historique
    utilisant cette adresse.
    """

    adresse_ble = adresse_ble.strip().upper()

    initialiser_schema()

    conn = get_connection()

    capteur = conn.execute("""
        SELECT
            id,
            nom,
            adresse_ble,
            plante_id,
            actif,
            date_fin
        FROM capteurs
        WHERE adresse_ble = ?
        ORDER BY actif DESC, id DESC
        LIMIT 1
    """, (adresse_ble,)).fetchone()

    conn.close()

    return capteur


def get_capteur_actif_par_adresse(adresse_ble):
    """Retourne le capteur actif correspondant à une adresse BLE."""

    adresse_ble = adresse_ble.strip().upper()

    initialiser_schema()

    conn = get_connection()

    capteur = conn.execute("""
        SELECT
            id,
            nom,
            adresse_ble,
            plante_id,
            actif,
            date_fin
        FROM capteurs
        WHERE adresse_ble = ?
          AND actif = 1
        ORDER BY id DESC
        LIMIT 1
    """, (adresse_ble,)).fetchone()

    conn.close()

    return capteur


def ajouter_capteur(
    nom,
    adresse_ble,
    plante_id=None
):
    """
    Ajoute un nouveau capteur.

    Un seul capteur actif doit utiliser une adresse BLE.
    """

    adresse_ble = adresse_ble.strip().upper()

    if not adresse_ble:
        raise ValueError(
            "L'adresse BLE ne peut pas être vide."
        )

    capteur_actif = get_capteur_actif_par_adresse(adresse_ble)

    if capteur_actif:
        raise ValueError(
            f"Un capteur actif existe déjà avec l'adresse BLE "
            f"{adresse_ble} (ID {capteur_actif[0]})."
        )

    if plante_id is not None and get_plante(plante_id) is None:
        raise ValueError(
            f"La plante ID {plante_id} n'existe pas."
        )

    initialiser_schema()

    conn = get_connection()

    curseur = conn.execute("""
        INSERT INTO capteurs
        (
            nom,
            adresse_ble,
            plante_id,
            actif,
            date_fin
        )
        VALUES (?, ?, ?, 1, NULL)
    """, (
        nom,
        adresse_ble,
        plante_id
    ))

    capteur_id = curseur.lastrowid

    conn.commit()
    conn.close()

    return capteur_id


def associer_capteur_plante(
    capteur_id,
    plante_id
):
    """
    Associe un capteur actif à une plante.

    Cette fonction est destinée à une association initiale.
    Pour déplacer un capteur déjà utilisé, utiliser
    deplacer_capteur().
    """

    capteur = get_capteur(capteur_id)

    if capteur is None:
        raise ValueError(
            f"Le capteur ID {capteur_id} n'existe pas."
        )

    if capteur[8] != 1:
        raise ValueError(
            f"Le capteur ID {capteur_id} est inactif."
        )

    if get_plante(plante_id) is None:
        raise ValueError(
            f"La plante ID {plante_id} n'existe pas."
        )

    conn = get_connection()

    conn.execute("""
        UPDATE capteurs
        SET plante_id = ?
        WHERE id = ?
          AND actif = 1
    """, (
        plante_id,
        capteur_id
    ))

    conn.commit()
    conn.close()


def desactiver_capteur(
    capteur_id,
    date_fin
):
    """
    Désactive un capteur sans supprimer son historique.
    """

    capteur = get_capteur(capteur_id)

    if capteur is None:
        raise ValueError(
            f"Le capteur ID {capteur_id} n'existe pas."
        )

    conn = get_connection()

    conn.execute("""
        UPDATE capteurs
        SET
            actif = 0,
            date_fin = ?
        WHERE id = ?
    """, (
        date_fin,
        capteur_id
    ))

    conn.commit()
    conn.close()


def deplacer_capteur(
    capteur_id,
    nouvelle_plante_id,
    date_fin
):
    """
    Déplace un capteur physique vers une nouvelle plante.

    L'ancienne affectation est conservée dans l'historique :
        - actif = 0
        - date_fin renseignée

    Une nouvelle ligne capteur est créée avec :
        - la même adresse BLE
        - la nouvelle plante
        - actif = 1
        - date_fin = NULL

    Les anciennes mesures restent liées à l'ancien capteur_id.
    """

    conn = get_connection()

    try:
        # --------------------------------------------------------
        # Vérification du capteur actuel
        # --------------------------------------------------------

        capteur = conn.execute("""
            SELECT
                id,
                nom,
                adresse_ble,
                plante_id,
                actif,
                date_fin
            FROM capteurs
            WHERE id = ?
        """, (capteur_id,)).fetchone()

        if capteur is None:
            raise ValueError(
                f"Le capteur ID {capteur_id} n'existe pas."
            )

        if capteur[4] != 1:
            raise ValueError(
                f"Le capteur ID {capteur_id} est déjà inactif."
            )

        # --------------------------------------------------------
        # Vérification de la nouvelle plante
        # --------------------------------------------------------

        plante = conn.execute("""
            SELECT id
            FROM plantes
            WHERE id = ?
        """, (nouvelle_plante_id,)).fetchone()

        if plante is None:
            raise ValueError(
                f"La plante ID {nouvelle_plante_id} n'existe pas."
            )

        # --------------------------------------------------------
        # Vérification : même plante ?
        # --------------------------------------------------------

        if capteur[3] == nouvelle_plante_id:
            raise ValueError(
                "Le capteur est déjà associé à cette plante."
            )

        # --------------------------------------------------------
        # Vérification de l'adresse BLE
        # --------------------------------------------------------

        adresse_ble = capteur[2]

        autre_capteur_actif = conn.execute("""
            SELECT id
            FROM capteurs
            WHERE adresse_ble = ?
              AND actif = 1
              AND id != ?
            LIMIT 1
        """, (
            adresse_ble,
            capteur_id
        )).fetchone()

        if autre_capteur_actif is not None:
            raise ValueError(
                f"L'adresse BLE {adresse_ble} est déjà utilisée "
                f"par le capteur actif ID {autre_capteur_actif[0]}."
            )

        # --------------------------------------------------------
        # 1. Clôture de l'ancienne affectation
        # --------------------------------------------------------

        conn.execute("""
            UPDATE capteurs
            SET
                actif = 0,
                date_fin = ?
            WHERE id = ?
              AND actif = 1
        """, (
            date_fin,
            capteur_id
        ))

        # --------------------------------------------------------
        # 2. Création de la nouvelle affectation
        # --------------------------------------------------------

        curseur = conn.execute("""
            INSERT INTO capteurs
            (
                nom,
                adresse_ble,
                plante_id,
                actif,
                date_fin
            )
            VALUES (?, ?, ?, 1, NULL)
        """, (
            capteur[1],
            adresse_ble,
            nouvelle_plante_id
        ))

        nouveau_capteur_id = curseur.lastrowid

        # --------------------------------------------------------
        # Validation de l'ensemble de l'opération
        # --------------------------------------------------------

        conn.commit()

        return nouveau_capteur_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def dissocier_capteur(capteur_id):
    """
    Dissocie un capteur d'une plante.

    Conservée pour compatibilité.

    Pour un déplacement physique du capteur,
    utiliser deplacer_capteur().
    """

    capteur = get_capteur(capteur_id)

    if capteur is None:
        raise ValueError(
            f"Le capteur ID {capteur_id} n'existe pas."
        )

    conn = get_connection()

    conn.execute("""
        UPDATE capteurs
        SET plante_id = NULL
        WHERE id = ?
          AND actif = 1
    """, (capteur_id,))

    conn.commit()
    conn.close()


# ============================================================
# MESURES
# ============================================================

def enregistrer_mesure(
    capteur_id,
    date_heure,
    temperature,
    humidite,
    luminosite,
    conductivite,
    donnees_brutes
):
    """
    Enregistre une mesure pour un capteur existant et actif.
    """

    if not date_heure_valide(date_heure):
        raise ValueError("Date de mesure absente ou invalide : mesure non enregistrée.")

    conn = get_connection()

    capteur = conn.execute("""
        SELECT
            id,
            actif
        FROM capteurs
        WHERE id = ?
    """, (capteur_id,)).fetchone()

    if capteur is None:
        conn.close()

        raise ValueError(
            f"Le capteur ID {capteur_id} n'existe pas."
        )

    if capteur[1] != 1:
        conn.close()

        raise ValueError(
            f"Le capteur ID {capteur_id} n'est plus actif."
        )

    conn.execute("""
        INSERT INTO mesures
        (
            date_heure,
            temperature,
            humidite,
            luminosite,
            conductivite,
            donnees_brutes,
            capteur_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        date_heure,
        temperature,
        humidite,
        luminosite,
        conductivite,
        donnees_brutes,
        capteur_id
    ))

    conn.commit()
    conn.close()


def get_nombre_mesures():
    """Retourne le nombre total de mesures."""

    initialiser_schema()

    conn = get_connection()

    nombre = conn.execute("""
        SELECT COUNT(*)
        FROM mesures
    """).fetchone()[0]

    conn.close()

    return nombre


def get_derniere_mesure():
    """Retourne la dernière mesure enregistrée."""

    initialiser_schema()

    conn = get_connection()

    mesure = conn.execute("""
        SELECT
            m.date_heure,
            m.temperature,
            m.humidite,
            m.luminosite,
            m.conductivite,
            c.nom,
            p.nom
        FROM mesures m
        LEFT JOIN capteurs c
            ON m.capteur_id = c.id
        LEFT JOIN plantes p
            ON c.plante_id = p.id
        ORDER BY m.date_heure DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    return mesure


def get_mesures(
    plante_id=None,
    limite=50
):
    """
    Retourne les dernières mesures.

    Si plante_id est fourni, les mesures sont filtrées
    par plante.
    """

    initialiser_schema()

    conn = get_connection()

    if plante_id is None:

        mesures = conn.execute("""
            SELECT
                m.id,
                m.date_heure,
                m.temperature,
                m.humidite,
                m.luminosite,
                m.conductivite,
                m.donnees_brutes,
                m.capteur_id
            FROM mesures m
            ORDER BY m.date_heure DESC
            LIMIT ?
        """, (limite,)).fetchall()

    else:

        mesures = conn.execute("""
            SELECT
                m.id,
                m.date_heure,
                m.temperature,
                m.humidite,
                m.luminosite,
                m.conductivite,
                m.donnees_brutes,
                m.capteur_id
            FROM mesures m
            JOIN capteurs c
                ON m.capteur_id = c.id
            WHERE c.plante_id = ?
            ORDER BY m.date_heure DESC
            LIMIT ?
        """, (
            plante_id,
            limite
        )).fetchall()

    conn.close()

    return mesures


def get_mesures_capteur(
    capteur_id,
    limite=50
):
    """Retourne les dernières mesures d'un capteur précis."""

    conn = get_connection()

    mesures = conn.execute("""
        SELECT
            m.id,
            m.date_heure,
            m.temperature,
            m.humidite,
            m.luminosite,
            m.conductivite,
            m.donnees_brutes,
            m.capteur_id
        FROM mesures m
        WHERE m.capteur_id = ?
        ORDER BY m.date_heure DESC
        LIMIT ?
    """, (
        capteur_id,
        limite
    )).fetchall()

    conn.close()

    return mesures

# ============================================================
# HISTORIQUE BRUT MI FLORA
# ============================================================

def initialiser_historique_miflora():
    """Crée la table de conservation brute de la mémoire Mi Flora."""

    conn = get_connection()

    conn.execute("""
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
            statut TEXT NOT NULL DEFAULT 'importe',
            FOREIGN KEY (capteur_id) REFERENCES capteurs(id),
            UNIQUE (capteur_id, raw_hex)
        )
    """)

    conn.commit()
    conn.close()


def enregistrer_entrees_historique_miflora(capteur_id, export_historique, import_date):
    """Enregistre les entrées historiques sans écraser les anciennes."""

    initialiser_historique_miflora()
    conn = get_connection()

    ajoutees = 0
    doublons = 0

    for entree in export_historique.get("entries", []):
        raw_hex = entree.get("raw_hex")
        if not raw_hex:
            continue
        if not date_heure_valide(entree.get("date_heure_utc")):
            continue

        curseur = conn.execute("""
            INSERT OR IGNORE INTO historique_miflora_brut
            (
                capteur_id,
                index_capteur,
                timestamp_capteur,
                date_heure_utc,
                temperature,
                humidite,
                luminosite,
                conductivite,
                raw_hex,
                import_date,
                statut
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            capteur_id,
            entree.get("index"),
            entree.get("timestamp_capteur"),
            entree.get("date_heure_utc"),
            entree.get("temperature"),
            entree.get("humidite"),
            entree.get("luminosite"),
            entree.get("conductivite"),
            raw_hex,
            import_date,
            "importe"
        ))

        if curseur.rowcount:
            ajoutees += 1
        else:
            doublons += 1

    conn.commit()
    conn.close()

    return {
        "ajoutees": ajoutees,
        "doublons": doublons,
        "total_lues": len(export_historique.get("entries", [])),
        "history_count": export_historique.get("history_count")
    }


def get_resume_historique_miflora(capteur_id):
    """Retourne un résumé de l'historique brut conservé."""

    initialiser_historique_miflora()
    conn = get_connection()

    resume = conn.execute("""
        SELECT
            COUNT(*),
            MIN(date_heure_utc),
            MAX(date_heure_utc),
            MIN(import_date),
            MAX(import_date)
        FROM historique_miflora_brut
        WHERE capteur_id = ?
    """, (capteur_id,)).fetchone()

    conn.close()
    return resume


# ============================================================
# ARROSAGES
# ============================================================

def initialiser_arrosages():
    """Crée la table des arrosages si besoin."""

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS arrosages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plante_id INTEGER NOT NULL,
            date_heure TEXT NOT NULL,
            quantite_ml REAL,
            type TEXT NOT NULL DEFAULT 'normal',
            fertilisant TEXT,
            dosage TEXT,
            commentaire TEXT,
            type_eau TEXT,
            rappel_date TEXT,
            rappel_fait INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (plante_id) REFERENCES plantes(id)
        )
    """)

    colonnes = [ligne[1] for ligne in conn.execute("PRAGMA table_info(arrosages)").fetchall()]

    if "type_eau" not in colonnes:
        conn.execute("ALTER TABLE arrosages ADD COLUMN type_eau TEXT")

    if "rappel_date" not in colonnes:
        conn.execute("ALTER TABLE arrosages ADD COLUMN rappel_date TEXT")

    if "rappel_fait" not in colonnes:
        conn.execute("ALTER TABLE arrosages ADD COLUMN rappel_fait INTEGER NOT NULL DEFAULT 0")

    conn.commit()
    conn.close()


def enregistrer_arrosage_plante(
    plante_id,
    date_heure,
    quantite_ml=None,
    type_arrosage="normal",
    fertilisant=None,
    dosage=None,
    commentaire=None,
    rappel_date=None,
    type_eau=None
):
    """Enregistre un arrosage manuel pour une plante, avec ou sans capteur."""

    initialiser_arrosages()
    conn = get_connection()

    curseur = conn.execute("""
        INSERT INTO arrosages
        (plante_id, date_heure, quantite_ml, type, fertilisant, dosage, commentaire, type_eau, rappel_date, rappel_fait)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        plante_id,
        date_heure,
        quantite_ml,
        type_arrosage,
        fertilisant,
        dosage,
        commentaire,
        type_eau,
        rappel_date
    ))

    arrosage_id = curseur.lastrowid
    conn.commit()
    conn.close()
    return arrosage_id


def get_dernier_arrosage(plante_id):
    """Retourne le dernier arrosage enregistré pour une plante."""

    initialiser_arrosages()
    conn = get_connection()

    arrosage = conn.execute("""
        SELECT
            id,
            plante_id,
            date_heure,
            quantite_ml,
            type,
            fertilisant,
            dosage,
            commentaire,
            type_eau,
            rappel_date,
            rappel_fait
        FROM arrosages
        WHERE plante_id = ?
        ORDER BY date_heure DESC, id DESC
        LIMIT 1
    """, (plante_id,)).fetchone()

    conn.close()
    return arrosage


def get_arrosages_plante(plante_id, limite=20):
    """Retourne les derniers arrosages d'une plante."""

    initialiser_arrosages()
    conn = get_connection()

    arrosages = conn.execute("""
        SELECT
            id,
            plante_id,
            date_heure,
            quantite_ml,
            type,
            fertilisant,
            dosage,
            commentaire,
            type_eau,
            rappel_date,
            rappel_fait
        FROM arrosages
        WHERE plante_id = ?
        ORDER BY date_heure DESC, id DESC
        LIMIT ?
    """, (plante_id, limite)).fetchall()

    conn.close()
    return arrosages



def _date_arrosage_iso(arrosage):
    try:
        return datetime.fromisoformat(arrosage[2])
    except (TypeError, ValueError, IndexError):
        return None


def construire_sessions_arrosage(arrosages, fenetre_minutes=90):
    """
    Regroupe logiquement des apports proches en sessions d'arrosage.

    Les lignes brutes restent inchangées. Une session est seulement une lecture
    calculée pour l'affichage et l'analyse : plusieurs apports rapprochés, sur
    la même plante, deviennent une session avec volume total et détail.
    """
    lignes = []
    for arrosage in arrosages or []:
        date = _date_arrosage_iso(arrosage)
        if date:
            lignes.append((date, arrosage))
    lignes.sort(key=lambda item: item[0])

    sessions = []
    fenetre_secondes = max(1, int(fenetre_minutes)) * 60
    for date, arrosage in lignes:
        if not sessions:
            sessions.append({"date_debut": date, "date_fin": date, "apports": [arrosage]})
            continue
        derniere = sessions[-1]
        ecart = (date - derniere["date_fin"]).total_seconds()
        if 0 <= ecart <= fenetre_secondes:
            derniere["apports"].append(arrosage)
            derniere["date_fin"] = date
        else:
            sessions.append({"date_debut": date, "date_fin": date, "apports": [arrosage]})

    for session in sessions:
        total = 0.0
        total_present = False
        for apport in session["apports"]:
            try:
                if apport[3] is not None:
                    total += float(apport[3])
                    total_present = True
            except (TypeError, ValueError, IndexError):
                pass
        session["quantite_totale_ml"] = total if total_present else None
        session["premier"] = session["apports"][0]
        session["dernier"] = session["apports"][-1]
        session["fractionnee"] = len(session["apports"]) > 1
    return sessions


def get_sessions_arrosage_plante(plante_id, limite=50, fenetre_minutes=90):
    """Retourne les sessions d'arrosage calculées, de la plus récente à la plus ancienne."""
    arrosages = get_arrosages_plante(plante_id, limite=limite)
    sessions = construire_sessions_arrosage(arrosages, fenetre_minutes=fenetre_minutes)
    return list(reversed(sessions))


def get_derniere_session_arrosage(plante_id, fenetre_minutes=90):
    sessions = get_sessions_arrosage_plante(plante_id, limite=50, fenetre_minutes=fenetre_minutes)
    return sessions[0] if sessions else None

# ============================================================
# COLLECTES PRIORITAIRES
# ============================================================

def initialiser_collectes_prioritaires():
    """Crée la table des demandes de collecte prioritaire."""

    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collectes_prioritaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plante_id INTEGER NOT NULL,
            arrosage_id INTEGER,
            date_creation TEXT NOT NULL,
            raison TEXT NOT NULL,
            priorite INTEGER NOT NULL DEFAULT 1,
            statut TEXT NOT NULL DEFAULT 'en_attente',
            derniere_tentative TEXT,
            commentaire TEXT,
            FOREIGN KEY (plante_id) REFERENCES plantes(id),
            FOREIGN KEY (arrosage_id) REFERENCES arrosages(id)
        )
    """)
    conn.commit()
    conn.close()


def enregistrer_collecte_prioritaire(
    plante_id,
    arrosage_id=None,
    date_creation=None,
    raison="post_arrosage",
    priorite=1,
    commentaire=None
):
    """Mémorise une demande de mesure prioritaire, exploitable par le PC ou le Raspberry."""

    initialiser_collectes_prioritaires()
    conn = get_connection()
    date_creation = date_creation or __import__('datetime').datetime.now().isoformat(timespec="seconds")

    curseur = conn.execute("""
        INSERT INTO collectes_prioritaires
        (plante_id, arrosage_id, date_creation, raison, priorite, statut, commentaire)
        VALUES (?, ?, ?, ?, ?, 'en_attente', ?)
    """, (
        plante_id,
        arrosage_id,
        date_creation,
        raison,
        priorite,
        commentaire
    ))

    demande_id = curseur.lastrowid
    conn.commit()
    conn.close()
    return demande_id


def get_collectes_prioritaires(plante_id=None, statut=None, limite=50):
    """Retourne les demandes de collecte prioritaire."""

    initialiser_collectes_prioritaires()
    conn = get_connection()
    conditions = []
    valeurs = []
    if plante_id is not None:
        conditions.append("plante_id = ?")
        valeurs.append(plante_id)
    if statut is not None:
        conditions.append("statut = ?")
        valeurs.append(statut)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    valeurs.append(limite)
    demandes = conn.execute(f"""
        SELECT id, plante_id, arrosage_id, date_creation, raison, priorite,
               statut, derniere_tentative, commentaire
        FROM collectes_prioritaires
        {where}
        ORDER BY priorite DESC, date_creation DESC, id DESC
        LIMIT ?
    """, valeurs).fetchall()
    conn.close()
    return demandes


def marquer_collecte_prioritaire_tentee(demande_id, statut="tentee", commentaire=None):
    """Met à jour l'état d'une demande prioritaire après tentative."""

    initialiser_collectes_prioritaires()
    conn = get_connection()
    date_tentative = __import__('datetime').datetime.now().isoformat(timespec="seconds")
    conn.execute("""
        UPDATE collectes_prioritaires
        SET statut = ?, derniere_tentative = ?, commentaire = COALESCE(?, commentaire)
        WHERE id = ?
    """, (statut, date_tentative, commentaire, demande_id))
    conn.commit()
    conn.close()


def get_rappel_arrosage_actif(plante_id):
    """Retourne le prochain rappel d'arrosage non terminé pour une plante."""

    initialiser_arrosages()
    conn = get_connection()

    rappel = conn.execute("""
        SELECT
            id,
            plante_id,
            date_heure,
            quantite_ml,
            type,
            fertilisant,
            dosage,
            commentaire,
            type_eau,
            rappel_date,
            rappel_fait
        FROM arrosages
        WHERE plante_id = ?
          AND rappel_date IS NOT NULL
          AND rappel_fait = 0
        ORDER BY rappel_date ASC, id DESC
        LIMIT 1
    """, (plante_id,)).fetchone()

    conn.close()
    return rappel


# ============================================================
# SYNTHESES JOURNALIERES / COMPACTAGE FUTUR
# ============================================================

SEUIL_COMPACTAGE_OCTETS = 5 * 1024 * 1024 * 1024


def get_taille_base_octets():
    """Retourne la taille du fichier SQLite principal, sans déclencher d'action."""
    try:
        return DB_PATH.stat().st_size
    except OSError:
        return 0


def diagnostic_compactage_mesures(seuil_octets=SEUIL_COMPACTAGE_OCTETS):
    """Indique si une synthèse/compaction devrait être envisagée.

    Cette fonction est volontairement passive : elle ne supprime rien et ne crée
    aucune synthèse seule. Elle sert à informer l'interface ou un futur outil de
    maintenance.
    """
    taille = get_taille_base_octets()
    return {
        "taille_octets": taille,
        "seuil_octets": seuil_octets,
        "compactage_conseille": taille >= seuil_octets,
    }


def initialiser_syntheses_mesures_journalieres():
    """Crée la table de synthèse journalière, sans compacter les mesures brutes."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS syntheses_mesures_journalieres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capteur_id INTEGER NOT NULL,
            jour TEXT NOT NULL,
            premiere_mesure TEXT,
            derniere_mesure TEXT,
            nombre_mesures INTEGER NOT NULL,
            temperature_min REAL,
            temperature_max REAL,
            temperature_moy REAL,
            humidite_min REAL,
            humidite_max REAL,
            humidite_moy REAL,
            luminosite_min REAL,
            luminosite_max REAL,
            luminosite_moy REAL,
            conductivite_min REAL,
            conductivite_max REAL,
            conductivite_moy REAL,
            sources TEXT,
            cree_le TEXT NOT NULL,
            statut TEXT NOT NULL DEFAULT 'synthese_seule',
            UNIQUE(capteur_id, jour)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_syntheses_mesures_jour
        ON syntheses_mesures_journalieres(jour, capteur_id)
    """)
    conn.commit()
    conn.close()


def _source_mesure(donnees_brutes):
    texte = str(donnees_brutes or "")
    if "passive_mibeacon" in texte:
        return "raspberry_passif"
    if len(texte.strip()) == 32:
        return "historique_miflora"
    return "mesure_directe"


def synthese_journaliere_exploitable(synthese):
    """Écarte les synthèses techniques vides ou issues d'une mesure brute manifestement suspecte.

    Les données brutes restent conservées. Ce filtre sert seulement à éviter d'afficher
    comme synthèse fiable une journée contenant une seule mesure entièrement à zéro.
    """
    if synthese is None:
        return False
    if isinstance(synthese, dict):
        nombre = synthese.get("nombre_mesures") or 0
        valeurs = [
            synthese.get("temperature_min"), synthese.get("temperature_max"), synthese.get("temperature_moy"),
            synthese.get("humidite_min"), synthese.get("humidite_max"), synthese.get("humidite_moy"),
            synthese.get("luminosite_min"), synthese.get("luminosite_max"), synthese.get("luminosite_moy"),
            synthese.get("conductivite_min"), synthese.get("conductivite_max"), synthese.get("conductivite_moy"),
        ]
    else:
        nombre = synthese[5] or 0
        valeurs = [synthese[i] for i in range(6, 18)]
    if nombre <= 0:
        return False
    valeurs_connues = [v for v in valeurs if v is not None]
    if not valeurs_connues:
        return False
    if nombre == 1 and all(float(v) == 0.0 for v in valeurs_connues):
        return False
    return True




def calculer_synthese_journaliere(capteur_id, jour):
    """Calcule une synthèse journalière en mémoire, sans écrire ni supprimer."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            date_heure,
            temperature,
            humidite,
            luminosite,
            conductivite,
            donnees_brutes
        FROM mesures
        WHERE capteur_id = ?
          AND substr(date_heure, 1, 10) = ?
        ORDER BY date_heure ASC
    """, (capteur_id, jour)).fetchall()
    conn.close()

    if not rows:
        return None

    temperatures = [row[1] for row in rows if row[1] is not None]
    humidites = [row[2] for row in rows if row[2] is not None]
    luminosites = [row[3] for row in rows if row[3] is not None]
    conductivites = [row[4] for row in rows if row[4] is not None]
    sources = sorted({_source_mesure(row[5]) for row in rows})

    def stats(valeurs):
        if not valeurs:
            return None, None, None
        return min(valeurs), max(valeurs), sum(valeurs) / len(valeurs)

    temperature_min, temperature_max, temperature_moy = stats(temperatures)
    humidite_min, humidite_max, humidite_moy = stats(humidites)
    luminosite_min, luminosite_max, luminosite_moy = stats(luminosites)
    conductivite_min, conductivite_max, conductivite_moy = stats(conductivites)

    synthese = {
        "capteur_id": capteur_id,
        "jour": jour,
        "premiere_mesure": rows[0][0],
        "derniere_mesure": rows[-1][0],
        "nombre_mesures": len(rows),
        "temperature_min": temperature_min,
        "temperature_max": temperature_max,
        "temperature_moy": temperature_moy,
        "humidite_min": humidite_min,
        "humidite_max": humidite_max,
        "humidite_moy": humidite_moy,
        "luminosite_min": luminosite_min,
        "luminosite_max": luminosite_max,
        "luminosite_moy": luminosite_moy,
        "conductivite_min": conductivite_min,
        "conductivite_max": conductivite_max,
        "conductivite_moy": conductivite_moy,
        "sources": ",".join(sources),
    }
    if not synthese_journaliere_exploitable(synthese):
        return None
    return synthese


def enregistrer_synthese_journaliere(capteur_id, jour):
    """Enregistre ou met à jour une synthèse journalière, sans supprimer les mesures."""
    initialiser_syntheses_mesures_journalieres()
    synthese = calculer_synthese_journaliere(capteur_id, jour)
    if synthese is None:
        return None

    conn = get_connection()
    conn.execute("""
        INSERT INTO syntheses_mesures_journalieres (
            capteur_id, jour, premiere_mesure, derniere_mesure, nombre_mesures,
            temperature_min, temperature_max, temperature_moy,
            humidite_min, humidite_max, humidite_moy,
            luminosite_min, luminosite_max, luminosite_moy,
            conductivite_min, conductivite_max, conductivite_moy,
            sources, cree_le, statut
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 'synthese_seule')
        ON CONFLICT(capteur_id, jour) DO UPDATE SET
            premiere_mesure=excluded.premiere_mesure,
            derniere_mesure=excluded.derniere_mesure,
            nombre_mesures=excluded.nombre_mesures,
            temperature_min=excluded.temperature_min,
            temperature_max=excluded.temperature_max,
            temperature_moy=excluded.temperature_moy,
            humidite_min=excluded.humidite_min,
            humidite_max=excluded.humidite_max,
            humidite_moy=excluded.humidite_moy,
            luminosite_min=excluded.luminosite_min,
            luminosite_max=excluded.luminosite_max,
            luminosite_moy=excluded.luminosite_moy,
            conductivite_min=excluded.conductivite_min,
            conductivite_max=excluded.conductivite_max,
            conductivite_moy=excluded.conductivite_moy,
            sources=excluded.sources,
            cree_le=excluded.cree_le,
            statut='synthese_seule'
    """, (
        synthese["capteur_id"],
        synthese["jour"],
        synthese["premiere_mesure"],
        synthese["derniere_mesure"],
        synthese["nombre_mesures"],
        synthese["temperature_min"],
        synthese["temperature_max"],
        synthese["temperature_moy"],
        synthese["humidite_min"],
        synthese["humidite_max"],
        synthese["humidite_moy"],
        synthese["luminosite_min"],
        synthese["luminosite_max"],
        synthese["luminosite_moy"],
        synthese["conductivite_min"],
        synthese["conductivite_max"],
        synthese["conductivite_moy"],
        synthese["sources"],
    ))
    conn.commit()
    conn.close()
    return synthese


def lister_syntheses_journalieres(capteur_id=None, limite=90):
    """Retourne les synthèses déjà calculées, sans créer de nouvelle synthèse."""
    initialiser_syntheses_mesures_journalieres()
    conn = get_connection()
    if capteur_id is None:
        rows = conn.execute("""
            SELECT * FROM syntheses_mesures_journalieres
            ORDER BY jour DESC, capteur_id
            LIMIT ?
        """, (limite,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM syntheses_mesures_journalieres
            WHERE capteur_id = ?
            ORDER BY jour DESC
            LIMIT ?
        """, (capteur_id, limite)).fetchall()
    conn.close()
    return [row for row in rows if synthese_journaliere_exploitable(row)]

def lister_jours_mesures_a_synthetiser():
    """Liste les couples capteur/jour présents dans les mesures brutes."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT capteur_id, substr(date_heure, 1, 10) AS jour, COUNT(*) AS nombre
        FROM mesures
        WHERE date_heure IS NOT NULL
          AND capteur_id IS NOT NULL
        GROUP BY capteur_id, jour
        ORDER BY jour DESC, capteur_id
    """).fetchall()
    conn.close()
    return rows


def preparer_syntheses_journalieres(limite_jours=None):
    """Calcule les synthèses existantes, sans supprimer les mesures brutes."""
    initialiser_syntheses_mesures_journalieres()
    couples = lister_jours_mesures_a_synthetiser()
    if limite_jours is not None:
        couples = couples[:limite_jours]
    creees = 0
    ignorees = 0
    for capteur_id, jour, _nombre in couples:
        if enregistrer_synthese_journaliere(capteur_id, jour) is None:
            ignorees += 1
        else:
            creees += 1
    return {
        "syntheses_preparees": creees,
        "jours_ignores": ignorees,
        "couples_capteur_jour": len(couples),
    }
def get_infos_capteur_pour_synthese(capteur_id):
    """Retourne les noms utiles pour afficher une synthèse de manière lisible."""
    conn = get_connection()
    row = conn.execute("""
        SELECT
            c.id,
            c.nom,
            c.adresse_ble,
            p.nom AS plante_nom
        FROM capteurs c
        LEFT JOIN plantes p ON p.id = c.plante_id
        WHERE c.id = ?
    """, (capteur_id,)).fetchone()
    conn.close()
    if row is None:
        return {
            "capteur_id": capteur_id,
            "capteur_nom": f"Capteur {capteur_id}",
            "adresse_ble": "",
            "plante_nom": "Plante inconnue",
            "libelle": f"Capteur {capteur_id}",
        }
    capteur_nom = row[1] or f"Capteur {row[0]}"
    plante_nom = row[3] or "Sans plante"
    return {
        "capteur_id": row[0],
        "capteur_nom": capteur_nom,
        "adresse_ble": row[2] or "",
        "plante_nom": plante_nom,
        "libelle": f"{plante_nom} · {capteur_nom}",
    }

def compactage_mesures_anciennes_non_implemente():
    """Garde-fou : la suppression/compaction destructrice n'est pas encore active."""
    raise RuntimeError(
        "Compactage destructeur non implémenté : créer et valider les synthèses avant toute suppression."
    )

# ============================================================
# DIAGNOSTIC GLOBAL / SANTE SYSTEME
# ============================================================


def get_diagnostic_mesures_par_capteur():
    """Retourne un résumé des mesures par capteur pour la santé système."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            c.id,
            c.nom,
            c.adresse_ble,
            p.nom AS plante_nom,
            COUNT(m.id) AS nombre_mesures,
            MAX(m.date_heure) AS derniere_mesure,
            SUM(CASE WHEN m.donnees_brutes LIKE '%passive_mibeacon%' THEN 1 ELSE 0 END) AS mesures_passives,
            MAX(CASE WHEN m.donnees_brutes LIKE '%passive_mibeacon%' THEN m.date_heure ELSE NULL END) AS derniere_passive,
            SUM(CASE WHEN length(trim(COALESCE(m.donnees_brutes, ''))) = 32 THEN 1 ELSE 0 END) AS mesures_historiques,
            MAX(CASE WHEN length(trim(COALESCE(m.donnees_brutes, ''))) = 32 THEN m.date_heure ELSE NULL END) AS derniere_historique
        FROM capteurs c
        LEFT JOIN plantes p ON p.id = c.plante_id
        LEFT JOIN mesures m ON m.capteur_id = c.id
        GROUP BY c.id, c.nom, c.adresse_ble, p.nom
        ORDER BY c.id
    """).fetchall()
    conn.close()
    return rows


def compter_mesures_entierement_zero():
    """Compte les mesures où les quatre valeurs numériques principales valent 0.

    Ces lignes peuvent indiquer une lecture incomplète ou une donnée de remplacement.
    Elles ne sont pas supprimées ici : le diagnostic sert à les rendre visibles.
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(*)
        FROM mesures
        WHERE temperature IS NOT NULL
          AND humidite IS NOT NULL
          AND luminosite IS NOT NULL
          AND conductivite IS NOT NULL
          AND temperature = 0
          AND humidite = 0
          AND luminosite = 0
          AND conductivite = 0
    """).fetchone()
    conn.close()
    return row[0] or 0


def compter_syntheses_entierement_zero():
    """Compte les synthèses stockées dont toutes les statistiques numériques sont à 0."""
    initialiser_syntheses_mesures_journalieres()
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(*)
        FROM syntheses_mesures_journalieres
        WHERE COALESCE(temperature_min, 0) = 0
          AND COALESCE(temperature_max, 0) = 0
          AND COALESCE(temperature_moy, 0) = 0
          AND COALESCE(humidite_min, 0) = 0
          AND COALESCE(humidite_max, 0) = 0
          AND COALESCE(humidite_moy, 0) = 0
          AND COALESCE(luminosite_min, 0) = 0
          AND COALESCE(luminosite_max, 0) = 0
          AND COALESCE(luminosite_moy, 0) = 0
          AND COALESCE(conductivite_min, 0) = 0
          AND COALESCE(conductivite_max, 0) = 0
          AND COALESCE(conductivite_moy, 0) = 0
    """).fetchone()
    conn.close()
    return row[0] or 0


def get_diagnostic_syntheses():
    """Retourne un résumé compact de l'état des synthèses journalières."""
    initialiser_syntheses_mesures_journalieres()
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(*), MIN(jour), MAX(jour)
        FROM syntheses_mesures_journalieres
    """).fetchone()
    conn.close()
    return {
        "nombre": row[0] or 0,
        "premier_jour": row[1],
        "dernier_jour": row[2],
    }


def get_diagnostic_global():
    """Construit un diagnostic global local, sans connexion réseau ni action."""
    compactage = diagnostic_compactage_mesures()
    syntheses = get_diagnostic_syntheses()
    capteurs = get_diagnostic_mesures_par_capteur()
    return {
        "base": compactage,
        "nombre_mesures": get_nombre_mesures(),
        "mesures_entierement_zero": compter_mesures_entierement_zero(),
        "syntheses_entierement_zero": compter_syntheses_entierement_zero(),
        "syntheses": syntheses,
        "capteurs": capteurs,
    }
