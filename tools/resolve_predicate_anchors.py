#!/usr/bin/env python3
"""Resolver/reproducer for tools/predicate_anchor_resolutions.json.

Produces the 236-entry fallback-anchor cache that the site renderer and the
REL audit consult for instances with no exact `predicate` anchor in the
JSON, using the DANTEStocks legacy CoNLL-U corpus as authority. The cache
itself is a committed, versioned artifact (see tools/predicate_anchor_cache.py)
so that consuming it never requires this script or the legacy corpus to be
present; this script is only needed to REGENERATE or RE-VERIFY it.

This script NEVER writes to jsons/*.json - it only produces the tooling-side
resolution cache; anchor resolution here is purely a visual recovery layer.

Never guesses, never silently degrades:
  - instance_id must parse strictly as "<sent_ID>::<lemma>::<ordinal>" with
    ordinal a base-10 integer >= 1. A malformed ordinal is a hard failure,
    never a silent default to 1.
  - ordinal must satisfy 1 <= ordinal <= len(candidates) exactly. It is
    never clamped to the nearest valid index.
  - text search proceeds strictly forward from the shared per-group cursor.
    If the expected occurrence does not exist at/after the cursor, that is
    a hard failure - the cursor is never rewound to search earlier in the
    text, since that can resurrect an earlier instance's occurrence.
  - any hard failure aborts the run before writing any output file: this
    script is all-or-nothing, never partial.

Algorithm:
  1. Parse sent_ID -> ordered list of (form, lemma) tokens from the legacy
     CoNLL-U corpus (train+dev+test), skipping multiword-range lines.
  2. For every residual instance (lemma, sent_ID, instance_id), collect all
     tokens in that sentence whose LEMMA matches the Npred lemma
     (accent/case-insensitive), in textual (token id) order.
  3. Assign per ordinal from instance_id (`...::N` -> the Nth such token).
  4. Take that token's FORM (the real inflected/typo'd surface form, not the
     lemma) and locate it in example.text using, in order: EXACT_SURFACE,
     CASE_INSENSITIVE, UNICODE_ACCENT_INSENSITIVE. These are the only
     automatic strategies: the corpus has zero attested cases needing
     anything more tolerant than that.
  5. A single known instance (a ticker glued directly to the REL word with
     no space, e.g. "#petr4Recompra") is resolved via an explicit,
     instance_id-keyed adjudication ledger
     (tools/predicate_anchor_adjudications.tsv), never a generic
     ticker-merge regex. Any future case shaped like it is a hard failure
     until it, too, is adjudicated explicitly.
  6. The output cache is schema-versioned and binds itself to the exact
     legacy corpus files and JSON text that produced it; see
     tools/predicate_anchor_cache.py for the consumer-side validation.

Before overwriting a previously-committed cache, this script always
compares the freshly-computed entries against it and reports
ANCHOR_ASSIGNMENTS_CHANGED - a non-zero count is not blocked automatically
(a deliberate correction may legitimately change assignments) but is always
surfaced loudly, never silent.
"""
import argparse
import csv
import glob
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from predicate_anchor_cache import (  # noqa: E402
    SCHEMA_VERSION_SUPPORTED,
    PredicateAnchorCache,
    compute_authority_hashes,
    resolve_corpus_dir,
    sha256_text,
)

JSON_DIR = Path("jsons")
OUT_RESOLUTIONS = Path("tools/predicate_anchor_resolutions.json")
OUT_RESIDUAL = Path("tools/predicate_anchor_residuals_after_legacy.tsv")
ADJUDICATIONS_PATH = Path("tools/predicate_anchor_adjudications.tsv")


class HardFailure(RuntimeError):
    pass


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm_lemma(s: str) -> str:
    return strip_accents((s or "").strip()).lower()


def parse_ordinal_strict(instance_id: str) -> int:
    """Strict instance_id parsing: no silent default, no clamp."""
    parts = instance_id.rsplit("::", 1)
    if len(parts) != 2:
        raise HardFailure(f"malformed instance_id (no '::'): {instance_id!r}")
    tail = parts[1]
    if not tail.isdigit():
        raise HardFailure(f"non-integer ordinal in instance_id: {instance_id!r}")
    ordinal = int(tail)
    if ordinal < 1:
        raise HardFailure(f"ordinal < 1 in instance_id: {instance_id!r}")
    return ordinal


# ---------- CoNLL-U parsing ----------
def parse_feats(misc_or_feats):
    d = {}
    if not misc_or_feats or misc_or_feats == "_":
        return d
    for kv in misc_or_feats.split("|"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            d[k] = v
    return d


def parse_conllu(path, source_name):
    """Return dict sent_id -> list of token dicts with keys:
    id, form, lemma, head, deprel, feats(dict), misc(dict), source."""
    sentences = {}
    sent_id = None
    tokens = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("# sent_id"):
                if sent_id is not None:
                    sentences[sent_id] = tokens
                sent_id = line.split("=", 1)[1].strip()
                tokens = []
            elif line.startswith("#"):
                continue
            elif not line.strip():
                continue
            else:
                cols = line.split("\t")
                if len(cols) < 10:
                    continue
                tid = cols[0]
                if "-" in tid or "." in tid:
                    continue  # multiword range / empty node
                try:
                    tid_i = int(tid)
                except ValueError:
                    continue
                form, lemma = cols[1], cols[2]
                head = cols[6]
                deprel = cols[7]
                feats = parse_feats(cols[5])
                misc = parse_feats(cols[9])
                tokens.append(
                    {
                        "id": tid_i,
                        "form": form,
                        "lemma": lemma,
                        "head": head,
                        "deprel": deprel,
                        "feats": feats,
                        "misc": misc,
                        "source": source_name,
                    }
                )
        if sent_id is not None:
            sentences[sent_id] = tokens
    return sentences


def load_corpus(corpus_dir):
    """Requires the DANTEStocks legacy corpus - this is the resolver, not
    the renderer. Fails loudly and explains how to provide it."""
    from predicate_anchor_cache import corpus_files

    files = corpus_files(corpus_dir)
    missing = [str(p) for p in files.values() if not p.exists()]
    if missing:
        raise HardFailure(
            "DANTEStocks legacy corpus not found at "
            f"{corpus_dir}: missing {missing}. Provide it with --corpus-dir "
            "PATH, or set the NOUNBANK_DS_DANTE_LEGACY_DIR environment "
            "variable to the directory containing DANTEStocks-{train,dev,test}.conllu."
        )
    all_sents = {}
    for name, path in files.items():
        all_sents.update(parse_conllu(path, name))
    return all_sents


def load_adjudications():
    """instance_id -> adjudication row. Explicit, instance_id-keyed
    overrides only - never a generic pattern."""
    if not ADJUDICATIONS_PATH.exists():
        return {}
    rows = {}
    with open(ADJUDICATIONS_PATH, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rows[row["instance_id"]] = row
    return rows


# ---------- text alignment strategies ----------
# All strategies are word-boundary safe (never match a substring embedded
# inside a larger token, e.g. the "d" in "@Adriano3Luis") and honor a
# `start` cursor so multi-occurrence groups are matched in strict textual
# order without colliding on an earlier occurrence. Only the three
# automatic strategies attested in the current corpus (232 + 2 + 1 = 235 of
# the 236 fallback cases) are implemented; the 236th (ticker-merge) is an
# explicit adjudication, not an automatic strategy.
def _boundary_pattern(core_pattern):
    return re.compile(rf"(?<![#\w])({core_pattern})(?!\w)")


def find_exact(text, form, start):
    pat = _boundary_pattern(re.escape(form))
    m = pat.search(text, start)
    return (m.start(1), m.end(1)) if m else None


def find_case_insensitive(text, form, start):
    pat = re.compile(_boundary_pattern(re.escape(form)).pattern, re.IGNORECASE)
    m = pat.search(text, start)
    return (m.start(1), m.end(1)) if m else None


def find_accent_insensitive(text, form, start):
    ntext = strip_accents(text)
    nform = strip_accents(form)
    pat = _boundary_pattern(re.escape(nform))
    m = re.compile(pat.pattern, re.IGNORECASE).search(ntext, start)
    return (m.start(1), m.end(1)) if m else None


STRATEGIES = [
    ("EXACT_SURFACE", find_exact),
    ("CASE_INSENSITIVE", find_case_insensitive),
    ("UNICODE_ACCENT_INSENSITIVE", find_accent_insensitive),
]


def resolve_span(text, form, start):
    """Strictly forward from `start`. Never retries from the beginning of
    the text - see module docstring."""
    for name, fn in STRATEGIES:
        span = fn(text, form, start)
        if span:
            return span, name
    return None, None


def find_candidate_forms(tokens, nlemma):
    """Return a list of dicts (in textual/token-id order) describing every
    candidate occurrence of a Npred lemma in a sentence's token list:
      {"form": ..., "route": LEMMA|ABBREVIATION_FULLFORM|COMPOUND,
       "legacy_token_id": ..., "legacy_source_file": ...}
    """
    candidates = []
    for t in tokens:
        if norm_lemma(t["lemma"]) == nlemma:
            candidates.append((t["id"], t["form"], "LEMMA", t["id"], t["source"]))
            continue
        full_form = t["feats"].get("FullForm") or t["misc"].get("FullForm")
        if full_form and norm_lemma(full_form) == nlemma:
            candidates.append((t["id"], t["form"], "ABBREVIATION_FULLFORM", t["id"], t["source"]))

    if not candidates:
        by_id = sorted(tokens, key=lambda t: t["id"])
        for i in range(len(by_id) - 1):
            a, b = by_id[i], by_id[i + 1]
            if b["id"] != a["id"] + 1:
                continue
            concat = norm_lemma(a["lemma"]) + norm_lemma(b["lemma"])
            if concat == nlemma:
                candidates.append((a["id"], f'{a["form"]} {b["form"]}', "COMPOUND", a["id"], a["source"]))

    candidates.sort(key=lambda c: c[0])
    return [
        {"form": form, "route": route, "legacy_token_id": tok_id, "legacy_source_file": src}
        for _, form, route, tok_id, src in candidates
    ]


def load_committed_entries():
    """The previously-committed cache's entries, for the before/after
    reproducibility comparison. Only ever read via the same local-validation
    path everything else uses - never trusted blindly."""
    if not OUT_RESOLUTIONS.exists():
        return {}
    try:
        cache = PredicateAnchorCache(OUT_RESOLUTIONS)
    except Exception:
        return {}
    return dict(cache.entries())


def compare_assignments(old_entries, new_entries):
    """Compare only the anchor identity (form, char_start, char_end) per
    instance_id - provenance/method bookkeeping can be enriched over time
    without that counting as an assignment change."""
    changed = []
    for iid, new in new_entries.items():
        old = old_entries.get(iid)
        if old is None:
            continue  # newly resolved, not a change to an existing assignment
        old_key = (old.get("form"), old.get("char_start"), old.get("char_end"))
        new_key = (new.get("form"), new.get("char_start"), new.get("char_end"))
        if old_key != new_key:
            changed.append((iid, old_key, new_key))
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--corpus-dir",
        metavar="PATH",
        help="Directory containing DANTEStocks-{train,dev,test}.conllu. "
        "Falls back to NOUNBANK_DS_DANTE_LEGACY_DIR, then to a local "
        "development-convenience default. Required in practice - this "
        "script cannot run without the legacy corpus.",
    )
    args = ap.parse_args()

    corpus_dir = resolve_corpus_dir(args.corpus_dir)
    sentences = load_corpus(corpus_dir)
    authority_hashes = compute_authority_hashes(corpus_dir)
    adjudications = load_adjudications()
    old_entries = load_committed_entries()

    entries = {}
    residual_rows = []
    n_resolved = 0
    n_total = 0

    for path in sorted(glob.glob(str(JSON_DIR / "*.json"))):
        if path.endswith("_manifest.json"):
            continue
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        lemma = doc.get("lemma") or doc.get("lemma_base")
        nlemma = norm_lemma(lemma)

        groups = defaultdict(list)
        for sense in doc["senses"]:
            for ex in sense["examples"]:
                groups[ex["sent_ID"]].append(ex)

        for sid, exs in groups.items():
            # Process the whole sent_ID group left-to-right with a shared
            # cursor so multiple instances of the same lemma never collide
            # on the same occurrence, and so an already-anchored instance's
            # span reserves its slot for the still-missing ones.
            exs_sorted = sorted(exs, key=lambda ex: parse_ordinal_strict(ex["instance_id"]))
            toks = sentences.get(sid, [])
            cand_forms = find_candidate_forms(toks, nlemma)
            cursor = 0

            for ex in exs_sorted:
                existing = ex.get("predicate")
                if existing:
                    cursor = max(cursor, existing.get("char_end", 0))
                    continue  # already anchored exactly, do not touch

                n_total += 1
                iid = ex["instance_id"]
                text = ex.get("text") or ""

                adj = adjudications.get(iid)
                if adj:
                    start, end = int(adj["char_start"]), int(adj["char_end"])
                    form = text[start:end]
                    if form != adj["legacy_form"]:
                        raise HardFailure(
                            f"{iid}: adjudicated span does not match current text "
                            f"(expected {adj['legacy_form']!r}, got {form!r})"
                        )
                    cursor = max(cursor, end)
                    entries[iid] = {
                        "sent_ID": sid,
                        "lemma": lemma,
                        "ordinal": parse_ordinal_strict(iid),
                        "legacy_source_file": adj["legacy_source_file"],
                        "legacy_token_id": int(adj["legacy_token_id"]),
                        "legacy_form": adj["legacy_form"],
                        "candidate_route": "ADJUDICATED",
                        "form": form,
                        "char_start": start,
                        "char_end": end,
                        "text_sha256": sha256_text(text),
                        "method": "ADJUDICATED_" + adj["reason"],
                    }
                    n_resolved += 1
                    continue

                ordinal = parse_ordinal_strict(iid)

                if not cand_forms:
                    residual_rows.append((lemma, sid, iid, "no-lemma-token-in-legacy-conllu"))
                    continue

                if ordinal < 1 or ordinal > len(cand_forms):
                    raise HardFailure(
                        f"{iid}: ordinal {ordinal} out of range for "
                        f"{len(cand_forms)} legacy candidate(s) in sent_ID {sid!r}"
                    )
                cand = cand_forms[ordinal - 1]
                form = cand["form"]

                span, method = resolve_span(text, form, cursor)
                if span is None:
                    # A cursor-forward miss on a legacy-attested candidate is
                    # a hard failure, not a residual to shrug off - it means
                    # the bookkeeping between legacy candidate order and
                    # JSON instance order has broken down for this group,
                    # and guessing (by rewinding the cursor) risks reusing a
                    # prior instance's occurrence.
                    raise HardFailure(
                        f"{iid}: legacy form {form!r} not found at/after cursor={cursor} "
                        f"in text (sent_ID {sid!r})"
                    )

                start, end = span
                cursor = end
                entries[iid] = {
                    "sent_ID": sid,
                    "lemma": lemma,
                    "ordinal": ordinal,
                    "legacy_source_file": cand["legacy_source_file"],
                    "legacy_token_id": cand["legacy_token_id"],
                    "legacy_form": form,
                    "candidate_route": cand["route"],
                    "form": text[start:end],
                    "char_start": start,
                    "char_end": end,
                    "text_sha256": sha256_text(text),
                    "method": method,
                }
                n_resolved += 1

    if residual_rows:
        # Do not write a (necessarily incomplete/unreliable) cache when
        # anything is unresolved: PREDICATE_ANCHOR_UNRESOLVED must be 0 for
        # the cache to be trustworthy at all.
        with open(OUT_RESIDUAL, "w", encoding="utf-8") as f:
            f.write("lemma\tsent_ID\tinstance_id\treason\n")
            for row in residual_rows:
                f.write("\t".join(row) + "\n")
        raise HardFailure(
            f"{len(residual_rows)} instance(s) unresolved - see {OUT_RESIDUAL}; "
            "cache NOT written"
        )

    # Zero residuals: still (re)write the file, empty, so the artifact
    # unambiguously reports 0 rather than going stale/missing.
    with open(OUT_RESIDUAL, "w", encoding="utf-8") as f:
        f.write("lemma\tsent_ID\tinstance_id\treason\n")

    changed = compare_assignments(old_entries, entries)

    cache = {
        "schema_version": SCHEMA_VERSION_SUPPORTED,
        "authority": {f"{k}_sha256": v for k, v in authority_hashes.items()},
        "entries": entries,
    }
    OUT_RESOLUTIONS.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"corpus_dir = {corpus_dir}")
    print(f"instances needing legacy resolution = {n_total}")
    print(f"resolved via legacy authority = {n_resolved}")
    print(f"still unresolved = {len(residual_rows)}")
    print(f"cache entries written = {len(entries)}")
    print(f"resolutions written to {OUT_RESOLUTIONS}")
    print(f"unresolved residual written to {OUT_RESIDUAL}")
    print(f"previously-committed entries compared = {len(old_entries)}")
    print(f"ANCHOR_ASSIGNMENTS_CHANGED = {len(changed)}")
    for iid, old_key, new_key in changed:
        print(f"  CHANGED {iid}: {old_key} -> {new_key}")


if __name__ == "__main__":
    main()
