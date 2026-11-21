"""Validate v0.9.2 package identity, file safety, baseline diff and SHA256 inventory."""
from pathlib import Path
from zipfile import ZipFile
import argparse, hashlib, json, re
P='custom_components/round_robin_hood/'

def entries(path):
    with ZipFile(path) as z:
        assert z.testzip() is None,'ZIP CRC failed'
        data={}
        for item in z.infolist():
            if item.is_dir(): continue
            name=item.filename
            assert name not in data,f'duplicate: {name}'
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert not set(Path(name).parts)&{'.git','__pycache__','.storage','test-results','.pytest_cache','site-build'}
            assert not name.endswith(('.pyc','.pyo'))
            assert ((item.external_attr>>16)&0o170000)!=0o120000, f'symlink {name}'
            data[name]=z.read(name)
        return data

def main(archive,baseline):
    data=entries(archive);old=entries(baseline)
    assert data['VERSION'].decode().strip()=='0.9.2'
    assert json.loads(data[P+'manifest.json'])['version']=='0.9.2'
    assert 'VERSION = "0.9.2"' in data[P+'const.py'].decode()
    assert 'const VERSION = "0.9.2"' in data[P+'frontend/panel.js'].decode()
    assert 'API_VERSION = 1' in data[P+'const.py'].decode()
    assert 'STORAGE_VERSION = 1' in data[P+'const.py'].decode()
    for name,content in data.items():
        if name.startswith('custom_components/'):assert name.startswith(P)
        if name.endswith('.json'):json.loads(content)
        assert not name.startswith(('/config/','.storage/'))
    required=['README.md','CHANGELOG.md','mkdocs.yml','VERSION',
        'docs/UPDATE_0.9.2.md','docs/TEST_REPORT_0.9.2.md',
        'tests/release_092_browser_check.py','tests/test_release_092.py',
        'tests/docs_092_check.py','tests/check_package_092.py','tests/upgrade_092_check.py',
        P+'frontend/panel.js',P+'brand/icon.png']
    for lang in ('de','en'):
        required += [f'{P}frontend/guides/{lang}/search-index.js',
                     f'{P}frontend/guides/{lang}/index.html',
                     f'{P}frontend/guides/{lang}/setup.html',
                     f'{P}frontend/guides/{lang}/startup.html',
                     f'docs/site/{lang}/setup.md',f'docs/site/{lang}/startup.md']
    for n in required:assert n in data,n
    checks={}
    for line in data['SHA256SUMS'].decode().splitlines():
        m=re.fullmatch(r'([a-f0-9]{64})  (.+)',line);assert m,line
        sha,name=m.groups();assert name not in checks;checks[name]=sha
    assert set(checks)==set(data)-{'SHA256SUMS'}
    for name,expected in checks.items():assert hashlib.sha256(data[name]).hexdigest()==expected,name
    before={k:v for k,v in old.items() if k.startswith(P)}
    after={k:v for k,v in data.items() if k.startswith(P)}
    assert not set(before)-set(after),f'Removed integration files: {set(before)-set(after)}'
    modified={n for n in before if n in after and before[n]!=after[n]}
    added=set(after)-set(before)
    allowed_changed={P+n for n in ('controller.py','const.py','manifest.json','frontend/panel.js')}
    allowed_changed|={f'{P}frontend/guides/{lang}/{name}.html' for lang in ('de','en') for name in ('index','installation','setup','dashboard','consumers','profiles','conditions','energy','settings','sensors','startup','troubleshooting','safety','faq','glossary','about')}
    assert modified<=allowed_changed,modified-allowed_changed
    assert added=={f'{P}frontend/guides/{lang}/search-index.js' for lang in ('de','en')},added
    assert before[P+'brand/icon.png']==after[P+'brand/icon.png']
    manifest_a=json.loads(before[P+'manifest.json']);manifest_b=json.loads(after[P+'manifest.json']);
    manifest_a.pop('version');manifest_b.pop('version');assert manifest_a==manifest_b
    print(f'PASS ZIP CRC, checksum manifest for {len(checks)} files, {len(data)} total entries')
    print(f'PASS baseline v0.9.1 diff: modified={len(modified)}, added={len(added)}, removed=0')
    print('SHA256 archive:',hashlib.sha256(archive.read_bytes()).hexdigest())

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True);parser.add_argument('--baseline',type=Path,required=True);args=parser.parse_args()
    main(args.archive,args.baseline)
