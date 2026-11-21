"""v0.1.8: configurable deficit delays and safe explicit timer expiration."""
import unittest
from copy import deepcopy

from test_core import Rig, config, document
from rrh_tested.model import Config, UserError


class DelayValidation(unittest.TestCase):
    def test_legacy_config_defaults_to_global_delay(self):
        cfg = Config.parse(config())
        self.assertTrue(cfg.global_shutdown_delay_enabled)
        self.assertEqual(cfg.shutdown_delay_s, 30)
        self.assertEqual(Config.parse(cfg.to_dict()), cfg)

    def test_global_toggle_rejects_non_booleans(self):
        for bad in (0, 1, "false", None, [], {}):
            cfg = config()
            cfg['global_shutdown_delay_enabled'] = bad
            with self.subTest(bad=bad), self.assertRaises(UserError):
                Config.parse(cfg)

    def test_global_off_keeps_consumer_override(self):
        cfg = config()
        cfg['global_shutdown_delay_enabled'] = False
        cfg['shutdown_delay_s'] = 30
        cfg['consumers'][0]['shutdown_delay_s'] = 12
        parsed = Config.parse(cfg)
        self.assertFalse(parsed.global_shutdown_delay_enabled)
        self.assertEqual(parsed.consumers[0].shutdown_delay_s, 12)


class TimerOperations(unittest.IsolatedAsyncioTestCase):
    async def test_global_disabled_sheds_immediately(self):
        cfg = config(); cfg['global_shutdown_delay_enabled'] = False
        r = Rig(document(cfg, owned=['a']), power=50, states={'switch.a':'on'})
        await r.run()
        self.assertEqual(r.calls, [('switch.a', 'off')])

    async def test_override_still_waits_when_global_disabled(self):
        cfg = config(); cfg['global_shutdown_delay_enabled'] = False
        cfg['consumers'][0]['shutdown_delay_s'] = 20
        r = Rig(document(cfg, owned=['a']), power=50, states={'switch.a':'on'})
        await r.run()
        self.assertEqual(r.calls, [])
        await r.tick(19)
        self.assertEqual(r.calls, [])
        await r.tick(1)
        self.assertEqual(r.calls, [('switch.a','off')])

    async def test_skip_cooldown_persists_without_immediate_command(self):
        cfg = config(); cfg['consumers'][0].update(cooldown_s=300, cooldown_wait=True)
        r = Rig(document(cfg), power=3000)
        r.c.cooldown_until['a'] = r.now + 300
        rev = r.c.revision
        await r.c.skip_timer('a','cooldown',rev)
        self.assertFalse(r.c.status()['consumers'][0]['cooldown_remaining_s'])
        self.assertEqual(r.calls, [])  # no direct command, the engine can run later
        restored = Rig(deepcopy(r.disk))
        self.assertEqual(restored.c.status()['consumers'][0]['cooldown_remaining_s'], 0)
        with self.assertRaises(UserError):
            await r.c.skip_timer('a', 'cooldown', rev)

    async def test_skip_minimum_persists_and_does_not_switch(self):
        cfg = config(); cfg['consumers'][0].update(min_on_s=600, min_on_strict=True)
        r = Rig(document(cfg, owned=['a']), power=1000, states={'switch.a':'on'})
        r.c.started_at['a'] = r.now
        assert r.c.status()['consumers'][0]['min_remaining_s'] == 600
        await r.c.skip_timer('a','minimum',r.c.revision)
        self.assertEqual(r.c.status()['consumers'][0]['min_remaining_s'],0)
        self.assertEqual(r.calls, [])
        restored = Rig(deepcopy(r.disk),states={'switch.a':'on'})
        self.assertEqual(restored.c.status()['consumers'][0]['min_remaining_s'],0)

    async def test_skip_rejected_for_invalid_request(self):
        r = Rig()
        for cid, kind in [('missing','minimum'), ('a','minimum'), ('a','cooldown'), ('a','other')]:
            with self.subTest(cid=cid,kind=kind), self.assertRaises(UserError):
                await r.c.skip_timer(cid,kind,r.c.revision)
        with self.assertRaises(UserError):
            await r.c.skip_timer('a','cooldown',r.c.revision+1)

    async def test_storage_failure_restores_timer_and_pauses(self):
        cfg = config(); cfg['consumers'][0]['cooldown_s']=100
        r = Rig(document(cfg))
        r.c.cooldown_until['a'] = r.now + 100
        async def fail(_):
            raise RuntimeError('disk error')
        r.save_hook = fail
        with self.assertRaises(UserError):
            await r.c.skip_timer('a','cooldown',r.c.revision)
        self.assertEqual(r.c.status()['consumers'][0]['cooldown_remaining_s'],100)
        self.assertEqual(r.c.mode,'error')


if __name__ == '__main__':
    unittest.main()
