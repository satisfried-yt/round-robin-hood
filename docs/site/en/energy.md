# Energy & costs – fields and calculations

The page combines reporting with the **single source** for nominal PV size and tariffs. Save changes while RRH is **paused**. These entries influence estimates, not the physical reserve or Home Assistant's own Energy Dashboard.

## Configuration fields

| Field | Meaning and unit |
|---|---|
| **Currency** | `EUR`, `CHF`, `USD`, `GBP`. Existing values are **not exchange-rate converted**. Check new local tariffs; existing valued history prevents currency changes until the ledger is explicitly reset. |
| **Nominal PV size (W)** | Fixed nameplate watts (e.g. `4000`) or HA numeric entity; stored legacy `kWp` is displayed as watts ×1000. Informational, not a live power meter. |
| **Electricity purchase tariff (per kWh)** | Fixed or numeric HA entity, e.g. `0.30` EUR/kWh. Unitless helpers are not accepted as tariff sources. |
| **Feed-in remuneration (per kWh)** | What exported electricity would earn, e.g. `0.08` EUR/kWh. Higher export tariff than import price can make the net advantage negative. |
| **PV live power sensor** | Optional existing HA `sensor.*` with W/kW for displaying instantaneous production. |
| **PV cumulative energy meter** | Optional existing `sensor.*` with Wh/kWh/MWh for supplemental information. |
| **Grid export cumulative meter** | Optional energy meter; do not confuse it with the required **instantaneous grid-power** control source. |

## Statistics cards

- **RRH-captured energy (kWh):** integrated, solar-attributed managed load; split between devices in proportion to confirmed nominal W.
- **Potential surplus** and **remaining export (kWh):** reconstructed only during valid live operation, never whole-system generation history.
- **Gross value:** credited kWh × purchase tariff.
- **Foregone feed-in revenue:** credited kWh × feed-in tariff.
- **Net advantage:** gross value less foregone feed-in income.
- **Priced kWh:** credited energy with valid tariff data; missing rates do not fabricate monetary values.
- **Runtime, starts, per-consumer and daily totals:** based on confirmed RRH states, separate from strategy fairness credits. Daily detail is bounded to 45 days, lifetime totals persist until manual reset.

## Real 24-hour history

The chart depicts **export utilization percentage for the last 24 hours** on a real time axis. Formula: `100 × RRH-managed W / (RRH-managed W + positive measured export W)` with valid fresh input. Y axis 0/50/100%; X axis hours before now. Typical interval 30 seconds, with at most 2890 stored history rows. Pauses, stale/missing data and outages create **gaps**, not interpolated usage. History is saved across HA restarts but no values are backfilled for the time before installation or while HA was stopped. It is **not a utility-grade energy/money meter**.

## Changing currency

Priced EUR history cannot silently become CHF/USD/GBP. Export and explicitly reset the **overall energy/statistics ledger** first, then select a new currency and enter or explicitly reconfirm correct local purchase/feed-in tariffs. Check the unit of dynamic tariff sensors including cents/kWh and currency/MWh. Fairness credits are not reset alongside the energy ledger.

[Dashboard](dashboard.md) · [Settings](settings.md)

## Features and usage

Nominal PV capacity, import/feed-in tariffs, currency and optional HA sensors now appear **above** the statistics in a compact responsive three-column layout (two or one column on smaller screens). The section starts expanded. Existing values and sensor sources survive the update.

## Features and usage

Sources are filtered by compatible units and currency; invalid live values are never priced. See [Choosing sensors](sensors.md).
