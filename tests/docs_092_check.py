"""Validate local full-text guide index and new articles in both supported doc languages."""
from pathlib import Path
import json,re
import docs_091_check  # runs inherited 32-document navigation/link checks
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'custom_components/round_robin_hood/frontend/guides'
for lang in ('de','en'):
    folder=DOC/lang
    data=(folder/'search-index.js').read_text()
    assert data.startswith('window.RRH_GUIDE_SEARCH_INDEX=')
    index=json.loads(data.split('=',1)[1].strip().rstrip(';'))
    assert len(index)==16
    assert len({item['href'] for item in index})==16
    assert all(len(item['text'])>400 for item in index),lang
    assert any('Hysterese' in x['text'] if lang=='de' else 'hysteresis' in x['text'].lower() for x in index)
    for p in folder.glob('*.html'):
        h=p.read_text()
        assert 'search-index.js' in h and 'id="filter"' in h
        assert 'a[hidden]{display:none!important}' in h
        assert 'window.RRH_GUIDE_SEARCH_INDEX' in h
        assert 'id="search-status"' in h
    for page in ('setup','startup','dashboard','settings','installation'):
        md=(ROOT/f'docs/site/{lang}/{page}.md').read_text()
        assert len(md)>300,(lang,page)
        assert (folder/(page+'.html')).exists()
print('PASS 32 guide pages, two full-text indices, offline CSS/JS/navigation')
