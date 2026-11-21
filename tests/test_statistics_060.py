"""v0.6.0: conservative telemetry accounting, schema, money and restart tests."""
import json
import unittest
from copy import deepcopy

import load_core
from rrh_tested.statistics import EnergyLedger
from rrh_tested.model import Config, UserError


def tick(ledger, start, end, *, managed=500, export=700, buy=.30, feed=.08, **kwargs):
    for t in range(start, end+1):
        ledger.sample(float(t), mode="running", export_w=export, managed_w=managed,
                      loads={"heater":managed} if managed else {},
                      buy_price=buy, feed_price=feed, **kwargs)


class StatsSchemaTests(unittest.TestCase):
    def test_old_config_migrates_without_inventing_prices(self):
        base=Config().to_dict()
        base.pop("energy");base.pop("dashboard")
        cfg=Config.parse(base)
        self.assertIsNone(cfg.energy.import_price.value)
        self.assertEqual(cfg.dashboard.chart_type,"gauge")
        self.assertTrue(cfg.dashboard.visible["rate"])
        self.assertEqual(cfg,Config.parse(json.loads(json.dumps(cfg.to_dict()))))

    def test_numeric_source_rates_capacity_and_languages(self):
        cfg=Config().to_dict()
        cfg["energy"]["pv_size"]={"mode":"entity","entity_id":"sensor.pv_size","value":None}
        cfg["energy"]["import_price"]={"mode":"fixed","entity_id":"","value":.27}
        cfg["energy"]["feed_in_price"]={"mode":"entity","entity_id":"input_number.feed_tariff","value":None}
        for lang in ("auto","de","en","fr","es","pt","it"):
            cfg["dashboard"]["language"]=lang
            with self.subTest(lang=lang):
                self.assertEqual(Config.parse(cfg).dashboard.language,lang)

    def test_bad_source_rejected_before_storage(self):
        cfg=Config().to_dict()
        cases=[("mode","script"),("entity_id","script.run"),("value",-1), ("value",float("inf"))]
        for field,value in cases:
            d=deepcopy(cfg);d["energy"]["import_price"][field]=value
            with self.subTest(field=field),self.assertRaises(UserError):Config.parse(d)

    def test_bad_chart_card_flag_and_language_rejected(self):
        cfg=Config().to_dict()
        cases=[("chart_type","roulette"),("language","xx"),("visible",{"rate":True})]
        for field,value in cases:
            d=deepcopy(cfg);d["dashboard"][field]=value
            with self.subTest(field=field),self.assertRaises(UserError):Config.parse(d)

    def test_card_flags_independent(self):
        d=Config().to_dict();d["dashboard"]["visible"]["pipeline"]=False
        d["dashboard"]["visible"]["live_chart"]=True
        self.assertFalse(Config.parse(d).dashboard.visible["pipeline"])


class StatsLedgerTests(unittest.TestCase):
    def test_load_estimates_and_capture_ratio(self):
        l=EnergyLedger(timezone="Europe/Berlin")
        tick(l,100,160)
        result=l.status()
        self.assertAlmostEqual(result["total"]["rrh_kwh"],500/1000/60,places=5)
        self.assertAlmostEqual(result["total"]["potential_kwh"],1200/1000/60,places=5)
        self.assertAlmostEqual(result["total"]["export_kwh"],700/1000/60,places=5)
        self.assertEqual(result["live"]["capture_pct"],41.7)

    def test_net_money_deducts_lost_feed_in(self):
        l=EnergyLedger()
        tick(l,100,3700,managed=1000,export=200,buy=.32,feed=.08)
        self.assertAlmostEqual(l.totals["rrh_kwh"],1.0,places=4)
        self.assertAlmostEqual(l.totals["net_benefit_eur"],.24,places=4)
        self.assertAlmostEqual(l.totals["gross_value_eur"],.32,places=4)
        self.assertAlmostEqual(l.totals["export_value_eur"],.08,places=4)
        self.assertAlmostEqual(l.status()["live"]["net_eur_min"],.004,places=6)

    def test_negative_tariff_spread_is_not_silently_zeroed(self):
        l=EnergyLedger()
        tick(l,100,700,managed=1000,export=0,buy=.04,feed=.10)
        self.assertAlmostEqual(l.totals["net_benefit_eur"],-.01,places=5)
        restored=EnergyLedger(json.loads(json.dumps(l.document())))
        self.assertAlmostEqual(restored.totals["net_benefit_eur"],-.01,places=5)

    def test_unconfigured_tariffs_do_not_invent_money(self):
        l=EnergyLedger()
        tick(l,100,160,buy=None,feed=None)
        self.assertGreater(l.totals["rrh_kwh"],0)
        self.assertEqual(l.totals["valued_kwh"],0)
        self.assertIsNone(l.status()["live"]["net_eur_min"])

    def test_stale_meter_and_pause_stop_all_credit(self):
        l=EnergyLedger()
        tick(l,100,150)
        before=l.totals["rrh_kwh"]
        for now in range(151,250):
            l.sample(now,mode="paused",export_w=700,managed_w=500,loads={"heater":500},buy_price=.30,feed_price=.08)
        for now in range(250,350):
            l.sample(now,mode="running",export_w=None,managed_w=500,loads={"heater":500},buy_price=.30,feed_price=.08)
        self.assertEqual(before,l.totals["rrh_kwh"])
        self.assertIsNone(l.status()["live"]["capture_pct"])

    def test_no_backfill_after_restart_or_large_gap(self):
        l=EnergyLedger()
        tick(l,100,110)
        before=l.totals["rrh_kwh"]
        l.sample(100000,mode="running",export_w=700,managed_w=500,loads={"heater":500},buy_price=.30,feed_price=.08)
        self.assertEqual(l.totals["rrh_kwh"],before)
        restored=EnergyLedger(json.loads(json.dumps(l.document())))
        self.assertEqual(restored.last_snapshot,None)
        restored.sample(100001,mode="running",export_w=700,managed_w=500,loads={"heater":500},buy_price=.30,feed_price=.08)
        self.assertAlmostEqual(restored.totals["rrh_kwh"],before,places=6)

    def test_meter_import_draw_not_counted_as_pv(self):
        l=EnergyLedger()
        tick(l,100,160,managed=500,export=-700)
        self.assertEqual(l.totals["rrh_kwh"],0)
        self.assertEqual(l.totals["potential_kwh"],0)

    def test_energy_meter_reset_does_not_create_energy(self):
        l=EnergyLedger()
        tick(l,100,110,pv_meter_kwh=500.0,export_meter_kwh=250.0)
        tick(l,111,112,pv_meter_kwh=1.0,export_meter_kwh=0.0)
        self.assertEqual(l.totals["pv_generation_kwh"],0)
        self.assertEqual(l.totals["meter_export_kwh"],0)

    def test_consumer_energy_and_starts(self):
        l=EnergyLedger()
        tick(l,100,160)
        self.assertEqual(l.consumer["heater"]["starts"],1)
        self.assertAlmostEqual(l.consumer["heater"]["runtime_h"],1/60,places=5)
        self.assertAlmostEqual(l.consumer["heater"]["kwh"],.5/60,places=5)
        self.assertAlmostEqual(l.consumer["heater"]["load_kwh"],.5/60,places=5)

    def test_histogram_is_bounded(self):
        l=EnergyLedger()
        tick(l,100,10000)
        self.assertLessEqual(len(l.history),2890)
        self.assertLessEqual(len(l.daily),45)

    def test_reset_preserves_no_previous_usage(self):
        l=EnergyLedger()
        tick(l,100,160)
        l.reset(200)
        self.assertEqual(l.totals["rrh_kwh"],0)
        self.assertEqual(l.started,200)
        self.assertFalse(l.history)

    def test_corrupt_saved_statistics_rejected(self):
        l=EnergyLedger()
        data=l.document();data["totals"]["rrh_kwh"]=-1
        with self.assertRaises(ValueError):EnergyLedger(data)
        data=l.document();data["consumer"]["x"]={"kwh":float("nan"),"runtime_h":0,"starts":0}
        with self.assertRaises(ValueError):EnergyLedger(data)


if __name__=="__main__":unittest.main()
