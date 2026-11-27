# Consumers – devices and safety limits

## Cards

The responsive grid uses **three equal-width slots** on wide panels. With four or five devices, empty slots remain in the last row; narrow panels use two or one column. Each card shows name, MDI icon, confirmed state, planned/current watts, enabled flag, profile, waiting reason and relevant fairness credits.

| Action | Result |
|---|---|
| **Participate / stop participating** | Allows/removes participation. An already running device may require controlled shutdown. |
| **↑ / ↓** | Reorders the global list; power-sorted strategies impose their own order. |
| **Edit** | Opens power mode, safety timers, icon and conditions. |
| **Remove** | Unassigns RRH, **does not delete the HA entity**. Unsafe removal of still-on owned devices is rejected. |

## Basic editor fields

| Field | Meaning / limit |
|---|---|
| **Name** | User label, 1–80 characters. |
| **Mode** | **Switch**, **staged**, **continuously variable**. Determines available HA actions. |
| **HA control entity** | Real entity, never shared between RRH loads. A new/rebound entity requires separate explicit authorization. |
| **Rated / minimum power (W)** | Positive, ≤100,000 W; scheduling estimate, not measured electricity. |
| **Participate** | Whether RRH can allocate this consumer; independent of HA state. |
| **Icon** | Clickable MDI gallery with preview, or PNG/WebP up to 48 KB; affects appearance only. |

## Modes and extra fields

**Fixed switch (`switch.*`):** single rated wattage, normal `switch.turn_on/turn_off`, feedback confirmation.

**Staged (`switch.*`, `select.*`, `climate.*`):** stage-control entity, rows `watts=option` (e.g. `500=1`, `1000=2`), an actual **OFF option** for `select.*` main controls. First stage is the minimum startup power. A climate fan mode is not proof of electrical wattage. Domain-specific OFF action is used.

**Variable (`number.*`):** minimum and **maximum watts**, **step resolution (W)**, **regulation hysteresis/minimum change (W)** and **minimum regulation interval (s)**. The HA `number` must support actual **0 = OFF**, report feedback and safely implement setpoints.

## Timing fields

| Field | Effect |
|---|---|
| **Override shutdown delay** | Per-consumer 0–600 s, replaces global default. |
| **Minimum ON duration** | Hours/minutes/seconds during which voluntary rotation is deferred. |
| **Enforce minimum ON during shortfall** | May intentionally import grid electricity and incur costs; not a thermal safety mechanism. |
| **Restart cooldown** | Hours/minutes/seconds preventing rapid restart after OFF. |
| **Cooldown policy** | Skip blocked device or wait for it. |
| **Skip timer** | Overrides timing protection, with optional confirmation. |

## Conditions and authorization

Enable and combine individual sensor predicates using `ALL` or `ANY`. See [Sensor conditions](conditions.md). Missing feedback or external commands must not be taken as successful RRH control. The old redundant editor checkbox was removed, but **new or rebound real entity bindings still require explicit safety approval**, and backend domain/action whitelists remain in place. Heaters require independent over-temperature and electrical protection.

## Features and usage

The consumer editor no longer has a textual MDI dropdown. Choose an icon from the clickable preview gallery; the selected tile is highlighted. Existing saved icons survive an update. Custom PNG and WebP images remain supported.


## New in 0.9.5: entity search and consumer schedules

Open Consumers → Edit. Control and stage entities use the searchable Home Assistant picker. Search by part of an entity name or ID; existing selections are retained.

Enable the consumer schedule only if needed. Add one or more time windows, select weekdays Mon–Sun and enter From/Until (HH:MM) for each row. Disabled schedules do not restrict operation.

For Monday 22:00–Tuesday 02:00, select Monday as the start day. End time is exclusive. Multiple windows allow operation if ANY matches, while profile schedule and sensor conditions must ALSO allow it.

When a window closes, RRH switches off its managed running consumer even if strict minimum runtime has not finished. This is not a substitute for independent electrical or thermal safety. The UI shows the next opening in HA's timezone.
