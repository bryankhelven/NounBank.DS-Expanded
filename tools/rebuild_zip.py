#!/usr/bin/env python3
"""PARTE E — rebuild jsons/nounbank.ds_all_jsons.zip from exactly the 145
files listed in jsons/_manifest.json, preserving manifest order, with each
zip member byte-identical to the corresponding individual JSON file.
"""
import json
import zipfile
from pathlib import Path

JSON_DIR = Path("jsons")
MANIFEST = JSON_DIR / "_manifest.json"
ZIP_PATH = JSON_DIR / "nounbank.ds_all_jsons.zip"


def main():
    names = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(names) == 145, f"manifest has {len(names)} entries, expected 145"

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            path = JSON_DIR / name
            zf.write(path, arcname=name)

    # verify
    with zipfile.ZipFile(ZIP_PATH) as zf:
        bad = zf.testzip()
        assert bad is None, f"CRC failed for {bad}"
        members = zf.namelist()
        assert members == names, "zip member order/names diverge from manifest"
        total_instances = 0
        for name in members:
            with zf.open(name) as f:
                data = f.read()
            on_disk = (JSON_DIR / name).read_bytes()
            assert data == on_disk, f"{name} not byte-identical in zip"
            doc = json.loads(data)
            total_instances += sum(len(s["examples"]) for s in doc["senses"])

    print(f"ZIP_MEMBERS = {len(members)}")
    print(f"ZIP_INSTANCES = {total_instances}")
    print("ZIP_CRC = PASS")
    print("ZIP_BYTE_IDENTICAL = PASS")


if __name__ == "__main__":
    main()
