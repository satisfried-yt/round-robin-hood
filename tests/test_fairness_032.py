"""v0.3.2: independent fair-time/energy accounting, persistence, windows, reset and dispatch."""
from copy import deepcopy
import unittest

from test_core import Rig, config, document
from rrh_tested.fairness import FairLedger
from rrh_tested.model import Config, UserError


def setup(strategy='fair_runtime', *, members=('a',), window='all', skip=False):
    cfg = config()
    cfg['profiles'] = [dict(id='standard', name='Standard', enabled=True,
                            strategy=strategy, dashboard_order='allocation',
                            consumer_ids=list(members), runtime_window=window,
                            fair_rotation_s=60, allow_power_skip=skip)]
    return cfg


def fairness(*, runtime=None, energy=None, segments=None):
    return {'totals': {'fair_runtime': {'standard': runtime} if runtime is not None else {},
                       'fair_energy': {'standard': energy} if energy is not None else {}},
            'segments': segments or []}


class FairModel032(unittest.TestCase):
    def test_new_energy_strategy_in_config_with_both_skip_modes(self):
        for strategy in ('fair_runtime','fair_energy'):
            for skip in (True, False):
                with self.subTest(strategy=strategy, skip=skip):
                    cfg = setup(strategy, members=('a','b'), skip=skip)
                    parsed = Config.parse(cfg)
                    self.assertEqual(parsed.profiles[0].strategy,strategy)
                    self.assertEqual(parsed.profiles[0].allow_power_skip,skip)
                    self.assertEqual(Config.parse(parsed.to_dict()),parsed)

    def test_ledger_rejects_invalid_records_and_does_not_invent_history(self):
        profile = Config.parse(setup()).profiles
        consumers = Config.parse(setup()).consumers
        for payload in ({}, {'totals':{},'segments':[]},
                        fairness(runtime={'nonexistent':1}),
                        fairness(segments=[['fair_energy','standard','a',0,10,-10]]),
                        fairness(segments=[['fair_runtime','standard','a',20,10,1800]])):
            with self.subTest(payload=payload),self.assertRaises(UserError):
                FairLedger(payload,profiles=profile,consumers=consumers)
        self.assertEqual(FairLedger(None).value('fair_runtime','standard','a','all',100),0)

    def test_fixed_period_windows_use_correct_overlaps_and_historical_watts(self):
        now = 40 * 86400.0
        records = [
            ['fair_runtime','standard','a',now-100,now-50,1800],
            ['fair_runtime','standard','a',now-2*86400,now-2*86400+100,1800],
            ['fair_energy','standard','a',now-100,now-50,500],
            ['fair_energy','standard','a',now-2*86400,now-2*86400+100,1800],
        ]
        state = fairness(runtime={'a':150},energy={'a':(50*500+100*1800)/3600},segments=records)
        cfg=Config.parse(setup()); l=FairLedger(state,profiles=cfg.profiles,consumers=cfg.consumers)
        # Anchored three days ago: the current 24-hour period has 50s,
        # while both 7-day and 14-day periods retain 150s.
        l.ensure_started('fair_runtime','standard',now-3*86400-100)
        l.ensure_started('fair_energy','standard',now-3*86400-100)
        self.assertAlmostEqual(l.value('fair_runtime','standard','a','24h',now),50)
        self.assertAlmostEqual(l.value('fair_runtime','standard','a','7d',now),150)
        self.assertAlmostEqual(l.value('fair_runtime','standard','a','14d',now),150)
        self.assertAlmostEqual(l.value('fair_runtime','standard','a','all',now),150)
        self.assertAlmostEqual(l.value('fair_energy','standard','a','24h',now),50*500/3600)
        self.assertAlmostEqual(l.value('fair_energy','standard','a','30d',now),(50*500+100*1800)/3600)

    def test_strategy_scoping_and_reset_do_not_affect_other_metric_or_profile(self):
        cfg=Config.parse(setup())
        state=fairness(runtime={'a':500},energy={'a':200},segments=[
            ['fair_runtime','standard','a',50,100,1800],
            ['fair_energy','standard','a',50,100,1800]])
        l=FairLedger(state,profiles=cfg.profiles,consumers=cfg.consumers)
        l.reset('fair_runtime','standard')
        self.assertEqual(l.value('fair_runtime','standard','a','all',100),0)
        self.assertEqual(l.value('fair_energy','standard','a','all',100),200)
        self.assertEqual(len(l.document()['segments']),1)


class FairController032(unittest.IsolatedAsyncioTestCase):
    async def test_migration_old_total_runtime_has_no_fairness_credit(self):
        cfg=setup(members=('a','b'),window='all')
        doc=document(cfg)
        doc['runtime_totals_s']={'a':5*86400,'b':6*3600}
        r=Rig(doc,power=2500)
        self.assertEqual(r.c._fair_value('fair_runtime',r.c.config.profiles[0],'a'),0)
        await r.run()
        self.assertEqual(r.calls[0],('switch.a','on'))
        self.assertEqual(r.disk['fairness']['totals']['fair_runtime'],{})
        self.assertEqual(r.c.runtime_totals_s['a'],5*86400)

    async def test_runtime_counts_only_running_owned_confirmed_and_pauses_freeze(self):
        r=Rig(document(setup()),power=2500)
        await r.run()
        self.assertEqual(r.calls,[('switch.a','on')])
        self.assertEqual(r.c.status()['profiles'][0]['fair_values']['a'],0)
        r.now += 3600
        self.assertAlmostEqual(r.c.status()['profiles'][0]['fair_values']['a'],3600)
        r.c.pause()
        self.assertAlmostEqual(r.c.status()['profiles'][0]['fair_values']['a'],3600)
        r.now += 999
        self.assertAlmostEqual(r.c.status()['profiles'][0]['fair_values']['a'],3600)
        r.c.observe_grid('2500','W')
        await r.c.activate()
        r.now += 600
        r.c.pause()
        self.assertAlmostEqual(r.c.status()['profiles'][0]['fair_values']['a'],4200)
        await r.c.close()
        restored=Rig(deepcopy(r.disk),power=2500,states={'switch.a':'on'})
        self.assertAlmostEqual(restored.c.fairness.value('fair_runtime','standard','a','all',restored.now),4200)
        self.assertEqual(restored.c.mode,'paused')

    async def test_energy_is_watt_hours_only_during_energy_strategy(self):
        cfg=setup('fair_energy')
        r=Rig(document(cfg),power=2600)
        await r.run()
        self.assertEqual(r.calls[0],('switch.a','on'))
        r.now += 1200
        r.c.pause()
        # 1800W * 1200s / 3600 = 600Wh
        self.assertAlmostEqual(r.c.fairness.value('fair_energy','standard','a','all',r.now),600)
        self.assertEqual(r.c.fairness.value('fair_runtime','standard','a','all',r.now),0)
        new=deepcopy(r.c.config.to_dict());new['profiles'][0]['strategy']='fair_runtime'
        await r.c.configure(new,r.c.revision)
        r.c.observe_grid('2600','W')
        await r.c.activate()
        r.now += 300
        r.c.pause()
        self.assertAlmostEqual(r.c.fairness.value('fair_runtime','standard','a','all',r.now),300)
        self.assertAlmostEqual(r.c.fairness.value('fair_energy','standard','a','all',r.now),600)
        new=deepcopy(r.c.config.to_dict());new['profiles'][0]['strategy']='fair_energy'
        await r.c.configure(new,r.c.revision)
        r.c.observe_grid('2600','W'); await r.c.activate()
        r.now += 120
        r.c.pause()
        self.assertAlmostEqual(r.c.fairness.value('fair_energy','standard','a','all',r.now),660)
        self.assertAlmostEqual(r.c.fairness.value('fair_runtime','standard','a','all',r.now),300)

    async def test_reset_is_scoped_confirmed_and_requires_pause(self):
        doc=document(setup('fair_runtime'))
        doc['fairness']=fairness(runtime={'a':3600},energy={'a':500})
        doc['runtime_totals_s']={'a':7200}
        r=Rig(doc,power=2500)
        await r.run()
        with self.assertRaisesRegex(UserError,'pausieren'):
            await r.c.reset_fair('standard','fair_runtime',r.c.revision)
        r.c.pause()
        old_rev=r.c.revision
        with self.assertRaises(UserError):
            await r.c.reset_fair('standard','other',old_rev)
        with self.assertRaises(UserError):
            await r.c.reset_fair('missing','fair_runtime',old_rev)
        await r.c.reset_fair('standard','fair_runtime',old_rev)
        self.assertEqual(r.c.fairness.value('fair_runtime','standard','a','all',r.now),0)
        self.assertEqual(r.c.fairness.value('fair_energy','standard','a','all',r.now),500)
        self.assertEqual(r.c.runtime_totals_s['a'],7200)
        self.assertEqual(r.c.revision,old_rev+1)
        self.assertEqual(r.disk['fairness']['totals']['fair_runtime'],{})

    async def test_energy_order_prefers_lower_received_kwh_even_if_runtime_differs(self):
        cfg=setup('fair_energy',members=('a','b'),skip=False)
        doc=document(cfg)
        doc['fairness']=fairness(energy={'a':300,'b':50})
        r=Rig(doc,power=2600)
        await r.run()
        self.assertEqual(r.calls[0],('switch.b','on'))
        self.assertEqual(r.c.status()['profiles'][0]['fair_unit'],'Wh')

    async def test_energy_strict_and_skipping_unfit_candidate(self):
        cfg=setup('fair_energy',members=('a','b'),skip=False)
        doc=document(cfg)
        doc['fairness']=fairness(energy={'a':0,'b':100})
        r=Rig(doc,power=900)
        await r.run()
        self.assertEqual(r.calls,[])
        cfg['profiles'][0]['allow_power_skip']=True
        r=Rig(document(cfg),power=900)
        await r.run()
        self.assertEqual(r.calls,[('switch.b','on')])

    async def test_external_on_does_not_earn_fairness(self):
        doc=document(setup('fair_energy'))
        r=Rig(doc,power=2500,states={'switch.a':'on'})
        # The switch was ON before RRH started; RRH never adopted it.
        await r.run()
        r.now += 900
        r.c.pause()
        self.assertEqual(r.c.fairness.value('fair_energy','standard','a','all',r.now),0)

    async def test_profile_deactivation_interrupts_accrual(self):
        r=Rig(document(setup('fair_energy')),power=2500)
        await r.run()
        r.now += 100
        await r.c.profile_participation('standard',False,r.c.revision)
        await r.c.settle()
        recorded=r.c.fairness.value('fair_energy','standard','a','all',r.now)
        self.assertAlmostEqual(recorded,50)
        r.now+=3600
        self.assertAlmostEqual(r.c.fairness.value('fair_energy','standard','a','all',r.now),recorded)

    async def test_fair_ledger_persists_after_periodic_grid_checkpoint(self):
        r=Rig(document(setup('fair_energy')),power=2500)
        await r.run()
        r.now += 61
        await r.grid(500)
        self.assertGreaterEqual(r.disk['fairness']['totals']['fair_energy']['standard']['a'],30)
        self.assertEqual(r.c.status()['profiles'][0]['fair_unit'],'Wh')
        self.assertEqual(r.disk['runtime_totals_s'],{})
