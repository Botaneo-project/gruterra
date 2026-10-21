import unittest,sys
from pathlib import Path
from datetime import datetime,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import database
from services.analyse_arrosage import mesurer_cycle_arrosage,analyser_qualite_cycle,resumer_cycles_arrosage
from i18n import utiliser_langue
class WateringAuditTests(unittest.TestCase):
    def water(self,i,plant,date,volume):return (i,plant,date,volume)
    def test_interleaved_plants_never_merge(self):
        rows=[self.water(1,1,'2026-10-01T10:00:00',40),self.water(2,2,'2026-10-01T10:05:00',80),self.water(3,1,'2026-10-01T10:10:00',55)]
        sessions=database.construire_sessions_arrosage(rows)
        self.assertEqual(len(sessions),2)
        self.assertEqual(sessions[0]['quantite_totale_ml'],95)
        self.assertEqual([a[0] for a in sessions[0]['apports']],[1,3])
    def test_partial_or_nonfinite_volume_not_a_complete_total(self):
        for volume in (None,'unknown',float('nan'),float('inf'),-5):
            session=database.construire_sessions_arrosage([self.water(1,1,'2026-10-01T10:00:00',40),self.water(2,1,'2026-10-01T10:10:00',volume)])[0]
            self.assertIsNone(session['quantite_totale_ml']);self.assertEqual(session['quantite_connue_ml'],40)
            self.assertTrue(session['quantite_partielle'])
    def test_long_gap_not_hidden_by_small_count(self):
        start=datetime(2026,10,1)
        self.assertEqual(analyser_qualite_cycle([(start,20),(start+timedelta(hours=48),16)])['niveau'],'interruption longue')
    def test_invalid_humidity_and_mixed_date_encodings(self):
        water=self.water(1,1,'2026-10-01T10:00:00',80)
        rows=[(1,'2026-10-01T10:10:00',20,'unknown'),(2,'2026-10-01T12:00:00+02:00',20,25),(3,'2026-10-02T14:00:00+02:00',20,20),(4,'2026-10-02T15:00:00+02:00',20,200)]
        with utiliser_langue('fr'):
            cycle=mesurer_cycle_arrosage(water,None,rows)
        self.assertEqual(cycle['premiere_humidite'],25);self.assertEqual(cycle['derniere_humidite'],20)
        self.assertEqual(cycle['duree_tendance_h'],26)
        self.assertIn('26 h',cycle['texte'])
    def test_fourth_cycle_does_not_create_automatic_advice(self):
        waters=[self.water(i,1,f'2026-10-{i:02}T10:00:00',80) for i in range(1,5)]
        with utiliser_langue('fr'):text=resumer_cycles_arrosage([],waters)
        self.assertIn('4 séance',text);self.assertIn('3 cycle',text);self.assertIn('Aucun seuil',text)
if __name__=='__main__':unittest.main()
