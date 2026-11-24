"""Regression tests: timezone resolution must never block Home Assistant's event loop."""
import tempfile
import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import load_core
from ha_doubles import Hass, stubs
from rrh_tested.controller import Controller
from rrh_tested.demo import DemoSandbox
from rrh_tested.model import UserError
from rrh_tested.statistics import EnergyLedger


class EnergyLedgerTimeZoneTests(unittest.TestCase):
    def test_resolved_timezone_used_for_day_rollover_and_reused_after_reset(self):
        berlin = ZoneInfo("Europe/Berlin")  # Resolve outside the event loop.
        ledger = EnergyLedger(timezone=berlin)
        self.assertIs(ledger.timezone, berlin)
        summer = datetime(2026, 7, 1, 22, 30, tzinfo=UTC).timestamp()
        winter = datetime(2026, 1, 1, 23, 30, tzinfo=UTC).timestamp()
        with patch("zoneinfo.ZoneInfo", side_effect=AssertionError("No tzdata read on event loop")):
            self.assertEqual(ledger._day(summer), "2026-07-02")
            self.assertEqual(ledger._day(winter), "2026-01-02")
            ledger.sample(summer, mode="running", export_w=500, managed_w=500,
                          loads={"heater": 500}, buy_price=None, feed_price=None)
            ledger.sample(summer + 1, mode="running", export_w=500, managed_w=500,
                          loads={"heater": 500}, buy_price=None, feed_price=None)
            self.assertIn("2026-07-02", ledger.daily)
            ledger.reset(winter)
            self.assertIs(ledger.timezone, berlin)
            self.assertEqual(ledger._day(winter), "2026-01-02")

    def test_timezone_key_is_rejected_instead_of_looked_up_synchronously(self):
        with self.assertRaisesRegex(TypeError, "resolved tzinfo"):
            EnergyLedger(timezone="Europe/Berlin")


class ControllerTimeZoneTests(unittest.IsolatedAsyncioTestCase):
    async def test_factory_reset_reuses_resolved_zone(self):
        berlin = ZoneInfo("Europe/Berlin")

        async def noop(*args):
            pass

        controller = Controller(None, send=noop, save=noop, timezone=berlin)
        controller.mode = "stopped"
        controller._has_confirmed_all_off = True
        with patch("zoneinfo.ZoneInfo", side_effect=AssertionError("No tzdata read on event loop")):
            await controller.factory_reset(controller.revision, "RESET ROUND ROBIN HOOD")
        self.assertIs(controller.statistics.timezone, berlin)
        await controller.close()

    async def test_demo_uses_utc_without_timezone_lookup(self):
        with patch("zoneinfo.ZoneInfo", side_effect=AssertionError("No tzdata read on event loop")):
            demo = DemoSandbox()
            self.assertIs(demo.controller.statistics.timezone, UTC)
            await demo.start()
            await demo.close()


class RuntimeTimeZoneTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.stub_patch = stubs()
        self.stub_patch.start()
        self.temp = tempfile.TemporaryDirectory()
        self.hass = Hass(self.temp.name)
        from rrh_tested.runtime import Runtime
        self.runtime = Runtime(self.hass)
        self.started = False

    async def asyncTearDown(self):
        if self.started:
            await self.runtime.stop()
        self.stub_patch.stop()
        self.temp.cleanup()

    async def test_resolve_once_off_loop_and_reuse_across_stats_reset(self):
        berlin = ZoneInfo("Europe/Berlin")
        self.hass.config.time_zone = "Europe/Berlin"
        with patch("rrh_tested.runtime.dt_util.async_get_time_zone", new_callable=AsyncMock) as resolve:
            resolve.return_value = berlin
            await self.runtime.start()
            self.started = True
            resolve.assert_awaited_once_with("Europe/Berlin")
            self.assertIs(self.runtime.controller.statistics.timezone, berlin)
            await self.runtime.controller.reset_statistics(self.runtime.controller.revision)
            self.assertIs(self.runtime.controller.statistics.timezone, berlin)
            resolve.assert_awaited_once()

    async def test_unknown_timezone_fails_before_starting_timer(self):
        self.hass.config.time_zone = "Invalid/Zone"
        with patch("rrh_tested.runtime.dt_util.async_get_time_zone", new_callable=AsyncMock) as resolve:
            resolve.return_value = None
            with self.assertRaisesRegex(UserError, "Ungültige Home-Assistant-Zeitzone"):
                await self.runtime.start()
        self.assertIsNone(self.runtime._timer)
