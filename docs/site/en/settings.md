# Settings – every field and action

**Note:** Editing affects the real controller; pause or turn all devices off and wait for in-flight commands. Pause does not necessarily turn devices off.

## Grid source

| Field | Meaning / default |
|---|---|
| **Grid power source** | Existing `sensor.*` with instantaneous net W/kW, required for allocation. |
| **Sign** | `Positive = export` (default) or `Negative = export`; choosing the wrong sign invalidates all available-watts decisions. |
| **Show data quality** | Visibility of the source freshness/diagnostics section, on by default. |

## Power and switching

| Field | Meaning / default |
|---|---|
| **Reserve** | W, default **100**, range 0–100,000; subtracts from positive export to reduce oscillation/grid import. |
| **Global deficit delay enabled** | On by default, delays normal shortfall OFF; **All OFF** remains immediate. |
| **Global deficit delay** | Seconds, default **30**, range 0–600; may temporarily draw from grid. |
| **Confirm skipping timers** | Request confirmation before manual override of minimum runtime/cooldown, on by default. |
| **Confirm disabling a profile** | Request confirmation for profile participation change, on by default. |
| **Residual-surplus consumer** | Optional one staged/variable load used *last*, never ahead of normal profiles. |

## Data quality

| Field | Meaning / default |
|---|---|
| **Maximum age of grid reading** | Seconds, default **60**, range 5–3600. Stale/unknown timestamps do **not** authorize new starts; a genuine new HA update can carry the same numeric value. |

## Dashboard appearance and language

| Field | Meaning |
|---|---|
| **Live chart type** | Gauge, line, bar, area, donut, stacked, sparkline; presentation only. |
| **Language** | `auto` follows HA locale; otherwise DE, EN, FR, ES, PT or IT. Some specialized feedback may fall back to English; all six UI languages are supported. |
| **Show/hide cards** | Grid, budget, managed power, live chart, live money, total money, used surplus, ratio, profile order and optional PV power. Full-width chart adapts if others are hidden. |

## Tools

| Action | Meaning |
|---|---|
| **Demo mode** | Completely separate in-memory scenario; entry requires the real controller fully OFF. Virtual loads, slider and synthetic stats never touch real HA services or financial ledger. |
| **Restart setup wizard** | Draft existing settings, save only after review; see [Setup](setup.md). |
| **Show safety notice** | Reopen warning at any time and optionally change persistence; see [Safety](safety.md). |
| **Reset overall statistics** (Energy & costs page) | Confirmed ledger reset, independent of fair-runtime/fair-energy credits. Old monetary totals are not re-labelled. |

**Moved to Energy & costs:** currency, PV nominal watts, tariffs and optional energy sensors are edited exclusively on [Energy & costs](energy.md).

## Features and usage

- **Show donation link on dashboard:** Shows/hides the optional Buy me a drink link; enabled by default for migrated installations. This does not change the energy ledger.
- **Delete all RRH data:** In Settings, open the factory-reset dialog and type exactly `RESET ROUND ROBIN HOOD`. RRH first dispatches **All OFF**, requiring confirmed OFF feedback from every configured actuator. Only then are RRH configuration, consumers, profiles, runtime/fairness history, statistics, setup flags and the stored safety acknowledgment cleared. **No undo** in RRH. Create a full HA backup including `.storage` first. If device confirmations or storage fail, check actual equipment and logs; do not blindly retry. External HA entities and recorder history are never deleted.
- After success, the safety notice appears before the first-use choice. Allocation does **not** start automatically.

## Features and usage

Choose **Always OFF** (default), **Always ON**, or **Restore last state**. See [Restart behavior](startup.md) for safety checks and physical-device caveats.

## Features and usage

Settings cards now have **equal heights within each grid row** on wide displays, even when descriptions differ in length. The optional donation link reads **“Buy me a drink”**, with a tap- and hover-accessible information tip: “Large amounts of rum and cola fueled this project. That isn't free.” It is still configurable. First-time users can choose the wizard, a fully isolated Demo, or skip setup after seeing the safety notice.

