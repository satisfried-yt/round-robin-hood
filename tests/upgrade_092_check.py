"""Execute the documented install/rollback commands against a disposable HA filesystem."""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, re, shutil, subprocess, tempfile

BASE=Path('/mnt/data/round-robin-hood-0.9.1.zip')
RELEASE=Path('/mnt/data/round-robin-hood-0.9.2.zip')
DOC=Path(__file__).resolve().parents[1]/'docs/UPDATE_0.9.2.md'
blocks=re.findall(r'```sh\n(.*?)\n```',DOC.read_text(),re.S)
assert len(blocks)==2
with tempfile.TemporaryDirectory() as td:
    cfg=Path(td)/'config';comp=cfg/'custom_components';comp.mkdir(parents=True)
    (cfg/'.storage').mkdir()
    with ZipFile(BASE) as z:
        for entry in z.infolist():
            if entry.filename.startswith('custom_components/round_robin_hood/') and not entry.is_dir():
                file=cfg/entry.filename;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(z.read(entry))
    old=comp/'round_robin_hood'
    def digest(base):
        return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file()}
    before=digest(old)
    original=b'{"schema":1,"revision":19,"config":{"consumers":["test-fixture"]}}'
    store=cfg/'.storage/round_robin_hood.rebuild_2026.state';store.write_bytes(original)
    shutil.copyfile(RELEASE,comp/RELEASE.name)
    for script,version in zip(blocks,('0.9.2','0.9.1')):
        res=subprocess.run(['sh','-c',script.replace('/config',str(cfg))],cwd=cfg,capture_output=True,text=True)
        assert res.returncode==0,(res.stdout,res.stderr)
        assert json.loads((old/'manifest.json').read_text())['version']==version
        if version=='0.9.2':
            assert digest(cfg/'rrh_code_backup_0.9.1')==before
            assert (cfg/'rrh_storage_backup_0.9.1.json').read_bytes()==original
            assert (old/'frontend/guides/de/search-index.js').is_file()
            assert store.read_bytes()==original
        else:
            assert digest(old)==before
            assert store.read_bytes()==original
print('PASS isolated 0.9.1 -> 0.9.2 installation and full rollback; code and HA storage restored byte-identically')
