from pathlib import Path
from zipfile import ZipFile
import json,re,tempfile,subprocess,shutil,hashlib
base=Path('/mnt/data/round-robin-hood-0.7.1.zip');release=Path('/mnt/data/round-robin-hood-0.8.0.zip')
doc=Path(__file__).resolve().parents[1]/'docs/UPDATE_0.8.0.md'
cmds=re.findall(r'```sh\n(.*?)\n```',doc.read_text(),re.S)
assert len(cmds)==2
with tempfile.TemporaryDirectory() as temp:
    cfg=Path(temp)/'config';comp=cfg/'custom_components';comp.mkdir(parents=True);(cfg/'.storage').mkdir()
    with ZipFile(base) as archive:
        for i in archive.infolist():
            if i.filename.startswith('custom_components/round_robin_hood/') and not i.is_dir():
                p=cfg/i.filename;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.read(i))
    old=comp/'round_robin_hood'
    def dig(d):return {str(p.relative_to(d)):hashlib.sha256(p.read_bytes()).hexdigest() for p in d.rglob('*') if p.is_file()}
    before=dig(old)
    store=cfg/'.storage/round_robin_hood.rebuild_2026.state'; original=b'{"data":{"consumers":["unchanged"],"profiles":["standard"]}}';store.write_bytes(original)
    shutil.copy2(release,comp/release.name)
    for cmd,expected in zip(cmds,['0.8.0','0.7.1']):
        run=subprocess.run(['sh','-c',cmd.replace('/config',str(cfg))],cwd=cfg,capture_output=True,text=True)
        assert run.returncode==0, (run.stdout,run.stderr)
        assert json.loads((old/'manifest.json').read_text())['version']==expected
        if expected=='0.8.0':
            assert dig(cfg/'rrh_code_backup_0.7.1')==before
            assert (cfg/'rrh_storage_backup_0.7.1.json').read_bytes()==original
        else:
            assert dig(old)==before and store.read_bytes()==original
    print('PASS 0.7.1 -> 0.8.0 installation and rollback, code and storage byte-perfect')
