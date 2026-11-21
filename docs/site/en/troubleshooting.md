# Troubleshooting and recovery

## RRH does not resume after restart

Check Settings → Restart behavior, the configured power sensor (unit, sign and freshness), all configured actuator states and Home Assistant Core logs. The default policy is Always OFF. Unknown actuators and unresolved All OFF commands block automatic restart.

## A tariff sensor is missing from the picker

Verify a numeric state and a currency-matching unit such as `EUR/kWh` or `ct/kWh`. Temperature, power, energy and unitless sensors must not be selected as tariff inputs. See [Sensor types](sensors.md).

## No consumer starts

Inspect export, reserve, enabled profiles, eligibility conditions, minimum runtimes, cooldowns, nominal watts, external state changes and confirmation errors. Pause does not disconnect power; All OFF requests and confirms off actions separately.

## Upgrade or storage problem

Preserve a full Home Assistant backup including `.storage` and consult the matching `docs/UPDATE_*.md` for the exact upgrade/rollback procedure. Do not rerun a failed install blindly. RRH uses `.storage/round_robin_hood.rebuild_2026.state` for its own persistent state.
