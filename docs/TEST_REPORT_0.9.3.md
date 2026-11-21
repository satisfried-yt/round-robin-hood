# Round Robin Hood 0.9.3 — Release-cleanup verification

## Scope

This is a public-facing text, localization, provenance and documentation cleanup based on 0.9.2. No intentional change to control logic, storage format or API. **Not yet a public release.**

## Automated verification

- **285 Python unittest cases passed** (`python -m unittest discover -s tests -p 'test_*.py' -q`).
- Chromium browser scenario logs were checked for dashboard, device control, restart settings, profile editing, statistics, guide search, mobile layout and simulated HA transport. The v0.9.1 browser regression was re-run after correcting an outdated locale assertion, and passed.
- All **six UI locales** (de/en/fr/es/pt/it) have integration translation JSON and 16 localized HTML/Markdown guide chapters each (96 articles total).
- All six in-app guide locales passed content-search checks.
- A scan of active integration text, translations and in-app handbooks found no obsolete DEV/pre-release badges. Obsolete historical update reports and roadmap/status documents are omitted from this distributable snapshot; they remain in earlier development ZIPs.
- Four comment-only provenance markers were verified against a separate private origin map. They do **not** implement copy protection or prove copyright by themselves.
- Archive file hashes and detached Ed25519 signature verified locally.

## Limits and release gates

- Tests use Home Assistant simulation boundaries; **no physical-load safety certification or full production HA integration acceptance** was performed in this build.
- The author selected the Apache License 2.0 and its full text, NOTICE and separate branding guidance were added on a private release-preparation branch. This historical test report predates those edits; it does **not** establish legal rights clearance or rerun test results. Third-party assets, brand conflicts and any legally required provider identification must be reviewed before the repository is made public.
- No public GitHub release, Marketplace/HACS registration, GitHub publication or live Home Assistant update was performed.
- The Ed25519 public key needs out-of-band trust establishment. Store the private signing key and secret origin map securely, never in GitHub/public ZIP.
