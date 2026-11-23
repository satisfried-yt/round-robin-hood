# Round Robin Hood 0.9.4 – development backlog

Status: **development only** on the public `develop` branch of `satisfried-yt/round-robin-hood`, based on public `main` (v0.9.3 release plus subsequent documentation updates). The first entity-picker implementation was imported from the private `round-robin-hood-dev/develop-0.9.4` branch. Do not deploy to production or update `main` or a public release without a tested versioned package and user acceptance.

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
- Separate optional time restrictions from existing numerical sensor conditions.
- Multiple time intervals per day and selectable weekdays; support midnight-crossing intervals and the HA timezone including daylight-saving changes.
- Allow only when **profile schedule AND consumer schedule AND sensor conditions** permit it.
- Controlled shutdown at the end of a permitted window; no new starts outside it. Display next active period and explicit reason when blocked.
- Test boundary transitions, restarts, clock changes, late reads and multiple overlapping windows.

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
- Python model/runtime/unit tests, offline HA simulation, browser UI tests in desktop and mobile, migration testing from 0.9.3, CI, and hands-on acceptance before any 0.9.4 publication.
