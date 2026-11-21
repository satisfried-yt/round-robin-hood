"""v0.8.0 regression: available power accounting, full reset durability and migration."""
import asyncio
from copy import deepcopy
import unittest

import load_core
from rrh_tested.model import Config, UserError
from rrh_tested.controller import Controller


class Release080Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.disk = None
        self.commands = []
        self.fail_save = False
        self.c = None
        async def save(document):
            if self.fail_save:
                raise OSError('disk failure')
            self.disk=deepcopy(document)
        async def send(entity, state, token):
            self.commands.append((entity,state))
            self.c.observe_switch(entity, state, command_token=token)
        async def off_all(entities):
            for eid in entities:
                self.commands.append((eid,'off'))
                self.c.observe_switch(eid,'off')
        self.c = Controller(None, send=send, send_all_off=off_all, save=save,
                            clock=lambda:100.0,wall_clock=lambda:100.0,confirmation_timeout=0.1)

    async def create_two_consumers(self):
        cfg=self.c.config.to_dict()
        cfg.update(grid_entity='sensor.netz',reserve_w=0,shutdown_delay_s=0)
        cfg['consumers']=[dict(id=ident,name=ident,entity_id='switch.'+ident,watts=500,
                               enabled=True,virtual_confirmed=True) for ident in ('one','two')]
        await self.c.configure(cfg,self.c.revision)
        for item in self.c.config.consumers:
            self.c.seed_switch(item.entity_id,'off')
        self.c.observe_grid('500','W')

    async def test_consumed_surplus_is_not_double_subtracted(self):
        c=self.c
        await self.create_two_consumers()
        await c.activate()
        await c.settle()
        self.assertEqual(self.commands,[('switch.one','on')])
        self.assertEqual(c.status()['managed_w'],500)
        # Net meter sees 0W remaining because that 500W is now locally used.
        c.observe_grid('0','W')
        await c.settle()
        self.assertEqual(self.commands,[('switch.one','on')])
        self.assertEqual(c.status()['power']['total_usable_w'],500)
        self.assertEqual(c.status()['power']['available_w'],0)
        # Extra 500 W PV can supply the next 500 W consumer.
        c.observe_grid('500','W')
        await c.settle()
        self.assertEqual(self.commands, [('switch.one','on'),('switch.two','on')])
        c.observe_grid('0','W')
        await c.settle()
        self.assertEqual(len(self.commands),2)
        self.assertEqual(c.status()['power']['total_usable_w'],1000)
        # Actual deficit (not 0W residual export) can cause shedding.
        c.observe_grid('-100','W')
        await c.settle()
        self.assertIn(('switch.one','off'),self.commands)

    async def test_full_reset_requires_stopped_and_verified_all_off(self):
        c=self.c
        await self.create_two_consumers()
        cfg=c.config.to_dict();cfg['notice_dismissed']=True;cfg['setup_complete']=True
        await c.configure(cfg,c.revision)
        c.runtime_totals_s['one']=12345
        c.statistics.totals['rrh_kwh']=77
        for token in ('', 'DELETE', 'reset round robin hood'):
            with self.assertRaisesRegex(UserError,'bestätigt'):
                await c.factory_reset(c.revision,token)
        with self.assertRaisesRegex(UserError,'Alle AUS'):
            await c.factory_reset(c.revision,'RESET ROUND ROBIN HOOD')
        # Merely pausing is insufficient; all OFF has to be dispatched and verified.
        await c.emergency_off()
        old_revision=c.revision
        with self.assertRaisesRegex(UserError,'Neu laden'):
            await c.factory_reset(old_revision-1,'RESET ROUND ROBIN HOOD')
        await c.factory_reset(old_revision,'RESET ROUND ROBIN HOOD')
        self.assertEqual(c.mode,'stopped')
        self.assertEqual(c.config,Config())
        self.assertEqual(c.statistics.totals['rrh_kwh'],0)
        self.assertFalse(c.runtime_totals_s)
        self.assertFalse(c.config.notice_dismissed)
        self.assertFalse(c.config.setup_complete)
        self.assertGreater(c.revision,old_revision)
        self.assertEqual(self.disk['config']['consumers'],[])
        self.assertFalse(self.disk['config']['notice_dismissed'])
        self.assertEqual(len(self.commands),2)
        restored=Controller(self.disk,send=c.send,send_all_off=c.send_all_off,save=c.save)
        self.assertFalse(restored.config.consumers)
        self.assertEqual(restored.statistics.totals['rrh_kwh'],0)
        self.assertEqual(restored.mode,'paused')

    async def test_unknown_or_on_state_blocks_reset_even_if_stopped(self):
        c=self.c
        await self.create_two_consumers()
        await c.emergency_off()
        c.observe_switch('switch.two','unavailable')
        before=deepcopy(self.disk)
        with self.assertRaisesRegex(UserError,'Alle AUS|Nicht alle'):
            await c.factory_reset(c.revision,'RESET ROUND ROBIN HOOD')
        self.assertEqual(self.disk,before)

    async def test_reset_persistence_failure_keeps_data_and_fails_closed(self):
        c=self.c
        await self.create_two_consumers()
        await c.emergency_off()
        previous=deepcopy(self.disk)
        self.fail_save=True
        with self.assertRaisesRegex(UserError,'Speicherprüfung'):
            await c.factory_reset(c.revision,'RESET ROUND ROBIN HOOD')
        self.assertEqual(c.config.grid_entity,'sensor.netz')
        self.assertEqual(len(c.config.consumers),2)
        self.assertEqual(self.disk,previous)
        self.assertEqual(c.mode,'error')

    async def test_config_with_new_dashboard_option_preserves_legacy(self):
        original=Config().to_dict()
        original['dashboard'].pop('show_donation')
        imported=Config.parse(original)
        self.assertTrue(imported.dashboard.show_donation)
        original['dashboard']['show_donation']=False
        self.assertFalse(Config.parse(original).dashboard.show_donation)
        for invalid in ('false',None,0,1):
            original['dashboard']['show_donation']=invalid
            with self.subTest(invalid=invalid),self.assertRaises(UserError):Config.parse(original)
