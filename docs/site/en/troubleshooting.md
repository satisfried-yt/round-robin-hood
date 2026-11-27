# Troubleshooting and recovery

## RRH does not resume after restart

Check Settings → Restart behavior, the configured power sensor (unit, sign and freshness), all configured actuator states and Home Assistant Core logs. The default policy is Always OFF. Unknown actuators and unresolved All OFF commands block automatic restart.

## A tariff sensor is missing from the picker

Verify a numeric state and a currency-matching unit such as `EUR/kWh` or `ct/kWh`. Temperature, power, energy and unitless sensors must not be selected as tariff inputs. See [Sensor types](sensors.md).

## No consumer starts

Inspect export, reserve, enabled profiles, eligibility conditions, minimum runtimes, cooldowns, nominal watts, external state changes and confirmation errors. Pause does not disconnect power; All OFF requests and confirms off actions separately.

## Upgrade or storage problem

Preserve a full Home Assistant backup including `.storage` and consult the matching `docs/UPDATE_*.md` for the exact upgrade/rollback procedure. Do not rerun a failed install blindly. RRH uses `.storage/round_robin_hood.rebuild_2026.state` for its own persistent state.


## Troubleshooting schedules and entity search (0.9.5)

No start despite PV surplus: inspect consumer and profile status. Both schedules and the sensor conditions must permit it. Also check grid data, reserve, wattage and cooldown.

Unexpected time or day: verify the configured Home Assistant timezone. Overnight intervals use the selected START weekday. During daylight-saving changes, local clock times can be skipped or repeated.

Missing entity: verify the HA entity, compatible domain and unit. Previously saved or temporarily unavailable IDs are preserved where possible. If the old interface appears, refresh the browser cache and restart HA after updating.

If switch-off confirmation fails, verify the physical actuator state and HA logs. RRH is not an electrical emergency stop; avoid uncontrolled retries.
