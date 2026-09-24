#!/usr/bin/env python3
"""Global audit of instance_id -> predicate{form,char_start,char_end} -> REL.

sent_ID identifies the TWEET, not the predicate occurrence. When a lemma has
more than one instance under the same sent_ID, each instance_id must point to
a distinct, correct lexical occurrence of the predicator in that tweet's
text. This script audits that invariant for every JSON instance in the
repository (not just the previously-known regression cases) and writes a
row-per-instance TSV plus a status summary.

READ-ONLY by default: prints the summary to stdout and writes no files.
Pass --output <path> to also write the row-per-instance TSV report to that
path. Pass --fix to write back deterministic corrections (collapsed/duplicate
spans inside a multi-instance group where an unambiguous non-overlapping
reassignment exists) and regenerate the affected site pages - this remains an
explicitly separate, opt-in operation from reporting.
Never guesses: AMBIGUOUS_REL cases are reported, not silently resolved.

Anchor source (consulted in this order, never guessed):
  JSON_PREDICATE_ANCHORED    - ex["predicate"] present and its offset matches
                               its own stored form.
  FALLBACK_PREDICATE_ANCHORED - no JSON predicate, but the schema-validated
                               legacy-authority cache
                               (tools/predicate_anchor_resolutions.json, via
                               tools/predicate_anchor_cache.py) has a binding,
                               validated entry for this instance_id.
  PREDICATE_ANCHOR_UNRESOLVED - neither source has a usable anchor. This is a
                               hard-failure-worthy state, not a cosmetic
                               category: the site renderer refuses to render
                               a row without a resolvable REL (see
                               tools/render_site_from_json.py). The old
                               TRUNCATED_REL/MISSING_REL distinction is
                               retired - it was scoped to the JSON predicate
                               field alone and is stale now that the fallback
                               cache exists.

Statuses (orthogonal to anchor source above):
  PASS_DISTINCT_REL      - group size N, N distinct correct occurrences, each
                            instance's anchor lands on its own occurrence and
                            (when it has realized Args) those Args are at
                            least as close to its own occurrence as to any
                            sibling occurrence in the same group.
  PASS_SAME_REL_JUSTIFIED - singleton group (nothing to disambiguate) with a
                            valid anchor.
  AMBIGUOUS_REL           - multi-instance group where the number of textual
                            candidate occurrences does not safely map 1:1 to
                            the number of instances, or where a realized Arg
                            sits strictly closer to a sibling's occurrence
                            than to its own assigned occurrence. Needs human
                            adjudication - never auto-resolved.
  WRONG_REL               - deterministic defect: two or more instances in
                            the same group collapsed onto the identical
                            (char_start, char_end) span, AND an unambiguous
                            non-overlapping reassignment exists (candidate
                            count == group size). Auto-fixable with --fix.
"""
import argparse
import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pt_pluralize import pluralize  # noqa: E402
from predicate_anchor_cache import load_cache  # noqa: E402

JSON_DIR = Path("jsons")
SITE_DIR = Path("site_pages")
ADJUDICATION_LEDGER = Path("tools/rel_instance_adjudications.tsv")

ARG_RE_CACHE = {}

PREDICATE_CACHE = load_cache()


def get_effective_predicate(ex, lemma, text):
    """Anchor authority for REL, consulted in the order the corpus actually
    supports it: the JSON `predicate` field first; when that is absent, the
    schema-validated legacy-authority fallback cache
    (tools/predicate_anchor_resolutions.json via predicate_anchor_cache.py).
    Returns (pred_dict_or_None, source) where source is one of
    "JSON_PREDICATE_ANCHORED", "FALLBACK_PREDICATE_ANCHORED", or None. Never
    guesses: an invalid/missing fallback entry yields (None, None), same as
    no anchor at all - it is NOT synthesized from scratch here."""
    pred = ex.get("predicate")
    if pred:
        return pred, "JSON_PREDICATE_ANCHORED"
    fb = PREDICATE_CACHE.get_validated(ex.get("instance_id"), ex.get("sent_ID"), lemma, text)
    if fb:
        return fb, "FALLBACK_PREDICATE_ANCHORED"
    return None, None


def load_adjudications(path=ADJUDICATION_LEDGER):
    """instance_id -> adjudication row (dict) from the human-reviewed ledger.

    The ledger is the sole source of per-instance overrides - no instance_id
    is ever hardcoded in the audit logic itself. Rows only ever *resolve* a
    heuristic AMBIGUOUS_REL/WRONG_REL flag to PASS_DISTINCT_REL; they never
    suppress the original heuristic evidence, which is preserved in the note.
    """
    if not path.exists():
        return {}
    rows = {}
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            fields = line.split("\t")
            row = dict(zip(header, fields))
            iid = row.get("instance_id")
            if iid:
                rows[iid] = row
    return rows


def candidate_forms(lemma, doc):
    """Return locally attested forms without consulting rendered HTML.

    The audit must not bootstrap its lexical candidates from the REL markup
    it is auditing. Forms therefore come only from the lemma/plural inventory
    and from already validated JSON/cache anchors in the source document.
    """
    forms = {lemma, lemma.capitalize()}
    for p in pluralize(lemma):
        forms.add(p)
        forms.add(p.capitalize())
    for sense in doc["senses"]:
        for ex in sense["examples"]:
            pred, _source = get_effective_predicate(ex, lemma, ex.get("text") or "")
            if pred:
                forms.add(pred["form"])
    return forms


def _boundary_pattern(form):
    return re.compile(rf"(?<![#\w])({re.escape(form)})(?!\w)", re.IGNORECASE)


def find_matches(text, forms):
    """Return left-to-right, non-overlapping literal candidate spans."""
    spans = []
    for form in forms:
        if not form:
            continue
        for match in _boundary_pattern(form).finditer(text):
            spans.append((match.start(1), match.end(1), match.group(1)))
    spans.sort(key=lambda span: (span[0], -(span[1] - span[0])))
    chosen = []
    occupied = [False] * len(text)
    for start, end, form in spans:
        if any(occupied[start:end]):
            continue
        chosen.append((start, end, form))
        for index in range(start, end):
            occupied[index] = True
    return chosen


def arg_positions(text, value):
    """All start positions of a literal Arg substring in text (word-ish
    boundary not enforced here since Arg spans are free phrases, not single
    lexical items - a plain literal search is what the renderer itself uses
    via highlight_once)."""
    if not value:
        return []
    positions = []
    start = 0
    while True:
        i = text.find(value, start)
        if i == -1:
            break
        positions.append(i)
        start = i + 1
    return positions


def min_distance_to_span(positions, value_len, span):
    """Minimal character gap between any Arg occurrence and a predicate
    span (0 if overlapping/adjacent)."""
    s, e = span
    best = None
    for p in positions:
        pe = p + value_len
        if pe <= s:
            d = s - pe
        elif p >= e:
            d = p - e
        else:
            d = 0
        if best is None or d < best:
            best = d
    return best


def load_docs():
    docs = {}
    for path in sorted(glob.glob(f"{JSON_DIR}/*.json")):
        if path.endswith("_manifest.json"):
            continue
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        lemma = doc.get("lemma") or doc.get("lemma_base")
        docs[lemma] = (Path(path), doc)
    return docs


def _apply_adjudications(rows, counts, adjudications):
    """Resolve AMBIGUOUS_REL/WRONG_REL rows that a human has adjudicated.

    Never invents a decision: only overrides a row whose instance_id has an
    explicit ledger entry, and only ever moves it to the adjudicated status
    the ledger records. The original heuristic status and note are preserved
    (prefixed into the note) so the suspicion that triggered adjudication
    stays visible in the audit trail.
    """
    if not adjudications:
        return
    for row in rows:
        iid = row["instance_id"]
        adj = adjudications.get(iid)
        if not adj or row["status"] not in ("AMBIGUOUS_REL", "WRONG_REL"):
            continue
        new_status = adj.get("status", "")
        if not new_status.startswith("ADJUDICATED_"):
            continue
        resolved_status = new_status[len("ADJUDICATED_"):]
        counts[row["status"]] -= 1
        counts[resolved_status] += 1
        row["note"] = (
            f"[heuristic flagged {row['status']}: {row['note']}] "
            f"ADJUDICATED ({adj.get('decision', '')}): {adj.get('evidence', '')}"
        )
        row["status"] = resolved_status
        row["outcome"] = "adjudicated"


def audit(docs, do_fix):
    rows = []
    counts = defaultdict(int)
    fixed_lemmas = set()

    for lemma, (path, doc) in docs.items():
        groups = defaultdict(list)
        for sense in doc["senses"]:
            for ex in sense["examples"]:
                groups[ex["sent_ID"]].append(ex)

        forms = None  # lazy per-lemma

        for sid, exs in groups.items():
            text = exs[0]["text"]
            if forms is None:
                forms = candidate_forms(lemma, doc)
            candidates = find_matches(text, forms)  # left-to-right, non-overlapping

            n = len(exs)

            # ---- singleton groups ----
            if n == 1:
                ex = exs[0]
                pred, src = get_effective_predicate(ex, lemma, text)
                if not pred:
                    status = "PREDICATE_ANCHOR_UNRESOLVED"
                    counts[status] += 1
                    rows.append(_row(lemma, sid, ex, 1, len(candidates), None, status,
                                      "no predicate anchor stored (JSON or validated fallback)"))
                    continue
                counts[src] += 1
                span = (pred["char_start"], pred["char_end"])
                ok = text[span[0]:span[1]] == pred["form"]
                if not ok:
                    counts["WRONG_REL"] += 1
                    rows.append(_row(lemma, sid, ex, 1, len(candidates), span, "WRONG_REL",
                                      "stored offset does not match stored form"))
                    continue
                status = "PASS_SAME_REL_JUSTIFIED"
                counts[status] += 1
                rows.append(_row(lemma, sid, ex, 1, len(candidates), span, status, f"anchor_source={src}"))
                continue

            # ---- multi-instance groups ----
            spans = []
            missing_any = False
            sources = []
            for ex in exs:
                pred, src = get_effective_predicate(ex, lemma, text)
                if not pred:
                    spans.append(None)
                    sources.append(None)
                    missing_any = True
                else:
                    sources.append(src)
                    s = (pred["char_start"], pred["char_end"])
                    if text[s[0]:s[1]] != pred["form"]:
                        spans.append("BADOFFSET")
                    else:
                        spans.append(s)
                        counts[src] += 1

            if missing_any or "BADOFFSET" in spans:
                for ex, sp in zip(exs, spans):
                    if sp is None:
                        status = "PREDICATE_ANCHOR_UNRESOLVED"
                        note = f"group of {n}, {len(candidates)} textual candidates found; no anchor stored (JSON or validated fallback)"
                    elif sp == "BADOFFSET":
                        status = "WRONG_REL"
                        note = "stored offset does not match stored form"
                    else:
                        continue
                    counts[status] += 1
                    rows.append(_row(lemma, sid, ex, n, len(candidates), None, status, note))
                # still fall through: instances with a valid span in a
                # partially-missing group are audited below too
                valid_pairs = [(ex, sp) for ex, sp in zip(exs, spans) if isinstance(sp, tuple)]
            else:
                valid_pairs = list(zip(exs, spans))

            if not valid_pairs:
                continue

            # collapse detection (two+ instances sharing identical span)
            span_owners = defaultdict(list)
            for ex, sp in valid_pairs:
                span_owners[sp].append(ex)

            collapsed = {sp: owners for sp, owners in span_owners.items() if len(owners) > 1}

            if collapsed:
                fixable = (len(candidates) == n) and len(set(candidates)) == n
                if fixable and do_fix:
                    _apply_fix(exs, candidates)
                    fixed_lemmas.add(lemma)
                    for ex in exs:
                        sp = (ex["predicate"]["char_start"], ex["predicate"]["char_end"])
                        counts["WRONG_REL_FIXED"] += 1
                        rows.append(_row(lemma, sid, ex, n, len(candidates), sp,
                                          "WRONG_REL", "collapsed span - auto-fixed by ordinal reassignment",
                                          outcome="fixed"))
                else:
                    for sp, owners in collapsed.items():
                        for ex in owners:
                            status = "WRONG_REL" if fixable else "AMBIGUOUS_REL"
                            counts[status] += 1
                            rows.append(_row(
                                lemma, sid, ex, n, len(candidates), sp, status,
                                f"{len(owners)} instances collapsed on identical span "
                                f"{sp}; {'deterministic fix available (rerun with --fix)' if fixable else 'candidate count does not resolve unambiguously'}"
                            ))
                    for sp, owners in span_owners.items():
                        if len(owners) == 1:
                            ex = owners[0]
                            counts["AMBIGUOUS_REL"] += 1
                            rows.append(_row(lemma, sid, ex, n, len(candidates), sp, "AMBIGUOUS_REL",
                                              "sibling instance(s) in this group collapsed; group needs adjudication"))
                continue

            # no collapse: verify each span is one of the known candidates
            cand_set = set(candidates_spans(candidates))
            all_on_candidates = all(sp in cand_set for _, sp in valid_pairs)

            if len(candidates) != n or not all_on_candidates:
                for ex, sp in valid_pairs:
                    counts["AMBIGUOUS_REL"] += 1
                    rows.append(_row(
                        lemma, sid, ex, n, len(candidates), sp, "AMBIGUOUS_REL",
                        f"candidate count ({len(candidates)}) != instance count ({n}) "
                        f"or anchor off known candidate spans"
                    ))
                continue

            # distinct, on-candidate spans for every instance: content check
            for ex, sp in valid_pairs:
                real = ex.get("realization") or {}
                own_best = None
                sib_best = None
                checked_any_arg = False
                for arg in ("Arg0", "Arg1", "Arg2", "Arg3", "Arg4"):
                    val = real.get(arg)
                    if not val:
                        continue
                    checked_any_arg = True
                    positions = arg_positions(text, val)
                    if not positions:
                        continue
                    d_own = min_distance_to_span(positions, len(val), sp)
                    if own_best is None or d_own < own_best:
                        own_best = d_own
                    for other_ex, other_sp in valid_pairs:
                        if other_sp == sp:
                            continue
                        d_sib = min_distance_to_span(positions, len(val), other_sp)
                        if sib_best is None or d_sib < sib_best:
                            sib_best = d_sib

                if checked_any_arg and own_best is not None and sib_best is not None and sib_best < own_best:
                    counts["AMBIGUOUS_REL"] += 1
                    rows.append(_row(
                        lemma, sid, ex, n, len(candidates), sp, "AMBIGUOUS_REL",
                        f"a realized Arg sits closer to a sibling occurrence "
                        f"(dist={sib_best}) than to this instance's own anchor "
                        f"(dist={own_best}) - possible occurrence swap, needs adjudication"
                    ))
                else:
                    counts["PASS_DISTINCT_REL"] += 1
                    rows.append(_row(lemma, sid, ex, n, len(candidates), sp, "PASS_DISTINCT_REL", ""))

    adjudications = load_adjudications()
    _apply_adjudications(rows, counts, adjudications)

    return rows, counts, fixed_lemmas


def candidates_spans(candidates):
    return [(s, e) for s, e, _f in candidates]


def _apply_fix(exs, candidates):
    for ex, (s, e, form) in zip(exs, candidates):
        ex["predicate"] = {"form": form, "char_start": s, "char_end": e}


def _row(lemma, sid, ex, n, n_candidates, span, status, note, outcome=""):
    real = ex.get("realization") or {}
    text = ex.get("text", "")
    substr = text[span[0]:span[1]] if span else ""
    return {
        "lemma": lemma,
        "sent_ID": sid,
        "n_instances_in_group": n,
        "n_candidate_occurrences": n_candidates,
        "instance_id": ex.get("instance_id", ""),
        "predicate_form": (ex.get("predicate") or {}).get("form", ""),
        "char_start": span[0] if span else "",
        "char_end": span[1] if span else "",
        "text_substring": substr,
        "arg1": real.get("Arg1") or "",
        "status": status,
        "note": note,
        "outcome": outcome,
        "text": text,
    }


def write_tsv(rows, path):
    fields = ["lemma", "sent_ID", "n_instances_in_group", "n_candidate_occurrences",
              "instance_id", "predicate_form", "char_start", "char_end",
              "text_substring", "arg1", "status", "note", "outcome", "text"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(fields) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(k, "")).replace("\t", " ").replace("\n", " ") for k in fields) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true",
                     help="Write back deterministic fixes (collapsed spans with an "
                          "unambiguous reassignment) and regenerate affected pages.")
    ap.add_argument("--output", metavar="PATH",
                     help="Write the row-per-instance TSV report to this path. "
                          "Without this flag, the audit is fully read-only and "
                          "writes no files (only prints the summary).")
    args = ap.parse_args()

    docs = load_docs()
    rows, counts, fixed_lemmas = audit(docs, args.fix)

    if args.fix and fixed_lemmas:
        for lemma in fixed_lemmas:
            path, doc = docs[lemma]
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Rewrote {len(fixed_lemmas)} JSON file(s): {sorted(fixed_lemmas)}")
        import subprocess
        subprocess.run([sys.executable, "tools/render_site_from_json.py"], check=True)
        print("Regenerated site_pages/ from updated JSONs.")

    if args.output:
        out_path = Path(args.output)
        write_tsv(rows, out_path)
        print(f"Wrote {len(rows)} rows -> {out_path}")
    else:
        print(f"READ-ONLY: {len(rows)} rows audited, no report file written "
              f"(pass --output <path> to write one).")

    multi_groups = set()
    multi_instances = 0
    for lemma, (path, doc) in docs.items():
        groups = defaultdict(list)
        for sense in doc["senses"]:
            for ex in sense["examples"]:
                groups[ex["sent_ID"]].append(ex)
        for sid, exs in groups.items():
            if len(exs) > 1:
                multi_groups.add((lemma, sid))
                multi_instances += len(exs)

    print(f"MULTI_INSTANCE_GROUPS = {len(multi_groups)}")
    print(f"MULTI_INSTANCE_INSTANCES = {multi_instances}")
    print()
    print(f"JSON_PREDICATE_ANCHORED = {counts.get('JSON_PREDICATE_ANCHORED', 0)}")
    print(f"FALLBACK_PREDICATE_ANCHORED = {counts.get('FALLBACK_PREDICATE_ANCHORED', 0)}")
    print(f"PREDICATE_ANCHOR_UNRESOLVED = {counts.get('PREDICATE_ANCHOR_UNRESOLVED', 0)}")
    print()
    for status in ["PASS_DISTINCT_REL", "PASS_SAME_REL_JUSTIFIED",
                    "AMBIGUOUS_REL", "WRONG_REL", "WRONG_REL_FIXED"]:
        print(f"{status} = {counts.get(status, 0)}")

    audit_pass = (
        counts.get("PREDICATE_ANCHOR_UNRESOLVED", 0) == 0
        and counts.get("AMBIGUOUS_REL", 0) == 0
        and counts.get("WRONG_REL", 0) == 0
    )
    print()
    print("REL_INSTANCE_AUDIT =", "PASS" if audit_pass else "FAIL")
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
