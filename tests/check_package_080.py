"""Check v0.8.0 release ZIP and compare strictly against shipped v0.7.1 runtime."""
from __future__ import annotations
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile
from PIL import Image

PREFIX='custom_components/round_robin_hood/'
FILES_CHANGED={PREFIX+name for name in (
    'const.py','manifest.json','model.py','controller.py','runtime.py','websocket.py','frontend/panel.js')}


def files_in_zip(path:Path):
    with ZipFile(path) as z:
        assert z.testzip() is None, 'Corrupt ZIP archive'
        records=[item for item in z.infolist() if not item.is_dir()]
        names=[item.filename for item in records]
        assert len(names)==len(set(names)), 'Duplicate archive entries'
        for item in records:
            name=item.filename
            assert not Path(name).is_absolute() and '..' not in Path(name).parts, name
            assert not (set(Path(name).parts)&{'__pycache__','.pytest_cache','.git','test-results'}), name
            assert not name.endswith(('.pyc','.pyo')), name
            assert ((item.external_attr >> 16) & 0o170000) != 0o120000, 'Symlink not allowed'
        return {name:z.read(name) for name in names}


def check_package(release:Path,baseline:Path):
    files=files_in_zip(release)
    assert files['VERSION'].decode().strip()=='0.8.0'
    manifest=json.loads(files[PREFIX+'manifest.json']); assert manifest['version']=='0.8.0'
    assert manifest['domain']=='round_robin_hood' and manifest['config_flow'] is True
    assert 'VERSION = "0.8.0"' in files[PREFIX+'const.py'].decode()
    assert 'const VERSION = "0.8.0";' in files[PREFIX+'frontend/panel.js'].decode()
    assert 'STORAGE_VERSION = 1' in files[PREFIX+'const.py'].decode()
    assert 'API_VERSION = 1' in files[PREFIX+'const.py'].decode()
    assert 'brand.png?v=0.8.0' in files[PREFIX+'frontend/panel.js'].decode()
    assert 'async def async_setup_entry' in files[PREFIX+'__init__.py'].decode() and 'panel_custom.async_register_panel' in files[PREFIX+'__init__.py'].decode()
    for name in files:
        if name.startswith('custom_components/'):
            assert name.startswith(PREFIX),name
        if name.endswith('.json'): json.loads(files[name])
    for require in ['README.md','CHANGELOG.md','docs/UPDATE_0.8.0.md','docs/TEST_REPORT_0.8.0.md',
                    'tests/test_release_080.py','tests/release_080_browser_check.py',
                    'tests/upgrade_080_check.py','tests/check_package_080.py','docs/site/de/index.md',
                    'docs/site/en/index.md','mkdocs.yml',PREFIX+'brand/icon.png',PREFIX+'brand/icon@2x.png',PREFIX+'brand/logo.png']:
        assert require in files, f'Missing file: {require}'
    expected_hashes={}
    for line in files['SHA256SUMS'].decode().splitlines():
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
        assert m, 'Invalid hash inventory entry'
        digest,name=m.groups()
        assert name not in expected_hashes, 'duplicate digest entry'
        expected_hashes[name]=digest
    assert set(expected_hashes)==set(files)-{'SHA256SUMS'},'Checksum inventory incomplete'
    for name,digest in expected_hashes.items():
        assert hashlib.sha256(files[name]).hexdigest()==digest, f'Hash mismatch {name}'
    with ZipFile(baseline) as z:
        assert z.testzip() is None
        old={name:z.read(name) for name in z.namelist() if name.startswith(PREFIX) and not name.endswith('/')}
    current={name:data for name,data in files.items() if name.startswith(PREFIX)}
    assert old.keys()==current.keys(),f'Runtime file set changed: {old.keys()^current.keys()}'
    changes={k for k in old if old[k]!=current[k]}
    assert changes==FILES_CHANGED, (changes,FILES_CHANGED)
    assert files[PREFIX+'__init__.py']==old[PREFIX+'__init__.py']
    assert files[PREFIX+'const.py'].decode().replace('0.8.0','0.7.1')==old[PREFIX+'const.py'].decode()
    other_new=json.loads(files[PREFIX+'manifest.json'])
    other_old=json.loads(old[PREFIX+'manifest.json'])
    other_new.pop('version');other_old.pop('version')
    assert other_new==other_old
    for name,n in [('icon.png',256),('icon@2x.png',512),('logo.png',512)]:
        with Image.open(BytesIO(current[PREFIX+'brand/'+name])) as img:
            assert img.format=='PNG' and img.size==(n,n)
    print(f'PASS v0.8.0 ZIP CRC, {len(files)} files, {len(expected_hashes)} SHA256 checks')
    print('PASS strict runtime diff from v0.7.1 (7 intended files); identity/API/storage schema and logo preserved')
    print('BASELINE_SHA256',hashlib.sha256(baseline.read_bytes()).hexdigest())
    print('ARCHIVE_SHA256',hashlib.sha256(release.read_bytes()).hexdigest())

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True)
    ap.add_argument('--archive',type=Path,required=True)
    args=ap.parse_args();check_package(args.archive,args.baseline)
