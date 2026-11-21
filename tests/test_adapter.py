"""Real adapter/bootstrap functions exercised against the documented test doubles."""
import asyncio
from datetime import datetime, timedelta, timezone
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import load_core
from ha_doubles import stubs,Hass,Connection,Context
from test_core import config
from rrh_tested.const import DOMAIN,STORAGE_KEY,ENTRY_GENERATION


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patch=stubs(); self.patch.start()
        self.tmp=tempfile.TemporaryDirectory()
        self.hass=Hass(self.tmp.name)
        spec=importlib.util.spec_from_file_location("rrh_tested.bootstrap",load_core.COMPONENT/"__init__.py")
        self.boot=importlib.util.module_from_spec(spec); self.boot.__package__="rrh_tested"; spec.loader.exec_module(self.boot)
        self.entry=SimpleNamespace(data={"generation":ENTRY_GENERATION},async_on_unload=lambda fn:None)
        self.hass.states.set("sensor.grid","2500",{"unit_of_measurement":"W"})
        for name in ["a","b","c"]: self.hass.states.set(f"switch.{name}","off")
        await self.boot.async_setup(self.hass,{})
        await self.boot.async_setup_entry(self.hass,self.entry)
        self.rt=self.entry.runtime_data
        await self.rt.configure(config(),0); await self.hass.drain()

    async def asyncTearDown(self):
        await self.boot.async_unload_entry(self.hass,self.entry)
        self.patch.stop(); self.tmp.cleanup()

    async def request(self,action,**fields):
        conn=Connection()
        self.hass.commands[f"{DOMAIN}/command"](self.hass,conn,{"id":1,"type":f"{DOMAIN}/command","action":action,**fields})
        await self.hass.drain(); return conn

    async def test_bootstrap_registers_one_panel_and_cache_safe_resource(self):
        self.assertEqual(len(self.hass.panels),1)
        self.assertEqual(len(self.hass.http.paths),3)
        self.assertFalse(self.hass.http.paths[0].cache_headers)
        self.assertTrue(Path(self.hass.http.paths[0].path).is_file())
        self.assertEqual(self.hass.http.paths[1].url_path, "/round_robin_hood/brand.png")
        self.assertTrue(Path(self.hass.http.paths[1].path).is_file())
        panel=next(iter(self.hass.panels.values()))
        self.assertTrue(panel["require_admin"])
        expected_version = (load_core.ROOT / "VERSION").read_text().strip()
        self.assertEqual(panel["module_url"], f"/{DOMAIN}/panel.js?v={expected_version}")
        self.assertEqual(self.rt.controller.mode,"stopped")
        self.assertTrue(self.rt.store.atomic_writes)

    async def test_same_value_real_report_unblocks_but_rebinding_does_not(self):
        seq=self.rt.controller.reading.sequence
        self.rt.bind(); self.assertEqual(self.rt.controller.reading.sequence,seq)
        await self.request("activate"); self.assertEqual(self.hass.services.calls,[])
        self.hass.states.set("sensor.grid","2500",{"unit_of_measurement":"W"})
        await self.hass.drain()
        self.assertEqual(len(self.hass.services.calls),1)
        self.assertEqual(self.rt.controller.cursor,"a")
        self.assertEqual(self.hass.services.calls[0][0:2],("switch","turn_on"))

    async def test_pause_command_does_not_send_off(self):
        await self.request("activate")
        self.hass.states.set("sensor.grid","2500",{"unit_of_measurement":"W"}); await self.hass.drain()
        await self.request("pause")
        self.assertEqual(len(self.hass.services.calls),1)
        self.assertEqual(self.rt.controller.mode,"paused")

    async def test_configuration_schema_and_revision_error_reaches_client(self):
        response=await self.request("configure",config=config(),revision=0)
        self.assertEqual(len(response.errors),1)
        response=await self.request("participation",consumer_id="a",enabled=False,revision=self.rt.controller.revision)
        self.assertFalse(response.errors)
        self.assertFalse(self.rt.controller.config.consumers[0].enabled)

    async def test_non_admin_denied_by_decorator_boundary_double(self):
        conn=Connection(admin=False)
        with self.assertRaises(PermissionError):
            self.hass.commands[f"{DOMAIN}/status"](self.hass,conn,{"id":1,"type":f"{DOMAIN}/status"})
        with self.assertRaises(PermissionError):
            self.hass.commands[f"{DOMAIN}/command"](self.hass,conn,{"id":2,"type":f"{DOMAIN}/command","action":"activate"})
        self.assertEqual(self.hass.services.calls,[])

    async def test_config_flow_refuses_existing_legacy_entry(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location("rrh_tested.flow",load_core.COMPONENT/"config_flow.py")
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        flow=module.RoundRobinHoodConfigFlow()
        flow.existing=[SimpleNamespace(data={})]
        result=await flow.async_step_user({})
        self.assertEqual(result,{"type":"abort","reason":"single_instance_allowed"})

    async def test_legacy_entry_cannot_load_rebuild(self):
        legacy=SimpleNamespace(data={},async_on_unload=lambda fn:None)
        with self.assertRaisesRegex(Exception,"Alter RRH-Eintrag"):
            await self.boot.async_setup_entry(self.hass,legacy)


    async def test_user_context_external_change_is_not_mistaken_for_own(self):
        await self.request("activate")
        self.hass.states.set("switch.b","on",context=Context(user_id="user")); await self.hass.drain()
        self.assertEqual(self.rt.controller.mode,"error"); self.assertEqual(self.rt.controller.owned,[])

    async def test_stale_existing_state_is_not_freshened_by_bind(self):
        old=datetime.now(timezone.utc)-timedelta(seconds=120)
        self.hass.states.set("sensor.grid","2500",{"unit_of_measurement":"W"},timestamp=old)
        self.rt.bind()
        conn=await self.request("activate")
        self.assertTrue(conn.errors); self.assertEqual(self.hass.services.calls,[])

    async def test_unload_reload_keeps_saved_config_and_cleans_listeners(self):
        await self.request("activate")
        self.hass.states.set("sensor.grid","2500",{"unit_of_measurement":"W"}); await self.hass.drain()
        await self.boot.async_unload_entry(self.hass,self.entry)
        self.assertEqual(self.hass.listeners,[]); self.assertEqual(self.hass.timers,[]); self.assertEqual(self.hass.panels,{})
        await self.boot.async_setup(self.hass,{})
        await self.boot.async_setup_entry(self.hass,self.entry)
        self.rt=self.entry.runtime_data; await self.hass.drain()
        self.assertEqual(self.rt.controller.mode,"stopped"); self.assertEqual(self.rt.controller.cursor,"a")
        self.assertEqual(len(self.hass.http.paths),3); self.assertEqual(len(self.hass.panels),1)
        saved=json.loads((Path(self.tmp.name)/STORAGE_KEY).read_text())
        self.assertEqual(saved["data"]["cursor"],"a")

    async def test_swallowed_ha_store_failure_is_caught_by_disk_verification(self):
        original=self.rt.store.async_save
        async def silently_fail(data): pass
        self.rt.store.async_save=silently_fail
        cfg=config(); cfg["reserve_w"]=250
        response=await self.request("configure",config=cfg,revision=self.rt.controller.revision)
        self.assertTrue(response.errors)
        self.assertEqual(self.rt.controller.mode,"error")
        self.assertEqual(self.rt.controller.config.reserve_w,100)
        self.assertEqual(self.hass.services.calls,[])
        self.rt.store.async_save=original

    async def test_existing_unreadable_store_does_not_boot_empty(self):
        from rrh_tested.runtime import Runtime
        rt=Runtime(self.hass)
        async def corrupt_load_returns_none(): return None
        rt.store.async_load=corrupt_load_returns_none
        with self.assertRaises(ValueError): await rt.start()
        self.assertEqual(self.hass.services.calls,[])

    async def test_config_flow_is_only_singleton_bootstrap(self):
        module=importlib.import_module("rrh_tested.config_flow")
        flow=module.RoundRobinHoodConfigFlow()
        self.assertEqual((await flow.async_step_user())["type"],"form")
        result=await flow.async_step_user({})
        self.assertEqual(result["type"],"create_entry"); self.assertEqual(result["data"],{"generation":ENTRY_GENERATION})
        flow.configured=True
        with self.assertRaises(UserWarning): await flow.async_step_user({})


if __name__=="__main__": unittest.main()
