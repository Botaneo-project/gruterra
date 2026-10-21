import sys,unittest
from pathlib import Path
from datetime import datetime,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from services.comparaison_sechage import observer,resume
from i18n import utiliser_langue
class DryingComparisonTests(unittest.TestCase):
    def cycle(self,*,hours=range(24,73,2),source=1,offset=0):
        start=datetime(2026,10,1)
        return {'date':start,'fin':None,'arrosage':{'date_debut':start-timedelta(minutes=15),'date_fin':start},'mesures':[(i,(start+timedelta(hours=h)).isoformat(),20,30-(h-24)/24+offset,100,50,None,source) for i,h in enumerate(hours)]}
    def test_same_window_uses_last_fraction_and_observed_rate(self):
        r=observer(self.cycle());self.assertEqual(r['state'],'ready');self.assertAlmostEqual(r['rate'],-1);self.assertEqual(r['hours'],48)
        self.assertEqual(r['start'],datetime(2026,10,2))
    def test_gaps_missing_bounds_and_insufficient_distinct_points(self):
        for hours in ([24,72],[0,12,84,96],[24,26,60,72]):
            self.assertEqual(observer(self.cycle(hours=hours))['state'],'insufficient')
    def test_fourth_cycle_pending_without_synthetic_watering(self):
        c=self.cycle(hours=[1,2,3]);before=list(c['mesures'])
        self.assertEqual(observer(c)['state'],'waiting');self.assertEqual(c['mesures'],before)
        c['mesures']=[];self.assertEqual(observer(c)['state'],'waiting')
    def test_mixed_sources_not_merged(self):
        c=self.cycle();row=list(c['mesures'][5]);row[7]=2;c['mesures'][5]=tuple(row)
        self.assertEqual(observer(c)['state'],'source_uncertain')
    def test_only_same_sensor_reference_and_translations(self):
        for lang in ('fr','en'):
            with utiliser_langue(lang):
                same=resume([self.cycle(),self.cycle(offset=5)])
                other=resume([self.cycle(),self.cycle(source=2)])
                self.assertIn('+0.00',same);self.assertNotIn('+0.00',other)
    def test_conflicting_timestamp_is_not_averaged(self):
        c=self.cycle();r=list(c['mesures'][5]);r[3]=5;c['mesures'].append(tuple(r))
        self.assertEqual(observer(c)['state'],'insufficient')
if __name__=='__main__':unittest.main()
