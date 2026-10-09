"""FR/EN : catalogue, contexte, sélection des séries et invariance des calculs."""
import ast
import copy
import json
import string
import sys
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / '_app'
sys.path.insert(0, str(APP))
from i18n import charger_locale, langue_courante, traduire_courant, utiliser_langue

class TestCatalogue(unittest.TestCase):
    def test_catalogues_et_parametres_identiques(self):
        fr, en = charger_locale('fr'), charger_locale('en')
        self.assertEqual(set(fr), set(en))
        formatter = string.Formatter()
        for key in fr:
            with self.subTest(key=key):
                self.assertTrue(fr[key].strip())
                self.assertTrue(en[key].strip())
                fields = lambda text: sorted((name, spec, conv or '') for _, name, spec, conv in formatter.parse(text) if name is not None)
                self.assertEqual(fields(fr[key]), fields(en[key]))

    def test_cles_reellement_utilisees_existent(self):
        keys = charger_locale('fr')
        files = list(APP.rglob('*.py')) + [APP.parent / 'update_gruterra.py']
        for path in files:
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'t', 'vh_t', '_tr', 'traduire', 'traduire_courant'} and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    with self.subTest(file=path.name, line=node.lineno):
                        self.assertIn(node.args[0].value, keys)

    def test_contexte_restaure_et_configuration_invalide(self):
        with patch('ui_preferences.charger_langue_interface', return_value='fr'):
            self.assertEqual(langue_courante(), 'fr')
            with utiliser_langue('en'):
                self.assertEqual(langue_courante(), 'en')
                with utiliser_langue('fr'):
                    self.assertEqual(langue_courante(), 'fr')
                self.assertEqual(langue_courante(), 'en')
            self.assertEqual(langue_courante(), 'fr')
        with patch('ui_preferences.charger_langue_interface', side_effect=ValueError('invalid JSON')):
            self.assertEqual(langue_courante(), 'fr')

    def test_series_affichees_restent_canoniques(self):
        from vue_historique import SerieLocaleVar, extraire_points
        interpreteur = tk.Tcl()
        with utiliser_langue('en'):
            serie = SerieLocaleVar(interpreteur, value='Lumière')
            self.assertEqual(serie.get(), 'Lumière')
            self.assertEqual(interpreteur.getvar(str(serie)), 'Light')
            serie.set('Humidité')
            self.assertEqual(serie.get(), 'Humidité')
            points = extraire_points([(1,'2026-10-08T12:00:00',24,21,3000,70)], serie.get())
            self.assertEqual(points[0][1], 21)

    def test_cycle_calcul_identique_dans_les_deux_langues(self):
        from services.analyse_arrosage import calculer_cycles_arrosage
        from vue_historique import reperes_visuels_cycle
        arrosages = [(1,1,'2026-09-20T10:00:00',40,'normal',None,None,'','Volvic',None,0), (2,1,'2026-09-20T10:33:00',55,'normal',None,None,'','Volvic',None,0)]
        mesures = [(1,'2026-09-20T09:30:00',24,18,100,70,'',1),(2,'2026-09-20T10:20:00',24,22,110,72,'',1),(3,'2026-09-20T10:45:00',24,25,120,73,'',1),(4,'2026-09-21T10:00:00',24,21,120,73,'',1)]
        results = {}
        for lang in ('fr','en'):
            with utiliser_langue(lang):
                cycle = calculer_cycles_arrosage(mesures, arrosages)[0]
                results[lang] = {key: cycle[key] for key in ('date','humidite_avant','premiere_humidite','pic_humidite','derniere_humidite','qualite_niveau')}
                markers = reperes_visuels_cycle(cycle)
                self.assertEqual([m['heures'] for m in markers if m['cle'] in ('24h','48h')], [24,48])
                self.assertEqual(cycle['arrosage']['quantite_totale_ml'],95)
        self.assertEqual(results['fr'], results['en'])

    def test_fiches_traduites_sans_modifier_catalogue(self):
        import mini_base_plantes
        original = copy.deepcopy(mini_base_plantes.PLANTES_CONNUES)
        with utiliser_langue('en'):
            for plant in original:
                report = mini_base_plantes.resume_besoins(plant)
                self.assertIn(plant['espece'], report)
                self.assertNotIn('Arrosage :', report)
                self.assertIn('Watering', report)
        self.assertEqual(original, mini_base_plantes.PLANTES_CONNUES)

    def test_updater_diagnostic_anglais(self):
        import update_gruterra
        with utiliser_langue('en'):
            diagnostic = {'version': {'statut':'a_jour','manifest_auto_update':True,'archive_url':'https://example.test/a.zip','sha256':'a'*64},'statut_global':'pret_a_verifier'}
            ok, errors = update_gruterra.valider_manifest_applicable(diagnostic)
            self.assertFalse(ok)
            self.assertEqual(errors, ['Gruterra is already up to date'])


class TestResultatUpdaterTraduit(unittest.TestCase):
    def test_succes_et_echec_dans_les_deux_langues(self):
        from i18n import traduire
        tree = ast.parse((APP / 'interface.py').read_text(encoding='utf-8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'update_appliquee_depuis_resultat')
        namespace = {'traduire': traduire}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<isolated-updater-result>', 'exec'), namespace)
        check = namespace['update_appliquee_depuis_resultat']
        for lang in ('fr','en'):
            code = traduire('interface_text_5241',lang)
            applied = traduire('updater_applied',lang).format(count=108,backup='backup.zip')
            self.assertTrue(check(code.format(v0=0)+'\n'+applied))
            self.assertFalse(check(code.format(v0=1)+'\n'+applied))
            self.assertFalse(check(code.format(v0=0)+'\n'+traduire('updater_cli_9',lang)))

if __name__ == '__main__':
    unittest.main()
