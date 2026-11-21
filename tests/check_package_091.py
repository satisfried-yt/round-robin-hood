"""Portable ZIP completeness, manifest identity and baseline comparison."""
from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile
import argparse, hashlib, json, re

P = 'custom_components/round_robin_hood/'

def entries(path):
    with ZipFile(path) as z:
        assert z.testzip() is None, 'Archive CRC failed'
        files={}
        for item in z.infolist():
            if item.is_dir(): continue
            name=item.filename
            assert name not in files, f'duplicate entry {name}'
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert not (set(Path(name).parts)&{'.git','__pycache__','test-results','.pytest_cache','site-build'})
            assert not name.endswith(('.pyc','.pyo'))
            assert ((item.external_attr >> 16) & 0o170000) != 0o120000, f'symlink {name}'
            files[name]=z.read(name)
        return files


def main(archive,baseline):
    f=entries(archive)
    old=entries(baseline)
    assert f['VERSION'].decode().strip()=='0.9.1'
    assert json.loads(f[P+'manifest.json'])['version']=='0.9.1'
    assert 'VERSION = "0.9.1"' in f[P+'const.py'].decode()
    assert 'const VERSION = "0.9.1"' in f[P+'frontend/panel.js'].decode()
    assert 'API_VERSION = 1' in f[P+'const.py'].decode()
    assert 'STORAGE_VERSION = 1' in f[P+'const.py'].decode()
    assert 'guide' in f[P+'__init__.py'].decode()
    for file in f:
        if file.startswith('custom_components/'):
            assert file.startswith(P)
        if file.endswith('.json'): json.loads(f[file])
        if file.startswith('/config/') or '.storage' in Path(file).parts:
            raise AssertionError(f'Live HA data included: {file}')
    required=['README.md','CHANGELOG.md','mkdocs.yml','docs/UPDATE_0.9.1.md','docs/TEST_REPORT_0.9.1.md',
            'tests/docs_091_check.py','tests/test_release_091.py','tests/release_091_browser_check.py','tests/upgrade_091_check.py',
            'tests/check_package_091.py',P+'brand/icon.png',P+'frontend/panel.js',P+'energy_sources.py']
    required += [f'{P}frontend/guides/{lang}/{name}.html' for lang in ('de','en') for name in ('index','settings','sensors','startup','troubleshooting','energy','profiles')]
    required += [f'docs/site/{lang}/{name}.md' for lang in ('de','en') for name in ('index','sensors','startup','troubleshooting')]
    for name in required: assert name in f,name
    checks={}
    for line in f['SHA256SUMS'].decode().splitlines():
        m=re.fullmatch(r'([a-f0-9]{64})  (.+)',line);assert m,line
        sha,name=m.groups();assert name not in checks,name;checks[name]=sha
    assert set(checks)==set(f)-{'SHA256SUMS'}
    for name,expected in checks.items():
        assert hashlib.sha256(f[name]).hexdigest()==expected,name
    base_runtime={k:v for k,v in old.items() if k.startswith(P)}
    new_runtime={k:v for k,v in f.items() if k.startswith(P)}
    removed=set(base_runtime)-set(new_runtime)
    assert not removed, f'No existing integration file may be lost: {removed}'
    changed=[k for k in base_runtime if new_runtime.get(k)!=base_runtime[k]]
    added=set(new_runtime)-set(base_runtime)
    permitted_modified={P+n for n in ('controller.py','model.py','runtime.py','__init__.py','const.py','manifest.json','frontend/panel.js')}
    assert set(changed).issubset(permitted_modified),changed
    assert set(added)=={P+'energy_sources.py'}|{f'{P}frontend/guides/{lang}/{name}.html' for lang in ('de','en') for name in ('index','installation','setup','dashboard','consumers','profiles','conditions','energy','settings','sensors','startup','troubleshooting','safety','faq','glossary','about')},sorted(added)
    assert base_runtime[P+'brand/icon.png']==new_runtime[P+'brand/icon.png'], 'Brand changed'
    before=json.loads(base_runtime[P+'manifest.json']);after=json.loads(new_runtime[P+'manifest.json'])
    del before['version'];del after['version'];assert before==after, 'Manifest changed beyond version'
    print('PASS ZIP CRC, manifest and checksums:',len(f),'files,',len(checks),'SHA256 entries')
    print('PASS baseline comparison: changed runtime',len(changed),'added',len(added),'no runtime files removed')
    print('SHA256 archive:',hashlib.sha256(archive.read_bytes()).hexdigest())

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    args=parser.parse_args();main(args.archive,args.baseline)
