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
        self.assertEqual(cycle["premiere_humidite"], 24)
        self.assertEqual(cycle["pic_humidite"], 26)
        self.assertEqual(cycle["derniere_humidite"], 22)
        self.assertEqual(cycle["baisse_apres_pic"], 4)
        self.assertAlmostEqual(cycle["sechage"], -4.0)
        self.assertEqual(cycle["qualite_niveau"], "prudence")
        self.assertEqual(cycle["plus_grand_trou_h"], 24.0)

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
        self.assertIn("vérification distante non configurée", texte.lower())
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
            bloque = botaneo_update.construire_plan_mise_a_jour(racine)["verification"]

        self.assertEqual(pret["statut"], "pret")
        self.assertEqual(prudence["statut"], "prudence")
        self.assertEqual(bloque["statut"], "bloque")
        self.assertFalse(pret["application_autorisee"])
        self.assertIn("plantes.db", bloque["message"])

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
