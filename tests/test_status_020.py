"""v0.2.0 user-visible condition and deficit scheduling state."""
import unittest
from test_core import Rig, config, document
from test_conditions_020 import cond_config


class StatusTests(unittest.IsolatedAsyncioTestCase):
    async def test_individual_deficit_countdown_visible_with_global_disabled(self):
        cfg=config(); cfg['global_shutdown_delay_enabled']=False
        cfg['consumers'][2]['shutdown_delay_s']=20
        r=Rig(document(cfg,owned=['c']),power=0,states={'switch.c':'on'})
        await r.run()
        item=next(c for c in r.c.status()['consumers'] if c['id']=='c')
        self.assertEqual(item['deficit_remaining_s'],20)
        self.assertEqual(r.c.mode,'running')
        await r.tick(7)
        item=next(c for c in r.c.status()['consumers'] if c['id']=='c')
        self.assertEqual(item['deficit_remaining_s'],13)
        await r.tick(13)
        self.assertEqual(r.calls,[('switch.c','off')])

    async def test_strict_minimum_cannot_mask_condition_off(self):
        cfg=cond_config()
        cfg['consumers'][0]['min_on_s']=600;cfg['consumers'][0]['min_on_strict']=True
        r=Rig(document(cfg,owned=['a']),power=300,states={'switch.a':'on'})
        r.c.started_at['a']=r.now
        r.c.observe_condition('sensor.room','19')
        await r.run()
        self.assertEqual(r.c.status()['consumers'][0]['min_remaining_s'],600)
        r.c.observe_condition('sensor.room','unavailable')
        await r.c.settle()
        self.assertEqual(r.calls,[('switch.a','off')])
        self.assertEqual(r.c.status()['consumers'][0]['min_remaining_s'],0)

    async def test_profile_bulk_overrides_all_strict_minimums(self):
        cfg=cond_config(consumer=False,profile=True)
        for c in cfg['consumers']:
            c['min_on_s']=600; c['min_on_strict']=True
        r=Rig(document(cfg,owned=['a','b']),power=300,states={'switch.a':'on','switch.b':'on'})
        r.c.started_at={'a':r.now,'b':r.now}
        bulks=[]
        async def send_all(entities):
            bulks.append(list(entities))
            for e in entities:r.c.observe_switch(e,'off',command_token='batch')
        r.c.send_all_off=send_all
        r.c.observe_condition('sensor.room','19')
        await r.run()
        r.c.observe_condition('sensor.room','unavailable')
        await r.c.settle()
        self.assertEqual(bulks,[['switch.a','switch.b']])
        self.assertEqual(r.c.owned,[])
        self.assertEqual(r.c.mode,'running')


if __name__=='__main__':unittest.main()
