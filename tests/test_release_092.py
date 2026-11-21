"""v0.9.2: boot safety and migration, including the observed manual-setup failure."""
import unittest
from copy import deepcopy
from pathlib import Path
import json

import load_core
from test_core import Rig, config, document
from rrh_tested.controller import Controller


class RestartControllerTests(unittest.IsolatedAsyncioTestCase):
    def rig(self, mode='on', *, resume='stopped', setup_complete=False, power=2500, states=None):
        cfg=config()
        cfg['startup_mode']=mode
        cfg['setup_complete']=setup_complete
        saved=document(cfg)
        saved['resume_mode']=resume
        return Rig(saved,power=power,states=states)

    async def test_manual_setup_autostarts_without_wizard_flag(self):
        r=self.rig('on',setup_complete=False)
        r.c.restore_startup();r.c.wake();await r.c.settle()
        self.assertEqual(r.c.mode,'paused')
        self.assertEqual(r.calls,[])
        self.assertTrue(r.c.status()['startup_pending'])
        await r.grid(2500)
        self.assertEqual(r.c.mode,'running')
        self.assertEqual(r.calls,[('switch.a','on')])
        self.assertEqual(r.disk['resume_mode'],'running')

    async def test_missing_actuator_recovers_later_without_blind_switching(self):
        r=self.rig('on',states={'switch.a':'unavailable'})
        r.c.restore_startup();await r.c.settle()
        await r.grid(2500)
        self.assertEqual(r.c.mode,'paused')
        self.assertEqual(r.calls,[])
        self.assertTrue(r.c._startup_restore)
        r.c.observe_switch('switch.a','off')
        await r.c.settle()
        self.assertEqual(r.c.mode,'running')
        self.assertEqual(r.calls,[('switch.a','on')])

    async def test_stale_and_restored_reading_do_not_autostart(self):
        r=self.rig('on')
        r.c.restore_startup()
        r.c.observe_grid('3000','W',restored=True)
        await r.c.settle()
        self.assertEqual(r.c.mode,'paused')
        self.assertFalse(r.calls)
        await r.grid(3000)
        self.assertEqual(r.c.mode,'running')
        self.assertTrue(r.calls)

    async def test_manual_pause_cancels_pending_start(self):
        r=self.rig('on')
        r.c.restore_startup()
        r.c.pause()
        await r.c.settle()
        await r.grid(3000)
        self.assertEqual(r.c.mode,'paused')
        self.assertFalse(r.calls)
        self.assertFalse(r.c.status()['startup_pending'])
        self.assertEqual(r.disk['resume_mode'],'paused')

    async def test_last_running_restored_without_completed_wizard(self):
        r=self.rig('last',resume='running',setup_complete=False)
        r.c.restore_startup();await r.c.settle()
        self.assertEqual(r.c.mode,'paused')
        await r.grid(2500)
        self.assertEqual(r.c.mode,'running')
        self.assertEqual(r.disk['resume_mode'],'running')

    async def test_never_restore_last_paused_or_last_stopped(self):
        for old in ('paused','stopped'):
            with self.subTest(old=old):
                r=self.rig('last',resume=old)
                r.c.restore_startup()
                await r.grid(2500)
                self.assertEqual(r.c.mode,'paused' if old=='paused' else 'stopped')
                self.assertFalse(r.calls)

    async def test_never_auto_when_off(self):
        r=self.rig('off',resume='running')
        r.c.restore_startup()
        await r.grid(3000)
        self.assertEqual(r.c.mode,'stopped')
        self.assertFalse(r.calls)

    async def test_incomplete_marker_blocks_auto(self):
        cfg=config();cfg['startup_mode']='on'
        saved=document(cfg,incomplete={'id':'a','target':'on'})
        r=Rig(saved);r.c.restore_startup()
        await r.grid(2500)
        self.assertEqual(r.c.mode,'paused')
        self.assertFalse(r.calls)
        self.assertFalse(r.c.status()['startup_pending'])


import test_adapter
from ha_doubles import Context

class ActualAdapterRestartTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=test_adapter.AdapterTests.asyncSetUp
    asyncTearDown=test_adapter.AdapterTests.asyncTearDown

    async def test_manual_configuration_and_reboot_starts_only_after_new_report(self):
        cfg=config();cfg['setup_complete']=False;cfg['startup_mode']='on'
        await self.rt.configure(cfg,self.rt.controller.revision)
        await self.rt.controller.activate()
        self.hass.states.set('sensor.grid','2500',{'unit_of_measurement':'W'})
        await self.hass.drain()
        await self.boot.async_unload_entry(self.hass,self.entry)
        calls_before=len(self.hass.services.calls)
        await self.boot.async_setup_entry(self.hass,self.entry)
        self.rt=self.entry.runtime_data
        self.assertEqual(self.rt.controller.mode,'paused')
        self.assertTrue(self.rt.controller.status()['startup_pending'])
        self.assertEqual(len(self.hass.services.calls),calls_before)
        self.hass.states.set('sensor.grid','2600',{'unit_of_measurement':'W'})
        await self.hass.drain()
        self.assertEqual(self.rt.controller.mode,'running')
        self.assertEqual(self.rt.controller.document()['resume_mode'],'running')

    async def test_late_sensor_appearance_unblocks_autostart(self):
        cfg=config();cfg['startup_mode']='on';cfg['setup_complete']=False
        await self.rt.configure(cfg,self.rt.controller.revision)
        await self.boot.async_unload_entry(self.hass,self.entry)
        self.hass.states.set('switch.a','unavailable')
        await self.boot.async_setup_entry(self.hass,self.entry)
        self.rt=self.entry.runtime_data
        self.hass.states.set('sensor.grid','2500',{'unit_of_measurement':'W'})
        await self.hass.drain()
        self.assertEqual(self.rt.controller.mode,'paused')
        self.assertTrue(self.rt.controller.status()['startup_pending'])
        self.hass.states.set('switch.a','off')
        await self.hass.drain()
        self.assertEqual(self.rt.controller.mode,'running')
