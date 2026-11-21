"""Validate all six in-app handbooks, local links, search, and language routing."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/site'
GUIDES = ROOT / 'custom_components/round_robin_hood/frontend/guides'
LANGS = ('de','en','fr','es','pt','it')
NAMES = ('index','installation','setup','dashboard','consumers','profiles','conditions','energy','settings','sensors','startup','troubleshooting','safety','faq','glossary','about')

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.lang = None
        self.options = []
        self.filter_seen = False
        self.switch_seen = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.lang = a.get('lang')
        if tag == 'a': self.refs.append(a.get('href',''))
        if tag == 'option' and a.get('value'): self.options.append(a['value'])
        if tag == 'input' and a.get('id') == 'filter': self.filter_seen = True
        if tag == 'select' and a.get('id') == 'guide-language': self.switch_seen = True

for lang in LANGS:
    source = SOURCE/lang
    dest = GUIDES/lang
    assert len(list(source.glob('*.md'))) == len(NAMES),lang
    assert len(list(dest.glob('*.html'))) == len(NAMES),lang
    search = (dest/'search-index.js').read_text(encoding='utf-8')
    assert search.startswith('window.RRH_GUIDE_SEARCH_INDEX=')
    entries = json.loads(search.split('=',1)[1].rstrip(' ;\n'))
    assert {x['href'] for x in entries} == {n+'.html' for n in NAMES}
    assert all(len(e['text']) > 280 for e in entries),lang
    for name in NAMES:
        md = (source/(name+'.md')).read_text(encoding='utf-8')
        h = (dest/(name+'.html')).read_text(encoding='utf-8')
        parser = Page(); parser.feed(h)
        assert parser.lang == lang,(lang,name)
        assert parser.filter_seen and parser.switch_seen,(lang,name)
        assert set(parser.options) == set(LANGS),(lang,name,parser.options)
        assert h.count('aside select{') == 1,(lang,name)
        assert 'search-index.js' in h
        assert 'location.href' in h
        assert 'Copyright (c) 2026 Satisfried' in h
        for href in parser.refs:
            if not href or href.startswith(('https:','http:','mailto:','#')):continue
            file = (dest / href.split('#',1)[0]).resolve()
            assert file.is_file() and str(file).startswith(str(GUIDES.resolve())),(lang,name,href)
        assert not re.search(r'\bD' + 'EV\b', md, re.I),(lang,name)
print(f'PASS {len(LANGS)*len(NAMES)} articles, {len(LANGS)} local indices, all links, language switch, and copyright')
