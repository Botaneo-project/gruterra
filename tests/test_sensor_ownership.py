import asyncio
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import sync_miflora as module


class SensorOwnershipTests(unittest.TestCase):
    def test_pi_pending_running_failed_or_already_imported_never_reads_from_pc(self):
        capteur=(1,'Fictif','00:00:00:00:00:00',1,'Plante','espèce','salon','zone',1,None)
        for response in ({'ok':True,'added':0,'collect_accepted':True,'collect_status':'pending'},
                         {'ok':True,'added':0,'collect_accepted':False,'collect_status':'running'},
                         {'ok':True,'added':1,'collect_accepted':False,'collect_status':'running'},
                         {'ok':False,'added':0,'collect_accepted':False,'collect_status':'unavailable'}):
            with self.subTest(response=response),patch.object(module.database,'get_capteur',return_value=capteur),patch.object(module.raspberry_sync,'owned',return_value=True),patch.object(module.raspberry_sync,'synchronize',return_value=response) as pi,patch.object(module,'synchroniser_capteur_direct_pc',new_callable=AsyncMock) as pc:
                result=asyncio.run(module.synchroniser_capteur_prioritaire(1,'test'))
                pc.assert_not_awaited();pi.assert_called_once()
                self.assertEqual(result['collecteur'],'raspberry')
                self.assertEqual(result['ok'],response['ok'])
                self.assertTrue(pi.call_args.args[3])

    def test_pc_only_sensor_still_reads_once(self):
        capteur=(1,'Fictif','00:00:00:00:00:00',1,'Plante','espèce','salon','zone',1,None)
        with patch.object(module.database,'get_capteur',return_value=capteur),patch.object(module.raspberry_sync,'owned',return_value=False),patch.object(module.raspberry_sync,'synchronize') as pi,patch.object(module,'synchroniser_capteur_direct_pc',new_callable=AsyncMock,return_value={'ok':True}) as pc:
            result=asyncio.run(module.synchroniser_capteur_prioritaire(1))
            pc.assert_awaited_once_with(capteur);pi.assert_not_called()
            self.assertEqual(result['collecteur'],'pc')
