# Round Robin Hood 0.9.3 — Verification

## Automated release checks

The GitHub Actions release source verification workflow checks Python compilation, all `tests/test_*.py` unittest modules, six offline handbook locales (96 articles and full-text indexes), JavaScript syntax, HACS metadata and the reproducible ZIP source archive with its internal and external SHA-256 checksums.

Hassfest and strict six-language MkDocs builds are run in separate CI workflows. The publication workflow also repeats HACS validation (without ignored checks), Hassfest, Python tests, guide and frontend checks, documentation build, and archive verification on the exact source prior to creating `v0.9.3`. Find the actual results in GitHub Actions; this document does not assert results for a future run.

## Prior evidence and limitations

The private 0.9.3 candidate was previously reported to pass 285 Python unit cases and simulator/browser regression checks. These preceded final publication edits and do not establish real-hardware electrical safety.

No independent software-security audit, physical-load certification, guaranteed energy saving, formal trademark registration, or comprehensive rights clearance is claimed. An Ed25519 signature that existed for a previous candidate ZIP **does not cover the newly built release archive**. Version 0.9.3 provides SHA-256 checksums only.

The release builder does not modify a running Home Assistant installation.
