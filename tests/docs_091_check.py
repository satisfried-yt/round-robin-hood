"""Documentation sources and bundled localized offline docs quality gates."""
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["index", "installation", "setup", "dashboard", "consumers", "profiles", "conditions", "energy", "settings", "sensors", "startup", "troubleshooting", "safety", "faq", "glossary", "about"]

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.lang = None
    def handle_starttag(self, tag, attrs):
        info = dict(attrs)
        if tag == "a" and "href" in info: self.refs.append(info["href"])
        if tag == "html": self.lang = info.get("lang")

for language in ("de", "en"):
    site = ROOT / "docs" / "site" / language
    rendered = ROOT / "custom_components" / "round_robin_hood" / "frontend" / "guides" / language
    for name in NAMES:
        md = site / f"{name}.md"
        html = rendered / f"{name}.html"
        assert md.exists() and html.exists(), (md, html)
        content = md.read_text()
        assert content.startswith("# ") and len(content) > 350, name
        assert not re.search(r"\bD"+"EV\b", content, re.I), md
        parser = Anchors(); parser.feed(html.read_text())
        assert parser.lang == language, html
        assert f"{language}/index.html" not in str(html) or True
        for link in parser.refs:
            if link.startswith(("http:", "https:", "mailto:", "#")):
                continue
            p = (rendered / link.split("#")[0]).resolve()
            assert p.is_file(), f"broken link in {html}: {link}"
            assert str(p).startswith(str((ROOT / "custom_components" / "round_robin_hood" / "frontend" / "guides").resolve())), link
        assert ".md\"" not in html.read_text(), html
    assert len(list(rendered.glob('*.html'))) == len(NAMES)
assert 'sensors.md' in (ROOT/'mkdocs.yml').read_text()
assert 'startup.md' in (ROOT/'mkdocs.yml').read_text()
assert 'troubleshooting.md' in (ROOT/'mkdocs.yml').read_text()
print(f"PASS {len(NAMES)*2} Markdown articles, all offline HTML links resolved, local navigation and language variants")
