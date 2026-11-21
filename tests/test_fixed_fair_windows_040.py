"""v0.4.0: deterministic fixed, first-start-anchored fairness periods.

All checks use the actual controller, saved state and explicit HA test doubles.
No physical device, Home Assistant Core instance or network access is involved.
"""
from copy import deepcopy
import math
import unittest

from test_core import Rig, document
from test_fairness_032 import setup, fairness
from rrh_tested.fairness import FairLedger
from rrh_tested.model import Config, UserError

DAY = 86400


class FixedPeriodLedger040(unittest.TestCase):
    def setUp(self):
        cfg = Config.parse(setup(members=('a', 'b')))
        self.profiles, self.consumers = cfg.profiles, cfg.consumers

    def ledger(self, saved=None):
        return FairLedger(saved, profiles=self.profiles, consumers=self.consumers)

    def test_v033_document_is_readable_and_historical_total_is_preserved(self):
        saved = fairness(runtime={'a': 400}, segments=[
            ['fair_runtime', 'standard', 'a', 100, 200, 1800]])
        ledger = self.ledger(saved)
        self.assertEqual(ledger.value('fair_runtime', 'standard', 'a', 'all', 300), 400)
        self.assertEqual(ledger.value('fair_runtime', 'standard', 'a', '24h', 300), 0)
        self.assertEqual(ledger.document()['anchors']['fair_runtime'], {})
        self.assertTrue(ledger.ensure_started('fair_runtime', 'standard', 300))
        self.assertEqual(ledger.value('fair_runtime', 'standard', 'a', '24h', 300), 0)
        self.assertFalse(ledger.ensure_started('fair_runtime', 'standard', 400))
        self.assertEqual(ledger.period('fair_runtime', 'standard', '24h', 400), (300, 300, 300 + DAY))
        restored = self.ledger(ledger.document())
        self.assertEqual(restored.period('fair_runtime', 'standard', '24h', 400), (300, 300, 300 + DAY))
        self.assertEqual(restored.value('fair_runtime', 'standard', 'a', 'all', 400), 400)

    def test_24h_is_anchored_not_sliding_and_partial_boundary_counts(self):
        l = self.ledger()
        l.ensure_started('fair_energy', 'standard', 100)
        # 60 seconds at 1800W = 30Wh in first period.
        l.sync({('fair_energy','standard','a'): 1800}, 100)
        l.sync({}, 160)
        self.assertAlmostEqual(l.value('fair_energy','standard','a','24h',160),30)
        # Eleven hours later, still 30Wh rather than a moving cutoff.
        self.assertAlmostEqual(l.value('fair_energy','standard','a','24h',100+11*3600),30)
        self.assertEqual(l.value('fair_energy','standard','a','24h',100+DAY),0)
        # Long confirmed run spans the *next* period boundary.
        l.sync({('fair_energy','standard','a'): 1800}, 100+DAY-2)
        l.sync({}, 100+DAY+3)
        self.assertAlmostEqual(l.value('fair_energy','standard','a','24h',100+DAY+3),1.5)
        self.assertAlmostEqual(l.value('fair_energy','standard','a','all',100+DAY+3),32.5)

    def test_7_14_30_days_each_have_independent_fixed_boundaries(self):
        l = self.ledger()
        l.ensure_started('fair_runtime','standard',1000)
        l.sync({('fair_runtime','standard','a'): 500}, 1100)
        l.sync({}, 1110)
        l.sync({('fair_runtime','standard','a'): 500}, 1000+8*DAY+100)
        l.sync({}, 1000+8*DAY+120)
        now = 1000+8*DAY+200
        self.assertEqual(l.value('fair_runtime','standard','a','24h',now),20)
        self.assertEqual(l.value('fair_runtime','standard','a','7d',now),20)
        self.assertEqual(l.value('fair_runtime','standard','a','14d',now),30)
        self.assertEqual(l.value('fair_runtime','standard','a','30d',now),30)
        self.assertEqual(l.value('fair_runtime','standard','a','all',now),30)
        self.assertEqual(l.period('fair_runtime','standard','7d',now)[1],1000+7*DAY)
        self.assertEqual(l.period('fair_runtime','standard','14d',now)[1],1000)

    def test_paused_period_does_not_stop_the_clock(self):
        l=self.ledger();l.ensure_started('fair_runtime','standard',100)
        l.sync({('fair_runtime','standard','a'): 1800},100)
        l.sync({},200)
        self.assertEqual(l.value('fair_runtime','standard','a','24h',100+DAY-1),100)
        self.assertEqual(l.value('fair_runtime','standard','a','24h',100+DAY),0)
        self.assertEqual(l.document()['anchors']['fair_runtime']['standard'],100)

    def test_reset_reanchors_only_selected_profile_strategy(self):
        l=self.ledger()
        l.ensure_started('fair_runtime','standard',100)
        l.ensure_started('fair_energy','standard',200)
        l.sync({('fair_runtime','standard','a'): 1800},300)
        l.sync({},360)
        l.reset('fair_runtime','standard',now=1000)
        self.assertEqual(l.value('fair_runtime','standard','a','24h',1000),0)
        self.assertEqual(l.period('fair_runtime','standard','24h',1000),(1000,1000,1000+DAY))
        self.assertEqual(l.period('fair_energy','standard','24h',1000),(200,200,200+DAY))
        self.assertEqual(l.value('fair_runtime','standard','a','all',1000),0)

    def test_strict_anchor_validation_rejects_corrupt_storage(self):
        for bad in [-1,float('nan'),float('inf'),'0',1e13,True]:
            saved=fairness()
            saved['anchors']={'fair_runtime':{'standard':bad},'fair_energy':{}}
            with self.subTest(bad=bad), self.assertRaises(UserError):self.ledger(saved)
        saved=fairness()
        saved['anchors']={'fair_runtime':{'unknown':0},'fair_energy':{}}
        with self.assertRaises(UserError):self.ledger(saved)
        saved=fairness()
        saved['anchors']={'fair_runtime':{}}
        with self.assertRaises(UserError):self.ledger(saved)

    def test_restrict_drops_deleted_profile_anchor_and_counters(self):
        l=self.ledger()
        l.ensure_started('fair_runtime','standard',100)
        l.restrict(profiles=[],consumers=[])
        self.assertEqual(l.document()['anchors']['fair_runtime'],{})

    def test_14d_roundtrip_config_validation(self):
        cfg=setup(window='14d')
        self.assertEqual(Config.parse(cfg).profiles[0].runtime_window,'14d')
        self.assertEqual(Config.parse(Config.parse(cfg).to_dict()).profiles[0].runtime_window,'14d')


class FixedPeriodController040(unittest.IsolatedAsyncioTestCase):
    async def test_first_running_activation_starts_even_with_no_confirmed_load(self):
        r=Rig(document(setup(window='24h')),power=0)
        self.assertIsNone(r.c.status()['profiles'][0]['fair_period_start'])
        await r.run()
        self.assertEqual(r.calls,[])
        p=r.c.status()['profiles'][0]
        self.assertEqual(p['fair_period_origin'],100)
        self.assertEqual(p['fair_period_start'],100)
        self.assertEqual(p['fair_period_end'],100+DAY)
        self.assertEqual(r.disk['fairness']['anchors']['fair_runtime']['standard'],100)
        r.c.pause();r.now+=100
        self.assertEqual(r.c.status()['profiles'][0]['fair_period_origin'],100)

    async def test_no_period_starts_for_disabled_profile(self):
        cfg=setup(window='24h');cfg['profiles'][0]['enabled']=False
        cfg['profiles'].append(dict(id='active',name='Other',enabled=True,strategy='classic',
                                    dashboard_order='fixed',consumer_ids=['b']))
        r=Rig(document(cfg),power=2500)
        await r.run()
        self.assertIsNone(r.c.status()['profiles'][0]['fair_period_origin'])

    async def test_energy_rollover_in_dashboard_without_manual_reset(self):
        r=Rig(document(setup('fair_energy',window='24h')),power=2500)
        await r.run()
        r.now+=100
        self.assertAlmostEqual(r.c.status()['profiles'][0]['fair_values']['a'],50)
        r.c.pause()
        r.now=100+DAY
        p=r.c.status()['profiles'][0]
        self.assertEqual(p['fair_values']['a'],0)
        self.assertEqual(p['fair_period_start'],100+DAY)
        self.assertEqual(p['fair_period_end'],100+2*DAY)
        self.assertAlmostEqual(r.c.fairness.value('fair_energy','standard','a','all',r.now),50)
        r.c.observe_grid('2500','W')
        await r.c.activate(); await r.c.settle()
        r.now+=60
        self.assertAlmostEqual(r.c.status()['profiles'][0]['fair_values']['a'],30)
        r.c.pause()
        await r.c.close()
        restored=Rig(deepcopy(r.disk),power=2500,states={'switch.a':'on'})
        restored.now=r.now
        self.assertEqual(restored.c.status()['profiles'][0]['fair_period_origin'],100)
        self.assertAlmostEqual(restored.c.status()['profiles'][0]['fair_values']['a'],30)

    async def test_window_change_keeps_anchor_history(self):
        r=Rig(document(setup(window='24h')),power=2500)
        await r.run();r.now+=120;r.c.pause()
        cfg=deepcopy(r.c.config.to_dict());cfg['profiles'][0]['runtime_window']='14d'
        await r.c.configure(cfg,r.c.revision)
        p=r.c.status()['profiles'][0]
        self.assertEqual(p['fair_values']['a'],120)
        self.assertEqual(p['fair_period_origin'],100)
        cfg['profiles'][0]['runtime_window']='all'
        await r.c.configure(cfg,r.c.revision)
        self.assertEqual(r.c.status()['profiles'][0]['fair_values']['a'],120)
        cfg['profiles'][0]['runtime_window']='24h'
        await r.c.configure(cfg,r.c.revision)
        self.assertEqual(r.c.status()['profiles'][0]['fair_values']['a'],120)

    async def test_legacy_credit_does_not_get_redistributed_into_new_period(self):
        cfg=setup(window='24h')
        saved=document(cfg)
        saved['fairness']=fairness(runtime={'a':600},segments=[['fair_runtime','standard','a',10,90,1800]])
        r=Rig(saved,power=2500)
        self.assertEqual(r.c.status()['profiles'][0]['fair_values']['a'],0)
        self.assertEqual(r.c.fairness.value('fair_runtime','standard','a','all',100),600)
        await r.run()
        self.assertEqual(r.c.status()['profiles'][0]['fair_values']['a'],0)
        self.assertEqual(r.c.fairness.value('fair_runtime','standard','a','all',100),600)
        self.assertIn('anchors',r.disk['fairness'])

    async def test_explicit_reset_restarts_anchor_and_retains_pause(self):
        r=Rig(document(setup(window='24h')),power=2500)
        await r.run();r.now+=120;r.c.pause()
        await r.c.reset_fair('standard','fair_runtime',r.c.revision)
        p=r.c.status()['profiles'][0]
        self.assertEqual(p['fair_period_origin'],220)
        self.assertEqual(p['fair_values']['a'],0)
        self.assertEqual(r.c.mode,'paused')
        self.assertEqual(r.disk['fairness']['anchors']['fair_runtime']['standard'],220)


if __name__=='__main__': unittest.main()
