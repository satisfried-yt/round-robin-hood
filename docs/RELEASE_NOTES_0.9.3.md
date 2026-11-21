# Round Robin Hood 0.9.3 — release notes (draft)

**Status:** For review only. Not yet a published GitHub release. Do not create a tag, publish a release or mark it generally available until the license and distribution review have been completed.

## What Round Robin Hood does

Round Robin Hood is a Home Assistant integration that allocates measured PV export surplus to selected household appliances. Use configurable consumer profiles, eight allocation strategies and safeguards such as hysteresis, run-time limits, cooldowns and sensor conditions. A responsive sidebar panel, first-run wizard and fully isolated demonstration help with setup.

RRH is a software controller, **not an electrical protection system**.

## What's included in 0.9.3

- Cleans up user-facing preview and old-version wording ahead of public distribution.
- Improves publisher and attribution information.
- Includes a searchable, offline handbook with 16 chapters in each of six languages: DE, EN, FR, ES, PT and IT.
- Documents package checksums and a detached Ed25519 signature, to be released with the original archive and a trusted public-key fingerprint.
- Preserves the existing storage format and controller behavior established in 0.9.2.

### Previous improvements delivered in the 0.9.x series

- More reliable restoration of profiles and consumers at Home Assistant startup.
- Configurable restart policy: stay off, start on after checks, or restore the prior mode.
- Setup choices for wizard, isolated demo or manual configuration.
- Improved unit handling and sensor source validation.

## Installation and updating

**Fresh installations:** Back up Home Assistant (including `.storage`), install the `custom_components/round_robin_hood` directory into the Home Assistant configuration, restart Core, then add the integration under Settings → Devices & services.

**Updating from 0.9.2:** Follow the [specific update and rollback procedure](UPDATE_0.9.3.md). Other upgrade paths are not covered by those commands. Verify that controlled devices are off before replacing code.

**HACS availability:** Not verified yet. Do not promise installation via HACS in a release announcement until its validation and distribution have been confirmed.

## Verification status

- User acceptance in a real Home Assistant environment: **reported successful**.
- Unit and package test evidence: see [test report](TEST_REPORT_0.9.3.md).
- Multilingual MkDocs build in strict mode: **passed on GitHub Actions**.
- Hassfest validation: **passed on GitHub Actions**.
- HACS validation: **deferred while repository remains private**.
- Public-release legal and asset review: **open**.

## Safety and limitations

RRH depends on Home Assistant states, communication and supported actuators. Device switching may fail; an energized heating device is a fire hazard without independent thermal cutoffs. The **All OFF** action is not a substitute for hardware protection. Power utilization and cost figures are estimates and do not guarantee savings.

Read the [English](site/en/safety.md) or [German](site/de/safety.md) safety guidance before controlling real loads.

## Publication checklist

- [ ] Finalize legally reviewed distribution license and asset rights.
- [x] Add authentic, privacy-reviewed screenshots.
- [ ] Validate the final package, checksums, public-key fingerprint and release attachments.
- [ ] Confirm HACS validation when public access is authorized.
- [ ] Review the precise version and tag, confirm installation in a clean environment and approve publication.

Publisher: **Satisfried** · Repository: https://github.com/satisfried-yt/round-robin-hood
