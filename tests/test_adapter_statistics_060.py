"""v0.6.0 HA adapter unit handling for optional statistics sources."""
import json
import tempfile
import unittest
from types import SimpleNamespace

import load_core
from ha_doubles import stubs, Hass
from rrh_tested.model import Config


class EnergyAdapterTests(unittest.TestCase):
    def setUp(self):
        self.patch=stubs();self.patch.start()
        from rrh_tested.runtime import Runtime
        self.temp=tempfile.TemporaryDirectory()
        self.hass=Hass(self.temp.name)
        self.rt=Runtime(self.hass)
        self.rt.controller=SimpleNamespace(config=Config())

    def tearDown(self):
        self.patch.stop();self.temp.cleanup()

    def conf(self):
        cfg=Config().to_dict()
        cfg["energy"].update({
            "pv_size":{"mode":"entity","value":None,"entity_id":"input_number.pv_kwp"},
            "import_price":{"mode":"entity","value":None,"entity_id":"sensor.buy"},
            "feed_in_price":{"mode":"entity","value":None,"entity_id":"sensor.feed"},
            "pv_power_entity":"sensor.solar_power", "pv_energy_entity":"sensor.solar_total",
            "grid_export_energy_entity":"sensor.export_total"})
        self.rt.controller.config=Config.parse(cfg)

    def test_ha_units_watt_kilowatt_and_cents(self):
        self.conf()
        self.hass.states.set("input_number.pv_kwp","4500",{"unit_of_measurement":"Wp"})
        self.hass.states.set("sensor.buy","29.5",{"unit_of_measurement":"ct/kWh"})
        self.hass.states.set("sensor.feed","0.082",{"unit_of_measurement":"EUR/kWh"})
        self.hass.states.set("sensor.solar_power","3.2",{"unit_of_measurement":"kW"})
        self.hass.states.set("sensor.solar_total","14000",{"unit_of_measurement":"Wh"})
        self.hass.states.set("sensor.export_total","1.2",{"unit_of_measurement":"MWh"})
        result=self.rt._stat_sources()
        self.assertEqual(result["pv_size_kwp"],4.5)
        self.assertAlmostEqual(result["import_price"],.295)
        self.assertAlmostEqual(result["feed_in_price"],.082)
        self.assertEqual(result["pv_power_w"],3200)
        self.assertEqual(result["pv_meter_kwh"],14)
        self.assertEqual(result["export_meter_kwh"],1200)
        self.assertFalse(result["warnings"])

    def test_invalid_price_unit_and_missing_states_are_not_zero(self):
        self.conf()
        self.hass.states.set("sensor.buy","2.1",{"unit_of_measurement":"EUR"})  # total currency, not price/kWh
        self.hass.states.set("sensor.feed","unavailable",{"unit_of_measurement":"EUR/kWh"})
        result=self.rt._stat_sources()
        self.assertIsNone(result["import_price"])
        self.assertIsNone(result["feed_in_price"])
        self.assertGreaterEqual(len(result["warnings"]),2)

    def test_fixed_values_and_missing_optional_inputs(self):
        d=Config().to_dict()
        d["energy"]["import_price"]["value"]=.35
        d["energy"]["feed_in_price"]["value"]=0
        self.rt.controller.config=Config.parse(d)
        result=self.rt._stat_sources()
        self.assertEqual(result["import_price"],.35)
        self.assertEqual(result["feed_in_price"],0)
        self.assertIsNone(result["pv_power_w"])


if __name__=="__main__":unittest.main()
