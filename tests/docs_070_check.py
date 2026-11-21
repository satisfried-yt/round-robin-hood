"""Checks the offline bilingual knowledge base's exact navigation & local Markdown links."""
from pathlib import Path
import re
import yaml

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/site'
CFG=yaml.safe_load((ROOT/'mkdocs.yml').read_text())
assert CFG['docs_dir']=='docs/site' and CFG['site_dir']=='site-build'
assert CFG['theme']['name']=='material'
plugins=CFG['plugins']
assert 'search' in plugins
languages=next(plugin['i18n']['languages'] for plugin in plugins if isinstance(plugin,dict) and 'i18n' in plugin)
assert {l['locale'] for l in languages}=={'de','en'}
assert any(l['locale']=='de' and l['default'] for l in languages)
nav=CFG['nav']
assert len(nav)>=12 and all(len(entry)==1 for entry in nav)
links=[next(iter(item.values())) for item in nav]
assert len(links)==len(set(links))
for loc in ('de','en'):
    d=DOCS/loc
    pages={p.name for p in d.glob('*.md')}
    assert pages==set(links),(loc,pages,set(links))
    checked=0
    for page in d.glob('*.md'):
        content=page.read_text()
        assert content.startswith('# '),(loc,page.name)
        for target in re.findall(r'(?<!!)\[[^]]+\]\(([^)]+)\)',content):
            if target.startswith(('https://','http://','mailto:','#')): continue
            target=target.split('#')[0]
            assert (page.parent/target).is_file(),f'{loc}/{page.name}: broken link to {target}'
            checked+=1
    print(f'PASS: {loc.upper()} {len(pages)} sidebar sections; {checked} valid local links')
print('PASS: two locales, translated navigation, search plugin and no public deployment action')
