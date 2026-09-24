#!/usr/bin/env python3
"""Add a deterministic, additive 'instance_id' field to every example in every
Npred JSON, per PARTE A of the decided-fixes spec.

instance_id = "<sent_ID>::<lemma>::<ordinal>"
ordinal is 1-based, computed across all examples of the SAME lemma that share
the same sent_ID, walking senses/examples in JSON file order (does not
reorder, does not touch sent_ID).
"""
import json
import glob
from collections import defaultdict

JSON_DIR = "jsons"


def process_file(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    lemma = doc.get("lemma") or doc.get("lemma_base")
    counts = defaultdict(int)
    n = 0
    for sense in doc.get("senses", []):
        for ex in sense.get("examples", []):
            sid = ex["sent_ID"]
            counts[sid] += 1
            ordinal = counts[sid]
            ex["instance_id"] = f"{sid}::{lemma}::{ordinal}"
            n += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return n


def main():
    total = 0
    ids = []
    for path in sorted(glob.glob(f"{JSON_DIR}/*.json")):
        if path.endswith("_manifest.json"):
            continue
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        lemma = doc.get("lemma") or doc.get("lemma_base")
        n = process_file(path)
        total += n
        # collect for uniqueness check
        with open(path, encoding="utf-8") as f:
            doc2 = json.load(f)
        for sense in doc2.get("senses", []):
            for ex in sense.get("examples", []):
                ids.append(ex["instance_id"])
    print(f"files processed, total examples = {total}")
    print(f"instance_ids collected = {len(ids)}")
    print(f"instance_ids unique = {len(set(ids))}")


if __name__ == "__main__":
    main()
