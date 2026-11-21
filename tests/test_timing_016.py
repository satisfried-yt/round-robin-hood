"""0.1.6 behaviour and persistence: real engine, fake HA service and clock."""
import asyncio
import unittest
from copy import deepcopy
from test_core import Rig, config, document
from rrh_tested.model import Config, UserError
from rrh_tested.controller import Controller


def opts(**fields):
    cfg = config()
    cfg['consumers'][0].update(fields)
    return cfg


class TimingValidation(unittest.TestCase):
    def test_legacy_configuration_loads_without_timer_fields(self):
        cfg = Config.parse(config())
        self.assertEqual((cfg.consumers[0].min_on_s, cfg.consumers[0].cooldown_s), (0, 0))
        self.assertEqual(Config.parse(cfg.to_dict()), cfg)

    def test_invalid_duration_and_policy_rejected(self):
        for key, value in [('min_on_s',-1),('cooldown_s',86401),('min_on_s',True),
                           ('cooldown_s',3.5),('min_on_strict','false'),('cooldown_wait',1)]:
            cfg = opts(**{key: value})
            with self.subTest(key=key,value=value), self.assertRaises(UserError):
                Config.parse(cfg)


class TimingOperations(unittest.IsolatedAsyncioTestCase):
    async def test_fifo_shutdown_oldest_confirmed_first(self):
        cfg = config(); cfg['shutdown_delay_s'] = 0
        r = Rig(document(cfg, cursor='c', owned=['b','c','a']), power=50,
                states={'switch.a':'on','switch.b':'on','switch.c':'on'})
        await r.run()
        self.assertEqual(r.calls[0], ('switch.b','off'))
        self.assertEqual(r.c.cursor,'c')
        await r.grid(20)
        self.assertEqual(r.calls[1], ('switch.c','off'))

    async def test_soft_minimum_yields_to_deficit(self):
        cfg = opts(min_on_s=600,min_on_strict=False)
        cfg['shutdown_delay_s']=0
        r=Rig(document(cfg,owned=['a']),power=50,states={'switch.a':'on'})
        await r.run()
        self.assertIn(('switch.a','off'),r.calls)

    async def test_strict_minimum_protects_but_can_shutdown_next_fifo(self):
        cfg=opts(min_on_s=600,min_on_strict=True)
        cfg['shutdown_delay_s']=0
        r=Rig(document(cfg,owned=['a','b']),power=50,states={'switch.a':'on','switch.b':'on'})
        await r.run()
        self.assertEqual(r.calls,[('switch.b','off')])
        await r.grid(50)
        self.assertIn('Mindestlaufzeiten',r.c.reason)
        for _ in range(12):
            await r.tick(50)
            await r.grid(50)
        await r.tick(1)
        await r.grid(50)
        self.assertEqual(r.calls[-1],('switch.a','off'))

    async def test_cooldown_skip_allows_following_eligible(self):
        cfg=opts(cooldown_s=300,cooldown_wait=False)
        r=Rig(document(cfg,cursor='c'),power=2500)
        r.c.observe_switch('switch.a','on',explicit_external=True)
        r.c.observe_switch('switch.a','off',explicit_external=True)
        await r.run()
        await r.grid(2500)
        self.assertEqual(r.calls[0],('switch.b','on'))
        self.assertEqual(r.c.cursor,'b')

    async def test_cooldown_wait_blocks_others_even_if_power_fits(self):
        cfg=opts(cooldown_s=300,cooldown_wait=True)
        r=Rig(document(cfg,cursor='c'),power=2500)
        r.c.observe_switch('switch.a','on',explicit_external=True)
        r.c.observe_switch('switch.a','off',explicit_external=True)
        await r.run()
        await r.grid(2500)
        self.assertEqual(r.calls,[])
        self.assertIn('Wiedereinschaltsperre',r.c.reason)
        for _ in range(6):
            await r.tick(50)
            await r.grid(2500)
        await r.tick(1)
        await r.grid(2500)
        self.assertEqual(r.calls[0],('switch.a','on'))

    async def test_manual_off_starts_cooldown_after_confirmed_start(self):
        cfg=opts(cooldown_s=180,min_on_s=600,min_on_strict=True)
        r=Rig(document(cfg,cursor='c'),power=2500)
        await r.run()
        self.assertEqual(r.c.cursor,'a')
        self.assertEqual(r.c.status()['consumers'][0]['min_remaining_s'],600)
        r.c.pause()
        r.c.observe_switch('switch.a','off',explicit_external=True)
        await r.c.settle()
        state=r.c.status()['consumers'][0]
        self.assertEqual(state['cooldown_remaining_s'],180)
        self.assertEqual(state['min_remaining_s'],0)

    async def test_cooldown_and_start_time_survive_restart(self):
        cfg=opts(cooldown_s=180,min_on_s=600,min_on_strict=True)
        r=Rig(document(cfg,cursor='c'),power=2500)
        await r.run()
        first=deepcopy(r.disk)
        r2=Rig(first,power=100,states={'switch.a':'on'})
        self.assertEqual(r2.c.status()['consumers'][0]['min_remaining_s'],600)
        r2.c.observe_switch('switch.a','off',explicit_external=True)
        await r2.c.settle()
        again=deepcopy(r2.disk)
        r3=Rig(again,power=100)
        self.assertEqual(r3.c.status()['consumers'][0]['cooldown_remaining_s'],180)
        await r3.tick(181)
        self.assertEqual(r3.c.status()['consumers'][0]['cooldown_remaining_s'],0)

    async def test_main_off_bypasses_strict_minimum_and_starts_cooldown(self):
        cfg=opts(cooldown_s=240,min_on_s=600,min_on_strict=True)
        r=Rig(document(cfg,cursor='c'),power=2500)
        await r.run()
        await r.c.emergency_off()
        self.assertEqual(r.c.mode,'stopped')
        self.assertEqual(r.c.status()['consumers'][0]['cooldown_remaining_s'],240)
        self.assertNotIn('a',r.c.owned)

    async def test_invalid_saved_timestamp_fails_closed(self):
        saved=document(); saved['cooldown_until']={'a':float('nan')}
        with self.assertRaises(UserError):
            Rig(saved)


if __name__ == '__main__': unittest.main()
