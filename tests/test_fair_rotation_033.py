"""v0.3.3 regressions: rotating to the first actually achievable fair candidate.

The simulated HA reproduction is: 1,800 W waiting first (lowest Wh), 1,200 W
running and now higher in Wh than the waiting 500 W load. A nominal
1,400 W source leaves only 100 W spare after the running 1,200 W load
and a 100 W reserve. Power-skip must enable a controlled swap 1200 -> 500.
"""
from copy import deepcopy
import unittest
from test_core import Rig, config, document
from rrh_tested.model import Config, UserError


def fixture(kind='fair_energy', *, skip=True, current=330, target=270,
            gap=None, protected=False, rotation=60):
    cfg=config()
    for c, watts in zip(cfg['consumers'], (1800, 500, 1200)):
        c['watts']=watts
    if protected:
        cfg['consumers'][2]['min_on_s']=3600
    profile=dict(id='standard', name='Standard', enabled=True, strategy=kind,
                 dashboard_order='allocation', runtime_window='all',
                 fair_rotation_s=rotation, allow_power_skip=skip,
                 consumer_ids=['a','b','c'])
    if gap is not None:
        profile['fair_min_gap_wh' if kind == 'fair_energy' else 'fair_min_gap_s']=gap
    cfg['profiles']=[profile]
    doc=document(cfg, owned=['c'])
    doc['started_at']={'c':100.0}
    doc['fairness']={'totals':{'fair_runtime':{},'fair_energy':{}},'segments':[]}
    doc['fairness']['totals'][kind]['standard']={
        'a':102 if kind=='fair_energy' else 0,
        'b':target,
        'c':current,
    }
    return doc


class RotationModel033(unittest.TestCase):
    def test_migrate_032_with_default_fairness_gaps(self):
        doc=fixture()
        raw=doc['config']['profiles'][0]
        self.assertNotIn('fair_min_gap_wh',raw)
        parsed=Config.parse(doc['config'])
        self.assertEqual(parsed.profiles[0].fair_min_gap_s,60)
        self.assertEqual(parsed.profiles[0].fair_min_gap_wh,10)
        self.assertEqual(Config.parse(parsed.to_dict()),parsed)

    def test_invalid_gaps_fail_closed(self):
        for field, bad in [('fair_min_gap_wh',0),('fair_min_gap_wh',float('nan')),
                           ('fair_min_gap_s',-10),('fair_min_gap_s','30')]:
            with self.subTest(field=field,bad=bad):
                doc=fixture()
                doc['config']['profiles'][0][field]=bad
                with self.assertRaises(UserError):Config.parse(doc['config'])


class RotationController033(unittest.IsolatedAsyncioTestCase):
    async def test_energy_reproduction_performs_automatic_swap(self):
        r=Rig(fixture(),power=200,states={'switch.c':'on'})
        await r.run()
        self.assertEqual(r.calls,[])  # Rotation period still protects C.
        self.assertEqual(r.c.status()['profiles'][0]['next_id'],'b')
        r.now += 61; await r.grid(200)
        self.assertEqual(r.calls,[('switch.c','off')])
        # The next grid report includes the 1,200 W no longer drawn.
        await r.grid(1400)
        self.assertEqual(r.calls,[('switch.c','off'),('switch.b','on')])
        self.assertEqual(r.c.mode,'running')
        self.assertEqual(r.c.owned,['b'])

    async def test_runtime_uses_same_rotation_path(self):
        r=Rig(fixture('fair_runtime',current=600,target=250),power=200,states={'switch.c':'on'})
        await r.run()
        r.now += 61; await r.grid(200)
        self.assertEqual(r.calls,[('switch.c','off')])
        await r.grid(1400)
        self.assertEqual(r.calls[-1],('switch.b','on'))

    async def test_strict_policy_does_not_overtake_a(self):
        r=Rig(fixture(skip=False),power=200,states={'switch.c':'on'})
        await r.run()
        r.now += 120; await r.grid(200)
        self.assertEqual(r.calls,[])
        self.assertEqual(r.c.status()['profiles'][0]['next_id'],'a')

    async def test_no_swap_below_min_gap(self):
        r=Rig(fixture(current=273,target=270,gap=10),power=200,states={'switch.c':'on'})
        await r.run()
        r.now += 61; await r.grid(200)  # C accrues 20 Wh; now eligible, because C=293Wh
        self.assertEqual(r.calls,[('switch.c','off')])
        # For a narrow gap use 60-second enforced minimum, static controller
        # values to isolate the fair-gap predicate.
        r=Rig(fixture(current=273,target=270,gap=50),power=200,states={'switch.c':'on'})
        await r.run(); r.now += 61; await r.grid(200)
        self.assertEqual(r.calls,[])

    async def test_no_swap_before_rotation_or_during_minimum_runtime(self):
        r=Rig(fixture(protected=True),power=200,states={'switch.c':'on'})
        await r.run(); r.now += 120; await r.grid(200)
        self.assertEqual(r.calls,[])
        r=Rig(fixture(rotation=180),power=200,states={'switch.c':'on'})
        await r.run(); r.now += 61; await r.grid(200)
        self.assertEqual(r.calls,[])

    async def test_no_speculative_shedding_when_all_candidates_unfittable(self):
        doc=fixture()
        doc['config']['consumers'][1]['watts']=1900
        r=Rig(doc,power=200,states={'switch.c':'on'})
        await r.run();r.now += 120; await r.grid(200)
        self.assertEqual(r.calls,[])
        self.assertEqual(r.c.status()['profiles'][0]['next_id'],'a')

    async def test_external_load_is_not_preempted(self):
        doc=fixture()
        doc['owned']=[]
        doc['started_at']={}
        r=Rig(doc,power=200,states={'switch.c':'on'})
        await r.run(); r.now += 61; await r.grid(200)
        self.assertEqual(r.calls,[])

    async def test_fair_stats_continue_on_confirmed_swap_only(self):
        doc=fixture()
        r=Rig(doc,power=200,states={'switch.c':'on'})
        await r.run();r.now += 61; await r.grid(200)
        old_c=r.c.fairness.value('fair_energy','standard','c','all',r.now)
        await r.grid(1400)
        self.assertGreater(old_c,330)
        r.now += 61; await r.grid(900)
        self.assertEqual(r.c.fairness.value('fair_energy','standard','c','all',r.now),old_c)
        self.assertGreater(r.c.fairness.value('fair_energy','standard','b','all',r.now),270)


if __name__=='__main__': unittest.main()
