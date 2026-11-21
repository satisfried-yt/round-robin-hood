# RRH 0.9.3 — publication clearance checklist

**Status: OPEN — review as of 2026-11-21.** This checklist is not legal advice, approval to distribute, or proof of rights clearance. Repository: `satisfried-yt/round-robin-hood`. Branch: `release-prep/apache-2.0-branding`. Do not add private identity, postal address, secrets or signing keys to this document.

## Prepared and verified

- [x] Separate clean private release repository; private development history not imported.
- [x] Apache License 2.0, NOTICE, attribution and BRANDING guidance prepared. Apache-2.0 permits commercial use, changes and redistribution under its conditions; section 6 does not grant trademark rights.
- [x] Python tests, strict six-language documentation build and Hassfest passed on the private branch (commit `66abb928d8b7132517ea5c5a1e6375410ae819e6`).
- [x] Integration manifest, `hacs.json` and local `brand/icon.png` are present. This does **not** establish Marketplace catalog acceptance.

## Publisher identification and rights — open

- [ ] Assess whether this specific public GitHub offering, linked YouTube/TikTok/Twitch channels, documentation, and the **donation link in the RRH panel** trigger provider identification duties under **§ 5 DDG** and/or **§ 18 MStV**. Free or hobby-origin distribution alone does not guarantee exemption. Use the law in force, not an unapproved draft. If unsure, obtain qualified German legal advice. [§ 5 DDG](https://www.gesetze-im-internet.de/ddg/__5.html) · [§ 18 MStV](https://www.gesetze-bayern.de/Content/Document/MStV-18) · [Niedersachsen media authority](https://www.nlm.de/telemedien).
- [ ] Where legally required, provide a **compliant and clearly accessible imprint** identifying the responsible natural person (the project pseudonym Satisfried alone may be insufficient), a suitable real/serviceable postal address and appropriate contact methods. Check the precise legal requirements and use a lawful privacy-conscious address solution. Do **not** invent a company or publish the owner's residential address without an explicit, informed decision. No personal data is placed here.
- [ ] Review the exact chain of rights for source code, screenshots and artwork. The mascot and PNG icons were made with AI assistance. OpenAI's output terms allocate its rights as against the user where permissible, but do not guarantee copyright exclusivity, non-infringement or uniqueness. Check adapted snippets and other inputs. [OpenAI EU Terms](https://openai.com/policies/eu-terms-of-use/) · [Third-party notices](../THIRD_PARTY_NOTICES.md).
- [ ] Search prior German/EU/international trademarks and similar names for **Round Robin Hood**, **RRH** and **Satisfried**, and review the artwork for visual conflicts. A quick web search is **not** an official trademark clearance and none is asserted. [DPMA research guidance](https://www.dpma.de/marken/markenrecherche/) (DPMAregister, EUIPO/TMview, WIPO).
- [ ] Verify the intended **logo/image licensing**. The current [BRANDING.md](../BRANDING.md) expressly licenses bundled project images under Apache-2.0. Its trademark guidance cannot override rights granted under the copyright license. No registered trademark or exclusive copyright for the AI mascot is claimed.
- [ ] Resolve third-party code/examples, visual assets, attribution notices, and any applicable consumer or product-liability wording before public release.

## Marketplace and publication — open

Starting with **Home Assistant 2026.11** (released 2026-11-04), HACS is built in as **Settings → Marketplace**, using the same `hacs/default` catalog, `hacs.json` and HACS Action. Older installations retain HACS.

- [ ] Inspect all reachable public repository refs, history, releases and files for sensitive material before approving visibility change.
- [ ] Re-run Python tests, Hassfest, strict documentation build and relevant UI checks on the **exact final release tree**.
- [ ] Owner explicitly approves merging the reviewed PR to `main`, then separately approves public visibility only after clearing legal/asset checks.
- [ ] Once public, require HACS Action to pass without ignores. Failures on the private repository **do not establish code defects**, but do not constitute a pass.
- [ ] Build and verify exact `0.9.3` ZIP, SHA-256 checksums, detached signature and independent trusted signing-key fingerprint.
- [ ] Publish an actual GitHub Release `v0.9.3` on the approved commit (a tag alone is insufficient). Verify installation and updating via a Marketplace custom repository.
- [ ] Only after acceptance, submit an integration-catalog PR to `hacs/default`; do not advertise catalog listing until approved.

## Primary sources

- [Home Assistant 2026.11 release](https://www.home-assistant.io/blog/2026/11/04/release-202611/)
- [Marketplace publishing documentation](https://contributors.home-assistant.io/marketplace/)
- [Marketplace catalog inclusion](https://contributors.home-assistant.io/marketplace/guides/catalog/)
- [Marketplace GitHub releases](https://contributors.home-assistant.io/marketplace/guides/releases/)
- [Apache-2.0 (OSI)](https://opensource.org/license/Apache-2.0)
- [DDG § 5](https://www.gesetze-im-internet.de/ddg/__5.html)
- [MStV § 18](https://www.gesetze-bayern.de/Content/Document/MStV-18)
- [DPMA trademark clearance guidance](https://www.dpma.de/marken/markenrecherche/)

**Do not merge, change visibility, tag, publish a release, deploy sites, or submit to the catalog solely because this checklist exists.**
