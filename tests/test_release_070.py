"""v0.7.0: migration, persistent onboarding, 24-hour chart ledger, currency safety."""
import asyncio
from copy import deepcopy
import json
import unittest

import load_core
from rrh_tested.model import Config, UserError
from rrh_tested.controller import Controller
from rrh_tested.statistics import EnergyLedger, HISTORY_SECONDS, MAX_HISTORY


class MigrationTests(unittest.TestCase):
    def test_old_config_keeps_all_values_and_defaults_eur(self):
        old = Config().to_dict()
        old['grid_entity'] = 'sensor.netz'
        old['consumers']=[{'id':'c1','name':'Heizlüfter','entity_id':'switch.heater','watts':1200,'enabled':True,'virtual_confirmed':True}]
        old['energy']['import_price']={'mode':'fixed','entity_id':'','value':.313}
        old['energy']['feed_in_price']={'mode':'fixed','entity_id':'','value':.082}
        old['energy']['pv_size']={'mode':'fixed','entity_id':'','value':4.5}
        old['energy'].pop('currency')
        old.pop('notice_dismissed');old.pop('setup_complete')
        restored=Config.parse(old)
        self.assertEqual(restored.energy.currency,'EUR')
        self.assertEqual(restored.energy.pv_size.value,4.5)
        self.assertEqual(restored.energy.import_price.value,.313)
        self.assertEqual(restored.energy.feed_in_price.value,.082)
        self.assertEqual(restored.consumers[0].entity_id,'switch.heater')
        self.assertEqual(restored.profiles[0].consumer_ids,('c1',))
        self.assertFalse(restored.setup_complete)
        self.assertEqual(Config.parse(restored.to_dict()),restored)

    def test_invalid_currency_and_notice_flags_fail_closed(self):
        original=Config().to_dict()
        for key,value in [('currency','BTC'),('currency','eur'),('currency',None)]:
            data=deepcopy(original);data['energy'][key]=value
            with self.subTest(value=value),self.assertRaises(UserError):Config.parse(data)
        for key in ['notice_dismissed','setup_complete']:
            data=deepcopy(original);data[key]='yes'
            with self.subTest(key=key),self.assertRaises(UserError):Config.parse(data)

    def test_24h_history_includes_data_gaps_and_survives_restart(self):
        ledger=EnergyLedger()
        base=1_800_000_000.0
        for index in range(26*60*2):
            now=base+30*index
            valid=index%73!=0
            ledger.sample(now,mode='running' if valid else 'paused',export_w=700 if valid else None,
                          managed_w=500 if valid else 0,loads={'heater':500} if valid else {},
                          buy_price=.30,feed_price=.08)
        self.assertLessEqual(len(ledger.history),MAX_HISTORY)
        self.assertLessEqual(ledger.history[-1][0]-ledger.history[0][0],HISTORY_SECONDS)
        self.assertTrue(any(point[5] is False for point in ledger.history))
        copy=EnergyLedger(json.loads(json.dumps(ledger.document())))
        self.assertEqual(copy.history,ledger.history)
        self.assertEqual(copy.money_currency,'EUR')
        self.assertIsNone(copy.last_snapshot)  # no invented on/off continuity

    def test_old_five_column_history_upgrades_without_rewriting_rows(self):
        sample=EnergyLedger().document()
        sample.pop('money_currency')
        sample['history']=[[101.0,500.0,300.0,62.5,800.0]]
        imported=EnergyLedger(sample)
        self.assertEqual(imported.history[0],sample['history'][0])
        self.assertEqual(imported.money_currency,'EUR')


class NoticeAndCurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.disk=None;self.sent=[]
        async def send(entity,action,token): self.sent.append((entity,action))
        async def save(data): self.disk=json.loads(json.dumps(data))
        self.controller=Controller(None,send=send,save=save,clock=lambda:100.0,wall_clock=lambda:100.0)

    async def test_notice_ack_persists_without_actuator_or_activation(self):
        c=self.controller
        await c.dismiss_notice(True)
        self.assertTrue(c.config.notice_dismissed)
        self.assertTrue(self.disk['config']['notice_dismissed'])
        self.assertEqual(c.mode,'paused')
        self.assertEqual(self.sent,[])
        restored=Controller(self.disk,send=lambda *args:None,save=lambda *args:None)
        self.assertTrue(restored.config.notice_dismissed)
        await c.dismiss_notice(False)
        self.assertFalse(c.config.notice_dismissed)
        self.assertEqual(self.sent,[])

    async def test_currency_guard_does_not_destroy_history(self):
        c=self.controller
        cfg=c.config.to_dict();cfg['energy']['currency']='CHF'
        await c.configure(cfg,c.revision)
        self.assertEqual(c.statistics.money_currency,'CHF')
        c.statistics.totals['valued_kwh']=1.0
        c.statistics.totals['net_benefit_eur']=.2
        cfg=c.config.to_dict();cfg['energy']['currency']='EUR'
        before=deepcopy(c.statistics.document())
        with self.assertRaisesRegex(UserError,'Währungswechsel'):
            await c.configure(cfg,c.revision)
        self.assertEqual(before,c.statistics.document())
        self.assertEqual(c.config.energy.currency,'CHF')
        self.assertEqual(self.sent,[])

    async def test_preexisting_prices_require_currency_tariff_confirmation(self):
        c=self.controller
        cfg=c.config.to_dict()
        cfg['energy']['import_price']={'mode':'fixed','value':.31,'entity_id':''}
        cfg['energy']['feed_in_price']={'mode':'fixed','value':.08,'entity_id':''}
        await c.configure(cfg,c.revision)
        other=c.config.to_dict()
        other['energy']['currency']='CHF'
        other['energy']['import_price']['value']=.41
        other['energy']['feed_in_price']['value']=.11
        with self.assertRaisesRegex(UserError,'Währungswechsel'):
            await c.configure(other,c.revision)
        self.assertEqual(c.config.energy.currency,'EUR')
        await c.configure(other,c.revision,currency_tariffs_confirmed=True)
        self.assertEqual(c.config.energy.currency,'CHF')
        self.assertEqual(c.config.energy.import_price.value,.41)
        self.assertEqual(c.config.energy.feed_in_price.value,.11)
        self.assertEqual(self.sent,[])

    async def test_setup_flag_stored_and_never_runs_controller(self):
        c=self.controller
        cfg=c.config.to_dict();cfg['setup_complete']=True
        await c.configure(cfg,c.revision)
        self.assertTrue(c.config.setup_complete)
        self.assertTrue(self.disk['config']['setup_complete'])
        self.assertEqual(c.mode,'paused')
        self.assertEqual(self.sent,[])
