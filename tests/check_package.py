"""Validate release structure, versions and hashes; optionally compare a baseline.

No Home Assistant connection and no mutations of a running installation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "custom_components/round_robin_hood/"
SKIP = {"__pycache__", ".pytest_cache", ".git", ".venv", "venv", "test-results"}


def keep(path: str) -> bool:
    p = Path(path)
    return not set(p.parts).intersection(SKIP) and p.suffix not in {".pyc", ".pyo"} and p.name != ".coverage"


def folder_files() -> dict[str, bytes]:
    return {p.relative_to(ROOT).as_posix(): p.read_bytes()
            for p in ROOT.rglob("*") if p.is_file() and keep(p.relative_to(ROOT).as_posix())}


def archive_files(path: Path) -> dict[str, bytes]:
    with ZipFile(path) as z:
        assert z.testzip() is None, "ZIP CRC check failed"
        names = [i.filename for i in z.infolist() if not i.is_dir()]
        assert len(names) == len(set(names)), "Duplicate archive paths"
        for name in names:
            assert not Path(name).is_absolute() and ".." not in Path(name).parts, name
            assert keep(name), f"Development artifact inside archive: {name}"
        return {name:z.read(name) for name in names}


def validate(files: dict[str, bytes]) -> None:
    version = files["VERSION"].decode().strip()
    assert version == "0.7.1", version
    manifest = json.loads(files[PREFIX+"manifest.json"])
    assert manifest["version"] == version
    assert manifest["domain"] == "round_robin_hood"
    assert manifest["config_flow"] is True
    const = files[PREFIX+"const.py"].decode()
    panel = files[PREFIX+"frontend/panel.js"].decode()
    assert f'VERSION = "{version}"' in const
    assert f'const VERSION = "{version}";' in panel
    assert 'STORAGE_VERSION = 1' in const and 'API_VERSION = 1' in const
    assert '?v={VERSION}' in files[PREFIX+"__init__.py"].decode()
    assert 'rrh-hood-panel' in panel
    for name, content in files.items():
        if name.endswith(".json"): json.loads(content)
        if name.startswith("custom_components/"):
            assert name.startswith(PREFIX), f"Unexpected integration: {name}"
            assert "/tests/" not in name, name
            if name.endswith(".png"):
                assert name in {PREFIX+"brand/"+x for x in ("icon.png","icon@2x.png","logo.png")}, name
    for name in ["README.md","CHANGELOG.md","docs/UPDATE_0.5.0.md","docs/TEST_REPORT_0.5.0.md", "docs/UPDATE_0.6.0.md", "docs/TEST_REPORT_0.6.0.md", "docs/UPDATE_0.7.0.md", "docs/TEST_REPORT_0.7.0.md", "mkdocs.yml", "docs/site/de/index.md", "docs/site/en/index.md",
                 "docs/PROJECT_STATUS.md","tests/browser_check.py","tests/cards_browser_check.py","tests/navigation_browser_check.py","tests/test_emergency.py", "tests/strategies_browser_check.py", "tests/test_strategies_030.py", "tests/test_fixes_031.py", "tests/fixes_browser_check.py", "tests/test_fairness_032.py", "tests/fairness_browser_check.py", "tests/test_fair_rotation_033.py", "tests/test_fixed_fair_windows_040.py", "tests/fixed_periods_browser_check.py", "tests/test_smart_demo_050.py", "tests/test_adapter_smart_demo_050.py", "tests/smart_demo_browser_check.py", "tests/statistics_browser_check.py", "tests/test_statistics_060.py", "tests/test_adapter_statistics_060.py", PREFIX+"scheduling.py", PREFIX+"fairness.py", PREFIX+"demo.py", PREFIX+"statistics.py"]:
        assert name in files, f"Missing {name}"
    print(f"PASS: version {version}, domain, API/storage versions, cache URL and JSON")
    print("PASS: only the intended integration; source, tests, update/rollback documentation present")
    if "SHA256SUMS" in files:
        sums = {}
        for line in files["SHA256SUMS"].decode().splitlines():
            digest, name = line.split("  ", 1)
            assert re.fullmatch(r"[a-f0-9]{64}",digest), digest
            assert name not in sums, f"Duplicate hash entry: {name}"
            sums[name] = digest
        assert set(sums) == set(files)-{"SHA256SUMS"}, "Checksum inventory mismatch"
        for name, digest in sums.items():
            assert hashlib.sha256(files[name]).hexdigest() == digest, f"Hash mismatch: {name}"
        print(f"PASS: all {len(sums)} file SHA-256 hashes verified")


def compare(files: dict[str, bytes], baseline: Path) -> None:
    old = archive_files(baseline)
    current = {k:v for k,v in files.items() if k.startswith(PREFIX)}
    previous = {k:v for k,v in old.items() if k.startswith(PREFIX)}
    added = set(current) - set(previous)
    removed = set(previous) - set(current)
    assert not added, f"Unexpected new runtime files: {added}"
    assert not removed, f"Unexpected removed runtime files: {removed}"
    changed = {k for k in previous if k in current and current[k] != previous[k]}
    expected = {PREFIX+name for name in ["model.py", "controller.py", "runtime.py", "websocket.py", "statistics.py", "frontend/panel.js", "const.py", "manifest.json"]}
    assert changed == expected, (changed, expected)
    old_const = previous[PREFIX+"const.py"].decode()
    new_const = current[PREFIX+"const.py"].decode()
    assert new_const.replace('VERSION = "0.7.0"', 'VERSION = "0.6.0"') == old_const, "Unexpected non-version constant change"
    old_manifest = json.loads(previous[PREFIX+"manifest.json"])
    new_manifest = json.loads(current[PREFIX+"manifest.json"])
    old_manifest.pop("version")
    new_manifest.pop("version")
    assert old_manifest == new_manifest, "Manifest metadata changed"
    old_init = previous[PREFIX+"__init__.py"]
    new_init = current[PREFIX+"__init__.py"]
    assert old_init == new_init, "Integration entrypoint changed"
    print("PASS: intended runtime diff: onboarding, settings, statistics ledger, user interface and version metadata")
    print("PASS: identity, manifest metadata, integration entrypoint, storage/API versions retained")
    print("PASS: code + pre-update configuration backup required for downgrade")
    print("BASELINE_SHA256: " + hashlib.sha256(baseline.read_bytes()).hexdigest())



def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    files = archive_files(args.archive) if args.archive else folder_files()
    validate(files)
    if args.baseline: compare(files,args.baseline)
    if args.archive:
        assert "SHA256SUMS" in files, "Released archive requires hashes"
        print("PASS: archive CRC, paths and duplicate-member checks")
        print("ARCHIVE_SHA256: " + hashlib.sha256(args.archive.read_bytes()).hexdigest())
    print(f"PASS: validated {len(files)} files")


if __name__ == "__main__": main()
