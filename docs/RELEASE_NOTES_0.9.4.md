# Round Robin Hood 0.9.4

Maintenance update addressing Home Assistant HACS / Marketplace compatibility feedback. This release **does not** include unfinished 0.9.5 features.

## Fixed

- Home Assistant's configured timezone is resolved once using `await dt_util.async_get_time_zone(hass.config.time_zone)` during runtime startup. No `ZoneInfo` objects are created from timezone strings in the event loop.
- The statistics ledger retains this `tzinfo` during one-second sampling, local-day rollover, statistics reset and factory reset.
- The isolated demo uses `datetime.UTC` with no timezone lookup.
- Regression tests cover time boundaries, resets, the demo and the HA adapter initialization path.

## Installation and updating

Search for **Round Robin Hood** in Home Assistant Marketplace (2026.11+) or HACS. If it is not listed yet, add `https://github.com/satisfried-yt/round-robin-hood` as a custom integration repository. Official catalog listing requires separate approval.

Before updating: issue RRH **All OFF**, physically verify controlled loads are off, and make a restorable **Home Assistant backup including `.storage`**. Follow the [0.9.3 → 0.9.4 upgrade and rollback guide](UPDATE_0.9.4.md). Restart Home Assistant Core after the update. There is no data migration.

## Safety and verification

RRH is **not** an electrical safety controller, certified energy meter or physical emergency disconnect. Independently protect potentially hazardous loads. Savings and energy figures are estimates.

Automated QA covers Python, frontend syntax, HACS, Hassfest, documentation and release archive integrity. It does not prove real-hardware behavior. See [release verification](../VERIFY_RELEASE.md) and the [project](https://github.com/satisfried-yt/round-robin-hood).
