"""v0.9.5 weekly schedules: migration, local-time/DST, safety, and gating."""
import asyncio
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo

from test_core import Rig, config, document
from rrh_tested.model import Config, UserError, WeeklySchedule


def schedule(days=(3,), start="00:00", end="00:10", enabled=True):
    return {"enabled": enabled, "windows": [
        {"weekdays": list(days), "start": start, "end": end}
    ]}


def at(zone, year, month, day, hour, minute=0, fold=0):
    return datetime(year, month, day, hour, minute, tzinfo=zone, fold=fold)


class ScheduleModelTests(unittest.TestCase):
    def test_legacy_configuration_has_no_time_restriction(self):
        old = config()
        parsed = Config.parse(old)
        self.assertFalse(parsed.consumers[0].schedule.enabled)
        self.assertFalse(parsed.profiles[0].schedule.enabled)
        self.assertEqual(Config.parse(parsed.to_dict()), parsed)
        self.assertTrue(parsed.consumers[0].schedule.allows(datetime.now(UTC)))

    def test_profile_consumer_roundtrip_and_disabled_draft(self):
        data = config()
        data["consumers"][0]["schedule"] = schedule((0, 2, 4), "08:00", "17:00")
        data["profiles"] = [{"id":"working", "name":"Working", "enabled":True,
             "strategy":"classic", "dashboard_order":"fixed", "consumer_ids":["a"],
             "schedule":schedule((1,), "22:00", "02:00", enabled=False)}]
        parsed = Config.parse(data)
        self.assertTrue(parsed.consumers[0].schedule.enabled)
        self.assertFalse(parsed.profiles[0].schedule.enabled)
        self.assertEqual(Config.parse(parsed.to_dict()), parsed)
        self.assertEqual(parsed.consumers[0].schedule.to_dict()["windows"][0]["weekdays"], [0,2,4])

    def test_invalid_windows_rejected(self):
        invalid = [
            {"enabled":True,"windows":[]},
            {"enabled":"true","windows":[]},
            {"enabled":True,"windows":{}},
            {"enabled":True,"windows":[{"weekdays":[],"start":"08:00","end":"18:00"}]},
            {"enabled":True,"windows":[{"weekdays":[7],"start":"08:00","end":"18:00"}]},
            {"enabled":True,"windows":[{"weekdays":[True],"start":"08:00","end":"18:00"}]},
            {"enabled":True,"windows":[{"weekdays":[0,0],"start":"08:00","end":"18:00"}]},
            {"enabled":True,"windows":[{"weekdays":[0],"start":"24:00","end":"18:00"}]},
            {"enabled":True,"windows":[{"weekdays":[0],"start":"8:00","end":"18:00"}]},
            {"enabled":True,"windows":[{"weekdays":[0],"start":"08:00","end":"08:00"}]},
            {"enabled":True,"windows":[{"weekdays":[0],"start":"08:00","end":"18:00","unknown":"x"}]},
            {"enabled":True,"windows":[{"weekdays":[0],"start":"08:00","end":"18:00"}]*2},
        ]
        for raw in invalid:
            for kind in ("consumer", "profile"):
                d = config()
                if kind == "consumer":
                    d["consumers"][0]["schedule"] = deepcopy(raw)
                else:
                    d["profiles"] = [{"id":"x","name":"X","enabled":True,"strategy":"classic",
                       "dashboard_order":"fixed","consumer_ids":["a"],"schedule":deepcopy(raw)}]
                with self.subTest(raw=raw,kind=kind), self.assertRaises(UserError):
                    Config.parse(d)

    def test_multiple_daily_windows_with_exclusive_end(self):
        raw = schedule((0,), "08:00", "10:00")
        raw["windows"].append({"weekdays":[0],"start":"12:00","end":"14:00"})
        gate = WeeklySchedule.parse(raw)
        utc = UTC
        self.assertFalse(gate.allows(at(utc,2026,11,30,7,59)))
        self.assertTrue(gate.allows(at(utc,2026,11,30,8,0)))
        self.assertFalse(gate.allows(at(utc,2026,11,30,10,0)))
        self.assertTrue(gate.allows(at(utc,2026,11,30,12,30)))
        self.assertFalse(gate.allows(at(utc,2026,12,1,12,30)))

    def test_overnight_belongs_to_start_weekday(self):
        gate = WeeklySchedule.parse(schedule((0,), "22:00", "02:00"))
        self.assertFalse(gate.allows(at(UTC,2026,11,30,1)))
        self.assertTrue(gate.allows(at(UTC,2026,11,30,22)))
        self.assertTrue(gate.allows(at(UTC,2026,12,1,1,59)))
        self.assertFalse(gate.allows(at(UTC,2026,12,1,2)))
        self.assertFalse(gate.allows(at(UTC,2026,12,2,1)))

    def test_dst_spring_skipped_local_start_uses_first_valid_minute(self):
        zone = ZoneInfo("Europe/Berlin")
        gate = WeeklySchedule.parse(schedule((6,), "02:30", "04:00"))
        self.assertFalse(gate.allows(at(zone,2027,3,28,1)))
        self.assertTrue(gate.allows(at(zone,2027,3,28,3)))
        self.assertEqual(gate.next_start(at(zone,2027,3,28,1).timestamp(),zone),
                         at(zone,2027,3,28,3).timestamp())

    def test_dst_autumn_repeated_hour_is_evaluated_twice(self):
        zone = ZoneInfo("Europe/Berlin")
        gate = WeeklySchedule.parse(schedule((6,), "02:15", "02:45"))
        first = at(zone,2027,10,31,2,20,fold=0)
        second = at(zone,2027,10,31,2,20,fold=1)
        self.assertNotEqual(first.timestamp(),second.timestamp())
        self.assertTrue(gate.allows(first))
        self.assertTrue(gate.allows(second))
        after_first = at(zone,2027,10,31,2,5,fold=1)
        self.assertFalse(gate.allows(after_first))
        self.assertEqual(gate.next_start(after_first.timestamp(),zone),
                         at(zone,2027,10,31,2,15,fold=1).timestamp())

    def test_next_start_weekday_and_disabled(self):
        zone = UTC
        gate = WeeklySchedule.parse(schedule((0,), "07:30", "08:30"))
        self.assertEqual(gate.next_start(at(zone,2026,12,1,9).timestamp(),zone),
                         at(zone,2026,12,7,7,30).timestamp())
        self.assertIsNone(WeeklySchedule().next_start(at(zone,2026,12,1,9).timestamp(),zone))


class ScheduleControllerTests(unittest.IsolatedAsyncioTestCase):
    async def test_consumer_window_closure_forces_off_before_strict_min_and_grid_barrier(self):
        cfg = config()
        cfg["consumers"][0]["schedule"] = schedule()
        cfg["consumers"][0].update(min_on_s=3600,min_on_strict=True)
        r = Rig(document(cfg),power=2500)
        await r.run()
        self.assertIn(("switch.a","on"),r.calls)
        self.assertEqual(r.c.status()["consumers"][0]["schedule_allowed"],True)
        # 1970-01-01 (Thursday), 00:01:40 UTC -> 00:11:40 outside.
        r.now += 600
        await r.grid(2500)
        self.assertIn(("switch.a","off"),r.calls)
        self.assertFalse(r.c.status()["consumers"][0]["schedule_allowed"])
        self.assertEqual(r.c.mode,"running")

    async def test_blocked_schedule_skips_consumer_but_not_sensor_or_profile(self):
        cfg = config()
        cfg["consumers"][0]["schedule"] = schedule((3,),"06:00","07:00")
        cfg["consumers"][1]["schedule"] = schedule((3,),"00:00","01:00")
        r = Rig(document(cfg),power=2500)
        await r.run()
        self.assertEqual(r.calls,[("switch.b","on")])
        card = r.c.status()["consumers"][0]
        self.assertFalse(card["schedule_allowed"])
        self.assertIn("Verbraucherzeitplan",card["wait_reason"])
        self.assertIsNotNone(card["schedule_next_start"])

    async def test_profile_schedule_blocks_all_members_and_reopens(self):
        cfg = config()
        cfg["profiles"] = [{"id":"p","name":"P","enabled":True,
           "strategy":"classic","dashboard_order":"fixed","consumer_ids":["a"],
           "schedule":schedule((3,),"01:00","02:00")}]
        r = Rig(document(cfg),power=2500)
        await r.run()
        self.assertEqual(r.calls,[])
        self.assertFalse(r.c.status()["profiles"][0]["schedule_allowed"])
        self.assertIn("Profilzeitplan",r.c.status()["consumers"][0]["wait_reason"])
        r.now += 3600
        await r.grid(2500)
        self.assertEqual(r.calls,[("switch.a","on")])

    async def test_profile_expiry_bulk_off_even_when_strict_min_is_active(self):
        cfg = config()
        cfg["consumers"][0].update(min_on_s=3600,min_on_strict=True)
        cfg["consumers"][1].update(min_on_s=3600,min_on_strict=True)
        cfg["profiles"] = [{"id":"p","name":"P","enabled":True,
           "strategy":"classic","dashboard_order":"fixed","consumer_ids":["a","b"],
           "schedule":schedule()}]
        r = Rig(document(cfg,owned=["a","b"]),power=100,
                states={"switch.a":"on","switch.b":"on"})
        sent = []
        async def bulk(entities):
            sent.append(list(entities))
            for eid in entities:
                r.c.observe_switch(eid,"off",command_token="bulk")
        r.c.send_all_off = bulk
        await r.run()
        r.now += 600
        await r.grid(100)
        self.assertEqual(sent,[["switch.a","switch.b"]])
        self.assertEqual(r.c.owned,[])
        self.assertEqual(r.c.mode,"running")

    async def test_schedule_expiry_during_preflight_persist_cancels_on(self):
        cfg = config()
        cfg["consumers"][0]["schedule"] = schedule()
        r = Rig(document(cfg),power=2500)
        reached,gated = asyncio.Event(),asyncio.Event()
        async def hold(data):
            if data.get("incomplete"):
                reached.set()
                await gated.wait()
        r.save_hook = hold
        task = asyncio.create_task(r.c.activate())
        await reached.wait()
        r.now += 600
        gated.set()
        await task
        await r.c.settle()
        self.assertNotIn(("switch.a","on"),r.calls)
        self.assertNotIn("a",r.c.owned)
        self.assertIsNone(r.c.incomplete)

    def test_frontend_has_both_weekly_editors_and_mobile_rules(self):
        panel = (Path(__file__).resolve().parents[1] /
                 "custom_components/round_robin_hood/frontend/panel.js").read_text(encoding="utf-8")
        for fragment in ("consumer-schedule-enable", "profile-schedule-enable",
                         "_fillScheduleEditor(", "_readSchedule(", "schedule-days",
                         "schedule_next_start", "schedule-fields[hidden]"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment,panel)


if __name__ == "__main__":
    unittest.main()
