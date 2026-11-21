"""User-facing cleanup, localization parity, safe non-functional ownership markers."""
from pathlib import Path
import unittest,json,re

ROOT=Path(__file__).resolve().parents[1]
COMP=ROOT/'custom_components/round_robin_hood'
LANGS=('de','en','fr','es','pt','it')
PAGES=('index','installation','setup','dashboard','consumers','profiles','conditions','energy','settings','sensors','startup','troubleshooting','safety','faq','glossary','about')

class ReleaseHygiene(unittest.TestCase):
    def test_identity_and_storage_unchanged(self):
        m=json.loads((COMP/'manifest.json').read_text())
        self.assertEqual(m['version'],'0.9.3')
        self.assertEqual(m['domain'],'round_robin_hood')
        self.assertIn('@satisfried-yt',m['codeowners'])
        c=(COMP/'const.py').read_text()
        self.assertIn('round_robin_hood.rebuild_2026.state',c)
        self.assertIn('rrh_rebuild_2026',c)
        self.assertEqual((ROOT/'VERSION').read_text().strip(),'0.9.3')

    def test_six_locales(self):
        for lang in LANGS:
            with self.subTest(lang=lang):
                j=json.loads((COMP/'translations'/f'{lang}.json').read_text())
                self.assertIn('Round Robin Hood',j['title'])
                self.assertNotIn('Version 0.1',j['config']['step']['user']['description'])
                for pg in PAGES:
                    self.assertTrue((ROOT/f'docs/site/{lang}/{pg}.md').exists())
                    self.assertTrue((COMP/f'frontend/guides/{lang}/{pg}.html').exists())
                self.assertTrue((COMP/f'frontend/guides/{lang}/search-index.js').exists())

    def test_no_user_facing_preview_indicators(self):
        bad=re.compile(r'\bD'+r'EV\b|\bpre[- ]release\b|private developer build',re.I)
        paths=list(COMP.rglob('*.json'))+list(COMP.rglob('*.html'))+[COMP/'frontend/panel.js', ROOT/'README.md', ROOT/'CHANGELOG.md']+list((ROOT/'docs/site').rglob('*.md'))
        for p in paths:
            with self.subTest(file=str(p.relative_to(ROOT))):
                self.assertIsNone(bad.search(p.read_text()),p)

    def test_markers_only_source_comments(self):
        for file in ('const.py','controller.py','model.py','frontend/panel.js'):
            with self.subTest(file=file):
                s=(COMP/file).read_text()
                self.assertRegex(s.splitlines()[0],r'rrh-origin:[0-9a-f]{32}')
        self.assertFalse((ROOT/'RRH_ORIGIN_PRIVATE.json').exists())
        self.assertFalse((ROOT/'rrh-release-private.pem').exists())

if __name__=='__main__':unittest.main()
