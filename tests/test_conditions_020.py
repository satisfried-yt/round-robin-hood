"""Sensor gating: strict fail-closed rules, hysteresis, profile bulk OFF."""
import asyncio
from copy import deepcopy
import unittest

from test_core import Rig, config, document
from rrh_tested.model import Config, UserError


def rules(*entries, logic="all", enabled=True):
    return {"enabled": enabled, "logic": logic, "rules": [
        {"id": f"r{i}", "entity_id": entity, "operator": op, "value": threshold,
         "hysteresis": hyst} for i, (entity, op, threshold, hyst) in enumerate(entries)
    ]}


def cond_config(consumer=True, profile=False, **kw):
    cfg = config()
    if consumer:
        cfg["consumers"][0]["conditions"] = rules(("sensor.room", "<", 21, 1), **kw)
    if profile:
        cfg["profiles"] = [{"id":"winter", "name":"Winter", "enabled":True,
           "strategy":"classic", "consumer_ids":["a", "b", "c"],
           "dashboard_order":"fixed", "conditions": rules(("sensor.room", "<", 21, 1), **kw)}]
    return cfg


class ConditionValidation(unittest.TestCase):
    def test_upgrade_roundtrip(self):
        cfg = Config.parse(config())
        self.assertEqual(Config.parse(cfg.to_dict()),cfg)
        self.assertFalse(cfg.consumers[0].conditions.enabled)
        self.assertTrue(cfg.confirm_timer_skip)
        self.assertTrue(cfg.confirm_profile_toggle)

    def test_profile_and_consumer_conditions_can_be_independent(self):
        cfg=cond_config(profile=True)
        c=Config.parse(cfg)
        self.assertTrue(c.consumers[0].conditions.enabled)
        self.assertTrue(c.profiles[0].conditions.enabled)
        self.assertEqual(Config.parse(c.to_dict()), c)

    def test_validation_rejects_bad_rules(self):
        base=cond_config()
        for key,value in [('entity_id','switch.bad'),('operator','eval'),('value','21'),('hysteresis',-1),('hysteresis',float('inf')),('id','../foo')]:
            cfg=deepcopy(base)
            cfg['consumers'][0]['conditions']['rules'][0][key]=value
            with self.subTest(key=key),self.assertRaises(UserError): Config.parse(cfg)
        for value in [0,None,'false']:
            cfg=deepcopy(base)
            cfg['consumers'][0]['conditions']['enabled']=value
            with self.assertRaises(UserError): Config.parse(cfg)
        cfg=deepcopy(base);cfg['consumers'][0]['conditions']['rules']=[]
        with self.assertRaises(UserError):Config.parse(cfg)
        cfg=deepcopy(base);cfg['consumers'][0]['conditions']['rules'][0]['operator']='=='
        with self.assertRaises(UserError):Config.parse(cfg) # == cannot have hysteresis
        cfg=deepcopy(base);cfg['consumers'][0]['conditions']['rules']*=2
        with self.assertRaises(UserError):Config.parse(cfg)
        cfg=deepcopy(base);cfg['confirm_timer_skip']='false'
        with self.assertRaises(UserError):Config.parse(cfg)


class GateEngine(unittest.IsolatedAsyncioTestCase):
    async def test_unknown_sensor_is_visible_and_prevents_start(self):
        cfg=cond_config()
        r=Rig(document(cfg),power=3000)
        await r.run()
        self.assertEqual(r.calls,[('switch.b','on')]) # bad a skipped; b may start
        card=r.c.status()['consumers'][0]
        self.assertIn('sensor.room',card['wait_reason'])
        self.assertIn('nicht verfügbar',card['wait_reason'])
        self.assertFalse(card['conditions_allowed'])

    async def test_hysteresis_persists_and_prevents_chatter(self):
        cfg=cond_config()
        r=Rig(document(cfg),power=2000)
        r.c.observe_condition('sensor.room','19.7')
        await r.run()
        self.assertEqual(r.calls,[('switch.a','on')])
        self.assertTrue(r.disk['condition_latches']['consumer:a:r0'])
        await r.c.settle()
        await r.grid(50) # no strict runtime here; update at room sensor event below
        r.c.observe_condition('sensor.room','20.6')
        await r.c.settle()
        self.assertTrue(r.c.status()['consumers'][0]['conditions_allowed'])
        self.assertNotIn(('switch.a','off'),r.calls)
        r.c.observe_condition('sensor.room','21')
        await r.c.settle()
        self.assertIn(('switch.a','off'),r.calls)
        self.assertFalse(r.c.status()['consumers'][0]['conditions_allowed'])
        r.c.observe_condition('sensor.room','20.5')
        await r.c.settle()
        self.assertFalse(r.c.status()['consumers'][0]['conditions_allowed'])
        r.c.observe_condition('sensor.room','19.9')
        await r.c.settle()
        self.assertTrue(r.c.status()['consumers'][0]['conditions_allowed'])
        restored=Rig(deepcopy(r.disk),power=50,states={'switch.a':'off'})
        restored.c.observe_condition('sensor.room','20.5')
        self.assertTrue(restored.c.status()['consumers'][0]['conditions_allowed'])

    async def test_invalid_state_forces_off_despite_strict_minimum_and_deficit_barrier(self):
        cfg=cond_config()
        cfg['consumers'][0].update(min_on_s=600,min_on_strict=True)
        r=Rig(document(cfg,owned=['a']),power=2000,states={'switch.a':'on'})
        r.c.started_at['a']=r.now
        r.c.observe_condition('sensor.room','19')
        await r.run()
        r.c.wait_after_sequence=r.c.reading.sequence
        r.c.observe_condition('sensor.room','unavailable')
        await r.c.settle()
        self.assertIn(('switch.a','off'),r.calls)
        self.assertFalse(r.c.status()['consumers'][0]['conditions_allowed'])
        self.assertEqual(r.c.mode,'running')

    async def test_or_all_and_invalid_sensor(self):
        cfg=cond_config(logic='any')
        cfg['consumers'][0]['conditions']['rules'].append({'id':'r1','entity_id':'sensor.humidity',
             'operator':'>=','value':70,'hysteresis':0})
        r=Rig(document(cfg),power=3000)
        r.c.observe_condition('sensor.room','unavailable')
        r.c.observe_condition('sensor.humidity','75')
        self.assertTrue(r.c.status()['consumers'][0]['conditions_allowed'])
        await r.run()
        self.assertEqual(r.calls,[('switch.a','on')])
        r.c.observe_condition('sensor.humidity','unknown')
        await r.c.settle()
        self.assertIn(('switch.a','off'),r.calls)

    async def test_profile_blocks_all_own_loads_with_one_bulk_call(self):
        cfg=cond_config(consumer=False,profile=True)
        r=Rig(document(cfg,owned=['a','b']),power=200,states={'switch.a':'on','switch.b':'on'})
        sent=[]
        async def bulk(entities):
            sent.append(list(entities))
            for e in entities: r.c.observe_switch(e,'off',command_token='batch')
        r.c.send_all_off=bulk
        r.c.observe_condition('sensor.room','19')
        await r.run()
        r.c.observe_condition('sensor.room','21')
        await r.c.settle()
        self.assertEqual(sent,[['switch.a','switch.b']])
        self.assertEqual(r.c.owned,[])
        self.assertEqual(r.c.mode,'running')
        self.assertFalse(r.c.status()['profiles'][0]['conditions_allowed'])
        self.assertIn('sensor.room',r.c.status()['profiles'][0]['conditions_reason'])

    async def test_bulk_command_without_confirmations_faults_and_does_not_retry(self):
        cfg=cond_config(consumer=False,profile=True)
        r=Rig(document(cfg,owned=['a','b']),power=1000,states={'switch.a':'on','switch.b':'on'},timeout=.01)
        sent=[]
        async def bulk(entities): sent.append(list(entities))
        r.c.send_all_off=bulk
        r.c.observe_condition('sensor.room','unknown')
        await r.run()
        self.assertEqual(r.c.mode,'error')
        self.assertEqual(len(sent),1)
        self.assertIsNotNone(r.disk['incomplete'])
        await r.tick(60)
        self.assertEqual(len(sent),1)

    async def test_candidate_condition_is_skipped_but_power_shortage_is_not(self):
        cfg=cond_config(consumer=True)
        r=Rig(document(cfg),power=1000)
        r.c.observe_condition('sensor.room','22')
        await r.run()
        self.assertEqual(r.c.status()['next_id'],'c')
        self.assertIn(('switch.b','on'),r.calls)
        # With conditions allowed, a is first, and cannot be overtaken by b on low power.
        r2=Rig(document(cfg),power=1000)
        r2.c.observe_condition('sensor.room','19')
        await r2.run()
        self.assertEqual(r2.c.status()['next_id'],'a')
        self.assertEqual(r2.calls,[])


if __name__=='__main__':unittest.main()
