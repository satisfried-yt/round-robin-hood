# Round Robin Hood 0.9.3

First public release of Round Robin Hood, a Home Assistant integration allocating PV export surplus to configurable appliances.

## Main features

- Eight distribution strategies, including round robin, fairness, priority, and efficiency.
- Configurable profiles, on/off and adjustable consumers, hysteresis, reserves, cooldown and sensor conditions.
- Responsive Home Assistant sidebar, first-run wizard and isolated demo mode.
- Estimates of energy, utilization and costs.
- A searchable offline handbook with 16 articles in each of six languages (DE, EN, FR, ES, PT, IT).
- Apache License 2.0 and separate guidance for truthful attribution and avoiding misleading use of project branding.
- A full source archive with internal `SHA256SUMS` and a separate ZIP `.sha256`. No cryptographic signature is claimed.

## Installation and updating

Home Assistant 2026.11+: under **Settings → Marketplace**, add the GitHub URL `https://github.com/satisfried-yt/round-robin-hood` as a custom repository. Earlier Home Assistant versions use **HACS custom repositories**. Approval for the *official* catalog is a separate process.

Alternatively, copy **only** `custom_components/round_robin_hood` from the ZIP into the same relative path in Home Assistant, restart, and add the integration in Settings → Devices & services. **Back up Home Assistant, including `.storage`, before installing or updating.**

To upgrade **0.9.2 → 0.9.3**, follow [the backup and rollback guide](UPDATE_0.9.3.md). Other upgrade paths are not covered there. Integration identity and persisted configuration are intended to stay unchanged.

## Safety and verification

RRH is **not** an electrical safety controller, physical disconnect or calibrated meter. Sensor failures, network errors and actuators can leave loads energized. Use independent thermal and electrical protection. **All OFF is not a hardware emergency stop.** Energy, cost and saving figures are estimates.

The GitHub release workflow only publishes after HACS validation, Hassfest, Python tests, JavaScript syntax checks, strict documentation build, and checksum verification succeed on the release source. It does not certify real-world electrical safety. See [verification notes](TEST_REPORT_0.9.3.md) and [Safety (EN)](site/en/safety.md).

Publisher: **Satisfried** · [Impressum](http://satisfried.de/) · [Project](https://github.com/satisfried-yt/round-robin-hood)
