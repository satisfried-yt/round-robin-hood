"""Public-imprint link consistency for the RRH 0.9.3 release candidate.

No network access or assumptions about legal compliance are made.
"""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "round_robin_hood"
URL = "http://satisfried.de/"
LANGUAGES = ("de", "en", "fr", "es", "pt", "it")


class ImprintLinkChecks(unittest.TestCase):
    def test_main_readme_and_panel(self):
        self.assertIn(URL, (ROOT / "README.md").read_text(encoding="utf-8"))
        panel = (COMP / "frontend" / "panel.js").read_text(encoding="utf-8")
        self.assertIn('href="' + URL + '"', panel)
        self.assertEqual(panel.count('data-release-i18n="aboutImprint"'), 1)
        self.assertEqual(panel.count("aboutImprint:"), len(LANGUAGES))

    def test_all_handbook_implementations(self):
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                source = ROOT / "docs" / "site" / lang / "about.md"
                folder = COMP / "frontend" / "guides" / lang
                html = folder / "about.html"
                js = (folder / "search-index.js").read_text(encoding="utf-8")
                marker = "window.RRH_GUIDE_SEARCH_INDEX="
                self.assertTrue(js.startswith(marker))
                index = json.loads(js[len(marker):].strip().rstrip(";"))
                self.assertEqual(len(index), 16)
                about = next(row for row in index if row["href"] == "about.html")
                self.assertIn(URL, source.read_text(encoding="utf-8"))
                self.assertIn('href="' + URL + '"', html.read_text(encoding="utf-8"))
                self.assertIn(URL, about["text"])


if __name__ == "__main__":
    unittest.main()
