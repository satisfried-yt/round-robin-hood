# Changelog

All changes below describe Round Robin Hood capabilities. Historical development and verification records remain in the project's version-control history and prior project backups, rather than in the user handbook.

## 0.9.5 - native entity search and weekly schedules

- Added native searchable Home Assistant entity pickers (with fallback), covering configuration, wizard, consumers, stage controllers, statistics and numeric sensor conditions; verified on desktop and mobile DEV.
- Added optional independent weekly schedules for profiles and consumers: selectable weekdays, multiple windows per day, overnight spans and HA-local timezone/DST handling.
- Combined profile and consumer schedules with existing numeric sensor conditions using AND; time-window expiry enforces confirmed shutdown for RRH-owned loads, even with minimum runtime, with profile group OFF where applicable.
- Display schedule status and next opening; preserve pre-existing configuration and leave new schedules disabled by default.
- Localized new schedule controls and synchronized offline/on-GitHub handbook documentation in German, English, French, Spanish, Portuguese and Italian.
- Added validation, DST, safety, and migration unit tests; full source CI and release checks required for publication. Notifications and a redesigned device-independent multistage wizard remain future work.

## 0.9.4 - Home Assistant event-loop timezone fix

- Resolve the configured Home Assistant timezone asynchronously once during startup and reuse the resolved tzinfo for each sample and day boundary.
- Preserve the timezone on statistics reset and factory reset; the isolated demo uses UTC without tzdata lookup.
- Add regression coverage for day boundaries and Home Assistant adapter initialization; no RRH storage migration or allocation behavior change.
- Prioritize search in Marketplace/HACS installation instructions while retaining custom-repository links before catalog listing.

## 0.9.3 - public-facing cleanup and ownership verification

- Prepared Apache License 2.0, NOTICE and separate name/logo branding guidance in the private release branch; distribution and rights checks remain pending.

- Removed obsolete preview warnings and incorrect old-version texts from the Home Assistant integration setup, sidebar and user documentation.
- Updated publisher copyright and AI-assistance disclosures without removing any safety warnings.
- Added six-language HA integration descriptions and six-language offline handbooks with searchable chapters (16 per language). The DE/EN guides remain more detailed.
- Added non-functional provenance markers and a separately documented origin-verification method.
- Prepared SHA-256 package inventory and Ed25519 detached package signature; signing credentials are stored separately from distributable sources.
- Preserved storage key, configuration schema, control API and consumer/profile migration behavior from 0.9.2.

## 0.9.2 - safer restart and onboarding

- Fixed restart restoration for manually configured profiles and devices and delayed HA state availability.
- Added initial choice of wizard, isolated demo or manual setup; searchable in-app handbooks, equal-height settings cards and improved donation wording.

## 0.9.1 - sensor sources and restart policy

- Added policy to stay OFF, start ON after checks, or restore the previous RRH mode on HA restart.
- Improved source-unit validation and integrated documentation.

## 0.9.0 - guided configuration

- Added name and HA-entity selection for PV and tariffs; compact horizontal efficiency visualization.

## 0.8.0 - safety and presentation

- Introduced factory reset with confirmed All OFF, visual updates and additional control-loop regression scenarios.

## 0.7.x - setup, analytics and branding

- Added first-run safety notice, setup wizard, cost/energy views, responsive pages and Satisfried branding.

## Earlier milestones

- Profiles and eight strategies, fair-runtime/energy accounting, smart and residual loads, separate demo isolation, sensor conditions and safety gating. Detailed historical records remain in earlier version snapshots.
