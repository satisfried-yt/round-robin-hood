"""v0.5.0 smart loads and completely isolated demo regression tests."""
import asyncio
import json
import unittest
from copy import deepcopy

import load_core
from rrh_tested.model import Config, UserError
from rrh_tested.controller import Controller
from rrh_tested.demo import DemoSandbox


def smart_config(mode="variable", residual=True, stage_master="select"):
    cfg = Config().to_dict()
    cfg["grid_entity"] = "sensor.grid"
    fixed = {"id":"f", "name":"Normal 500 W", "entity_id":"switch.normal", "watts":500,
             "enabled":True,"virtual_confirmed":True}
    flex = {"id":"r", "name":"Regler", "entity_id":"number.heater" if mode=="variable" else "select.heater",
            "watts":200 if mode=="variable" else 500,"enabled":True,"virtual_confirmed":True,
            "power_mode":mode,"power_hysteresis_w":50,"power_interval_s":5}
    if mode == "variable":
        flex.update(max_watts=3000,power_step_w=50)
    else:
        flex.update(power_steps=[{"watts":500,"option":"1"},{"watts":1000,"option":"2"},{"watts":1500,"option":"3"}],
                    stage_entity_id="select.heater", off_option="off")
    cfg["consumers"] = [fixed, flex]
    cfg["profiles"] = [{"id":"standard","name":"Standard","enabled":True,"strategy":"classic",
                        "consumer_ids":["f","r"],"dashboard_order":"fixed", "allow_power_skip":True}]
    cfg["residual_consumer_id"] = "r" if residual else ""
    return cfg


class Fake:
    def __init__(self, cfg, generation=2000):
        self.t=100
        self.generation=generation
        self.saves=[]
        self.calls=[]
        self.control=Controller(None, send=self.send, send_level=self.level, save=self.save,
                                clock=lambda: self.t, wall_clock=lambda: self.t,
                                confirmation_timeout=0.5)
        self.cfg=cfg

    async def start(self):
        await self.control.configure(self.cfg,0)
        for c in self.control.config.consumers:
            self.control.seed_switch(c.entity_id,"off")
        self.grid()

    def grid(self):
        consume=sum(self.control._load_w(c) for c in self.control.config.consumers
                    if self.control.states.get(c.entity_id)=="on")
        self.control.observe_grid(str(self.generation - consume),"W")

    async def save(self, data):
        self.saves.append(json.loads(json.dumps(data)))

    async def send(self, eid, target, token):
        self.calls.append((eid,target))
        c=next(x for x in self.control.config.consumers if x.entity_id==eid)
        self.control.observe_switch(eid,target,command_token=token)
        if target == "on" and c.power_mode!="fixed": self.control.observe_power_level(c.id,c.watts)
        self.grid()

    async def level(self,c,watts,token):
        self.calls.append((c.entity_id,watts))
        self.control.observe_power_level(c.id,watts)
        self.grid()

    async def tick(self,seconds=10):
        self.t+=seconds
        self.grid()
        await self.control.settle()


class SchemaTests(unittest.TestCase):
    def test_roundtrip_variable_and_stage(self):
        for mode in ["staged","variable"]:
            with self.subTest(mode=mode):
                cfg=Config.parse(smart_config(mode))
                self.assertEqual(cfg,Config.parse(json.loads(json.dumps(cfg.to_dict()))))
                self.assertEqual(cfg.residual_consumer_id,"r")
                self.assertEqual(cfg.consumers[1].power_mode,mode)

    def test_unsafe_control_schema_denied(self):
        cases=[("variable", "entity_id", "light.heater"),
               ("variable", "max_watts", 199),
               ("variable", "power_step_w", 0),
               ("staged", "power_steps", [{"watts":1000,"option":"1"}, {"watts":500,"option":"2"}]),
               ("staged", "stage_entity_id", "script.turn_on"),
               ("staged", "off_option", "1")]
        for mode,key,value in cases:
            d=smart_config(mode);d["consumers"][1][key]=value
            with self.subTest(mode=mode,key=key), self.assertRaises(UserError): Config.parse(d)

    def test_no_shared_stage_actuator(self):
        d=smart_config(mode="staged")
        d["consumers"][0]["entity_id"]="select.others"
        d["consumers"][0]["power_mode"]="staged"
        d["consumers"][0]["power_steps"]=[{"watts":500,"option":"1"},{"watts":1000,"option":"2"}]
        d["consumers"][0]["stage_entity_id"]="select.heater"
        with self.assertRaises(UserError): Config.parse(d)

    def test_fixed_does_not_become_residual(self):
        d=smart_config();d["residual_consumer_id"]="f"
        with self.assertRaises(UserError): Config.parse(d)


class SmartTests(unittest.IsolatedAsyncioTestCase):
    async def test_residual_low_priority_and_power_ramp(self):
        rig=Fake(smart_config(),generation=2100)
        await rig.start();await rig.control.activate();await rig.control.settle()
        self.assertEqual(rig.calls[:2],[("switch.normal","on"),("number.heater","on")])
        self.assertGreaterEqual(rig.control.power_levels["r"],200)
        await rig.tick()
        self.assertTrue(any(call[0]=="number.heater" and isinstance(call[1],(int,float)) and call[1]>200 for call in rig.calls))
        self.assertLessEqual(rig.control.status()["managed_w"],2000)

    async def test_regulated_stage_quantization(self):
        rig=Fake(smart_config(mode="staged"),generation=1950)
        await rig.start();await rig.control.activate();await rig.control.settle()
        await rig.tick()
        self.assertIn(("select.heater",1000.),rig.calls)
        self.assertNotIn(("select.heater",1500.),rig.calls)

    async def test_priority_consumes_residual_headroom(self):
        cfg=smart_config()
        rig=Fake(cfg,generation=1800)
        await rig.start()
        # Only residual is eligible at first.
        await rig.control.configure({**cfg,"consumers":[{**cfg["consumers"][0],"enabled":False},cfg["consumers"][1]]},1)
        await rig.control.activate(); await rig.control.settle(); await rig.tick()
        self.assertIn("r",rig.control.owned)
        start_power=rig.control._load_w(rig.control.config.consumers[1])
        # Enabling a higher priority normal load must first reclaim residual watts.
        await rig.control.participation("f",True,rig.control.revision); await rig.tick(); await rig.tick()
        self.assertIn("f",rig.control.owned)
        self.assertLessEqual(rig.control._load_w(rig.control.config.consumers[1]),start_power)

    async def test_level_mismatch_faults_closed(self):
        rig=Fake(smart_config(),generation=1500)
        await rig.start();await rig.control.activate();await rig.control.settle()
        c=rig.control
        # A manual setpoint change without an RRH pending request is never adopted silently.
        c.observe_power_level("r",999,explicit_external=True)
        self.assertEqual(c.mode,"error")


class DemoTests(unittest.IsolatedAsyncioTestCase):
    async def test_six_isolated_consumers_and_generation_feedback(self):
        d=DemoSandbox();await d.start()
        self.assertEqual(len(d.controller.config.consumers),6)
        self.assertTrue(all(c.entity_id.startswith("switch.rrh_demo_") for c in d.controller.config.consumers))
        await d.controller.activate();await d.controller.settle()
        self.assertEqual(d.controller.status()["managed_w"],800)
        self.assertEqual(d.controller.status()["power"]["export_w"],800)
        d.set_power(3000); await d.controller.settle()
        self.assertGreaterEqual(len(d.controller.owned),2)
        await d.controller.emergency_off()
        self.assertEqual(d.controller.status()["managed_w"],0)
        await d.close()

    async def test_slider_bounds_and_no_external_storage(self):
        d=DemoSandbox();await d.start()
        for invalid in [-1,10001,True,5.5]:
            with self.subTest(invalid=invalid),self.assertRaises(UserError):d.set_power(invalid)
        self.assertEqual(d.controller.config.grid_entity,"sensor.rrh_demo_grid")
        await d.close()

if __name__=="__main__": unittest.main()
