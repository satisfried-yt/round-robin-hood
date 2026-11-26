# Round Robin Hood 0.9.5 – development backlog

Status: **development only** on the public `develop` branch of `satisfried-yt/round-robin-hood`, based on public `main` at the v0.9.4 HACS timezone maintenance release. The first entity-picker implementation was originally developed in the former private DEV repository and is now maintained in this public `develop` branch. Do not deploy to production or update `main` or a public release without a tested versioned package and user acceptance.

## 1. Native Home Assistant entity selection
- Searchable HA entity picker wherever an HA entity is selected: settings, wizard, consumers, stage controller, statistics, condition sensors.
- Preserve role-based domain/unit filters, existing or missing entity IDs, all current configuration values, keyboard/mobile usability.
- Accessible search fallback when Home Assistant's picker custom element is not registered.
- Test empty/invalid selections, forms, late custom-element registration and Home Assistant 2026.11.x behavior.

## 2. Device-independent multistage consumer editor
- Show a guided flow: choose device/entitites, identify a verified ON/OFF path, then map control options to measured or manually confirmed watts.
- Handle switch-only, switch+select, climate fan modes, multiple switch stages, numeric power/current targets, and supported charger/heater models through explicit capabilities; never infer watts from a fan mode, a temperature setpoint or a charger ampere value without validated information.
- Display actual HA options and required parameters, readable stage rows, validation messages and non-destructive help.
- Keep independent temperature protections, feedback confirmation, safe shutdown, external control behavior, and backward-compatible 0.9.3 profiles/configuration.

## 3. Weekly schedules on profiles and consumers
- **Implemented in develop (source CI passed; DEV acceptance pending):** optional weekly schedules on every profile and consumer, disabled by default on migrated settings.
- Each interval has one or more selectable weekdays (Monday=0 through Sunday=6), local HH:MM start and exclusive end. Multiple intervals per day and overlapping windows are supported. A cross-midnight interval belongs to its selected START day.
- The HA timezone is resolved once outside the event loop's scheduling path. Local-time checks honor DST; skipped hours open at the first valid local minute and repeated hours are evaluated on both occurrences. No forced UTC scheduling.
- Effective eligibility is **profile schedule AND consumer schedule AND numeric sensor conditions**. An active schedule closing forces OFF of RRH-owned consumers ahead of grid-data barriers and strict minimum on-time. A profile closing can use the existing confirmed bulk OFF path. External loads are never adopted or switched off merely for a schedule.
- HA panel: responsive weekday checkboxes, time inputs, multiple rows, add/remove, independent enable switches, visible blocked/allowed state and next opening in the HA timezone.
- Automatic tests in `tests/test_weekly_schedules_095.py` cover migration, input validation, mixed windows, overnight, DST gaps/folds, gating, expiry, bulk OFF, and preflight race.
- **Source CI:** successful run [45838213099](https://github.com/satisfried-yt/round-robin-hood/actions/runs/45838213099) (Python unit tests, JavaScript syntax, documentation checks and preview bundle). The frontend uses a development-only cache token to avoid retaining an old JavaScript module after manual DEV updates.
- **Remaining before release:** DEV hands-on acceptance, translation/documentation sweep, and explicit release approval.

## 4. Multiple notification destinations
- **Multiple phones AND multiple speakers can be selected**: zero, one or many of each, in the same notification policy.
- Each event has an independently configurable target list; deduplicate destinations and prevent noisy repeats.
- Phone targets use supported Home Assistant notify actions/entities. Speaker targets use available announcement/TTS integrations and media players, not hardcoded Alexa, Google or Tuya APIs. Detect capability and offer a harmless explicit test.
- Event: **first successfully confirmed RRH-controlled consumer start per local calendar day**, persisted to avoid repeated notifications after restart.
- Event: actionable failures and failed device confirmations with transition/deduplication and optional recovery notification.
- Event: surplus utilization/capture below user threshold for a chosen persistence interval **when available eligible loads cannot use any additional measured surplus**; use RRH's defined capture metric, not PV plant efficiency. Provide actual values and explain exclusions.
- No automatic external notification action until recipients and each event are explicitly enabled. Never block safety shutdown if a notification fails.

## Release and safety gates
- Isolated DEV install with backup and rollback procedure; no changes to production HA or to public `main` while testing.
- Python model/runtime/unit tests, offline HA simulation, browser UI tests in desktop and mobile, migration testing from 0.9.3, CI, and hands-on acceptance before any 0.9.5 publication.
