# Round Robin Hood - User guide

**Version 0.9.5.** [Deutsch](../) | [Safety](safety.md) | [Getting started](setup.md)

RRH allocates measured solar export surplus to eligible consumers using configured power ratings, profiles and allocation strategies. Its control input is **instantaneous grid power** (W or kW), not a cumulative kWh meter. The grid reading already reflects power used by running appliances.

**Safety:** This software can switch real equipment but cannot replace electrical or thermal protection. Errors can cause unexpected costs, overheating and damage. Read [Safety](safety.md) before use.

## Chapters

- [Installation and upgrades](installation.md) - backups and rollback.
- [Setup](setup.md) - safety notice, wizard, demo and skip.
- [Dashboard](dashboard.md) - measurements, actions, charts.
- [Consumers](consumers.md) - switches and adjustable appliances.
- [Profiles and strategies](profiles.md) - eight scheduling strategies.
- [Conditions](conditions.md) - thresholds and hysteresis.
- [Energy and costs](energy.md) - tariffs, PV rating, estimates.
- [Settings](settings.md) - operation, reserve, startup, demo and reset.
- [Sensors](sensors.md) - units, values and quality.
- [Startup behavior](startup.md) - restoration after HA restart.
- [Troubleshooting](troubleshooting.md) - problems and remedies.
- [Safety](safety.md), [FAQ](faq.md), [Glossary](glossary.md), [About](about.md).

RRH has no metering hardware of its own and does not configure the Home Assistant Energy Dashboard. Nominal ratings and financial totals are estimates, not calibrated measurements.


## New in version 0.9.5

- Searchable Home Assistant entity selection in settings, setup, consumer, sensor-condition and energy forms, including mobile browsers.
- Optional weekly schedules for profiles and individual consumers, supporting weekdays, multiple windows and overnight operation.
- Sensor conditions and both schedules must pass; when permission ends, RRH switches off its own running loads even before minimum runtime ends.
- Existing configuration is retained and schedules default to disabled. Back up all Home Assistant data, including .storage, before upgrading.
