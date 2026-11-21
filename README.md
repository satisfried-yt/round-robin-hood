# Round Robin Hood

**Power your home. Not their profits.**  
*Less to the grid. More for the little guy.*

![Round Robin Hood mascot](custom_components/round_robin_hood/brand/logo.png)

**Round Robin Hood (RRH)** is a Home Assistant custom integration by **Satisfried**. Instead of sending every available watt of solar surplus to the grid, RRH allocates measured grid-export surplus to suitable loads in your home—subject to your priorities, device limits and safety settings.

> **Release preparation:** Version **0.9.3** has passed user acceptance, the six-language documentation build and Hassfest. Apache-2.0 licensing and a separate branding policy are prepared for review; third-party rights, publication approval and Marketplace/HACS validation on a public repository remain pending. This private branch is not a public release or HACS listing.

## At a glance

| Control | Your options |
| --- | --- |
| Solar input | Home Assistant grid-power sensor (W or kW), with selectable export sign |
| Loads | On/off switches, multi-stage appliances, adjustable power targets and an optional residual-surplus consumer |
| Scheduling | Eight allocation strategies, including round robin, fairness, priority and efficiency |
| Safeguards | Reserve, hysteresis, minimum run time, cooldown, delayed deficit handling, sensor freshness and conditions |
| Operation | Responsive sidebar panel, profiles, restart policy, setup wizard and isolated demonstration |
| Insights | Estimates for energy use, utilized surplus and costs based on configured device power and tariffs |

### Eight scheduling strategies

Classic round robin · Fair runtime · Fair energy · Fixed priority · Maximum efficiency · Ascending power · Descending power · Stable operation.

RRH reads the **instantaneous grid power**, not a cumulative energy meter. The measured grid flow already includes consumption by devices that are running. RRH does not independently measure electrical power or guarantee that available PV surplus will cover each appliance.

## Screenshots

Real Round Robin Hood 0.9.3 screens from a Home Assistant test setup. Live values are snapshots; energy and cost figures are **estimates**, not guaranteed savings.

### Dashboard

![RRH dashboard showing live surplus utilization, two allocation profiles and consumer status](docs/images/dashboard-desktop.png)

### More views

| Consumers | Profiles |
| --- | --- |
| ![Three configured consumers and their current switching states](docs/images/consumers.png) | ![Two active profiles with priority and scheduling strategy](docs/images/profiles.png) |

| Energy and costs | Settings |
| --- | --- |
| ![Energy and tariff configuration with estimated statistics](docs/images/energy-costs.png) | ![Grid sensor, reserves, restart behavior and dashboard settings](docs/images/settings.png) |

| In-app handbook | About |
| --- | --- |
| ![Searchable sixteen-chapter in-app handbook with language selection](docs/images/handbook.png) | ![Publisher information and installed RRH version](docs/images/about.png) |
## Install manually

> **Before starting:** Make a restorable full Home Assistant backup **including `.storage`**. Use a supported Home Assistant installation and make sure that independently protected loads and suitable Home Assistant entities are already available.

1. Obtain a release package from the **official project** when a release has been published. Do not use the entire repository as the Home Assistant integration directory.
2. Copy **only** `custom_components/round_robin_hood` to `/config/custom_components/round_robin_hood` on your Home Assistant installation.
3. Restart Home Assistant Core.
4. Add **Round Robin Hood** under **Settings → Devices & services** and open the RRH sidebar panel.
5. Follow the setup wizard, try the isolated demo or configure manually. Verify the grid sensor's sign and unit before enabling control of real devices.

**Already using RRH?** Back up first, then use the version-specific [upgrade and rollback instructions](docs/UPDATE_0.9.3.md). Those instructions cover **0.9.2 → 0.9.3 only**. Avoid mixing older integration code with newer RRH `.storage` data.

**Home Assistant Marketplace (formerly HACS):** Starting with Home Assistant 2026.11, the HACS catalog is built into Home Assistant under **Settings → Marketplace**. Older installations still use HACS. **Round Robin Hood is not yet in the shared catalog, and installation via a custom repository is not verified.** Repository validation must be repeated when publication is approved and the GitHub repository becomes public.

## Documentation — six languages

The integration includes an **offline, searchable 16-article handbook** in German, English, French, Spanish, Portuguese and Italian. The same handbook is available as Markdown source for a future documentation website. The German and English guides currently provide more technical detail.

| Language | Start | Safety |
| --- | --- | --- |
| Deutsch | [Handbuch](docs/site/de/index.md) | [Sicherheit](docs/site/de/safety.md) |
| English | [User guide](docs/site/en/index.md) | [Safety](docs/site/en/safety.md) |
| Français | [Guide](docs/site/fr/index.md) | [Sécurité](docs/site/fr/safety.md) |
| Español | [Guía](docs/site/es/index.md) | [Seguridad](docs/site/es/safety.md) |
| Português | [Guia](docs/site/pt/index.md) | [Segurança](docs/site/pt/safety.md) |
| Italiano | [Guida](docs/site/it/index.md) | [Sicurezza](docs/site/it/safety.md) |

For a local documentation website build, see [MkDocs instructions](docs/SITE_BUILD.md). The documentation website has **not** been publicly deployed.

## Safety first

**RRH is not a certified safety controller, electrical protection device, emergency disconnect or calibrated energy meter.** It communicates with devices through Home Assistant; software, sensors and connectivity may fail. A device might remain energized even after RRH attempts to switch it off.

Use appropriate independent thermal protection, wiring and circuit protection, safe physical installation and a real disconnect for heaters and other potentially hazardous loads. **All OFF is not a physical emergency stop.** Costs, energy and savings displayed by RRH are estimates—not certified measurements or guaranteed financial results.

Read the [full safety guidance](docs/site/en/safety.md) before use.

## Version, permissions and project status

- **Current release candidate:** 0.9.3. [Changelog](CHANGELOG.md) · [Release notes](docs/RELEASE_NOTES_0.9.3.md)
- **Software license (prepared for release):** [Apache License 2.0](LICENSE) · [NOTICE](NOTICE). The license allows private and commercial use, modification and redistribution under its conditions. A separate [branding policy](BRANDING.md) explains name, logo and impersonation concerns; Apache-2.0 does not grant trademark rights. Third-party rights and publisher identification still need review before publication.
- **Other software:** [Third-party notices](THIRD_PARTY_NOTICES.md).
- **Publication readiness:** [Release clearance checklist](docs/RELEASE_CLEARANCE_0.9.3.md). Legal identification, brand clearance, Marketplace verification and the actual release package remain outstanding.
- **Package verification:** When signed release files are published, follow the [verification guide](VERIFY_RELEASE.md). The repository does not contain the private signing key.

Project development has been assisted by AI. Rights in individual components, including artwork, must be checked before release.

## Satisfried

[YouTube](https://www.youtube.com/@Satisfried_yt) · [TikTok](https://www.tiktok.com/@satisfried_yt) · [Twitch](https://www.twitch.tv/satisfried_yt) · [GitHub](https://github.com/satisfried-yt)

**Impressum / Legal notice:** [satisfried.de](http://satisfried.de/)

Copyright © 2026 Satisfried (project pseudonym), to the extent the publisher holds rights. See [LICENSE](LICENSE) for copyright permissions; no trademark rights are granted by Apache-2.0.
