"""v0.9.1 restart safety and source-unit validation, without a live HA instance."""
import unittest
from copy import deepcopy
from types import SimpleNamespace

import load_core
from test_core import Rig, config, document
from rrh_tested.model import Config, UserError
from rrh_tested.energy_sources import divisor_and_scale, numeric_source_value


class UnitAndMigrationTests(unittest.TestCase):
    def test_default_and_legacy_startup_option(self):
        self.assertEqual(Config().startup_mode, 'off')
        self.assertEqual(Config.parse(config()).startup_mode, 'off')
        old=config();old.pop('startup_mode')
        self.assertEqual(Config.parse(old).startup_mode,'off')
        for mode in ('off','on','last'):
            raw=config();raw['startup_mode']=mode
            self.assertEqual(Config.parse(raw).startup_mode,mode)
        for mode in ('always','true',None,True):
            raw=config();raw['startup_mode']=mode
            with self.assertRaises(UserError): Config.parse(raw)

    def test_price_compatibility_currency_conversion_and_bad_units(self):
        self.assertEqual(numeric_source_value('32', 'ct/kWh', 'price','EUR'), .32)
        self.assertEqual(numeric_source_value('300', 'EUR/MWh', 'price','EUR'), .3)
        self.assertEqual(numeric_source_value('5', 'kW', 'capacity','EUR'), 5)
        self.assertEqual(numeric_source_value('250', 'W', 'capacity','EUR'), .25)
        self.assertEqual(numeric_source_value('2', 'kW', 'power','EUR'), 2000)
        self.assertEqual(numeric_source_value('2000','Wh','energy','EUR'),2)
        self.assertEqual(divisor_and_scale('price','CHF/kWh','EUR'),None)
        for val,unit in [('0.29','°C'),('1','kWh'),('0.29',''),('unknown','EUR/kWh'),('nan','EUR/kWh'),('-2','EUR/kWh')]:
            with self.subTest(val=val,unit=unit), self.assertRaises(ValueError):
                numeric_source_value(val,unit,'price','EUR')
        for curr,unit in [('CHF','CHF/kWh'),('GBP','GBP/kWh'),('USD','USD/kWh')]:
            self.assertEqual(numeric_source_value('0.10',unit,'price',curr),.1)


class RestartAndPersistenceTests(unittest.IsolatedAsyncioTestCase):
    def setup(self,mode='off',*,last=None,states=None):
        cfg=config();cfg['startup_mode']=mode;cfg['setup_complete']=True
        data=document(cfg)
        if last is not None: data['resume_mode']=last
        return Rig(data,power=2500,states=states)

    async def test_explicit_off_blocks_autostart_and_does_not_fault_external_on(self):
        r=self.setup('off');r.c.restore_startup()
        self.assertEqual(r.c.mode,'stopped')
        r.c.observe_switch('switch.a','on',explicit_external=True)
        await r.c.settle()
        self.assertEqual(r.calls,[])
        self.assertFalse(r.c.emergency_unresolved)
        self.assertEqual(r.c.resume_mode,'stopped')

    async def test_always_on_waits_for_new_grid_report(self):
        r=self.setup('on');r.c.restore_startup();r.c.wake()
        await r.c.settle()
        self.assertEqual(r.calls,[])
        self.assertEqual(r.c.mode,'paused')
        self.assertTrue(r.c.status()['startup_pending'])
        await r.grid(2500)
        self.assertEqual(r.c.mode,'running')
        self.assertTrue(r.calls)
        self.assertEqual(r.calls[0],('switch.a','on'))
        self.assertEqual(r.disk['resume_mode'],'running')

    async def test_last_running_restored_but_pause_and_off_are_not(self):
        r=self.setup('last');await r.run()
        self.assertEqual(r.disk['resume_mode'],'running')
        await r.c.close()
        self.assertEqual(r.disk['resume_mode'],'running','Normal HA unload must preserve intent')
        r2=Rig(deepcopy(r.disk), power=2500,states={'switch.a':'on'})
        r2.c.restore_startup();r2.c.wake();await r2.c.settle()
        self.assertEqual(r2.c.mode,'paused')
        self.assertTrue(r2.c.status()['startup_pending'])
        self.assertEqual(r2.calls,[],'No immediate dispatch on cached grid value')
        await r2.grid(2500)
        self.assertEqual(r2.c.mode,'running')
        r2.c.pause();await r2.c.settle()
        self.assertEqual(r2.disk['resume_mode'],'paused')
        r3=Rig(deepcopy(r2.disk), power=2500,states={'switch.a':'on'})
        r3.c.restore_startup();r3.c.wake();await r3.c.settle()
        self.assertEqual(r3.c.mode,'paused');self.assertEqual(r3.calls,[])
        await r3.c.emergency_off()
        self.assertEqual(r3.disk['resume_mode'],'stopped')
        r4=Rig(deepcopy(r3.disk));r4.c.restore_startup()
        self.assertEqual(r4.c.mode,'stopped')

    async def test_unknown_actuator_and_incomplete_commands_block_autostart(self):
        r=self.setup('on',states={'switch.a':'unavailable'});r.c.restore_startup()
        self.assertEqual(r.c.mode,'paused')
        self.assertIn('Rückmeldungen',r.c.reason)
        self.assertTrue(r.c.status()['startup_pending'])
        self.assertEqual(r.calls,[])
        cfg=config();cfg['startup_mode']='on';cfg['setup_complete']=True
        saved=document(cfg,incomplete={'id':'a','target':'on'})
        r=Rig(saved);r.c.restore_startup()
        self.assertEqual(r.c.mode,'paused')
        self.assertFalse(r.c._startup_restore)

    async def test_invalid_first_poststart_grid_never_dispatches(self):
        r=self.setup('on');r.c.restore_startup();r.c.wake();await r.c.settle()
        await r.grid('unavailable')
        self.assertEqual(r.calls,[])
        self.assertEqual(r.c.mode,'paused')
        self.assertTrue(r.c.status()['startup_pending'])
        await r.grid(2500)
        self.assertEqual(r.c.mode,'running')

import test_adapter

class EnergySourceBoundaryTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=test_adapter.AdapterTests.asyncSetUp
    asyncTearDown=test_adapter.AdapterTests.asyncTearDown

    async def test_reject_incompatible_new_source_without_mutating_storage(self):
        before=self.rt.controller.document()
        self.hass.states.set('sensor.wrong','0.29',{'unit_of_measurement':'°C'})
        cfg=self.rt.controller.config.to_dict()
        cfg['energy']['import_price']={'mode':'entity','value':None,'entity_id':'sensor.wrong'}
        with self.assertRaisesRegex(UserError,'Einheit'):
            await self.rt.configure(cfg,self.rt.controller.revision)
        self.assertEqual(self.rt.controller.document(),before)
        self.assertFalse(self.hass.services.calls)

    async def test_valid_tariffs_and_invalid_update_yield_no_fabricated_price(self):
        self.hass.states.set('sensor.price','0.30',{'unit_of_measurement':'EUR/kWh'})
        self.hass.states.set('sensor.feed','6',{'unit_of_measurement':'ct/kWh'})
        cfg=self.rt.controller.config.to_dict()
        cfg['energy']['import_price']={'mode':'entity','value':None,'entity_id':'sensor.price'}
        cfg['energy']['feed_in_price']={'mode':'entity','value':None,'entity_id':'sensor.feed'}
        await self.rt.configure(cfg,self.rt.controller.revision)
        result=self.rt._stat_sources()
        self.assertAlmostEqual(result['import_price'],.30)
        self.assertAlmostEqual(result['feed_in_price'],.06)
        self.hass.states.set('sensor.price','unavailable',{'unit_of_measurement':'EUR/kWh'})
        result=self.rt._stat_sources()
        self.assertIsNone(result['import_price'])
        self.assertTrue(result['warnings'])
        self.assertAlmostEqual(result['feed_in_price'],.06)
