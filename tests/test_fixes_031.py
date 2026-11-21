"""v0.3.1: consumer-visible scheduling regressions reproduced in simulated HA."""
from copy import deepcopy
import unittest

from test_core import Rig, document, config
from rrh_tested.model import Config, UserError


def one_profile(strategy, watts=(1800,500,800), skip=None):
    data = config()
    for row, watt in zip(data['consumers'], watts):
        row['watts'] = watt
    data['profiles'] = [dict(id='standard', name='Standard', enabled=True,
                             strategy=strategy, dashboard_order='fixed',
                             consumer_ids=['a','b','c'])]
    if skip is not None:
        data['profiles'][0]['allow_power_skip'] = skip
    return data


def two_profiles(*, high_enabled=False, protected=False):
    cfg = one_profile('stable_operation', (1800,500,800))
    cfg['profiles'] = [dict(id='sommer', name='Sommer', enabled=high_enabled,
                            strategy='classic', dashboard_order='fixed',
                            consumer_ids=['c']),
                       dict(id='standard', name='Standard', enabled=True,
                            strategy='stable_operation', dashboard_order='fixed',
                            consumer_ids=['a','b'])]
    if protected:
        cfg['consumers'][0]['min_on_s'] = 3600
    return cfg


class Model031(unittest.TestCase):
    def test_explicit_choice_and_legacy_migration(self):
        for strategy in ('classic','fair_runtime','fixed_priority','power_asc','power_desc'):
            cfg = one_profile(strategy)
            restored = Config.parse(cfg)
            expected = strategy in ('power_asc','power_desc')
            self.assertEqual(restored.profiles[0].allow_power_skip, expected)
            self.assertEqual(Config.parse(restored.to_dict()), restored)
            cfg['profiles'][0]['allow_power_skip'] = False
            self.assertFalse(Config.parse(cfg).profiles[0].allow_power_skip)
            cfg['profiles'][0]['allow_power_skip'] = True
            self.assertTrue(Config.parse(cfg).profiles[0].allow_power_skip)
        cfg = one_profile('stable_operation')
        cfg['profiles'][0]['allow_power_skip'] = True
        with self.assertRaises(UserError): Config.parse(cfg)
        for bad in ('false',0,None):
            cfg = one_profile('power_desc')
            cfg['profiles'][0]['allow_power_skip'] = bad
            with self.subTest(value=bad), self.assertRaises(UserError):Config.parse(cfg)
        cfg = one_profile('maximum_efficiency')
        cfg['profiles'][0]['efficiency_start_margin_w'] = 30
        self.assertEqual(Config.parse(cfg).profiles[0].efficiency_start_margin_w,30)
        cfg['profiles'][0]['efficiency_start_margin_w'] = -20
        with self.assertRaises(UserError):Config.parse(cfg)


class Strategy031(unittest.IsolatedAsyncioTestCase):
    async def test_repro_late_priority_activation_preempts_running_standard(self):
        cfg = two_profiles(high_enabled=False)
        r=Rig(document(cfg,owned=['a','b']),power=300,
              states={'switch.a':'on','switch.b':'on'})
        await r.run()
        self.assertEqual(r.calls, [])
        await r.c.profile_participation('sommer',True,r.c.revision)
        await r.c.settle()
        self.assertEqual(r.calls,[('switch.a','off')])
        await r.grid(2100)  # after switching off 1800 W; measured export rose
        self.assertEqual(r.calls[-1],('switch.c','on'))
        await r.grid(1300)  # still enough spare; 800 W is now in high priority
        self.assertEqual(r.c.owned,['b','c'])
        self.assertEqual(r.c.config.profiles[0].enabled,True)

    async def test_no_priority_shedding_when_high_cannot_fit_or_protected(self):
        cfg=two_profiles(high_enabled=True,protected=True)
        doc=document(cfg,owned=['a','b'])
        doc['started_at']={'a':99,'b':99}
        r=Rig(doc,power=300,states={'switch.a':'on','switch.b':'on'})
        await r.run()
        self.assertEqual(r.calls,[])  # V1 protected; V2=500 alone can't free 600
        cfg=two_profiles(high_enabled=True)
        cfg['consumers'][2]['watts']=2800
        r=Rig(document(cfg,owned=['a','b']),power=300,
              states={'switch.a':'on','switch.b':'on'})
        await r.run()
        self.assertEqual(r.calls,[])  # even all available lower power is too small

    async def test_priority_does_not_take_over_external_switches(self):
        cfg=two_profiles(high_enabled=True)
        r=Rig(document(cfg,owned=['b']),power=300,
              states={'switch.a':'on','switch.b':'on'})
        await r.run()
        self.assertEqual(r.calls,[])  # A is external, reclaiming 500 alone insufficient

    async def test_fair_runtime_can_skip_unfit_candidate(self):
        cfg=one_profile('fair_runtime', skip=True)
        cfg['profiles'][0]['runtime_window']='all'
        doc=document(cfg)
        doc['runtime_totals_s']={'a':0,'b':100,'c':200}
        doc['fairness']={'totals':{'fair_runtime':{'standard':{'a':0,'b':100,'c':200}},'fair_energy':{}},'segments':[]}
        r=Rig(doc,power=988)
        await r.run()
        self.assertEqual(r.calls,[('switch.b','on')])
        self.assertEqual(r.c.status()['next_id'],'c')  # Another fitting, lower-runtime candidate

    async def test_fair_runtime_strict_waits_for_1800(self):
        cfg=one_profile('fair_runtime',skip=False)
        r=Rig(document(cfg),power=988)
        await r.run()
        self.assertEqual(r.calls,[])
        self.assertEqual(r.c.status()['next_id'],'a')

    async def test_power_strict_and_skip_both_directions(self):
        for strategy,available,skip_result in [('power_desc',900,'switch.c'),
                                               ('power_asc',600,'switch.b')]:
            # Power ascending first B/500 fits at available 600, so for strict
            # contrast we force its first B to be too expensive (400 available).
            if strategy=='power_asc':available=400
            for skip in (False,True):
                cfg=one_profile(strategy,skip=skip)
                r=Rig(document(cfg),power=available+100)
                await r.run()
                expected=[('switch.c','on')] if strategy=='power_desc' and skip else []
                with self.subTest(strategy=strategy,skip=skip): self.assertEqual(r.calls,expected)
        cfg=one_profile('power_asc',skip=True,watts=(700,300,500))
        r=Rig(document(cfg),power=450)
        await r.run(); self.assertEqual(r.calls,[('switch.b','on')])
        cfg=one_profile('power_asc',skip=False,watts=(700,300,500))
        r=Rig(document(cfg),power=450)
        await r.run(); self.assertEqual(r.calls,[('switch.b','on')])

    async def test_classic_fixed_skip_and_strict(self):
        for strategy in ('classic','fixed_priority'):
            for skip in (False,True):
                cfg=one_profile(strategy,skip=skip)
                r=Rig(document(cfg),power=800)
                await r.run()
                with self.subTest(strategy=strategy,skip=skip):
                    self.assertEqual(r.calls, [('switch.b','on')] if skip else [])

    async def test_efficiency_margin_avoids_edge_start_and_running_chatter(self):
        cfg=one_profile('maximum_efficiency',watts=(1800,500,1200))
        cfg['profiles'][0]['efficiency_start_margin_w'] = 50
        cfg['profiles'][0]['efficiency_min_gain_w'] = 200
        r=Rig(document(cfg),power=2410)
        await r.run()
        self.assertEqual(r.calls,[('switch.a','on')])
        await r.grid(610)  # 2410 - 1800; below margin for B
        self.assertEqual(r.calls,[('switch.a','on')])
        await r.grid(650)  # 2450 - 1800; 50 W headroom for B
        self.assertEqual(r.calls[-1],('switch.b','on'))
        await r.grid(130)  # transient -20 W around 2450 W generation
        self.assertEqual(r.calls[-1],('switch.b','on'))
        self.assertEqual(r.c.mode,'running')


if __name__=='__main__': unittest.main()
