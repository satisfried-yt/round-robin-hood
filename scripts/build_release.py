#!/usr/bin/env python3
"""Build and verify RRH 0.9.3 archive from Git-tracked files only.

Includes SHA256SUMS inside ZIP and a separate ZIP .sha256 checksum.
No signature is generated or claimed.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.9.3"
BASENAME = f"round-robin-hood-{VERSION}"
NEEDED = {
    "VERSION", "LICENSE", "NOTICE", "README.md", "BRANDING.md",
    "hacs.json", "custom_components/round_robin_hood/manifest.json",
    "custom_components/round_robin_hood/brand/icon.png",
    "custom_components/round_robin_hood/frontend/panel.js",
}
DENIED_SUFFIXES = {".pem", ".p12", ".pfx", ".key", ".sig", ".pyc", ".pyo"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source():
    raw = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"])
    paths = sorted(v.decode("utf-8") for v in raw.split(b"\0") if v)
    if not NEEDED.issubset(paths):
        raise ValueError(f"Missing release files: {sorted(NEEDED - set(paths))}")
    result = {}
    for name in paths:
        path = ROOT / name
        if (not path.is_file() or path.is_symlink()
                or not path.resolve().is_relative_to(ROOT.resolve())):
            raise ValueError(f"Unsafe or missing file: {name}")
        if path.suffix.lower() in DENIED_SUFFIXES or path.name.startswith(".env"):
            raise ValueError(f"Private or build material in Git index: {name}")
        result[name] = path.read_bytes()
    if result["VERSION"].decode().strip() != VERSION:
        raise ValueError("VERSION mismatch")
    manifest = json.loads(result["custom_components/round_robin_hood/manifest.json"])
    if manifest.get("domain") != "round_robin_hood" or manifest.get("version") != VERSION:
        raise ValueError("Integration manifest mismatch")
    if json.loads(result["hacs.json"]).get("name") != "Round Robin Hood":
        raise ValueError("HACS metadata mismatch")
    return result


def put(z, name, data):
    info = ZipInfo(name, (2020, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = ZIP_DEFLATED
    z.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)


def build(dest):
    files = source()
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / f"{BASENAME}.zip"
    checks = "".join(f"{digest(data)}  {name}\n" for name, data in files.items())
    with ZipFile(zip_path, "w") as z:
        for name, data in files.items():
            put(z, name, data)
        put(z, "SHA256SUMS", checks.encode("utf-8"))
    (dest / f"{BASENAME}.sha256").write_text(
        f"{digest(zip_path.read_bytes())}  {zip_path.name}\n", encoding="utf-8")
    verify(zip_path)
    print(f"PASS: built {zip_path} ({len(files)} source members + SHA256SUMS)")
    return zip_path


def verify(path):
    with ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP CRC check failed")
        names = z.namelist()
        if len(set(names)) != len(names) or not NEEDED.issubset(names):
            raise ValueError("Missing or duplicated ZIP files")
        if "SHA256SUMS" not in names:
            raise ValueError("Internal checksum inventory missing")
        for name in names:
            if name.startswith("/") or ".." in Path(name).parts or "\\" in name:
                raise ValueError(f"Unsafe archive entry: {name}")
        expected = {}
        for line in z.read("SHA256SUMS").decode().splitlines():
            value, name = line.split("  ", 1)
            if name in expected or len(value) != 64:
                raise ValueError("Bad checksum inventory entry")
            expected[name] = value
        if set(expected) != set(names) - {"SHA256SUMS"}:
            raise ValueError("Checksum inventory differs from ZIP contents")
        for name, value in expected.items():
            if digest(z.read(name)) != value:
                raise ValueError(f"Source checksum mismatch: {name}")
    chk = path.with_suffix(".sha256")
    if chk.exists():
        expected, filename = chk.read_text().strip().split("  ", 1)
        if filename != path.name or expected != digest(path.read_bytes()):
            raise ValueError("Whole-ZIP checksum mismatch")
    print(f"PASS: verified {path.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        verify(args.verify)
    else:
        build(args.output_dir)


if __name__ == "__main__":
    main()
