"""Conservative, persisted RRH surplus statistics (estimated from grid + confirmed loads).

The ledger is deliberately separate from scheduling and fair-energy bookkeeping.
Grid export is already affected by controlled devices. Reconstructed potential is
export + RRH load; never add the load to *measured* export a second time.
A paused controller receives no new RRH energy credit. A stale meter receives no
sample credit. At startup the clock is rebased, not backfilled across HA downtime.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, tzinfo
import math

MAX_GAP_S = 8.0
MAX_HISTORY = 2890  # 24 h at 30-second sampling, including a restart boundary
HISTORY_SECONDS = 24 * 3600
MAX_DAYS = 45


def finite_positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _safe_number(value):
    return round(value, 8) if finite_positive(value) else None


@dataclass
class EnergyLedger:
    totals: dict = field(default_factory=dict)
    consumer: dict = field(default_factory=dict)
    daily: dict = field(default_factory=dict)
    history: list = field(default_factory=list)
    started: float | None = None
    last_at: float | None = None
    last_snapshot: dict | None = None
    last_history_at: float = 0
    last_checkpoint_at: float = 0
    last_source_values: dict = field(default_factory=dict)
    timezone: tzinfo = UTC

    def __init__(self, raw=None, *, timezone: tzinfo = UTC):
        # The caller must provide an already-resolved timezone. Loading tzdata
        # (ZoneInfo(key)) on Home Assistant's event loop is a blocking call.
        if not isinstance(timezone, tzinfo):
            raise TypeError("EnergyLedger requires a resolved tzinfo object")
        self.timezone = timezone
        self.started = None
        self.last_at = None
        self.last_snapshot = None
        self.last_history_at = 0.0
        self.last_checkpoint_at = 0.0
        self.last_source_values = {}
        self.totals = {k:0.0 for k in ("rrh_kwh", "potential_kwh", "export_kwh", "export_value_eur", "gross_value_eur", "net_benefit_eur", "valued_kwh", "runtime_h", "pv_generation_kwh", "meter_export_kwh")}
        self.consumer = {}
        self.daily = {}
        self.history = []
        self.money_currency = "EUR"  # Historical v0.6.0 totals are always EUR
        if raw is not None:
            self._load(raw)

    def _load(self, raw):
        if not isinstance(raw, dict) or not {"totals", "consumer", "daily", "history", "started", "meter_last"} <= set(raw) or not set(raw) <= {"totals", "consumer", "daily", "history", "started", "meter_last", "money_currency"}:
            raise ValueError("RRH-Statistik: unbekanntes gespeichertes Format")
        currency = raw.get("money_currency", "EUR")
        if currency not in ("EUR", "CHF", "USD", "GBP"):
            raise ValueError("RRH-Statistik: unbekannte Währung")
        self.money_currency = currency
        for key, v in raw["totals"].items():
            if key not in self.totals or not isinstance(v,(float,int)) or isinstance(v,bool) or not math.isfinite(v) or abs(v) > 1e12 or (v<0 and key!="net_benefit_eur"):
                raise ValueError("RRH-Statistik: ungültiger Gesamtwert")
            self.totals[key] = float(v)
        if not isinstance(raw["consumer"], dict) or len(raw["consumer"]) > 100:
            raise ValueError("RRH-Statistik: ungültige Verbraucherwerte")
        for cid, item in raw["consumer"].items():
            if not isinstance(cid, str) or not isinstance(item, dict) or set(item) != {"kwh", "load_kwh", "runtime_h", "starts"}:
                raise ValueError("RRH-Statistik: ungültige Verbraucherzeile")
            if any(not finite_positive(v) or v > 1e12 for v in item.values()):
                raise ValueError("RRH-Statistik: ungültiger Verbraucherwert")
            self.consumer[cid] = {k:float(v) for k,v in item.items()}
        if not isinstance(raw["daily"], dict) or len(raw["daily"]) > MAX_DAYS:
            raise ValueError("RRH-Statistik: ungültige Tageswerte")
        for date, row in raw["daily"].items():
            if not isinstance(date, str) or len(date) != 10 or not isinstance(row, dict) or any(k not in self.totals or not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or abs(v)>1e12 or (v<0 and k!="net_benefit_eur") for k,v in row.items()):
                raise ValueError("RRH-Statistik: ungültige Tageswerte")
            self.daily[date] = {k:float(v) for k,v in row.items()}
        if not isinstance(raw["history"], list) or len(raw["history"]) > MAX_HISTORY:
            raise ValueError("RRH-Statistik: ungültiger Live-Verlauf")
        for row in raw["history"]:
            if not isinstance(row, list) or len(row) not in (5, 6) or any(not finite_positive(v) for v in row[:5]) or (len(row) == 6 and type(row[5]) is not bool):
                raise ValueError("RRH-Statistik: ungültige Verlaufspunkte")
            self.history.append(row)
        self.started = raw["started"]
        if self.started is not None and (not finite_positive(self.started) or self.started > 1e12):
            raise ValueError("RRH-Statistik: ungültiger Startzeitpunkt")
        ml = raw["meter_last"]
        if not isinstance(ml, dict) or any(k not in ("pv", "export") or not finite_positive(v) for k,v in ml.items()):
            raise ValueError("RRH-Statistik: ungültiger Zählerstand")
        # On restart, don't bridge a missing period, even if the meter increased.
        self.last_source_values = {}
        # These history points are display-only; do not replay stale values.

    def document(self):
        return {"totals": {k:round(v,8) for k,v in self.totals.items()},
                "consumer": {k:{n:round(v,8) for n,v in row.items()} for k,row in self.consumer.items()},
                "daily": {d:{k:round(v,8) for k,v in row.items()} for d,row in self.daily.items()},
                "history": self.history[-MAX_HISTORY:], "started": self.started,
                "money_currency": self.money_currency,
                "meter_last": {k:round(v,8) for k,v in self.last_source_values.items()}}

    def reset(self, at):
        currency = self.money_currency
        self.__init__(timezone=self.timezone)
        self.money_currency = currency
        self.started = float(at)

    def _day(self, at):
        return datetime.fromtimestamp(at, tz=self.timezone).strftime("%Y-%m-%d")

    def _add(self, key, amount, at):
        if not isinstance(amount,(float,int)) or isinstance(amount,bool) or not math.isfinite(amount) or amount == 0 or (amount < 0 and key != "net_benefit_eur"):
            return
        self.totals[key] += amount
        date = self._day(at)
        row = self.daily.setdefault(date, {})
        row[key] = row.get(key,0.0) + amount
        if len(self.daily) > MAX_DAYS:
            for d in sorted(self.daily)[:-MAX_DAYS]: del self.daily[d]

    def sample(self, now:float, *, mode:str, export_w:float|None, managed_w:float,
               loads:dict, buy_price:float|None, feed_price:float|None,
               pv_meter_kwh:float|None=None, export_meter_kwh:float|None=None):
        """Return True when a storage checkpoint is due. The caller persists at stop/close too."""
        if not finite_positive(now): return False
        valid = mode == "running" and export_w is not None and isinstance(export_w, (float,int)) and math.isfinite(export_w) and finite_positive(managed_w)
        reconstructed_w = max(0.0, float(export_w)+float(managed_w)) if valid else 0.0
        usable_managed_w = min(max(0.0, float(managed_w)), reconstructed_w) if valid else 0.0
        visible_export_w = max(0.0, float(export_w)) if valid else 0.0
        current = {"valid": valid, "rrh_w":usable_managed_w, "potential_w":reconstructed_w,
                   "export_w":visible_export_w,
                   "buy":buy_price if finite_positive(buy_price) else None,
                   "feed":feed_price if finite_positive(feed_price) else None,
                   "loads":{k:float(v) for k,v in loads.items() if finite_positive(v) and v>0}}
        if self.started is None and valid: self.started = now
        if self.last_at is not None and self.last_snapshot is not None:
            dt = now - self.last_at
            previous = self.last_snapshot
            # A good sample is never extrapolated across HA downtime, clock jumps,
            # paused periods or stale/missing net readings.
            if 0 < dt <= MAX_GAP_S and previous["valid"] and valid:
                hours = dt / 3600
                rrh_kwh = previous["rrh_w"]*hours/1000
                self._add("rrh_kwh", rrh_kwh, now)
                self._add("potential_kwh", previous["potential_w"]*hours/1000, now)
                self._add("export_kwh", previous["export_w"]*hours/1000, now)
                self._add("runtime_h", len(previous["loads"])*hours, now)
                for cid, load in previous["loads"].items():
                    item = self.consumer.setdefault(cid,{"kwh":0.0,"load_kwh":0.0,"runtime_h":0.0,"starts":0.0})
                    item["load_kwh"] += load*hours/1000
                    item["kwh"] += load*hours/1000 * (previous["rrh_w"]/max(1,sum(previous["loads"].values())))
                    item["runtime_h"] += hours
                buy, feed = previous["buy"], previous["feed"]
                if buy is not None and feed is not None:
                    self._add("gross_value_eur", rrh_kwh*buy, now)
                    self._add("export_value_eur", rrh_kwh*feed, now)
                    self._add("net_benefit_eur", rrh_kwh*(buy-feed), now)
                    self._add("valued_kwh", rrh_kwh, now)
                # Cumulative meters are ancillary independent sources; never add
                # them to reconstructed grid/RRH integration or backdate resets.
                for key, measurement, metric in (("pv",pv_meter_kwh,"pv_generation_kwh"),("export",export_meter_kwh,"meter_export_kwh")):
                    if finite_positive(measurement):
                        before=self.last_source_values.get(key)
                        if before is not None and measurement>=before:
                            increment=measurement-before
                            if increment <= 100*hours: self._add(metric,increment,now)
        for key, measurement in (("pv",pv_meter_kwh),("export",export_meter_kwh)):
            if finite_positive(measurement): self.last_source_values[key]=float(measurement)
            else: self.last_source_values.pop(key,None)
        prev_loads=(self.last_snapshot or {}).get("loads",{})
        if valid:
            for cid in current["loads"]:
                if cid not in prev_loads:
                    item=self.consumer.setdefault(cid,{"kwh":0.0,"load_kwh":0.0,"runtime_h":0.0,"starts":0.0})
                    item["starts"] += 1
        self.last_at = now
        self.last_snapshot = current
        if now - self.last_history_at >= 30:
            eff=100*usable_managed_w/reconstructed_w if reconstructed_w>0 else 0
            self.history.append([round(now,1),round(usable_managed_w,1),round(visible_export_w,1),round(eff,2),round(reconstructed_w,1), bool(valid)])
            self.history = [row for row in self.history if row[0] >= now - HISTORY_SECONDS][-MAX_HISTORY:]
            self.last_history_at=now
        if now - self.last_checkpoint_at >= 30:
            self.last_checkpoint_at=now
            return True
        return False

    def status(self):
        s=self.last_snapshot or {}
        valid=bool(s.get("valid"))
        cap=s.get("potential_w",0)
        rrh=s.get("rrh_w",0)
        buy=s.get("buy")
        feed=s.get("feed")
        live_rate = rrh/1000*(buy-feed)/60 if valid and buy is not None and feed is not None else None
        totals={k:round(v,5) for k,v in self.totals.items()}
        result={"since":self.started,"total":totals,"consumer":{cid:{k:round(v,4) for k,v in row.items()} for cid,row in self.consumer.items()},
                "daily":[{"date":date,**{k:round(v,5) for k,v in row.items()}} for date,row in sorted(self.daily.items(),reverse=True)],
                "history":self.history[-MAX_HISTORY:],"money_currency":self.money_currency,"live":{
                    "valid":valid,"rrh_w":round(rrh,1) if valid else None,
                    "surplus_w":round(cap,1) if valid else None,
                    "grid_export_w":round(s.get("export_w",0),1) if valid else None,
                    "capture_pct":round(100*rrh/cap,1) if valid and cap>0 else None,
                    "gross_eur_min":round(rrh/1000*buy/60,6) if valid and buy is not None else None,
                    "lost_export_eur_min":round(rrh/1000*feed/60,6) if valid and feed is not None else None,
                    "net_eur_min":round(live_rate,6) if live_rate is not None else None,
                    "buy_eur_kwh":buy,"feed_eur_kwh":feed},
                "capture_total_pct":round(100*totals["rrh_kwh"]/totals["potential_kwh"],2) if totals["potential_kwh"]>0 else None,
                "sensors":{}}
        return result
