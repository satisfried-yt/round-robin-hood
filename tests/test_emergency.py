"""Explicit main switch OFF: all configured virtual switches, confirmed and durable.

No physical devices; real core and HA adapter executed against injected fakes.
"""
import asyncio
from copy import deepcopy
import unittest

import load_core
from rrh_tested.controller import Controller
from rrh_tested.model import UserError
from test_core import Rig, document, config
from test_adapter import AdapterTests


class EmergencyCoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_off_includes_external_disabled_and_unknown_and_preserves_cursor(self):
        cfg=config(); cfg["consumers"][1]["enabled"]=False
        saved=document(cfg,cursor="c",owned=["a"])
        r=Rig(saved,power=0,states={"switch.a":"on","switch.b":"on","switch.c":"unavailable"})
        # B is external, disabled; C has an unknown state. Still command OFF for all.
        await r.c.emergency_off()
        self.assertEqual([e for e,t in r.calls if t=="off"],["switch.a","switch.b","switch.c"])
        self.assertEqual(r.c.mode,"stopped")
        self.assertEqual(r.c.cursor,"c")
        self.assertEqual(r.c.owned,[])
        self.assertFalse(r.c.emergency_unresolved)
        self.assertFalse(r.disk["emergency_unresolved"])

    async def test_off_works_without_source_and_in_error_and_is_idempotent(self):
        r=Rig(power=1000,states={"switch.a":"on"}); r.c.observe_grid("unavailable","W")
        self.assertEqual(r.c.mode,"paused")
        await r.c.emergency_off()
        self.assertEqual(r.c.mode,"stopped")
        await r.c.emergency_off()
        self.assertEqual(r.c.mode,"stopped")
        self.assertEqual([target for e,target in r.calls if target=="on"],[])

    async def test_stop_during_in_flight_start_does_not_commit_allocation(self):
        r=Rig(timeout=.4)
        dispatched=asyncio.Event(); release=asyncio.Event()
        async def send(entity_id,target,token):
            if target=="on":
                dispatched.set(); await release.wait()
                r.c.observe_switch(entity_id,"on",command_token=token)
            else:
                r.c.observe_switch(entity_id,"off",command_token=token)
        r.send_hook=send
        await r.c.activate(); await dispatched.wait()
        stop_task=asyncio.create_task(r.c.emergency_off())
        await asyncio.sleep(0)
        release.set()
        await stop_task; await r.c.settle()
        self.assertEqual(r.c.cursor,None)
        self.assertEqual(r.disk["cursor"],None)
        self.assertEqual(r.c.mode,"stopped")
        self.assertEqual(r.c.states["switch.a"],"off")
        self.assertFalse(r.c.emergency_unresolved)

    async def test_unconfirmed_off_is_not_reported_as_success_and_blocks_restart(self):
        r=Rig(timeout=.02,states={"switch.a":"on"})
        async def send(entity_id,target,token):
            if entity_id != "switch.a":
                r.c.observe_switch(entity_id,target,command_token=token)
        r.send_hook=send
        with self.assertRaisesRegex(UserError,"unvollst"):
            await r.c.emergency_off()
        self.assertEqual(r.c.mode,"error")
        self.assertTrue(r.disk["emergency_unresolved"])
        with self.assertRaises(UserError): await r.c.activate()
        restored=Rig(deepcopy(r.disk),timeout=.02,states={"switch.a":"on"})
        with self.assertRaises(UserError): await restored.c.activate()
        r.send_hook=None
        await r.c.emergency_off()
        self.assertEqual(r.c.mode,"stopped")
        self.assertFalse(r.disk["emergency_unresolved"])

    async def test_service_error_does_not_clear_emergency_marker(self):
        r=Rig(timeout=.02,states={"switch.a":"on"})
        async def fails(e,t,k):
            raise RuntimeError("service unavailable")
        r.send_hook=fails
        with self.assertLogs("rrh_tested.controller",level="ERROR"):
            with self.assertRaises(UserError): await r.c.emergency_off()
        self.assertTrue(r.c.emergency_unresolved)
        self.assertTrue(r.disk["emergency_unresolved"])
        self.assertIsNone(r.c.cursor)

    async def test_unexpected_on_after_successful_main_off_is_visible(self):
        r=Rig(states={"switch.a":"on"})
        await r.c.emergency_off()
        r.c.observe_switch("switch.a","on",explicit_external=True)
        await r.c.settle()
        self.assertEqual(r.c.mode,"error")
        self.assertTrue(r.c.emergency_unresolved)
        self.assertEqual([t for e,t in r.calls], ["off","off","off"])

    async def test_no_configured_consumers_is_safe(self):
        cfg=config(); cfg["consumers"]=[]
        r=Rig(document(cfg))
        await r.c.emergency_off()
        self.assertEqual(r.c.mode,"stopped")
        self.assertEqual(r.calls,[])

    async def test_saved_schema_1_without_new_flag_remains_readable(self):
        r=Rig(); self.assertNotIn("emergency_unresolved", document())
        self.assertFalse(r.c.emergency_unresolved)
        self.assertEqual(r.c.document()["schema"],1)


class MainOffAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self): await AdapterTests.asyncSetUp(self)
    async def asyncTearDown(self): await AdapterTests.asyncTearDown(self)
    async def request(self, action, **fields): return await AdapterTests.request(self, action, **fields)
    async def test_api_uses_one_bulk_off_even_when_panel_not_open(self):
        await self.request("activate")
        self.hass.states.set("sensor.grid","2500",{"unit_of_measurement":"W"})
        await self.hass.drain()
        self.hass.states.set("switch.b","on")  # externally switched in paused? triggers fault
        conn=await self.request("emergency_off")
        self.assertFalse(conn.errors,conn.errors)
        calls=[item for item in self.hass.services.calls if item[1]=="turn_off"]
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][2]["entity_id"],["switch.a","switch.b","switch.c"])
        self.assertEqual(self.rt.controller.mode,"stopped")
        self.assertEqual(self.rt.controller.cursor,"a")
        self.assertEqual(self.rt.controller.status()["managed_w"],0)


if __name__ == "__main__": unittest.main()
