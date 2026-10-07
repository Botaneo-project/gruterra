import gc
import importlib
import json
import os
import sys
import tempfile
import unittest
import zipfile
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


class TestAlertesEmail(unittest.TestCase):
    def test_memoire_alerte_respecte_delai_minimal(self):
        botaneo_email = importlib.import_module("botaneo_email")
        settings = botaneo_email.EmailSettings(
            enabled=True,
            mode="preview",
            host="",
            port=587,
            starttls=True,
            user="",
            secret_env="BOTANEO_SMTP_SECRET",
            sender="",
            recipients=(),
            subject_prefix="[Botaneo]",
            min_delay_hours_same_alert=24,
            require_manual_validation=True,
        )
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            path = Path(dossier) / "email_alert_state.local.json"
            botaneo_email.memoriser_alerte_envoyee(
                plante_id=12,
                type_alerte="rappel_arrosage",
                titre="Cactus",
                date_envoi=datetime(2026, 9, 20, 10, 0),
                path=path,
            )

            trop_tot = botaneo_email.alerte_autorisee(
                plante_id=12,
                type_alerte="rappel_arrosage",
                titre="Cactus",
                reference=datetime(2026, 9, 20, 20, 0),
                settings=settings,
                path=path,
            )
            apres_delai = botaneo_email.alerte_autorisee(
                plante_id=12,
                type_alerte="rappel_arrosage",
                titre="Cactus",
                reference=datetime(2026, 9, 21, 11, 0),
                settings=settings,
                path=path,
            )

        self.assertFalse(trop_tot["autorisee"])
        self.assertEqual(trop_tot["raison"], "délai minimal non écoulé")
        self.assertTrue(apres_delai["autorisee"])



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


class TestCyclesArrosage(unittest.TestCase):
    def test_cycle_arrosage_calcule_pic_et_sechage_simple(self):
        analyse_arrosage = importlib.import_module("services.analyse_arrosage")
        vue_historique = importlib.import_module("vue_historique")
        arrosages = [
            (1, 1, "2026-09-20T10:00:00", 80, "normal", None, None, "", "Volvic", None, 0),
        ]
        mesures = [
            (1, "2026-09-20T09:00:00", 24.0, 18, 100, 70, "", 1),
            (2, "2026-09-20T10:30:00", 24.1, 24, 120, 72, "", 1),
            (3, "2026-09-20T11:30:00", 24.2, 26, 130, 73, "", 1),
            (4, "2026-09-21T11:30:00", 24.0, 22, 110, 71, "", 1),
        ]

        cycles = analyse_arrosage.calculer_cycles_arrosage(mesures, arrosages)
        cycles_vue = vue_historique.calculer_cycles_arrosage(mesures, arrosages)

        self.assertEqual(cycles, cycles_vue)
        self.assertEqual(len(cycles), 1)
        cycle = cycles[0]
        self.assertEqual(cycle["humidite_avant"], 18)
        self.assertEqual(cycle["premiere_date"].isoformat(), "2026-09-20T10:30:00")
        self.assertEqual(cycle["pic_date"].isoformat(), "2026-09-20T11:30:00")
        self.assertEqual(cycle["derniere_date"].isoformat(), "2026-09-21T11:30:00")
        self.assertEqual(cycle["premiere_humidite"], 24)
        self.assertEqual(cycle["pic_humidite"], 26)
        self.assertEqual(cycle["derniere_humidite"], 22)
        self.assertEqual(cycle["baisse_apres_pic"], 4)
        self.assertEqual(cycle["hausse_apres_arrosage"], 8)
        self.assertEqual(cycle["ecart_final_depart"], 4)
        self.assertIn("retour partiel", cycle["lecture_courte"])
        self.assertEqual(cycle["lecture_sechage"], "séchage progressif après le pic")
        self.assertAlmostEqual(cycle["sechage"], -4.0)
        self.assertEqual(cycle["qualite_niveau"], "prudence")
        self.assertEqual(cycle["plus_grand_trou_h"], 24.0)

    def test_reperes_visuels_cycle_place_arrosage_pic_24h_48h(self):
        vue_historique = importlib.import_module("vue_historique")
        analyse_arrosage = importlib.import_module("services.analyse_arrosage")
        arrosages = [
            (1, 1, "2026-09-20T10:00:00", 80, "normal", None, None, "", "Volvic", None, 0),
        ]
        mesures = [
            (1, "2026-09-20T09:00:00", 24.0, 18, 100, 70, "", 1),
            (2, "2026-09-20T10:30:00", 24.1, 24, 120, 72, "", 1),
            (3, "2026-09-20T11:30:00", 24.2, 26, 130, 73, "", 1),
            (4, "2026-09-21T11:30:00", 24.0, 22, 110, 71, "", 1),
        ]
        cycle = analyse_arrosage.calculer_cycles_arrosage(mesures, arrosages)[0]

        reperes = vue_historique.reperes_visuels_cycle(cycle)
        par_cle = {repere["cle"]: repere for repere in reperes}

        self.assertEqual(par_cle["arrosage"]["heures"], 0)
        self.assertAlmostEqual(par_cle["pic"]["heures"], 1.5)
        self.assertEqual(par_cle["24h"]["heures"], 24)
        self.assertEqual(par_cle["48h"]["heures"], 48)
        self.assertEqual(par_cle["pic"]["couleur"], "ORANGE")

    def test_valeur_cycle_proche_repere_utilise_la_mesure_proche_sans_inventer(self):
        vue_historique = importlib.import_module("vue_historique")
        cycle = {
            "date": datetime(2026, 9, 20, 10, 0),
            "mesures": [
                (1, "2026-09-20T10:30:00", 24.0, 24, 120, 72, "", 1),
                (2, "2026-09-21T09:30:00", 24.1, 21, 130, 73, "", 1),
                (3, "2026-09-23T12:00:00", 24.2, 19, 140, 74, "", 1),
            ],
        }

        proche_24h = vue_historique.valeur_cycle_proche_repere(cycle, "Humidité", 24)
        absent_48h = vue_historique.valeur_cycle_proche_repere(cycle, "Humidité", 48)

        self.assertEqual(proche_24h["valeur"], 21)
        self.assertAlmostEqual(proche_24h["heures"], 23.5)
        self.assertIsNone(absent_48h)

    def test_interpreter_reponse_cycle_retour_depart(self):
        analyse_arrosage = importlib.import_module("services.analyse_arrosage")

        retour = analyse_arrosage.interpreter_reponse_cycle(18, 24, 30, 19, "bonne")
        faible = analyse_arrosage.interpreter_reponse_cycle(18, 18, 19, 18, "bonne")

        self.assertEqual(retour["hausse_apres_arrosage"], 12)
        self.assertEqual(retour["ecart_final_depart"], 1)
        self.assertIn("Retour proche", retour["lecture_courte"])
        self.assertIn("Réponse faible", faible["lecture_courte"])

    def test_analyse_cycles_distingue_reponse_sechage_et_tendance(self):
        analyse_arrosage = importlib.import_module("services.analyse_arrosage")
        cycles = [{
            "humidite_avant": 18,
            "premiere_humidite": 24,
            "pic_humidite": 30,
            "derniere_humidite": 19,
            "baisse_apres_pic": 11,
            "sechage": -5.5,
            "vitesse_24h": -2.2,
            "lecture_courte": "Retour proche du niveau de départ dans la zone du capteur.",
            "qualite": "bonne",
            "qualite_niveau": "bonne",
        }]

        texte = analyse_arrosage.analyser_cycles_arrosage(cycles)

        self.assertIn("réponse à l’arrosage", texte)
        self.assertIn("séchage après pic", texte)
        self.assertIn("tendance sur les dernières 24 h", texte)
        self.assertIn("zone du capteur", texte)

    def test_cycle_signale_interruption_longue_et_vitesse_24h(self):
        analyse_arrosage = importlib.import_module("services.analyse_arrosage")
        arrosages = [
            (1, 1, "2026-09-20T10:00:00", 80, "normal", None, None, "", "Volvic", None, 0),
        ]
        mesures = [
            (1, "2026-09-20T09:00:00", 24.0, 18, 100, 70, "", 1),
            (2, "2026-09-20T10:30:00", 24.1, 25, 120, 72, "", 1),
            (3, "2026-09-20T11:30:00", 24.2, 28, 130, 73, "", 1),
            (4, "2026-09-21T12:30:00", 24.0, 20, 110, 71, "", 1),
            (5, "2026-09-21T13:30:00", 24.0, 19, 110, 71, "", 1),
        ]

        cycle = analyse_arrosage.calculer_cycles_arrosage(mesures, arrosages)[0]

        self.assertEqual(cycle["qualite_niveau"], "interruption longue")
        self.assertIn("trou", cycle["qualite"])
        self.assertAlmostEqual(cycle["plus_grand_trou_h"], 25.0)
        self.assertAlmostEqual(cycle["vitesse_24h"], -8.307692307692307)


    def test_cycle_fractionne_part_du_debut_de_session(self):
        vue_historique = importlib.import_module("vue_historique")
        arrosages = [
            (1, 1, "2026-09-20T10:00:00", 40, "normal", None, None, "début", "Volvic", None, 0),
            (2, 1, "2026-09-20T10:33:00", 55, "normal", None, None, "complément", "Volvic", None, 0),
        ]
        mesures = [
            (1, "2026-09-20T09:30:00", 24.0, 18, 100, 70, "", 1),
            (2, "2026-09-20T10:20:00", 24.1, 22, 110, 72, "", 1),
            (3, "2026-09-20T10:45:00", 24.2, 25, 120, 73, "", 1),
            (4, "2026-09-20T12:00:00", 24.3, 24, 115, 72, "", 1),
        ]

        cycles = vue_historique.calculer_cycles_arrosage(mesures, arrosages)

        self.assertEqual(len(cycles), 1)
        cycle = cycles[0]
        self.assertEqual(cycle["date"].isoformat(), "2026-09-20T10:00:00")
        self.assertTrue(cycle["arrosage"]["fractionnee"])
        self.assertEqual(cycle["arrosage"]["quantite_totale_ml"], 95)
        self.assertEqual([apport[0] for apport in cycle["arrosage"]["apports"]], [1, 2])
        self.assertEqual([mesure[0] for mesure in cycle["mesures"]], [2, 3, 4])
        self.assertEqual(cycle["humidite_avant"], 18)
        self.assertEqual(cycle["premiere_humidite"], 22)
        self.assertEqual(cycle["pic_humidite"], 25)
        self.assertEqual(cycle["derniere_humidite"], 24)

    def test_compare_conditions_cycles_signale_quantite_et_qualite(self):
        analyse_arrosage = importlib.import_module("services.analyse_arrosage")
        cycle_a = {
            "arrosage": (1, 1, "2026-09-20T10:00:00", 80, "normal", None, None, "", "Volvic", None, 0),
            "qualite_niveau": "bonne",
        }
        cycle_b = {
            "arrosage": (2, 1, "2026-09-27T10:00:00", 130, "normal", None, None, "", "eau du robinet", None, 0),
            "qualite_niveau": "interruption longue",
        }

        comparaison = analyse_arrosage.comparer_conditions_cycles(cycle_a, cycle_b)

        self.assertEqual(comparaison["niveau"], "à éviter")
        self.assertIn("quantités différentes", comparaison["texte"])
        self.assertIn("types d’eau différents", comparaison["texte"])
        self.assertIn("interruption longue", comparaison["texte"])



class TestAnalyseLumiere(unittest.TestCase):
    def test_construit_expositions_balcon_et_filtre_par_jour(self):
        analyse_lumiere = importlib.import_module("services.analyse_lumiere")
        evenements = [
            (1, 1, "2026-09-25T10:00:00", "exposition", "Sortie balcon"),
            (2, 1, "2026-09-25T12:30:00", "exposition", "Retour intérieur"),
            (3, 1, "2026-09-26T09:00:00", "exposition", "Sortie balcon"),
        ]

        expositions = analyse_lumiere.construire_expositions_balcon(evenements)
        expositions_25 = analyse_lumiere.filtrer_expositions_jour(expositions, datetime(2026, 9, 25).date())
        expositions_26 = analyse_lumiere.filtrer_expositions_jour(expositions, datetime(2026, 9, 26).date())

        self.assertEqual(len(expositions), 2)
        self.assertEqual(expositions[0][0].isoformat(), "2026-09-25T10:00:00")
        self.assertEqual(expositions[0][1].isoformat(), "2026-09-25T12:30:00")
        self.assertIsNone(expositions[1][1])
        self.assertEqual(expositions_25, [expositions[0]])
        self.assertEqual(expositions_26, [expositions[1]])

    def test_resume_expositions_jour_separe_interieur_et_balcon(self):
        analyse_lumiere = importlib.import_module("services.analyse_lumiere")
        expositions = [(datetime(2026, 9, 25, 10, 0), datetime(2026, 9, 25, 12, 0))]
        mesures = [
            (1, "2026-09-25T09:00:00", 24.0, 20, 100, 70, "", 1),
            (2, "2026-09-25T10:30:00", 24.1, 20, 18000, 71, "", 1),
            (3, "2026-09-25T13:00:00", 24.2, 20, 200, 72, "", 1),
        ]

        resume = analyse_lumiere.resume_expositions_jour(mesures, expositions)

        self.assertIn("10:00 → 12:00", resume)
        self.assertIn("Hors balcon", resume)
        self.assertIn("Pendant balcon : 1 mesure(s)", resume)
        self.assertIn("Exposition lumineuse cumulée", resume)
        self.assertIn("pics lumineux", resume)

    def test_exposition_lumineuse_cumulee_ignore_les_grands_trous(self):
        analyse_lumiere = importlib.import_module("services.analyse_lumiere")
        mesures = [
            (1, "2026-09-25T09:00:00", 24.0, 20, 100, 70, "", 1),
            (2, "2026-09-25T10:00:00", 24.1, 20, 500, 71, "", 1),
            (3, "2026-09-25T11:00:00", 24.2, 20, 12000, 72, "", 1),
            (4, "2026-09-25T20:00:00", 24.3, 20, 50, 73, "", 1),
        ]

        stats = analyse_lumiere.calculer_exposition_lumineuse(mesures)

        self.assertEqual(stats["points"], 4)
        self.assertAlmostEqual(stats["duree_totale_h"], 2.0)
        self.assertAlmostEqual(stats["cumul_lux_h"], 600.0)
        self.assertAlmostEqual(stats["durees_par_plage_h"]["très faible"], 1.0)
        self.assertAlmostEqual(stats["durees_par_plage_h"]["faible"], 1.0)
        self.assertAlmostEqual(stats["durees_par_plage_h"]["forte"], 0.0)


class TestImportRaspberry(BaseTemporaireMixin, unittest.TestCase):
    def test_import_batch_est_idempotent_pour_mesure_courante(self):
        db = self.database
        db.initialiser_schema()
        plante_id = db.ajouter_plante("Crassula", "Crassula ovata")
        capteur_id = db.ajouter_capteur("Mi Flora", "AA:BB:CC:DD:EE:FF", plante_id)
        raspberry_sync = importlib.import_module("raspberry_sync")
        config = {
            "device_id": "pi-test",
            "sensors": ["AA:BB:CC:DD:EE:FF"],
        }
        row = {
            "device_id": "pi-test",
            "measurement_id": "m-001",
            "schema_version": 1,
            "kind": "current",
            "sensor_id": "AA:BB:CC:DD:EE:FF",
            "measured_at": "2026-09-20T13:39:29+00:00",
            "time_quality": "ntp",
            "raw": "01020304",
            "temperature_c": 25.1,
            "moisture_percent": 26,
            "illuminance_lux": 311,
            "conductivity_us_cm": 90,
        }
        batch = {"version": 1, "device_id": "pi-test", "rows": [row]}

        premier, ack1 = raspberry_sync.import_batch(db.DB_PATH, batch, config)
        second, ack2 = raspberry_sync.import_batch(db.DB_PATH, batch, config)

        self.assertEqual(premier["added"], 1)
        self.assertEqual(premier["current_added"], 1)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["current_duplicates"], 1)
        self.assertEqual(len(ack1["rows"]), 1)
        self.assertEqual(ack1, ack2)
        mesures = db.get_mesures(plante_id=plante_id, limite=10)
        self.assertEqual(len(mesures), 1)
        self.assertEqual(mesures[0][7], capteur_id)


    def test_import_batch_historique_stocke_archive_et_dedoublonne(self):
        db = self.database
        db.initialiser_schema()
        plante_id = db.ajouter_plante("Crassula", "Crassula ovata")
        capteur_id = db.ajouter_capteur("Mi Flora", "AA:BB:CC:DD:EE:FF", plante_id)
        raspberry_sync = importlib.import_module("raspberry_sync")
        config = {
            "device_id": "pi-test",
            "sensors": ["AA:BB:CC:DD:EE:FF"],
        }
        sensor_seconds = 1_908_000
        frame = bytearray(16)
        frame[0:4] = sensor_seconds.to_bytes(4, "little")
        frame[4:6] = int(25.1 * 10).to_bytes(2, "little", signed=True)
        frame[7:11] = int(311).to_bytes(4, "little")
        frame[11] = 26
        frame[12:14] = int(90).to_bytes(2, "little")
        raw = frame.hex()
        row = {
            "device_id": "pi-test",
            "measurement_id": "h-001",
            "schema_version": 1,
            "kind": "history",
            "sensor_id": "AA:BB:CC:DD:EE:FF",
            "sensor_seconds": sensor_seconds,
            "measured_at": "2026-09-20T13:39:29+00:00",
            "time_quality": "estimated_from_sensor_clock",
            "raw": raw,
            "temperature_c": 25.1,
            "moisture_percent": 26,
            "illuminance_lux": 311,
            "conductivity_us_cm": 90,
        }
        batch = {"version": 1, "device_id": "pi-test", "rows": [row]}

        premier, ack1 = raspberry_sync.import_batch(db.DB_PATH, batch, config)
        second, ack2 = raspberry_sync.import_batch(db.DB_PATH, batch, config)

        self.assertEqual(premier["added"], 1)
        self.assertEqual(premier["history_added"], 1)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["history_duplicates"], 1)
        self.assertEqual(ack1, ack2)
        mesures = db.get_mesures(plante_id=plante_id, limite=10)
        self.assertEqual(len(mesures), 1)
        self.assertEqual(mesures[0][3], 26)
        self.assertEqual(mesures[0][7], capteur_id)
        conn = db.get_connection()
        try:
            archives = conn.execute("SELECT capteur_id, timestamp_capteur, raw_hex, statut FROM historique_miflora_brut").fetchall()
        finally:
            conn.close()
        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0][0], capteur_id)
        self.assertEqual(archives[0][1], sensor_seconds)
        self.assertEqual(archives[0][2], raw)
        self.assertEqual(archives[0][3], "raspberry_estimated_from_sensor_clock")


class TestHistoriqueZerosSuspects(unittest.TestCase):
    def test_zero_humidite_isole_est_exclu_du_graphique_mais_identifie(self):
        vue_historique = importlib.import_module("vue_historique")
        mesures = [
            (1, "2026-09-20T10:00:00", 24.0, 22, 120, 80, "", 1),
            (2, "2026-09-20T11:00:00", 24.1, 0, 130, 81, "", 1),
            (3, "2026-09-20T12:00:00", 24.2, 21, 140, 82, "", 1),
        ]

        suspects = vue_historique.ids_humidite_zero_suspects(mesures)
        mesures_filtrees, suspects_filtres = vue_historique.filtrer_mesures_pour_serie(mesures, "Humidité")

        self.assertEqual(suspects, {2})
        self.assertEqual(suspects_filtres, {2})
        self.assertEqual([mesure[0] for mesure in mesures_filtrees], [1, 3])
        self.assertEqual(len(mesures), 3)

    def test_zero_humidite_non_encadre_reste_conserve(self):
        vue_historique = importlib.import_module("vue_historique")
        mesures = [
            (1, "2026-09-20T10:00:00", 24.0, 0, 120, 80, "", 1),
            (2, "2026-09-20T11:00:00", 24.1, 0, 130, 81, "", 1),
            (3, "2026-09-20T12:00:00", 24.2, 3, 140, 82, "", 1),
        ]

        mesures_filtrees, suspects = vue_historique.filtrer_mesures_pour_serie(mesures, "Humidité")

        self.assertEqual(suspects, set())
        self.assertEqual(mesures_filtrees, mesures)


class TestPreparationMiseAJour(unittest.TestCase):
    def test_plan_mise_a_jour_preserve_les_donnees_personnelles(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            (racine / "_config").mkdir()
            (racine / "_app" / "data").mkdir(parents=True)
            (racine / "plantes.db").write_text("sqlite fictif", encoding="utf-8")

            plan = botaneo_update.construire_plan_mise_a_jour(racine)
            texte = botaneo_update.formater_plan_mise_a_jour(plan)

        elements = {element.chemin: element for element in plan["elements_personnels"]}
        self.assertTrue(elements["plantes.db"].existe)
        self.assertTrue(elements["_config"].existe)
        self.assertTrue(elements["_app/data"].existe)
        self.assertIn("préserver _config", texte)
        self.assertIn("Interdit sans validation explicite", texte)
        self.assertIn("manifeste de version local absent", texte.lower())
        self.assertIn("Séparation programme / données", texte)
        self.assertIn("programme remplaçable", texte)

    def test_separation_programme_donnees_identifie_les_zones(self):
        botaneo_update = importlib.import_module("botaneo_update")

        separation = botaneo_update.construire_separation_programme_donnees(Path("C:/Plantes"))

        self.assertIn("_app", separation["programme_actuel"])
        self.assertIn("_config", separation["donnees_utilisateur_actuelles"])
        self.assertIn("base SQLite réelle", separation["donnees_utilisateur_futures"])

    def test_plan_mise_a_jour_ne_detaille_pas_les_secrets(self):
        botaneo_update = importlib.import_module("botaneo_update")

        plan = botaneo_update.construire_plan_mise_a_jour(Path("C:/Plantes"))
        texte = botaneo_update.formater_plan_mise_a_jour(plan).lower()

        self.assertIn("_config", texte)
        self.assertNotIn("netatmo_config.json", texte)
        self.assertNotIn("email.local.json", texte)
        self.assertNotIn("raspberry.local.json", texte)

    def test_verification_plan_bloque_sans_separation_programme_donnees(self):
        botaneo_update = importlib.import_module("botaneo_update")
        plan = {
            "elements_personnels": [],
            "separation_programme_donnees": {},
        }

        verification = botaneo_update.verifier_plan_mise_a_jour(plan)

        self.assertEqual(verification["statut"], "bloque")
        self.assertIn("séparation programme/données absente", verification["message"])

    def test_verification_plan_mise_a_jour_pret_prudence_bloque(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            (racine / "_config").mkdir()
            (racine / "_security_backups").mkdir()
            (racine / "plantes.db").write_text("sqlite fictif", encoding="utf-8")

            pret = botaneo_update.construire_plan_mise_a_jour(racine)["verification"]
            (racine / "_security_backups").rmdir()
            prudence = botaneo_update.construire_plan_mise_a_jour(racine)["verification"]
            (racine / "plantes.db").unlink()
            sans_base = botaneo_update.construire_plan_mise_a_jour(racine)["verification"]

        self.assertEqual(pret["statut"], "pret")
        self.assertEqual(prudence["statut"], "prudence")
        self.assertEqual(sans_base["statut"], "prudence")
        self.assertFalse(pret["application_autorisee"])
        self.assertIn("plantes.db", sans_base["message"])

    def test_resume_court_mise_a_jour_est_lisible_et_non_applicatif(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            (racine / "_config").mkdir()
            (racine / "plantes.db").write_text("sqlite fictif", encoding="utf-8")
            plan = botaneo_update.construire_plan_mise_a_jour(racine)
            resume = botaneo_update.resume_court_mise_a_jour(plan).lower()

        self.assertIn("préparation uniquement", resume)
        self.assertIn("application automatique : désactivée", resume)
        self.assertIn("données personnelles", resume)
        self.assertIn("fichiers secrets", resume)
        self.assertNotIn("netatmo_config.json", resume)

    def test_resume_court_affiche_notes_version_si_disponibles(self):
        botaneo_update = importlib.import_module("botaneo_update")
        plan = {
            "verification": {"statut": "pret", "message": "OK"},
            "elements_personnels": [],
            "statut_version": {
                "message": "Version distante 0.2.0 disponible ; sauvegarde et validation nécessaires avant application.",
                "notes": "Amélioration historique",
                "url": "https://example.invalid/release",
            },
        }
        resume = botaneo_update.resume_court_mise_a_jour(plan)

        self.assertIn("Amélioration historique", resume)
        self.assertIn("https://example.invalid/release", resume)
        self.assertIn("application automatique : désactivée", resume)

    def test_version_locale_lue_depuis_fichier_version(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            self.assertEqual(botaneo_update.lire_version_locale(racine), botaneo_update.VERSION_LOCALE_DEFAUT)
            (racine / "VERSION").write_text("0.1.4-dev\n", encoding="utf-8")
            self.assertEqual(botaneo_update.lire_version_locale(racine), "0.1.4-dev")

    def test_statut_version_depuis_manifest_local(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            manifest = Path(dossier) / "version.json"
            absent = botaneo_update.construire_statut_version_depuis_manifest("0.1.0", manifest)
            manifest.write_text('{"version": "0.2.0", "notes": "Correction test", "url": "https://example.invalid/release"}', encoding="utf-8")
            disponible = botaneo_update.construire_statut_version_depuis_manifest("0.1.0", manifest)

        self.assertEqual(absent["statut"], "verification_non_configuree")
        self.assertEqual(disponible["statut"], "mise_a_jour_disponible")
        self.assertFalse(disponible["application_autorisee"])
        self.assertIn("source", disponible)
        self.assertEqual(disponible["notes"], "Correction test")
        self.assertEqual(disponible["url"], "https://example.invalid/release")

    def test_statut_version_depuis_manifest_distant_reste_non_applicatif(self):
        botaneo_update = importlib.import_module("botaneo_update")

        class ReponseFictive:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def read(self, _taille):
                return b'{"version":"0.3.0","notes":"Test distant","url":"https://example.invalid/release","archive_url":"https://example.invalid/app.zip","sha256":"abc","mise_a_jour_automatique":true}'

        def ouvreur(_requete, timeout=0):
            return ReponseFictive()

        manifest = botaneo_update.lire_manifest_version_distant("https://example.invalid/version.json", ouvreur=ouvreur)
        statut = botaneo_update.construire_statut_version_depuis_manifest_charge("0.1.0", manifest)

        self.assertTrue(manifest["disponible"])
        self.assertEqual(statut["statut"], "mise_a_jour_disponible")
        self.assertEqual(statut["notes"], "Test distant")
        self.assertEqual(statut["archive_url"], "https://example.invalid/app.zip")
        self.assertFalse(statut["application_autorisee"])
        self.assertTrue(statut["manifest_auto_update"])

    def test_statut_version_distant_indisponible_retombe_sur_local(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            manifest = Path(dossier) / "version_manifest.json"
            manifest.write_text('{"version": "0.2.0", "notes": "Fallback local"}', encoding="utf-8")

            def ouvreur(_requete, timeout=0):
                raise OSError("réseau indisponible")

            original = botaneo_update.lire_manifest_version_distant
            try:
                botaneo_update.lire_manifest_version_distant = lambda url, timeout=5: original(url, timeout=timeout, ouvreur=ouvreur)
                statut = botaneo_update.construire_statut_version(
                    "0.1.0",
                    chemin_manifest_local=manifest,
                    url_manifest_distant="https://example.invalid/version.json",
                    verifier_distant=True,
                )
            finally:
                botaneo_update.lire_manifest_version_distant = original

        self.assertEqual(statut["statut"], "mise_a_jour_disponible")
        self.assertIn("manifeste local utilisé", statut["message"].lower())
        self.assertIn("Manifeste distant non vérifié", statut["avertissement_distant"])
        self.assertEqual(statut["notes"], "Fallback local")
        self.assertFalse(statut["application_autorisee"])

    def test_libelle_statut_global_est_lisible(self):
        botaneo_update = importlib.import_module("botaneo_update")

        self.assertEqual(botaneo_update.libelle_statut_global("pret_a_verifier"), "Prêt pour vérification manuelle")
        self.assertEqual(botaneo_update.libelle_statut_global("prudence"), "À contrôler avant mise à jour")
        self.assertEqual(botaneo_update.libelle_statut_global("bloque"), "Bloqué tant que les protections manquent")
        self.assertEqual(botaneo_update.libelle_statut_global("autre"), "État inconnu")

    def test_diagnostic_mise_a_jour_reste_non_applicatif(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            (racine / "_config").mkdir()
            (racine / "_security_backups").mkdir()
            (racine / "plantes.db").write_text("sqlite fictif", encoding="utf-8")
            diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(racine)
            texte = botaneo_update.formater_diagnostic_mise_a_jour(diagnostic)

        self.assertEqual(diagnostic["statut_global"], "pret_a_verifier")
        self.assertFalse(diagnostic["application_autorisee"])
        self.assertIn("plantes.db", diagnostic["elements_presents"])
        self.assertIn("Diagnostic de mise à jour Gruterra", texte)
        self.assertIn("Prêt pour vérification manuelle", texte)
        self.assertIn("Application automatique autorisée : non", texte)

    def test_exporter_diagnostic_mise_a_jour_json(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            (racine / "_config").mkdir()
            (racine / "_security_backups").mkdir()
            (racine / "plantes.db").write_text("sqlite fictif", encoding="utf-8")
            diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(racine)
            texte = botaneo_update.exporter_diagnostic_mise_a_jour_json(diagnostic)
            donnees = json.loads(texte)

        self.assertEqual(donnees["type"], "diagnostic_mise_a_jour_botaneo")
        self.assertEqual(donnees["statut_global"], "pret_a_verifier")
        self.assertFalse(donnees["application_autorisee"])
        self.assertIn("plantes.db", donnees["elements_presents"])
        self.assertNotIn("netatmo_config.json", texte)

    def test_diagnostic_mise_a_jour_installation_fraiche_est_en_prudence(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(racine)

        self.assertEqual(diagnostic["statut_global"], "prudence")
        self.assertIn("contrôler les avertissements", diagnostic["prochaines_actions"][0])
        self.assertIn("plantes.db absente", diagnostic["verification"]["message"])

    def test_diagnostic_mise_a_jour_mode_demo_utilise_base_demo(self):
        botaneo_update = importlib.import_module("botaneo_update")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            demo_dir = racine / "_app" / "data" / "demo"
            demo_dir.mkdir(parents=True)
            (demo_dir / "plantes_demo.db").write_text("sqlite demo", encoding="utf-8")

            diagnostic = botaneo_update.construire_diagnostic_mise_a_jour(racine)
            texte = botaneo_update.formater_diagnostic_mise_a_jour(diagnostic)

        self.assertNotEqual(diagnostic["statut_global"], "bloque")
        self.assertEqual(diagnostic["mode"], "démo")
        self.assertIn("Base de démonstration détectée : plantes_demo.db", texte)
        self.assertNotIn("base plantes.db introuvable", texte)
        self.assertNotIn("plantes.db, _security_backups, _historique", texte)

    def test_comparer_versions_ne_declenche_jamais_application(self):
        botaneo_update = importlib.import_module("botaneo_update")

        disponible = botaneo_update.comparer_versions("0.1.0", "0.2.0")
        stable = botaneo_update.comparer_versions("0.1.0-dev", "0.1.0")
        a_jour = botaneo_update.comparer_versions("0.1.0", "0.1.0")

        self.assertEqual(disponible["statut"], "mise_a_jour_disponible")
        self.assertEqual(stable["statut"], "version_stable_disponible")
        self.assertEqual(a_jour["statut"], "a_jour")
        self.assertFalse(disponible["application_autorisee"])



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

class TestAssistantMiseAJour(unittest.TestCase):
    def test_manifest_incomplet_refuse_application(self):
        update_gruterra = importlib.import_module("update_gruterra")
        diagnostic = {
            "statut_global": "pret_a_verifier",
            "version": {
                "manifest_auto_update": False,
                "archive_url": "",
                "sha256": "",
            },
        }

        ok, erreurs = update_gruterra.valider_manifest_applicable(diagnostic)

        self.assertFalse(ok)
        self.assertIn("mise_a_jour_automatique vaut false dans le manifeste", erreurs)
        self.assertIn("archive_url absent du manifeste", erreurs)
        self.assertIn("sha256 absent ou invalide dans le manifeste", erreurs)

    def test_version_deja_a_jour_refuse_application_normale(self):
        update_gruterra = importlib.import_module("update_gruterra")
        diagnostic = {
            "statut_global": "pret_a_verifier",
            "version": {
                "statut": "a_jour",
                "manifest_auto_update": True,
                "archive_url": "https://example.invalid/gruterra.zip",
                "sha256": "a" * 64,
            },
        }

        ok, erreurs = update_gruterra.valider_manifest_applicable(diagnostic)
        resultat = update_gruterra.appliquer_mise_a_jour(diagnostic, Path.cwd(), dry_run=True)
        message = update_gruterra.construire_message_validation(diagnostic)

        self.assertFalse(ok)
        self.assertIn("Gruterra est déjà à jour", erreurs)
        self.assertFalse(resultat["ok"])
        self.assertFalse(resultat["applique"])
        self.assertIn("déjà à jour", message)

    def test_message_validation_supporte_unicode_patch_note(self):
        update_gruterra = importlib.import_module("update_gruterra")
        diagnostic = {
            "statut_global": "pret_a_verifier",
            "mode": "démo",
            "application_autorisee": False,
            "version": {
                "notes": "é è à ç œ ’ — → 🇫🇷 🇬🇧 🌱",
                "manifest_auto_update": False,
                "archive_url": "",
                "sha256": "",
            },
            "verification": {"statut": "prudence", "message": "é è à ç œ ’ — → 🇫🇷 🇬🇧 🌱"},
            "elements_presents": [],
            "elements_absents": [],
            "prochaines_actions": ["vérifier → 🇫🇷"],
            "resume": "Patch note : é è à ç œ ’ — → 🇫🇷 🇬🇧 🌱",
        }

        message = update_gruterra.construire_message_validation(diagnostic)

        self.assertIn("🇫🇷", message)
        self.assertIn("🌱", message)
        self.assertIsInstance(message.encode("utf-8"), bytes)

    def test_update_gruterra_configure_sorties_utf8(self):
        update_gruterra = importlib.import_module("update_gruterra")

        self.assertTrue(callable(update_gruterra.configurer_sorties_utf8))
        self.assertTrue(callable(update_gruterra.safe_print))

    def test_listing_update_preserve_les_donnees_personnelles(self):
        update_gruterra = importlib.import_module("update_gruterra")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            source = Path(dossier)
            (source / "_app").mkdir()
            (source / "_app" / "data").mkdir()
            (source / "_config").mkdir()
            (source / "discord_bot").mkdir()
            (source / "README.md").write_text("nouveau readme", encoding="utf-8")
            (source / "_app" / "interface.py").write_text("print('ok')", encoding="utf-8")
            (source / "_app" / "data" / "demo.db").write_text("demo", encoding="utf-8")
            (source / "_config" / "secret.json").write_text("secret", encoding="utf-8")
            (source / "discord_bot" / ".env").write_text("token", encoding="utf-8")
            (source / "plantes.db").write_text("base", encoding="utf-8")

            fichiers = {item.as_posix() for item in update_gruterra.lister_fichiers_programme(source)}

        self.assertIn("README.md", fichiers)
        self.assertIn("_app/interface.py", fichiers)
        self.assertNotIn("_app/data/demo.db", fichiers)
        self.assertNotIn("_config/secret.json", fichiers)
        self.assertNotIn("discord_bot/.env", fichiers)
        self.assertNotIn("plantes.db", fichiers)


class TestPreparationRelease(unittest.TestCase):
    def test_validation_release_detecte_manifest_et_sha256_coherents(self):
        prepare_release = importlib.import_module("prepare_release")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            archive = racine / "gruterra-9.9.9.zip"
            archive.write_bytes(b"archive fictive")
            sha256 = prepare_release.calculer_sha256(archive)
            manifest = racine / "version_manifest-9.9.9-ready.json"
            manifest.write_text(
                json.dumps(
                    {
                        "version": "9.9.9",
                        "archive_url": "https://github.com/Botaneo-project/gruterra/releases/download/v9.9.9/gruterra-9.9.9.zip",
                        "sha256": sha256,
                        "mise_a_jour_automatique": True,
                    }
                ),
                encoding="utf-8",
            )
            changelog = racine / "gruterra-9.9.9-changelog.md"
            changelog.write_text("# Gruterra 9.9.9\n\n## Changements importants\n- Test\n", encoding="utf-8")

            erreurs = prepare_release.valider_sortie_release("9.9.9", archive, sha256, manifest, changelog)

        self.assertEqual(erreurs, [])

    def test_validation_release_refuse_sha256_incoherent(self):
        prepare_release = importlib.import_module("prepare_release")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            archive = racine / "gruterra-9.9.9.zip"
            archive.write_bytes(b"archive fictive")
            manifest = racine / "version_manifest-9.9.9-ready.json"
            manifest.write_text(
                json.dumps(
                    {
                        "version": "9.9.9",
                        "archive_url": "https://github.com/Botaneo-project/gruterra/releases/download/v9.9.9/gruterra-9.9.9.zip",
                        "sha256": "0" * 64,
                        "mise_a_jour_automatique": True,
                    }
                ),
                encoding="utf-8",
            )
            changelog = racine / "gruterra-9.9.9-changelog.md"
            changelog.write_text("# Gruterra 9.9.9\n\n## Changements importants\n- Test\n", encoding="utf-8")

            erreurs = prepare_release.valider_sortie_release("9.9.9", archive, "0" * 64, manifest, changelog)

        self.assertTrue(any("SHA256 recalculé" in erreur for erreur in erreurs))
class TestPreferencesInterface(unittest.TestCase):
    def test_i18n_normalise_langue_et_traduit(self):
        i18n = importlib.import_module("i18n")

        self.assertEqual(i18n.normaliser_langue("en"), "en")
        self.assertEqual(i18n.normaliser_langue("fr"), "fr")
        self.assertEqual(i18n.normaliser_langue("de"), "fr")
        self.assertEqual(i18n.traduire("settings", "en"), "⚙ Settings")
        self.assertEqual(i18n.traduire("settings", "fr"), "⚙ Paramètres")

    def test_preferences_langue_interface_sont_locales(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            os.environ["BOTANEO_CONFIG_DIR"] = dossier
            try:
                if "botaneo_config" in sys.modules:
                    importlib.reload(sys.modules["botaneo_config"])
                if "ui_preferences" in sys.modules:
                    ui_preferences = importlib.reload(sys.modules["ui_preferences"])
                else:
                    ui_preferences = importlib.import_module("ui_preferences")

                self.assertEqual(ui_preferences.charger_langue_interface(), "fr")
                self.assertTrue(ui_preferences.sauvegarder_langue_interface("en"))
                self.assertEqual(ui_preferences.charger_langue_interface(), "en")
                self.assertTrue(ui_preferences.sauvegarder_langue_interface("invalide"))
                self.assertEqual(ui_preferences.charger_langue_interface(), "fr")
            finally:
                os.environ.pop("BOTANEO_CONFIG_DIR", None)
                if "botaneo_config" in sys.modules:
                    importlib.reload(sys.modules["botaneo_config"])
                if "ui_preferences" in sys.modules:
                    importlib.reload(sys.modules["ui_preferences"])


class TestInstallateurWindows(unittest.TestCase):
    def test_installer_windows_verifie_les_dependances_essentielles(self):
        bat = Path(__file__).resolve().parents[1] / "Installer_Gruterra.bat"
        contenu = bat.read_text(encoding="ascii")

        self.assertIn("[1/6] Verification de Python", contenu)
        self.assertIn("[5/6] Verification de Gruterra", contenu)
        self.assertIn("pip disponible dans l'environnement local", contenu)
        self.assertNotIn("pip install --upgrade pip", contenu)
        self.assertIn("pip install -r requirements.txt", contenu)
        self.assertIn("import tkinter, requests, bleak", contenu)
        self.assertIn("Python est introuvable sur ce PC", contenu)
        self.assertIn("Invoke-WebRequest", contenu)
        self.assertIn("InstallAllUsers=0", contenu)
        self.assertIn("PYTHON_EXPECTED_EXE", contenu)
        self.assertIn("Programs\\Python\\Python312\\python.exe", contenu)
        self.assertIn("Installation interrompue ou incomplete", contenu)


class TestLanceursWindows(unittest.TestCase):
    def test_lanceurs_bat_utilisent_environnement_local(self):
        racine = Path(__file__).resolve().parents[1]
        demo = (racine / "Lancer_Demo.bat").read_text(encoding="ascii")
        reel = (racine / "Lancer_Gruterra.bat").read_text(encoding="ascii")

        self.assertIn(".venv\\Scripts\\python.exe", demo)
        self.assertIn("Lancer_Demo.py", demo)
        self.assertIn("Installer_Gruterra.bat", demo)
        self.assertIn("call :ensure_environment", demo)
        self.assertIn("pause", demo.lower())
        self.assertIn(".venv\\Scripts\\python.exe", reel)
        self.assertIn("Lancer_Gruterra.py", reel)
        self.assertIn("Installer_Gruterra.bat", reel)
        self.assertIn("call :ensure_environment", reel)
        self.assertIn("pause", reel.lower())


class TestSauvegardeUtilisateur(unittest.TestCase):
    def test_manifest_sauvegarde_complete_signale_le_prive(self):
        sauvegarde = importlib.import_module("sauvegarde_utilisateur")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            (racine / "_config").mkdir()
            (racine / "_config" / "netatmo_config.json").write_text("{}", encoding="utf-8")
            manifest = sauvegarde.construire_manifest_sauvegarde(racine, mode="complete")

        self.assertTrue(manifest["contient_elements_prives"])
        self.assertIn("Ne la partagez pas", manifest["avertissement"])
        self.assertFalse(manifest["restauration_automatique"])

    def test_creer_export_donnees_n_inclut_pas_config_privee(self):
        sauvegarde = importlib.import_module("sauvegarde_utilisateur")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            (racine / "plantes.db").write_text("base fictive", encoding="utf-8")
            (racine / "_config").mkdir()
            (racine / "_config" / "secret.local.json").write_text("secret", encoding="utf-8")
            archive = sauvegarde.creer_sauvegarde_utilisateur(racine, mode="donnees")
            with zipfile.ZipFile(archive) as zipf:
                noms = set(zipf.namelist())

        self.assertIn("plantes.db", noms)
        self.assertIn("MANIFEST_GRUTERRA_BACKUP.json", noms)
        self.assertNotIn("_config/secret.local.json", noms)

    def test_creer_sauvegarde_complete_peut_inclure_config_privee(self):
        sauvegarde = importlib.import_module("sauvegarde_utilisateur")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
            racine = Path(dossier)
            (racine / "plantes.db").write_text("base fictive", encoding="utf-8")
            (racine / "_config").mkdir()
            (racine / "_config" / "secret.local.json").write_text("secret", encoding="utf-8")
            archive = sauvegarde.creer_sauvegarde_utilisateur(racine, mode="complete")
            with zipfile.ZipFile(archive) as zipf:
                noms = set(zipf.namelist())
                manifest = json.loads(zipf.read("MANIFEST_GRUTERRA_BACKUP.json").decode("utf-8"))

        self.assertIn("_config/secret.local.json", noms)
        self.assertTrue(manifest["contient_elements_prives"])

    def test_rapport_sauvegarde_affiche_horaire_et_avertissement(self):
        sauvegarde = importlib.import_module("sauvegarde_utilisateur")
        manifest = {
            "mode": "complete",
            "cree_le": "2026-10-06T21:15:00",
            "contient_elements_prives": True,
            "avertissement": "Sauvegarde privée",
            "elements": [
                {"chemin": "plantes.db", "existe": True},
                {"chemin": "_config", "existe": True},
                {"chemin": "_historique", "existe": False},
            ],
        }
        rapport = sauvegarde.formater_rapport_sauvegarde(manifest)

        self.assertIn("Horaire : 2026-10-06T21:15:00", rapport)
        self.assertIn("Mode : complete", rapport)
        self.assertIn("Éléments inclus : plantes.db, _config", rapport)
        self.assertIn("Éléments absents : _historique", rapport)
        self.assertIn("Sauvegarde privée", rapport)


class TestParametresUtf8(unittest.TestCase):
    def test_parametres_nettoient_textes_update_utf8(self):
        interface = Path(__file__).resolve().parents[1] / "_app" / "interface.py"
        contenu = interface.read_text(encoding="utf-8")

        self.assertIn("def texte_interface_utf8_sur", contenu)
        self.assertIn("texte_interface_utf8_sur(texte)", contenu)
        self.assertIn("texte_interface_utf8_sur(botaneo_update.formater_diagnostic_mise_a_jour", contenu)
        self.assertIn("texte_interface_utf8_sur(botaneo_update.exporter_diagnostic_mise_a_jour_json", contenu)


class TestUpdateUtf8Interface(unittest.TestCase):
    def test_interface_lance_update_en_utf8(self):
        interface = Path(__file__).resolve().parents[1] / "_app" / "interface.py"
        contenu = interface.read_text(encoding="utf-8")

        self.assertIn('environnement["PYTHONIOENCODING"] = "utf-8"', contenu)
        self.assertIn('environnement["PYTHONUTF8"] = "1"', contenu)
        self.assertIn("env=environnement", contenu)


class TestPatchNoteUpdateInterface(unittest.TestCase):
    def test_interface_contient_patch_note_update(self):
        interface = Path(__file__).resolve().parents[1] / "_app" / "interface.py"
        contenu = interface.read_text(encoding="utf-8")

        self.assertIn("def patch_note_update_a_propos", contenu)
        self.assertIn("Patch note Gruterra", contenu)
        self.assertIn("patch_note_update_a_propos(verifier_distant=True)", contenu)


class TestParametresLangue(unittest.TestCase):
    def test_parametres_langue_affiche_drapeaux(self):
        interface = Path(__file__).resolve().parents[1] / "_app" / "interface.py"
        contenu = interface.read_text(encoding="utf-8")

        self.assertIn('"🇫🇷 FR": "fr"', contenu)
        self.assertIn('"🇬🇧 EN": "en"', contenu)
        self.assertIn("options_langue.get(langue_var.get(), langue_var.get())", contenu)


class TestRedemarrageUpdate(unittest.TestCase):
    def test_interface_prepare_redemarrage_post_update(self):
        interface = Path(__file__).resolve().parents[1] / "_app" / "interface.py"
        contenu = interface.read_text(encoding="utf-8")

        self.assertIn("def update_appliquee_depuis_resultat", contenu)
        self.assertIn("def proposer_redemarrage_apres_update", contenu)
        self.assertIn("def redemarrer_gruterra", contenu)
        self.assertIn("Lancer_Demo.py", contenu)
        self.assertIn("Lancer_Gruterra.py", contenu)
        self.assertIn("update_restart_question", contenu)


class TestUpdateDansParametres(unittest.TestCase):
    def test_parametres_contiennent_bloc_mises_a_jour(self):
        interface = Path(__file__).resolve().parents[1] / "_app" / "interface.py"
        contenu = interface.read_text(encoding="utf-8")

        self.assertIn('t("updates_section")', contenu)
        self.assertIn("updates_settings_help", contenu)
        self.assertIn("settings_verifier_update", contenu)
        self.assertIn("settings_tester_update", contenu)
        self.assertIn("lancer_application_update", contenu)

    def test_parametres_notes_update_sont_defilables_et_copiables(self):
        interface = Path(__file__).resolve().parents[1] / "_app" / "interface.py"
        contenu = interface.read_text(encoding="utf-8")

        self.assertIn("update_info_zone = tk.Text", contenu)
        self.assertIn("update_info_scroll = ttk.Scrollbar", contenu)
        self.assertIn("def set_update_info", contenu)
        self.assertIn("afficher_resultat=set_update_info", contenu)
