import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("BOTANEO_DB_PATH", BASE_DIR / "plantes.db"))


def get_connection():
    """Ouvre une connexion à la base de données."""
    return sqlite3.connect(DB_PATH)


# ============================================================
# PLANTES
# ============================================================

def get_plantes():
    """Retourne toutes les plantes."""

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

    conn = get_connection()

    nombre = conn.execute("""
        SELECT COUNT(*)
        FROM mesures
    """).fetchone()[0]

    conn.close()

    return nombre


def get_derniere_mesure():
    """Retourne la dernière mesure enregistrée."""

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

