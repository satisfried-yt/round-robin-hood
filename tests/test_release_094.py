"""Release 0.9.4 identity, installation docs and timezone hotfix consistency."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "round_robin_hood"


class Release094Checks(unittest.TestCase):
    def test_version_consistency(self):
        version = (ROOT / "VERSION").read_text().strip()
        self.assertEqual(version, "0.9.4")
        self.assertEqual(json.loads((COMP / "manifest.json").read_text())["version"], version)
        self.assertIn(f'VERSION = "{version}"', (COMP / "const.py").read_text())
        self.assertIn(f'const VERSION = "{version}";', (COMP / "frontend/panel.js").read_text())
        self.assertIn(f'VERSION = "{version}"', (ROOT / "scripts/build_release.py").read_text())

    def test_release_documents_and_marketplace_search_with_fallback(self):
        for path in ("docs/RELEASE_NOTES_0.9.4.md", "docs/UPDATE_0.9.4.md", "VERIFY_RELEASE.md"):
            self.assertTrue((ROOT / path).is_file(), path)
        readme = (ROOT / "README.md").read_text()
        self.assertIn('Search for “Round Robin Hood”', readme)
        self.assertIn('add it as a **custom integration repository**', readme)
        self.assertIn("docs/UPDATE_0.9.4.md", readme)
        self.assertIn("docs/RELEASE_NOTES_0.9.4.md", readme)

    def test_release_workflow_references_existing_python_check_scripts(self):
        workflow = (ROOT / ".github/workflows/publish-release.yml").read_text()
        scripts = re.findall(r"\bpython\s+(tests/[a-zA-Z0-9_]+\.py)", workflow)
        self.assertTrue(scripts)
        for script in scripts:
            self.assertTrue((ROOT / script).is_file(), script)

    def test_zoneinfo_is_not_called_from_statistics(self):
        code = (COMP / "statistics.py").read_text()
        self.assertNotIn("from zoneinfo import ZoneInfo", code)
        self.assertNotIn("ZoneInfo(self.timezone)", code)
        self.assertIn("tz=self.timezone", code)


if __name__ == "__main__":
    unittest.main()
