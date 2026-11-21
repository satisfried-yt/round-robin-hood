"""Verify 0.7.1 logo-only patch against shipped 0.7.0 baseline."""
import json
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OLD=Path('/mnt/data/round-robin-hood-0.7.0.zip')
NEW=Path('/mnt/data/round-robin-hood-0.7.1.zip')
assert NEW.is_file() and OLD.is_file()
with ZipFile(OLD) as a, ZipFile(NEW) as b:
    assert b.testzip() is None
    old={i.filename:a.read(i) for i in a.infolist() if not i.is_dir() and i.filename.startswith('custom_components/')}
    new={i.filename:b.read(i) for i in b.infolist() if not i.is_dir() and i.filename.startswith('custom_components/')}
    path='custom_components/round_robin_hood/'
    changed={key for key in old if key in new and old[key]!=new[key]}
    assert changed=={path+x for x in ('manifest.json','const.py','__init__.py','frontend/panel.js')},changed
    assert set(new)-set(old)=={path+'brand/'+x for x in ('icon.png','icon@2x.png','logo.png')}
    assert not (set(old)-set(new))
    assert json.loads(new[path+'manifest.json'])['version']=='0.7.1'
    assert 'brand.png?v=0.7.1' in new[path+'frontend/panel.js'].decode()
    assert '/{DOMAIN}/brand.png' in new[path+'__init__.py'].decode()
    for f,n in [('icon.png',256),('icon@2x.png',512),('logo.png',512)]:
        from io import BytesIO
        im=Image.open(BytesIO(new[path+'brand/'+f]));assert im.size==(n,n) and im.format=='PNG'
print('PASS 0.7.1 logo-only runtime diff, valid image sizes, HA brand files, header and resource path')
