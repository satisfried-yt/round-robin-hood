# External components and rights – preliminary inventory

This document records dependencies detected by inspection of the Round Robin Hood v0.9.3 source. It is **not** a complete legal clearance or an assertion of ownership of external material.

- **Home Assistant Core / frontend APIs:** RRH imports and uses Home Assistant modules, including `homeassistant.components`, `homeassistant.helpers`, and `homeassistant.core`. Home Assistant is separately licensed; RRH does not vendor Home Assistant source code. Check the applicable Home Assistant license for any copied examples or code.
- **Probatio:** `custom_components/round_robin_hood/websocket.py` imports `probatio`. Probatio is provided by current Home Assistant versions and is MIT-licensed, with copyright attributed upstream to Franck Nijhof (2026). RRH does not vendor the package. See https://github.com/frenck/probatio and its MIT LICENSE.
- **Python standard library:** Imports such as `asyncio`, `json`, `dataclasses` and `datetime` are part of Python.
- **Frontend assets:** The source package contains RRH's own JavaScript and generated logo/icon imagery; no bundled external font or npm distribution was detected in the package inspection. The logo's AI-generation provenance and third-party resemblance rights require separate legal review.

Before public distribution, inspect any copied snippets, templates, artwork and reference material, and confirm rights to distribute the resulting work. Third-party permissions are unaffected by the RRH license draft.
