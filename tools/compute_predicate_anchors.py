#!/usr/bin/env python3
"""PARTE B2 — compute predicate (REL) character-offset anchors per instance.

For every example, tries to locate the exact occurrence of the predicate
lemma that corresponds to that specific instance (distinguishing multiple
instances that share the same sent_ID). Never fabricates an offset: an
anchor is written to the JSON ("predicate": {form, char_start, char_end})
only when it can be derived from evidence in the stored text. Cases that
can't be resolved safely are left without an anchor and reported as
residuals (--report) instead of guessed.

Evidence used:
  1. Surface forms already marked with class="rel" in the existing
     site_pages/<lemma>.html (attested inflected forms actually seen in the
     corpus).
  2. The lemma itself, plus heuristic PT plural candidates (tools/pt_pluralize.py) —
     only accepted if the resulting string is literally found in the text.

Disambiguation across multiple instances sharing one sent_ID: JSON example
order is assumed to mirror left-to-right order of occurrence in the text
(the ordinal used for instance_id in PARTE A makes the same assumption).
  - group size == number of found candidate-form matches -> assign in order
    (exact, safe).
  - group size == 1 and >=1 matches -> take the first (leftmost) match,
    consistent with the legacy renderer's historically-validated behavior
    for the singleton case.
  - group size == 1 and 0 matches -> residual: REL not found in stored text
    (commonly a truncated tweet) — no anchor written.
  - group size > 1 and match count != group size -> residual: ambiguous,
    no anchor written for that group.
"""
import json
import re
import glob
import html as htmllib
from collections import defaultdict

from pt_pluralize import pluralize

JSON_DIR = "jsons"
SITE_DIR = "site_pages"

REL_SPAN_RE = re.compile(r'<span class="rel">([^<]*)</span>')


def attested_forms(lemma):
    path = f"{SITE_DIR}/{lemma}.html"
    forms = set()
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for m in REL_SPAN_RE.finditer(content):
            forms.add(htmllib.unescape(m.group(1)))
    except FileNotFoundError:
        pass
    return forms


def boundary_pattern(phrase):
    core = re.escape(phrase)
    return re.compile(rf"(?<![#\w])({core})(?!\w)", re.IGNORECASE)


def find_matches(text, forms):
    spans = []
    for form in forms:
        if not form:
            continue
        for m in boundary_pattern(form).finditer(text):
            spans.append((m.start(), m.end(), m.group(1)))
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    chosen = []
    occupied = [False] * (len(text) + 1)
    for start, end, form in spans:
        if any(occupied[start:end]):
            continue
        chosen.append((start, end, form))
        for i in range(start, end):
            occupied[i] = True
    chosen.sort(key=lambda s: s[0])
    return chosen


def process_file(path, report):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    lemma = doc.get("lemma") or doc.get("lemma_base")
    forms = attested_forms(lemma)
    forms.add(lemma)
    forms.add(lemma.capitalize())
    for p in pluralize(lemma):
        forms.add(p)
        forms.add(p.capitalize())

    groups = defaultdict(list)
    for sense in doc["senses"]:
        for ex in sense["examples"]:
            groups[ex["sent_ID"]].append(ex)

    n_anchored = 0
    n_total = 0
    for sid, exs in groups.items():
        n_total += len(exs)
        text = exs[0]["text"]
        matches = find_matches(text, forms)
        if len(exs) == 1:
            ex = exs[0]
            if matches:
                start, end, form = matches[0]
                ex["predicate"] = {"form": form, "char_start": start, "char_end": end}
                assert text[start:end] == form
                n_anchored += 1
            else:
                report.append((lemma, sid, ex["instance_id"], "no-match-in-text"))
        else:
            if len(matches) == len(exs):
                for ex, (start, end, form) in zip(exs, matches):
                    ex["predicate"] = {"form": form, "char_start": start, "char_end": end}
                    assert text[start:end] == form
                    n_anchored += 1
            else:
                for ex in exs:
                    report.append(
                        (
                            lemma,
                            sid,
                            ex["instance_id"],
                            f"count-mismatch found={len(matches)} need={len(exs)}",
                        )
                    )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return n_total, n_anchored


def main():
    report = []
    total = 0
    anchored = 0
    for path in sorted(glob.glob(f"{JSON_DIR}/*.json")):
        if path.endswith("_manifest.json"):
            continue
        t, a = process_file(path, report)
        total += t
        anchored += a
    print(f"total instances = {total}")
    print(f"anchored = {anchored}")
    print(f"residual (no anchor) = {total - anchored}")
    with open("tools/predicate_anchor_residuals.tsv", "w", encoding="utf-8") as f:
        f.write("lemma\tsent_ID\tinstance_id\treason\n")
        for row in report:
            f.write("\t".join(row) + "\n")
    print(f"residual list written to tools/predicate_anchor_residuals.tsv ({len(report)} rows)")


if __name__ == "__main__":
    main()
