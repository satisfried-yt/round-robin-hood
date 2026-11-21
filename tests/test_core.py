"""Behaviour tests of the actual engine. HA service/storage are explicit fakes."""
import asyncio
from copy import deepcopy
import json
import unittest

import load_core
from rrh_tested.model import Config, Consumer, UserError, grid_watts, next_consumer
from rrh_tested.controller import Controller


def config():
    d = Config().to_dict()
    d["grid_entity"] = "sensor.grid"
    d["consumers"] = [dict(id=i, name=f"Load {i.upper()}", entity_id=f"switch.{i}", watts=w,
                            enabled=True, virtual_confirmed=True) for i, w in [("a",1800),("b",500),("c",800)]]
    return d


def document(cfg=None, cursor=None, owned=None, incomplete=None):
    return dict(schema=1, config=cfg or config(), revision=0, cursor=cursor,
                owned=owned or [], incomplete=incomplete)


class Rig:
    def __init__(self, saved=None, power=2500, states=None, timeout=0.15):
        self.now = 100.0
        self.calls = []
        self.writes = []
        self.disk = deepcopy(saved or document())
        self.send_hook = None
        self.save_hook = None
        self.c = Controller(self.disk, send=self.send, save=self.save, clock=lambda:self.now,
                            wall_clock=lambda:self.now, confirmation_timeout=timeout)
        for consumer in self.c.config.consumers:
            self.c.seed_switch(consumer.entity_id, (states or {}).get(consumer.entity_id, "off"))
        self.c.observe_grid(str(power), "W")

    async def save(self, data):
        if self.save_hook:
            await self.save_hook(data)
        self.disk = json.loads(json.dumps(data))
        self.writes.append(deepcopy(data))

    async def send(self, entity_id, target, token):
        self.calls.append((entity_id, target))
        if self.send_hook:
            await self.send_hook(entity_id, target, token)
        else:
            self.c.observe_switch(entity_id, target, command_token=token)

    async def run(self):
        await self.c.activate()
        await self.c.settle()

    async def grid(self, power, unit="W"):
        self.c.observe_grid(str(power), unit)
        await self.c.settle()

    async def tick(self, seconds):
        self.now += seconds
        self.c.wake()
        await self.c.settle()


class ModelTests(unittest.TestCase):
    def test_default_configuration_roundtrip(self):
        self.assertEqual(Config.parse(Config().to_dict()), Config())

    def test_power_units_direction_and_import(self):
        cases=[("1.2","kW",True,1200),("-1.2","kW",False,1200),("-700","W",True,-700),("0","W",False,0)]
        for raw,unit,sign,w in cases:
            with self.subTest(raw=raw,sign=sign):
                self.assertEqual(grid_watts(raw,unit,sign),w)

    def test_bad_power_is_not_zero(self):
        for raw in (None,"unknown","unavailable","nan","inf","-inf",True,"",{},"1,2"):
            with self.subTest(raw=raw), self.assertRaises(UserError):
                grid_watts(raw,"W",True)
        for unit in (None,"kWh","Wh","w",""):
            with self.subTest(unit=unit), self.assertRaises(UserError):
                grid_watts("10",unit,True)

    def test_config_rejects_invalid_numbers_and_duplicates(self):
        for key,value in [("reserve_w",True),("reserve_w",-1),("max_age_s",0),("shutdown_delay_s",-1),("reserve_w",float("nan"))]:
            d=config(); d[key]=value
            with self.subTest(key=key,value=value), self.assertRaises(UserError): Config.parse(d)
        d=config(); d["consumers"][1]["entity_id"]="switch.a"
        with self.assertRaises(UserError): Config.parse(d)
        d=config(); d["consumers"][1]["id"]="a"
        with self.assertRaises(UserError): Config.parse(d)

    def test_virtual_confirmation_required(self):
        d=config(); d["consumers"][0]["virtual_confirmed"]=False
        with self.assertRaises(UserError): Config.parse(d)

    def test_unknown_fields_and_bad_entity_rejected(self):
        d=config(); d["reserve"]=100
        with self.assertRaises(UserError): Config.parse(d)
        for key,value in [("entity_id","light.a"),("watts",0),("name","  "),("enabled","true"),("id","../x")]:
            d=config(); d["consumers"][0][key]=value
            with self.subTest(key=key), self.assertRaises(UserError): Config.parse(d)

    def test_cyclic_order_and_removed_anchor(self):
        cfg=Config.parse(config()); states={c.entity_id:"off" for c in cfg.consumers}
        self.assertEqual(next_consumer(cfg,"a",states).id,"b")
        self.assertEqual(next_consumer(cfg,"c",states).id,"a")
        self.assertEqual(next_consumer(cfg,"removed",states).id,"a")

    def test_running_disabled_and_unavailable_are_skipped(self):
        d=config(); d["consumers"][1]["enabled"]=False
        cfg=Config.parse(d)
        self.assertEqual(next_consumer(cfg,None,{"switch.a":"on","switch.b":"off","switch.c":"off"}).id,"c")
        self.assertEqual(next_consumer(cfg,None,{"switch.a":"unavailable","switch.b":"off","switch.c":"off"}).id,"c")
        self.assertIsNone(next_consumer(cfg,None,{}))


class ControllerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await asyncio.sleep(0)

    async def test_no_overtaking_or_cursor_change_while_waiting(self):
        r=Rig(power=1300); await r.run()
        self.assertEqual(r.calls,[]); self.assertIsNone(r.c.cursor)
        self.assertEqual(r.c.status()["next_id"],"a")
        self.assertIn("Kein",r.c.reason)

    async def test_confirmed_start_is_saved_and_waits_for_new_report(self):
        r=Rig(); await r.run()
        self.assertEqual(r.calls,[("switch.a","on")]); self.assertEqual(r.disk["cursor"],"a")
        self.assertEqual(r.disk["owned"],["a"]); self.assertIsNone(r.disk["incomplete"])
        for _ in range(20): r.c.wake()
        await r.c.settle(); self.assertEqual(len(r.calls),1)
        await r.grid(700)
        self.assertEqual(r.calls[-1],("switch.b","on")); self.assertEqual(r.c.cursor,"b")
        await r.grid(200); self.assertEqual(len(r.calls),2)
        self.assertEqual(r.c.status()["power"]["available_w"],100)

    async def test_budget_not_double_subtracted(self):
        r=Rig(document(cursor="a",owned=["a"]),power=700,states={"switch.a":"on"})
        await r.run()
        self.assertEqual(r.calls,[("switch.b","on")])

    async def test_no_forced_rotation_for_big_waiting_candidate(self):
        r=Rig(document(cursor="c",owned=["b","c"]),power=1200,states={"switch.b":"on","switch.c":"on"})
        await r.run(); await r.tick(40)
        self.assertEqual(r.calls,[]); self.assertEqual(r.c.cursor,"c")

    async def test_ack_alone_is_insufficient_until_service_returns(self):
        r=Rig(); gate=asyncio.Event(); reached=asyncio.Event()
        async def send(e,t,k):
            r.c.observe_switch(e,t,command_token=k); reached.set(); await gate.wait()
        r.send_hook=send
        await r.c.activate(); await reached.wait()
        self.assertIsNone(r.c.cursor); self.assertIsNone(r.disk["cursor"])
        self.assertEqual(r.disk["incomplete"],{"id":"a","target":"on"})
        gate.set(); await r.c.settle(); self.assertEqual(r.c.cursor,"a")

    async def test_service_success_without_state_times_out_once(self):
        r=Rig(timeout=.01)
        async def send(e,t,k): pass
        r.send_hook=send; await r.run()
        self.assertEqual(r.c.mode,"error"); self.assertIsNone(r.c.cursor)
        for _ in range(50): r.c.wake()
        await r.c.settle(); self.assertEqual(len(r.calls),1)
        self.assertEqual(r.disk["incomplete"],{"id":"a","target":"on"})

    async def test_service_error_after_state_on_does_not_commit(self):
        r=Rig()
        async def send(e,t,k):
            r.c.observe_switch(e,t,command_token=k); raise RuntimeError("injected service error")
        r.send_hook=send
        with self.assertLogs("rrh_tested.controller",level="ERROR"): await r.run()
        self.assertIsNone(r.c.cursor); self.assertEqual(r.c.owned,[]); self.assertEqual(r.c.mode,"error")

    async def test_late_confirmation_is_not_owned_or_counted(self):
        r=Rig(timeout=.01)
        async def send(e,t,k): pass
        r.send_hook=send; await r.run()
        r.c.observe_switch("switch.a","on"); await r.c.settle()
        self.assertEqual(r.c.owned,[]); self.assertIsNone(r.c.cursor)
        r.send_hook=None; await r.run()
        self.assertEqual(len(r.calls),1) # Re-activation still needs a post-command measurement.
        await r.grid(700); self.assertEqual(r.calls[-1],("switch.b","on"))

    async def test_pause_during_dispatched_command_records_ack_but_no_next(self):
        r=Rig(); gate=asyncio.Event(); reached=asyncio.Event()
        async def send(e,t,k):
            reached.set(); await gate.wait(); r.c.observe_switch(e,t,command_token=k)
        r.send_hook=send; await r.c.activate(); await reached.wait()
        r.c.pause(); gate.set(); await r.c.settle(); await r.grid(8000)
        self.assertEqual(r.c.mode,"paused"); self.assertEqual(r.c.cursor,"a"); self.assertEqual(len(r.calls),1)

    async def test_pause_before_dispatch_cancels_proposal(self):
        r=Rig(); await r.c.settle(); reached=asyncio.Event(); gate=asyncio.Event()
        async def save(data):
            if data["incomplete"]:
                reached.set(); await gate.wait()
        r.save_hook=save; await r.c.activate(); await reached.wait()
        r.c.pause(); gate.set(); await r.c.settle()
        self.assertEqual(r.calls,[]); self.assertIsNone(r.disk["cursor"]); self.assertIsNone(r.disk["incomplete"])

    async def test_pause_during_activation_storage_is_not_lost(self):
        r=Rig(); await r.c.settle(); reached=asyncio.Event(); gate=asyncio.Event()
        async def save(data): reached.set(); await gate.wait()
        r.save_hook=save; task=asyncio.create_task(r.c.activate()); await reached.wait()
        r.c.pause(); gate.set()
        with self.assertRaises(UserError): await task
        await r.c.settle(); self.assertEqual(r.c.mode,"paused"); self.assertEqual(r.calls,[])

    async def test_power_change_during_preflight_write_revalidated(self):
        r=Rig(); reached=asyncio.Event(); gate=asyncio.Event()
        async def save(data):
            if data["incomplete"]: reached.set(); await gate.wait()
        r.save_hook=save; await r.c.activate(); await reached.wait()
        r.c.observe_grid("300","W"); gate.set(); await r.c.settle()
        self.assertEqual(r.calls,[]); self.assertIsNone(r.c.cursor)

    async def test_invalid_source_during_preflight_sends_nothing(self):
        r=Rig(); reached=asyncio.Event(); gate=asyncio.Event()
        async def save(data):
            if data["incomplete"]: reached.set(); await gate.wait()
        r.save_hook=save; await r.c.activate(); await reached.wait()
        r.c.observe_grid("unavailable","W"); gate.set(); await r.c.settle()
        self.assertEqual(r.calls,[]); self.assertEqual(r.c.mode,"error")

    async def test_source_loss_never_means_zero_or_automatic_off(self):
        r=Rig(); await r.run(); await r.grid("unavailable")
        self.assertEqual(r.c.mode,"error"); self.assertIsNone(r.c.status()["power"]["available_w"])
        self.assertEqual(r.calls,[("switch.a","on")]); self.assertEqual(r.c.states["switch.a"],"on")
        await r.grid(0); self.assertEqual(len(r.calls),1); self.assertEqual(r.c.mode,"error")

    async def test_stale_value_stays_visible_but_unusable(self):
        r=Rig(power=1000); await r.run(); await r.tick(61)
        self.assertEqual(r.c.mode,"error"); self.assertEqual(r.c.status()["power"]["export_w"],1000)
        self.assertIsNone(r.c.status()["power"]["available_w"])
        with self.assertRaises(UserError): await r.c.activate()

    async def test_equal_reports_are_fresh_without_artificial_wiggle(self):
        r=Rig(power=1000); await r.run()
        for _ in range(10):
            r.now+=40; await r.grid(1000)
        self.assertEqual(r.c.mode,"running"); self.assertEqual(r.calls,[])
        self.assertEqual(r.c.status()["power"]["age_s"],0)

    async def test_restored_and_future_dated_values_block_activation(self):
        r=Rig(); await r.c.settle()
        r.c.observe_grid("2500","W",restored=True)
        with self.assertRaises(UserError): await r.c.activate()
        r.c.observe_grid("2500","W",age_s=-60)
        with self.assertRaises(UserError): await r.c.activate()
        await r.c.settle(); self.assertEqual(r.calls,[])

    async def test_deficit_delay_fifo_and_no_cursor_change_on_stop(self):
        r=Rig(document(cursor="b",owned=["a","b"]),power=50,states={"switch.a":"on","switch.b":"on"})
        await r.run(); await r.tick(29); self.assertEqual(r.calls,[])
        await r.tick(1); self.assertEqual(r.calls,[("switch.a","off")]); self.assertEqual(r.c.cursor,"b")
        await r.grid(-200); self.assertEqual(r.calls[-1],("switch.b","off")); self.assertEqual(r.c.cursor,"b")

    async def test_deficit_recovery_resets_timer(self):
        r=Rig(document(cursor="a",owned=["a"]),power=-100,states={"switch.a":"on"})
        await r.run(); await r.tick(25); await r.grid(100)
        await r.tick(10); await r.grid(50); await r.tick(29)
        self.assertEqual(r.calls,[])
        await r.tick(1); self.assertEqual(r.calls,[("switch.a","off")])

    async def test_zero_delay_is_immediate_protection_not_disabled(self):
        cfg=config(); cfg["shutdown_delay_s"]=0
        r=Rig(document(cfg,cursor="a",owned=["a"]),power=50,states={"switch.a":"on"})
        await r.run(); self.assertEqual(r.calls,[("switch.a","off")])

    async def test_invalid_measurement_resets_deficit_not_counted_as_elapsed(self):
        r=Rig(document(cursor="a",owned=["a"]),power=0,states={"switch.a":"on"})
        await r.run(); await r.tick(20); await r.grid("unknown"); await r.tick(40)
        await r.grid(0); await r.run(); await r.tick(20)
        self.assertEqual(r.calls,[])
        await r.tick(10); self.assertEqual(r.calls,[("switch.a","off")])

    async def test_manual_change_pauses_and_relinquishes_ownership(self):
        r=Rig(); await r.run(); r.c.observe_switch("switch.a","off",explicit_external=True); await r.c.settle()
        self.assertEqual(r.c.mode,"error"); self.assertEqual(r.c.owned,[]); self.assertEqual(r.disk["owned"],[])
        self.assertEqual(r.c.cursor,"a"); self.assertEqual(len(r.calls),1)

    async def test_foreign_running_load_is_not_adopted_or_shed(self):
        r=Rig(power=0,states={"switch.a":"on"}); await r.run(); await r.tick(31)
        self.assertEqual(r.calls,[]); self.assertEqual(r.c.owned,[])

    async def test_external_change_while_paused_is_not_reacquired(self):
        r=Rig(document(cursor="a",owned=["a"]),states={"switch.a":"on"})
        r.c.observe_switch("switch.a","off"); r.c.observe_switch("switch.a","on"); await r.c.settle()
        self.assertEqual(r.c.mode,"paused"); self.assertEqual(r.c.owned,[])
        await r.grid(0); await r.run(); await r.tick(31); self.assertEqual(r.calls,[])

    async def test_unknown_owned_load_pauses_without_blind_off(self):
        r=Rig(); await r.run(); r.c.observe_switch("switch.a","unavailable"); await r.c.settle()
        self.assertEqual(r.c.mode,"error"); self.assertEqual(len(r.calls),1)

    async def test_contradictory_state_and_explicit_external_ack_fail(self):
        for external in (False, True):
            with self.subTest(external=external):
                r=Rig()
                async def send(e,t,k):
                    r.c.observe_switch(e,t,command_token=None if external else k,explicit_external=external)
                    if not external: r.c.observe_switch(e,"off")
                r.send_hook=send
                with self.assertLogs("rrh_tested.controller",level="ERROR"): await r.run()
                self.assertEqual(r.c.mode,"error"); self.assertIsNone(r.c.cursor)

    async def test_disable_running_owned_load_stops_without_delay(self):
        r=Rig(document(cursor="a",owned=["a"]),power=500,states={"switch.a":"on"})
        # B would not fit because of reserve; no other start.
        await r.run(); await r.c.participation("a",False,r.c.revision); await r.c.settle()
        self.assertEqual(r.calls,[("switch.a","off")]); self.assertEqual(r.c.cursor,"a")

    async def test_disable_while_paused_defers_all_commands(self):
        r=Rig(document(cursor="a",owned=["a"]),power=500,states={"switch.a":"on"})
        await r.c.participation("a",False,0); await r.c.settle(); self.assertEqual(r.calls,[])
        await r.run(); self.assertEqual(r.calls,[("switch.a","off")])

    async def test_configuration_crud_reorder_and_stale_revision(self):
        r=Rig(); await r.c.settle(); cfg=r.c.config.to_dict()
        cfg["consumers"][0]["name"]="Renamed"
        cfg["consumers"].reverse(); await r.c.configure(cfg,0)
        self.assertEqual(r.disk["config"]["consumers"][-1]["name"],"Renamed")
        with self.assertRaises(UserError): await r.c.configure(cfg,0)
        removed = cfg["consumers"].pop()
        for profile in cfg["profiles"]:
            profile["consumer_ids"] = [cid for cid in profile["consumer_ids"] if cid != removed["id"]]
        await r.c.configure(cfg,1)
        self.assertEqual(len(r.c.config.consumers),2); self.assertEqual(r.calls,[])

    async def test_edit_running_or_remove_owned_on_is_rejected(self):
        r=Rig(document(cursor="a",owned=["a"]),power=500,states={"switch.a":"on"})
        await r.c.settle(); cfg=config(); cfg["consumers"]=cfg["consumers"][1:]
        with self.assertRaises(UserError): await r.c.configure(cfg,0)
        await r.run()
        with self.assertRaises(UserError): await r.c.configure(config(),0)

    async def test_cursor_removal_retains_history_without_faking_allocation(self):
        r=Rig(document(cursor="a")); await r.c.settle(); cfg=config(); cfg["consumers"]=cfg["consumers"][1:]
        await r.c.configure(cfg,0)
        self.assertEqual(r.c.cursor,"a"); self.assertEqual(r.c.status()["next_id"],"b")

    async def test_store_failure_before_send_blocks_actuation(self):
        r=Rig(); await r.c.settle()
        async def save(data):
            if data["incomplete"]: raise OSError("injected disk failure")
        r.save_hook=save
        with self.assertLogs("rrh_tested.controller",level="ERROR"): await r.run()
        self.assertEqual(r.calls,[]); self.assertIsNone(r.c.cursor); self.assertEqual(r.c.mode,"error")

    async def test_store_failure_after_confirmation_does_not_commit_cursor(self):
        r=Rig()
        async def save(data):
            if data["cursor"]=="a": raise OSError("injected disk failure")
        r.save_hook=save
        with self.assertLogs("rrh_tested.controller",level="ERROR"): await r.run()
        self.assertEqual(r.calls,[("switch.a","on")]); self.assertIsNone(r.c.cursor); self.assertIsNone(r.disk["cursor"])
        self.assertEqual(r.c.mode,"error"); self.assertIsNotNone(r.disk["incomplete"])

    async def test_storage_failure_keeps_previous_configuration(self):
        r=Rig(); await r.c.settle(); cfg=config(); cfg["reserve_w"]=300
        async def save(data): raise OSError("injected write failure")
        r.save_hook=save
        with self.assertRaises(UserError): await r.c.configure(cfg,0)
        self.assertEqual(r.c.config.reserve_w,100); self.assertEqual(r.c.mode,"error")
        r.save_hook=None; await r.c.close()

    async def test_storage_errors_are_not_retried_on_every_source_tick(self):
        r=Rig(); await r.c.settle(); attempts=0
        async def save(data):
            nonlocal attempts
            attempts+=1
            if data["incomplete"]: raise OSError("injected disk failure")
        r.save_hook=save
        with self.assertLogs("rrh_tested.controller",level="ERROR"): await r.run()
        after_failure=attempts
        for _ in range(20): await r.grid(2500)
        self.assertEqual(attempts,after_failure)
        self.assertEqual(r.calls,[])
        r.save_hook=None
        await r.run(); self.assertEqual(r.calls,[("switch.a","on")])

    async def test_restart_preserves_cursor_owned_order_and_stays_paused(self):
        r=Rig(); await r.run(); saved=deepcopy(r.disk)
        r2=Rig(saved,states={"switch.a":"on"}); await r2.c.settle()
        self.assertEqual(r2.c.cursor,"a"); self.assertEqual(r2.c.owned,["a"]); self.assertEqual(r2.c.mode,"paused")
        self.assertEqual(r2.calls,[])
        await r2.grid(100); await r2.run(); self.assertEqual(r2.calls,[])

    async def test_interrupted_start_is_not_adopted_on_restart(self):
        saved=document(incomplete={"id":"a","target":"on"})
        r=Rig(saved,power=100,states={"switch.a":"on"}); await r.run()
        self.assertIsNone(r.c.cursor); self.assertEqual(r.c.owned,[]); self.assertEqual(r.calls,[])

    async def test_corrupt_storage_is_not_reset_silently(self):
        for key,value in [("schema",99),("owned",["missing"]),("cursor",{}),("revision",True),("incomplete",{"id":"x","target":"on"})]:
            saved=document(); saved[key]=value
            with self.subTest(key=key),self.assertRaises(UserError):
                Controller(saved,send=None,save=None)

    async def test_repeated_activate_does_not_reset_deficit_timer(self):
        r=Rig(document(cursor="a",owned=["a"]),power=0,states={"switch.a":"on"})
        await r.run(); await r.tick(29); await r.c.activate(); await r.tick(1)
        self.assertEqual(r.calls,[("switch.a","off")])

    async def test_close_while_pending_never_starts_followup(self):
        r=Rig(); gate=asyncio.Event(); reached=asyncio.Event()
        async def send(e,t,k): reached.set(); await gate.wait(); r.c.observe_switch(e,t,command_token=k)
        r.send_hook=send; await r.c.activate(); await reached.wait()
        closing=asyncio.create_task(r.c.close()); await asyncio.sleep(0); gate.set(); await closing
        self.assertTrue(r.c.closed); self.assertEqual(len(r.calls),1); self.assertEqual(r.disk["cursor"],"a")


if __name__ == "__main__":
    unittest.main()

class CommandDiagnosticTests(unittest.IsolatedAsyncioTestCase):
    async def test_service_finished_but_no_state_event_is_named_and_logged(self):
        r = Rig(timeout=0.01)
        async def no_event(entity_id, target, token):
            return None
        r.send_hook = no_event
        with self.assertLogs('rrh_tested.controller', level='INFO') as captured:
            await r.run()
        self.assertEqual(r.c.mode, 'error')
        self.assertIn('HA-Dienstaufruf abgeschlossen', r.c.reason)
        self.assertIn('RRH Schaltauftrag Timeout:', '\n'.join(captured.output))
        self.assertEqual(r.calls, [('switch.a', 'on')])
        self.assertIsNone(r.c.cursor)

    async def test_unfinished_service_is_distinguished_and_not_retried(self):
        r = Rig(timeout=0.01)
        async def blocked(entity_id, target, token):
            await asyncio.sleep(1)
        r.send_hook = blocked
        with self.assertLogs('rrh_tested.controller', level='INFO') as captured:
            await r.run()
        self.assertEqual(r.c.mode, 'error')
        self.assertIn('HA-Dienstaufruf nicht abgeschlossen', r.c.reason)
        self.assertIn('Dienst_fertig=False', '\n'.join(captured.output))
        self.assertEqual(r.calls, [('switch.a', 'on')])
        self.assertIsNone(r.c.cursor)
