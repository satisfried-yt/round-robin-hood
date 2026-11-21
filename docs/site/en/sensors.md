# Choosing valid Home Assistant sensors

RRH uses **control inputs** and **statistics inputs** for different purposes. The grid-power sensor provides the switching budget; prices and PV meters affect statistics only.

## What belongs where?

| Field | Supported unit | Use |
|---|---|---|
| Grid power | W or kW | Actual export/import and dispatch decisions |
| Nominal PV capacity | W, Wp, kW or kWp | Installed capacity; not current generation |
| Actual PV power | W or kW | Current PV generation display |
| PV energy counter | Wh, kWh or MWh | Extra cumulative statistics |
| Import tariff | Currency/kWh, EUR cents/kWh or currency/MWh | Valuation of self-consumed energy |
| Feed-in tariff | Same as import tariff | Opportunity cost of not exporting energy |

The source picker offers only compatible numeric `sensor.*` entities. **An unlabelled `0.32` is ambiguous**: for a new price source, use a Home Assistant template sensor with an explicit `unit_of_measurement`. Currency must match the selected RRH currency.

## Unavailable or invalid measurements

**Grid power**: no new control action may be based on invalid or stale readings. Existing running loads are not physically disconnected merely because a reading failed.

**Prices/PV sources**: invalid, unavailable or restored readings are omitted from financial calculations and surfaced as source warnings; RRH does not invent a fallback tariff. Price-sensor loss does not stop the PV surplus controller.

## Conversions

`ct/kWh` ÷ 100 = EUR/kWh, `EUR/MWh` ÷ 1,000 = EUR/kWh, `kW` × 1,000 = W, `Wh` ÷ 1,000 = kWh.

RRH measures the remaining export **after** its controlled consumers have drawn power. Do not subtract running loads a second time. See [Dashboard](dashboard.md).

If a source is absent from the picker, check its unit, value, state and configured currency in Home Assistant Developer Tools. Incompatible previously saved sources stay visible with a warning; they are not silently replaced.
