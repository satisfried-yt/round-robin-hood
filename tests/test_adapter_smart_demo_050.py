"""0.5.0: actual RRH Home Assistant transport against explicit HA boundary doubles.

These are integration-adapter tests, not tests on physical equipment or HA Core.
"""
import asyncio
import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

import load_core
from ha_doubles import stubs, Hass, Connection
from rrh_tested.const import DOMAIN, ENTRY_GENERATION, STORAGE_KEY
from rrh_tested.model import Config
from test_smart_demo_050 import smart_config


class SmartServices:
    def __init__(self, hass):
        self.hass = hass
        self.calls = []
        self.suppress_level_feedback = False

    def has_service(self, domain, service):
        return (domain, service) in {
            ("switch", "turn_on"), ("switch", "turn_off"),
            ("number", "set_value"), ("select", "select_option"),
            ("climate", "set_fan_mode"), ("climate", "set_hvac_mode")}

    async def async_call(self, domain, service, data, *, blocking, context):
        assert blocking
        self.calls.append((domain, service, data.copy()))
        eid = data["entity_id"]
        if domain == "switch":
            for key in ([eid] if isinstance(eid, str) else eid):
                self.hass.states.set(key, "on" if service == "turn_on" else "off", context=context)
        elif domain == "number" and not self.suppress_level_feedback:
            self.hass.states.set(eid, str(data["value"]), context=context)
        elif domain == "select" and not self.suppress_level_feedback:
            self.hass.states.set(eid, data["option"], context=context)
        elif domain == "climate":
            old = self.hass.states.get(eid)
            attrs = dict(old.attributes if old else {})
            if service == "set_fan_mode" and not self.suppress_level_feedback:
                attrs["fan_mode"] = data["fan_mode"]
            self.hass.states.set(eid, data["hvac_mode"] if service == "set_hvac_mode" else old.state,
                                 attrs, context=context)


class AdapterSmartDemoTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patch = stubs(); self.patch.start()
        self.tmp = tempfile.TemporaryDirectory()
        self.hass = Hass(self.tmp.name)
        self.hass.services = SmartServices(self.hass)
        self.hass.states.set("sensor.grid", "2000", {"unit_of_measurement":"W"})
        self.hass.states.set("switch.normal", "off")
        self.hass.states.set("number.heater", "0", {"min":0,"max":3000,"step":50})
        self.hass.states.set("select.heater", "off", {"options":["off","1","2","3"]})
        self.hass.states.set("switch.heater", "off")
        self.hass.states.set("climate.heater", "off", {"fan_mode":"1", "fan_modes":["1","2","3"],"hvac_modes":["off","heat"]})
        spec = importlib.util.spec_from_file_location("rrh_tested.bootstrap",load_core.COMPONENT/"__init__.py")
        self.boot=importlib.util.module_from_spec(spec); self.boot.__package__="rrh_tested"; spec.loader.exec_module(self.boot)
        self.entry=SimpleNamespace(data={"generation":ENTRY_GENERATION},async_on_unload=lambda fn:None)
        await self.boot.async_setup(self.hass,{})
        await self.boot.async_setup_entry(self.hass,self.entry)
        self.rt=self.entry.runtime_data

    async def asyncTearDown(self):
        await self.boot.async_unload_entry(self.hass,self.entry)
        self.patch.stop()
        self.tmp.cleanup()

    async def request(self, action, **fields):
        conn=Connection()
        self.hass.commands[f"{DOMAIN}/command"](self.hass,conn,{"id":1,"type":f"{DOMAIN}/command","action":action,**fields})
        await self.hass.drain()
        return conn

    async def test_demo_isolated_and_restores_live_without_services_or_store_write(self):
        cfg=smart_config(); await self.rt.configure(cfg, self.rt.controller.revision)
        live_before=self.rt.controller.status()
        storage=Path(self.tmp.name)/STORAGE_KEY
        bytes_before=storage.read_bytes()
        errors=await self.request("demo_mode",demo_enabled=True)
        self.assertEqual(errors.errors,[])
        self.assertEqual(len(self.rt.active.config.consumers),6)
        self.assertEqual(self.rt.active.config.profiles[0].name,"Demo – Standard")
        await self.request("demo_power",demo_power_w=3000)
        await self.request("activate")
        await self.rt.active.settle()
        self.assertGreater(self.rt.active.status()["managed_w"],0)
        self.assertEqual(self.hass.services.calls,[])
        self.assertEqual(storage.read_bytes(),bytes_before)
        await self.request("emergency_off")
        result=await self.request("demo_mode",demo_enabled=False)
        self.assertFalse(result.errors,result.errors)
        self.assertIs(self.rt.active, self.rt.controller)
        self.assertEqual(self.rt.controller.status()["config"],live_before["config"])
        self.assertEqual(storage.read_bytes(),bytes_before)
        self.assertEqual(self.hass.services.calls,[])

    async def test_demo_denied_when_real_automation_running(self):
        cfg=smart_config();await self.rt.configure(cfg,self.rt.controller.revision)
        await self.request("activate")
        result=await self.request("demo_mode",demo_enabled=True)
        self.assertTrue(result.errors)
        self.assertIsNone(self.rt.demo)
        self.assertEqual(self.hass.services.calls,[])

    async def test_stepless_number_control_and_all_off(self):
        cfg=smart_config();await self.rt.configure(cfg,self.rt.controller.revision)
        await self.request("activate")
        self.hass.states.set("sensor.grid","2000",{"unit_of_measurement":"W"})
        await self.hass.drain()
        # A completed command requires a fresh meter report before the next allocation.
        self.hass.states.set("sensor.grid","1500",{"unit_of_measurement":"W"})
        await self.hass.drain()
        self.assertTrue(any(call[0:2]==("number","set_value") and call[2].get("value")==200 for call in self.hass.services.calls),self.hass.services.calls)
        self.assertIn("r",self.rt.controller.owned)
        await self.request("emergency_off")
        self.assertEqual(self.hass.states.get("number.heater").state,"0")

    async def test_staged_select_levels_and_confirmed_off(self):
        cfg=smart_config(mode="staged")
        await self.rt.configure(cfg,self.rt.controller.revision)
        await self.request("activate")
        self.hass.states.set("sensor.grid","2000",{"unit_of_measurement":"W"})
        await self.hass.drain()
        # A completed command requires a fresh meter report before the next allocation.
        self.hass.states.set("sensor.grid","1500",{"unit_of_measurement":"W"})
        await self.hass.drain()
        self.assertTrue(any(x[:2]==("select","select_option") and x[2]["option"]=="1" for x in self.hass.services.calls))
        self.assertEqual(self.hass.states.get("select.heater").state,"1")
        await self.request("emergency_off")
        self.assertEqual(self.hass.states.get("select.heater").state,"off")

    async def test_staged_climate_with_separate_or_shared_master(self):
        cfg=smart_config(mode="staged")
        cfg["consumers"][1]["entity_id"]="climate.heater"
        cfg["consumers"][1]["stage_entity_id"]="climate.heater"
        await self.rt.configure(cfg,self.rt.controller.revision)
        await self.request("activate")
        self.hass.states.set("sensor.grid","2000",{"unit_of_measurement":"W"})
        await self.hass.drain()
        # A completed command requires a fresh meter report before the next allocation.
        self.hass.states.set("sensor.grid","1500",{"unit_of_measurement":"W"})
        await self.hass.drain()
        calls=[(a,b) for a,b,_ in self.hass.services.calls]
        self.assertIn(("climate","set_fan_mode"),calls)
        self.assertIn(("climate","set_hvac_mode"),calls)
        self.assertEqual(self.hass.states.get("climate.heater").state,"heat")
        await self.request("emergency_off")
        self.assertEqual(self.hass.states.get("climate.heater").state,"off")

    async def test_failed_stage_feedback_pauses_without_power_assumption(self):
        cfg=smart_config(mode="staged")
        self.hass.services.suppress_level_feedback=True
        await self.rt.configure(cfg,self.rt.controller.revision)
        await self.request("activate")
        self.hass.states.set("sensor.grid","2000",{"unit_of_measurement":"W"})
        await self.hass.drain()
        # A completed command requires a fresh meter report before the next allocation.
        self.hass.states.set("sensor.grid","1500",{"unit_of_measurement":"W"})
        await self.hass.drain()
        self.assertEqual(self.rt.controller.mode,"error")
        self.assertNotIn("r",self.rt.controller.owned)

if __name__ == "__main__": unittest.main()
