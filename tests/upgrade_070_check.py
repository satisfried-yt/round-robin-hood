"""Run the literally shipped shell upgrade and rollback against fake /config.

A temporary directory replaces /config for safety; no Home Assistant access.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASELINE=Path('/mnt/data/round-robin-hood-0.6.0(1).zip')
RELEASE=Path('/mnt/data/round-robin-hood-0.7.0.zip')
GUIDE=ROOT/'docs/UPDATE_0.7.0.md'
assert BASELINE.is_file() and RELEASE.is_file() and GUIDE.is_file()
commands=re.findall(r'```sh\n(.*?)\n```',GUIDE.read_text(),re.S)
assert len(commands)==2,len(commands)
assert all('/config' in s for s in commands)

def digest_tree(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}

with tempfile.TemporaryDirectory(prefix='rrh070-install-') as tmp:
    cfg=Path(tmp)/'config'
    components=cfg/'custom_components'
    components.mkdir(parents=True)
    (cfg/'.storage').mkdir()
    with zipfile.ZipFile(BASELINE) as src:
        for member in src.infolist():
            if member.filename.startswith('custom_components/round_robin_hood/') and not member.is_dir():
                target=cfg/member.filename
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(src.read(member))
    old=components/'round_robin_hood'
    assert json.loads((old/'manifest.json').read_text())['version']=='0.6.0'
    oldhash=digest_tree(old)
    storage=cfg/'.storage/round_robin_hood.rebuild_2026.state'
    # A deliberately distinct 0.6-style fixture including a live profile, consumers and statistics.
    fixture={'version':1,'key':'round_robin_hood.rebuild_2026.state',
             'data':{'config':{'grid_entity':'sensor.netz','consumers':[{'id':'test1','entity_id':'switch.heater','watts':800}],
                               'profiles':[{'id':'standard','name':'Standard'}]},
                     'statistics':{'totals':{'net_benefit_eur':12.31}},'fairness':{'credits':{'test1':100}}}}
    original=json.dumps(fixture,ensure_ascii=False,sort_keys=True).encode('utf-8')
    storage.write_bytes(original)
    shutil.copy2(RELEASE,components/RELEASE.name)
    for step,label in [(commands[0],'upgrade'),(commands[1],'rollback')]:
        rewritten=step.replace('/config',str(cfg))
        ran=subprocess.run(['sh','-c',rewritten],cwd=cfg,capture_output=True,text=True,timeout=20)
        assert ran.returncode==0,(label,ran.returncode,ran.stdout,ran.stderr)
        assert '"version"' in ran.stdout,(label,ran.stdout)
        expected='0.7.0' if label=='upgrade' else '0.6.0'
        assert json.loads((old/'manifest.json').read_text())['version']==expected
        if label=='upgrade':
            assert digest_tree(cfg/'rrh_code_backup_0.6.0')==oldhash
            assert (cfg/'rrh_storage_backup_0.6.0.json').read_bytes()==original
            print('PASS: exact documented v0.6→v0.7 command, staged code, version guards, code/storage backups')
        else:
            assert digest_tree(old)==oldhash
            assert storage.read_bytes()==original
            assert json.loads((cfg/'rrh_failed_code_0.7.0/manifest.json').read_text())['version']=='0.7.0'
            print('PASS: exact documented paired rollback; original code and .storage bytes restored')
print('PASS: isolated only; did not access /config or a Home Assistant instance')
