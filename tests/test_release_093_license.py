"""Regression tests for the RRH 0.9.3 Apache-2.0 release preparation."""

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "round_robin_hood"
LANGS = ("de", "en", "fr", "es", "pt", "it")
OLD_RESTRICTIONS = (
    "Alle Rechte vorbehalten.",
    "All rights reserved.",
    "Tous droits réservés.",
    "Todos los derechos reservados.",
    "Todos os direitos reservados.",
    "Tutti i diritti riservati.",
)


class ApacheReleaseChecks(unittest.TestCase):
    def test_license_notice_and_branding(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", license_text)
        self.assertIn("Version 2.0, January 2004", license_text)
        self.assertIn("6. Trademarks.", license_text)
        self.assertIn("END OF TERMS AND CONDITIONS", license_text)

        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
        branding = (ROOT / "BRANDING.md").read_text(encoding="utf-8")
        self.assertIn("Round Robin Hood", notice)
        self.assertIn("This policy does not add restrictions", branding)
        self.assertIn("No trademark registration is asserted", branding)
        self.assertIn("Apache License 2.0", (ROOT / "README.md").read_text())

    def test_six_handbook_sources_pages_and_search_indexes(self):
        for lang in LANGS:
            with self.subTest(locale=lang):
                source = (ROOT / "docs" / "site" / lang / "about.md").read_text(encoding="utf-8")
                folder = COMP / "frontend" / "guides" / lang
                html = (folder / "about.html").read_text(encoding="utf-8")
                raw = (folder / "search-index.js").read_text(encoding="utf-8")
                marker = "window.RRH_GUIDE_SEARCH_INDEX="
                self.assertTrue(raw.startswith(marker))
                entries = json.loads(raw[len(marker):].strip().rstrip(";"))
                self.assertEqual(len(entries), 16)
                about = next(entry for entry in entries if entry["href"] == "about.html")
                for content in (source, html, about["text"]):
                    self.assertIn("Apache", content)
                    for restricted in OLD_RESTRICTIONS:
                        self.assertNotIn(restricted, content)

    def test_panel_discloses_software_license_without_mark_claims(self):
        js = (COMP / "frontend" / "panel.js").read_text(encoding="utf-8")
        self.assertGreaterEqual(js.count("Apache"), len(LANGS))
        for restricted in OLD_RESTRICTIONS:
            self.assertNotIn(restricted, js)

    def test_hacs_structure_preserved(self):
        hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
        manifest = json.loads((COMP / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(hacs["name"], "Round Robin Hood")
        self.assertEqual(manifest["domain"], "round_robin_hood")
        self.assertEqual(manifest["version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual([p.name for p in COMP.parent.iterdir() if p.is_dir()], ["round_robin_hood"])
        self.assertTrue((COMP / "brand" / "icon.png").is_file())


if __name__ == "__main__":
    unittest.main()
