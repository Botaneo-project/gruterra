import gc
import importlib
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "_app"
sys.path.insert(0, str(APP_DIR))


class BaseTemporaireMixin:
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.temp_dir.name) / "botaneo_test.db"
        os.environ["BOTANEO_DB_PATH"] = str(self.db_path)
        if "database" in sys.modules:
            self.database = importlib.reload(sys.modules["database"])
        else:
            self.database = importlib.import_module("database")

    def tearDown(self):
        os.environ.pop("BOTANEO_DB_PATH", None)
        if "database" in sys.modules:
            importlib.reload(sys.modules["database"])
        gc.collect()
        self.temp_dir.cleanup()


class TestSchemaEtNettoyage(BaseTemporaireMixin, unittest.TestCase):
    def test_schema_neuf_permet_plante_capteur_mesure(self):
        db = self.database
        db.initialiser_schema()
        plante_id = db.ajouter_plante("Crassula", "Crassula ovata", "Salon", "Intérieur")
        capteur_id = db.ajouter_capteur("Mi Flora", "AA:BB:CC:DD:EE:FF", plante_id)

        conn = db.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO mesures
                (date_heure, temperature, humidite, luminosite, conductivite, donnees_brutes, capteur_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("2026-09-20T13:39:29", 25.1, 26, 311, 90, "test", capteur_id),
            )
            conn.commit()
        finally:
            conn.close()

        mesures = db.get_mesures(plante_id=plante_id, limite=10)
        self.assertEqual(len(mesures), 1)
        self.assertEqual(mesures[0][3], 26)

    def test_suppression_mesures_sans_date_ne_garde_pas_les_valeurs_orphelines(self):
        db = self.database
        db.initialiser_schema()
        plante_id = db.ajouter_plante("Crassula", "Crassula ovata")
        capteur_id = db.ajouter_capteur("Mi Flora", "AA:BB:CC:DD:EE:FF", plante_id)

        conn = db.get_connection()
        try:
            conn.executemany(
                """
                INSERT INTO mesures
                (date_heure, temperature, humidite, luminosite, conductivite, donnees_brutes, capteur_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("2026-09-20T13:39:29", 25.1, 26, 311, 90, "ok", capteur_id),
                    ("", 25.1, 0, 999, 90, "date-vide", capteur_id),
                    ("date-invalide", 25.1, 18, 888, 90, "date-invalide", capteur_id),
                ],
            )
            conn.commit()
        finally:
            conn.close()

        resultat = db.supprimer_mesures_sans_date()
        self.assertEqual(resultat["mesures"], 2)
        mesures = db.get_mesures(plante_id=plante_id, limite=10)
        self.assertEqual(len(mesures), 1)
        self.assertEqual(mesures[0][1], "2026-09-20T13:39:29")


class TestSessionsArrosage(unittest.TestCase):
    def test_apports_proches_sont_regroupes_sans_modifier_les_lignes(self):
        database = importlib.import_module("database")
        arrosages = [
            (1, 1, "2026-09-20T10:00:00", 40, "normal", None, None, "début", "Volvic", None, 0),
            (2, 1, "2026-09-20T10:33:00", 55, "normal", None, None, "complément", "Volvic", None, 0),
            (3, 1, "2026-09-25T09:00:00", 80, "normal", None, None, "autre jour", "Volvic", None, 0),
        ]

        sessions = database.construire_sessions_arrosage(arrosages, fenetre_minutes=90)

        self.assertEqual(len(sessions), 2)
        self.assertTrue(sessions[0]["fractionnee"])
        self.assertEqual(sessions[0]["quantite_totale_ml"], 95)
        self.assertEqual([apport[0] for apport in sessions[0]["apports"]], [1, 2])
        self.assertFalse(sessions[1]["fractionnee"])
        self.assertEqual(sessions[1]["quantite_totale_ml"], 80)


class TestDatesBotaneo(unittest.TestCase):
    def test_parse_z_et_formatage_local(self):
        dates = importlib.import_module("botaneo_dates")
        utc = dates.parse_iso("2026-09-20T11:39:29Z")
        self.assertIsNotNone(utc)
        self.assertEqual(utc.tzinfo, timezone.utc)
        local = dates.vers_local_naif("2026-09-20T11:39:29Z")
        self.assertIsInstance(local, datetime)
        self.assertIsNone(local.tzinfo)
        self.assertIn("20/09/2026", dates.formater_local("2026-09-20T13:39:29"))


if __name__ == "__main__":
    unittest.main()
