"""Release 0.9.5 identity, six-language offline parity, and schedule UI localization."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "round_robin_hood"
LANGS = ("de", "en", "fr", "es", "pt", "it")
PAGES = ("index", "installation", "setup", "consumers", "profiles",
         "conditions", "faq", "troubleshooting")


class Release095(unittest.TestCase):
    def test_version_and_public_release_documents(self):
        self.assertEqual((ROOT / "VERSION").read_text().strip(), "0.9.5")
        self.assertEqual(json.loads((COMP / "manifest.json").read_text())["version"], "0.9.5")
        self.assertIn('VERSION = "0.9.5"', (COMP / "const.py").read_text())
        self.assertIn('const VERSION = "0.9.5";', (COMP / "frontend/panel.js").read_text())
        self.assertIn('VERSION = "0.9.5"', (ROOT / "scripts/build_release.py").read_text())
        for name in ("RELEASE_NOTES_0.9.5.md", "UPDATE_0.9.5.md"):
            path = ROOT / "docs" / name
            self.assertGreater(path.stat().st_size, 1000)
            self.assertIn("0.9.5", path.read_text())
        self.assertIn("gh release create v0.9.5",
                      (ROOT / ".github/workflows/publish-release.yml").read_text())
        self.assertIn("round-robin-hood-0.9.5.zip",
                      (ROOT / ".github/workflows/publish-release.yml").read_text())
        self.assertIn("0.9.4 → 0.9.5", (ROOT / "README.md").read_text())
        self.assertIn("New in 0.9.5", (ROOT / "README.md").read_text())

    def test_all_languages_guide_search_and_source(self):
        for lang in LANGS:
            search = (COMP / "frontend/guides" / lang / "search-index.js").read_text()
            prefix = "window.RRH_GUIDE_SEARCH_INDEX="
            self.assertTrue(search.startswith(prefix))
            entries = json.loads(search[len(prefix):].rstrip(" ;\n"))
            by_href = {item["href"]: item["text"] for item in entries}
            for page in PAGES:
                md = (ROOT / "docs/site" / lang / (page + ".md")).read_text()
                html = (COMP / "frontend/guides" / lang / (page + ".html")).read_text()
                with self.subTest(lang=lang,page=page):
                    self.assertIn("0.9.5", md)
                    self.assertIn("0.9.5", html)
                    self.assertIn(page + ".html", by_href)
                    self.assertTrue(len(by_href[page + ".html"]) > 280)
            self.assertIn("0.9.5", by_href["index.html"])

    def test_schedule_labels_exist_for_all_ui_locales(self):
        js = (COMP / "frontend/panel.js").read_text()
        match = re.search(r"const SCHEDULE_COPY = (\{.*?\});\nconst CHART_LABELS", js)
        self.assertIsNotNone(match)
        labels = json.loads(match.group(1))
        self.assertEqual(set(labels), set(LANGS))
        keys = set(labels["de"])
        for lang in LANGS:
            with self.subTest(lang=lang):
                self.assertEqual(set(labels[lang]), keys)
                self.assertEqual(len(labels[lang]["days"]), 7)
                self.assertTrue(all(labels[lang].get(k) for k in (
                    "consumerEnable", "profileEnable", "addWindow", "help",
                    "start", "end", "remove", "allowed", "blocked", "next"
                )))
        self.assertIn('data-schedule-i18n="consumerEnable"', js)
        self.assertIn('data-schedule-i18n="profileEnable"', js)
        self.assertIn("_scheduleText(\"days\")", js)


if __name__ == "__main__":
    unittest.main()
