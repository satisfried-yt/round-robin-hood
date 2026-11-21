"""v0.3.0: scheduler strategy, persistence, profile priority and anti-flapping tests."""
import asyncio
import itertools
import math
import random
from copy import deepcopy
import unittest

from test_core import Rig, config, document
from rrh_tested.model import Config, UserError
from rrh_tested.scheduling import efficient_subset


def setup(strategy='classic', *, consumer_watts=(1800, 500, 800)):
    cfg = config()
    for row, watts in zip(cfg['consumers'], consumer_watts):
        row['watts'] = watts
    cfg['profiles'] = [dict(id='main', name='Main', enabled=True, strategy=strategy,
                            dashboard_order='allocation', consumer_ids=['a','b','c'])]
    return cfg


class StrategyModelTests(unittest.TestCase):
    def test_all_strategies_roundtrip_and_legacy_defaults(self):
        for strategy in ('classic','fair_runtime','fixed_priority','maximum_efficiency',
                         'power_asc','power_desc','stable_operation'):
            cfg=setup(strategy)
            with self.subTest(strategy=strategy):
                result=Config.parse(cfg)
                self.assertEqual(result.profiles[0].strategy,strategy)
                self.assertEqual(result,Config.parse(result.to_dict()))
                self.assertEqual(result.profiles[0].runtime_window,'7d')
        self.assertTrue(Config.parse(config()).data_quality_visible)

    def test_reject_incorrect_extended_config(self):
        for field,value in [('runtime_window','99d'),('fair_rotation_s',30),
                            ('fair_rotation_s',True),('efficiency_interval_s',0),
                            ('efficiency_min_gain_w',-1),('strategy','xyz')]:
            cfg=setup('fair_runtime');cfg['profiles'][0][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(UserError):Config.parse(cfg)
        cfg=setup();cfg['data_quality_visible']='false'
        with self.assertRaises(UserError):Config.parse(cfg)
        cfg=setup('maximum_efficiency')
        for i in range(24):
            row=dict(cfg['consumers'][0],id=f'extra{i}',entity_id=f'switch.extra{i}')
            cfg['consumers'].append(row)
            cfg['profiles'][0]['consumer_ids'].append(row['id'])
        with self.assertRaises(UserError):Config.parse(cfg)

    def test_optimizer_exact_vs_bruteforce_and_stable_ties(self):
        from rrh_tested.model import Consumer
        for seed in range(40):
            random.seed(seed)
            n=random.randint(1,12)
            values=[random.randint(10,1200) for _ in range(n)]
            cap=random.randint(20,4000)
            devices=[Consumer(str(i),str(i),f'switch.s{i}',w,True,True) for i,w in enumerate(values)]
            running={str(i) for i in range(n) if random.getrandbits(1)}
            chosen=efficient_subset(devices,cap,running)
            chosen_w=sum(d.watts for d in devices if d.id in chosen)
            brute=max(sum(values[i] for i in range(n) if mask&(1<<i)) for mask in range(1<<n)
                      if sum(values[i] for i in range(n) if mask&(1<<i)) <= cap)
            with self.subTest(seed=seed):
                self.assertEqual(chosen_w,brute)
                self.assertLessEqual(chosen_w,cap)
        devices=[Consumer(str(i),str(i),f'switch.s{i}',500,True,True) for i in range(4)]
        self.assertEqual(efficient_subset(devices,1000,{'0','2'}),{'0','2'})


class StrategiesInOperation(unittest.IsolatedAsyncioTestCase):
    async def test_fixed_priority_ignores_cursor_and_preempts_lower_member(self):
        cfg=setup('fixed_priority')
        r=Rig(document(cfg,cursor='c'),power=2000)
        await r.run()
        self.assertEqual(r.calls,[('switch.a','on')])
        await r.grid(100)
        self.assertEqual(r.calls,[('switch.a','on')])
        cfg=setup('fixed_priority')
        r=Rig(document(cfg,owned=['b','c']),power=700,
              states={'switch.b':'on','switch.c':'on'})
        await r.run()
        self.assertEqual(r.calls[0],('switch.c','off'))
        await r.grid(1500)
        self.assertEqual(r.calls[-1],('switch.b','off'))
        await r.grid(2000)
        self.assertEqual(r.calls[-1],('switch.a','on'))

    async def test_power_ascending_descending_order(self):
        for strategy, first in [('power_asc','switch.b'),('power_desc','switch.a')]:
            r=Rig(document(setup(strategy)),power=2500)
            await r.run()
            with self.subTest(strategy=strategy):self.assertEqual(r.calls[0],(first,'on'))

    async def test_descending_skips_unaffordable_larger_device(self):
        r=Rig(document(setup('power_desc')),power=900)
        await r.run()
        self.assertEqual(r.calls,[('switch.c','on')])

    async def test_stable_operation_leaves_running_on_and_no_repacking(self):
        cfg=setup('stable_operation')
        r=Rig(document(cfg,owned=['b']),power=150,
              states={'switch.b':'on'})
        await r.run()
        self.assertEqual(r.calls,[])
        await r.tick(10)
        self.assertEqual(r.calls,[])
        await r.grid(1900)
        self.assertEqual(r.calls,[('switch.a','on')])

    async def test_fair_runtime_all_time_and_fixed_period(self):
        cfg=setup('fair_runtime')
        cfg['profiles'][0]['runtime_window']='all'
        d=document(cfg)
        d['runtime_totals_s']={'a':600,'b':60,'c':360}
        d['fairness']={'totals':{'fair_runtime':{'main':{'a':600,'b':60,'c':360}},'fair_energy':{}},'segments':[]}
        r=Rig(d,power=2500);await r.run()
        self.assertEqual(r.calls,[('switch.b','on')])
        r2=Rig(deepcopy(r.disk),power=2500,states={'switch.b':'on'})
        self.assertEqual(r2.c.runtime_totals_s['a'],600)
        self.assertEqual(r2.c._runtime_seconds('b','all'),60)  # now=100; elapsed=0
        cfg['profiles'][0]['runtime_window']='24h'
        d=document(cfg)
        d['runtime_segments']=[['a',10,20],['b',40,50],['c',0,30]]
        d['fairness']={'totals':{'fair_runtime':{'main':{'a':10,'b':10,'c':30}},'fair_energy':{}},
                       'segments':[['fair_runtime','main','a',10,20,1800],['fair_runtime','main','b',40,50,500],['fair_runtime','main','c',0,30,800]]}
        r=Rig(d,power=2500); await r.run()
        self.assertEqual(r.calls,[('switch.a','on')])  # Legacy rolling credits excluded until the first new fixed period begins.

    async def test_fair_runtime_replacement_after_rotation_and_protection(self):
        cfg=setup('fair_runtime',consumer_watts=(1000,500,800))
        cfg['profiles'][0].update(fair_rotation_s=60,runtime_window='all')
        d=document(cfg,owned=['a']);d['started_at']={'a':5}
        d['fairness']={'totals':{'fair_runtime':{'main':{'a':95,'b':0,'c':0}},'fair_energy':{}},'segments':[]}
        r=Rig(d,power=100,states={'switch.a':'on'})
        await r.run()
        self.assertEqual(r.calls,[('switch.a','off')])
        await r.grid(1100)
        self.assertEqual(r.calls[-1],('switch.b','on'))
        cfg['consumers'][0].update(min_on_s=500,min_on_strict=True)
        r=Rig(document(cfg,owned=['a']),power=100,states={'switch.a':'on'})
        await r.run()
        self.assertEqual(r.calls,[])

    async def test_fair_ledger_recorded_on_confirmed_off_and_persisted(self):
        cfg=setup('fair_runtime')
        r=Rig(document(cfg),power=2500)
        await r.run()
        await r.tick(50)
        await r.grid(150)
        await r.tick(50)
        await r.grid(0)
        await r.tick(31)
        self.assertIn(('switch.a','off'),r.calls)
        self.assertGreaterEqual(r.c.runtime_totals_s.get('a',0),122)
        self.assertTrue(r.disk['runtime_segments'])
        restored=Rig(deepcopy(r.disk),power=100)
        restored.now = r.now  # Real wall-clock keeps advancing across HA restarts.
        self.assertEqual(restored.c.runtime_totals_s['a'],r.c.runtime_totals_s['a'])
        self.assertGreaterEqual(restored.c._runtime_seconds('a','7d'),122)

    async def test_efficiency_replaces_two_with_one_improving_use(self):
        cfg=setup('maximum_efficiency',consumer_watts=(1800,500,800))
        r=Rig(document(cfg,owned=['b','c']),power=700,
              states={'switch.b':'on','switch.c':'on'})
        await r.run()
        self.assertEqual(r.calls,[('switch.b','off')])
        await r.grid(1200)
        self.assertEqual(r.calls[-1],('switch.c','off'))
        await r.grid(2000)
        self.assertEqual(r.calls[-1],('switch.a','on'))
        await r.grid(200)
        self.assertEqual(r.c.owned,['a'])
        self.assertEqual(r.c.mode,'running')

    async def test_ordinary_minimum_runtime_blocks_strategy_rotation(self):
        # Non-strict minimum run still guards voluntary scheduling swaps;
        # strict only differentiates power-deficit shedding.
        for strategy in ('fixed_priority', 'maximum_efficiency', 'fair_runtime'):
            cfg = setup(strategy, consumer_watts=(1800, 500, 800))
            cfg['consumers'][1].update(min_on_s=400, min_on_strict=False)
            cfg['profiles'][0].update(fair_rotation_s=60)
            d = document(cfg, owned=['b', 'c'])
            d['started_at'] = {'b': 80, 'c': 0}
            r = Rig(d, power=700, states={'switch.b': 'on', 'switch.c': 'on'})
            await r.run()
            with self.subTest(strategy=strategy):
                self.assertEqual(r.calls, [])

    async def test_optimizer_forgets_plan_when_paused_or_stopped(self):
        cfg = setup('maximum_efficiency', consumer_watts=(1800, 500, 800))
        r = Rig(document(cfg, owned=['b','c']), power=700,
                states={'switch.b':'on','switch.c':'on'})
        await r.run()
        self.assertEqual(r.calls, [('switch.b', 'off')])
        self.assertTrue(r.c._efficiency_goals)
        r.c.pause()
        self.assertFalse(r.c._efficiency_goals)
        r.c._efficiency_goals['main'] = {'a'}
        await r.c.emergency_off()
        self.assertFalse(r.c._efficiency_goals)

    async def test_efficiency_respects_min_gain_and_min_on(self):
        cfg=setup('maximum_efficiency',consumer_watts=(1300,500,800))
        # Running B+C = 1300 W, can trade for A =1300 but no gain.
        r=Rig(document(cfg,owned=['b','c']),power=100,
              states={'switch.b':'on','switch.c':'on'})
        await r.run();self.assertEqual(r.calls,[])
        cfg=setup('maximum_efficiency',consumer_watts=(1800,500,800))
        cfg['consumers'][1].update(min_on_s=300,min_on_strict=True)
        r=Rig(document(cfg,owned=['b','c']),power=700,states={'switch.b':'on','switch.c':'on'})
        await r.run()
        self.assertEqual(r.calls,[])

    async def test_protected_profile_priority_and_classic_not_bypassed(self):
        cfg=setup('classic'); cfg['profiles'].append(dict(id='second',name='Other',enabled=True,
                     strategy='power_asc',dashboard_order='fixed',consumer_ids=[]))
        cfg['profiles'][0]['consumer_ids']=['a'];cfg['profiles'][1]['consumer_ids']=['b','c']
        r=Rig(document(cfg),power=1200);await r.run()
        self.assertEqual(r.calls,[])  # Classic does not allow lower strategy to skip blocked A.

    async def test_strategy_conserves_condition_shutdown_priority(self):
        cfg=setup('maximum_efficiency')
        cfg['consumers'][0]['conditions']={'enabled':True,'logic':'all','rules':[
            dict(id='temp',entity_id='sensor.temp',operator='<',value=21,hysteresis=0)]}
        r=Rig(document(cfg,owned=['a']),power=500,states={'switch.a':'on'})
        r.c.observe_condition('sensor.temp','30')
        await r.run()
        self.assertEqual(r.calls[0],('switch.a','off'))

if __name__ == '__main__':unittest.main()
