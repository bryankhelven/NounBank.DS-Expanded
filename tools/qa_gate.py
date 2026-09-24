#!/usr/bin/env python3
"""PARTE F — QA gate for the decided-fixes work.

Run: python3 tools/qa_gate.py
Exits non-zero if any hard check fails. Prints a PASS/FAIL summary matching
the PARTE G report keys.
"""
import json
import re
import zipfile
import glob
from pathlib import Path

JSON_DIR = Path("jsons")
SITE_DIR = Path("site_pages")

ok = True


def check(name, cond, detail=""):
    global ok
    status = "PASS" if cond else "FAIL"
    if not cond:
        ok = False
    print(f"{name} = {status}" + (f"  ({detail})" if detail and not cond else ""))
    return cond


def main():
    json_files = sorted(p for p in JSON_DIR.glob("*.json") if p.name != "_manifest.json")
    docs = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in json_files}

    # ---- Inventory ----
    # NOTE: GLOBAL_RECON_STATUS (whole-corpus legacy reconciliation) and
    # PROPOSTA_RECON_STATUS (the `proposta` lemma specifically) are
    # independent axes. GLOBAL_RECON_STATUS is OPEN, so the global instance
    # total is NOT a hard gate - forcing it would mean silently deleting a
    # real corpus occurrence or fabricating a compensatory exclusion, which
    # is explicitly prohibited. `proposta` cardinality, by contrast, HAS been
    # closed out (PROPOSTA_RECON_STATUS=CLOSED) and is pinned to 8 by the
    # legacy authority - see PROPOSTA_LEGACY_RECONCILED_8 below, which IS a
    # hard gate. The global total is reported informationally with the
    # three-way distinction the continuation prompt requires:
    #   PUBLISHED_BASELINE_INSTANCES   - the historically published total (1756)
    #   CURRENT_WORKTREE_INSTANCES     - what is on disk right now
    #   LEGACY_CORPUS_CONFIRMED_MISSING - occurrences the legacy corpus proves
    #                                     exist but are not yet in the JSON
    #                                     (evidence-backed, not guessed; see
    #                                     docs in nounbank_ds_authority/DANTEStocks_legacy_v1/reports/LATEST/)
    check("NPREDS", len(docs) == 145, f"got {len(docs)}")
    total_instances = sum(sum(len(s["examples"]) for s in d["senses"]) for d in docs.values())
    PUBLISHED_BASELINE_INSTANCES = 1756  # historical metadata only, never a gate
    CURRENT_WORKTREE_INSTANCES = total_instances
    # proposta.01 was fully reconciled against the DANTEStocks legacy trees:
    # the 2 previously-confirmed-missing occurrences (dante_01_449542704209612801l,
    # dante_01_451323756733296640l) were added with evidence-backed Args/syntax,
    # and all 8 real proposta occurrences were cross-checked against the legacy
    # UD trees (3 syntax corrections applied: 448061183451746304 Arg1 amod->nmod,
    # 456842896021278720 Arg1 nmod->acl, 449545769029496834 Arg1 amod->parataxis;
    # plus 460783757025624064 Arg0 flat:name->nmod and Arg2 "Ago"->"Ago/e"/nmod).
    # No entries remain in LEGACY_CORPUS_CONFIRMED_MISSING - extend this dict
    # again only when a NEW reconciliation report backs an entry with concrete
    # sent_IDs, never as a guess.
    LEGACY_CORPUS_CONFIRMED_MISSING = {}
    print(f"PUBLISHED_BASELINE_INSTANCES = {PUBLISHED_BASELINE_INSTANCES}")
    print(f"CURRENT_WORKTREE_INSTANCES = {CURRENT_WORKTREE_INSTANCES}")
    print(f"LEGACY_CORPUS_CONFIRMED_MISSING = {sum(LEGACY_CORPUS_CONFIRMED_MISSING.values())} "
          f"({LEGACY_CORPUS_CONFIRMED_MISSING})")
    # GLOBAL_RECON_STATUS and PROPOSTA_RECON_STATUS are independent axes.
    # Closing the proposta reconciliation does not close reconciliation for
    # the corpus as a whole - other lemmas' legacy reconciliation remains
    # OPEN and out of scope for this pass.
    print("PROPOSTA_RECON_STATUS = CLOSED  (proposta.01 fully reconciled against "
          "the DANTEStocks legacy trees; pinned at 8 instances by the legacy "
          "authority - see PROPOSTA_LEGACY_RECONCILED_8 below)")
    print("GLOBAL_RECON_STATUS = OPEN  (other lemmas' legacy reconciliation is "
          "unaffected by the proposta closure and remains out of scope for "
          "this pass)")

    manifest = json.loads((JSON_DIR / "_manifest.json").read_text(encoding="utf-8"))
    check("MANIFEST_145", len(manifest) == 145, f"got {len(manifest)}")

    check("SELLER_PRESENT", "seller" in docs)
    check("DESISTENCIA_PRESENT", "desistência" in docs)
    proposta_n = sum(len(s["examples"]) for s in docs["proposta"]["senses"]) if "proposta" in docs else -1
    check("PROPOSTA_LEGACY_RECONCILED_8", proposta_n == 8, f"got {proposta_n}")

    zip_path = JSON_DIR / "nounbank.ds_all_jsons.zip"
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        check("ZIP_CRC", bad is None, f"bad member {bad}")
        members = zf.namelist()
        check("ZIP_145", len(members) == 145, f"got {len(members)}")
        zip_instances = 0
        byte_identical = True
        for name in members:
            data = zf.read(name)
            on_disk = (JSON_DIR / name).read_bytes()
            if data != on_disk:
                byte_identical = False
            zip_instances += sum(len(s["examples"]) for s in json.loads(data)["senses"])
        # Internal consistency (zip must mirror the worktree JSONs), not a
        # pin to the historical PUBLISHED_BASELINE_INSTANCES=1756 figure,
        # which is not enforceable while reconciliation is OPEN.
        check("ZIP_MATCHES_WORKTREE_INSTANCES", zip_instances == CURRENT_WORKTREE_INSTANCES,
              f"zip={zip_instances} worktree={CURRENT_WORKTREE_INSTANCES}")
        check("ZIP_BYTE_IDENTICAL", byte_identical)
        check("ZIP_EXCLUDES_MANIFEST", "_manifest.json" not in members)
        check("ZIP_ORDER_MATCHES_MANIFEST", members == manifest)

    # ---- Identity ----
    all_ids = []
    order_ok = True
    for lemma, d in docs.items():
        for s in d["senses"]:
            for ex in s["examples"]:
                iid = ex.get("instance_id")
                if not iid:
                    order_ok = False
                all_ids.append(iid)
                if not iid or not iid.endswith(f"::{ex['sent_ID']}"[::-1][::-1]):
                    pass  # cheap structural check done below
    check("INSTANCE_IDS_COUNT", len(all_ids) == CURRENT_WORKTREE_INSTANCES,
          f"ids={len(all_ids)} worktree={CURRENT_WORKTREE_INSTANCES}")
    check("INSTANCE_IDS_UNIQUE", len(set(all_ids)) == len(all_ids),
          f"{len(all_ids) - len(set(all_ids))} duplicates")
    check("INSTANCE_IDS_ALL_PRESENT", all(all_ids), "some examples missing instance_id")

    # instance_id format sanity: "<sent_ID>::<lemma>::<ordinal>"
    fmt_ok = True
    for lemma, d in docs.items():
        for s in d["senses"]:
            for ex in s["examples"]:
                expected_prefix = f"{ex['sent_ID']}::{lemma}::"
                if not (ex.get("instance_id") or "").startswith(expected_prefix):
                    fmt_ok = False
    check("INSTANCE_ID_FORMAT", fmt_ok)

    # ---- JSON literal-substring / null-pairing checks ----
    # PARTE F requires this strictly for the files touched by PARTE C
    # (semantic fixes). Pre-existing baseline issues in untouched files are
    # reported separately as informational (out of scope for this pass —
    # several are explicitly named residuals in PARTE D, e.g. oferta's
    # -5.199999999999999).
    MODIFIED_INSTANCE_IDS = {
        "dante_01_452088399588249600l::carteira::1",       # C1
        "dante_01_449147872840548353l::compra::1",         # C2
        "dante_01_448289071920472064l::compra::1",         # C3
        "dante_01_454284964583190528l::compra::1",         # C4
        "dante_01_443463813623738368l::reunião::1",        # C5
        # C6 cara: all 6 examples of the sole sense were remapped
        "dante_01_454691501646557184l::cara::1",
        "dante_01_443436776175443968l::cara::1",
        "dante_01_443438174216671233l::cara::1",
        "dante_01_451345855191478273l::cara::1",
        "dante_01_441563014731665408l::cara::1",
        "dante_01_459024422691954688l::cara::1",
        "dante_01_443438866146807809l::comparação::1",     # C7
        "dante_01_443125288709279744l::oferta::1",         # C8 ex2
        "dante_01_443546558307778560l::oferta::1",          # C8 ex3
    }
    substr_ok_scoped = True
    pairing_ok_scoped = True
    substr_baseline_issues = 0
    pairing_baseline_issues = 0
    pred_offsets_ok = True
    for lemma, d in docs.items():
        for s in d["senses"]:
            for ex in s["examples"]:
                text = ex["text"]
                real = ex.get("realization") or {}
                syn = ex.get("syntax") or {}
                touched = ex.get("instance_id") in MODIFIED_INSTANCE_IDS
                for arg in ("Arg0", "Arg1", "Arg2", "Arg3", "Arg4"):
                    v = real.get(arg)
                    sy = syn.get(arg)
                    if v is not None and v not in text:
                        if touched:
                            substr_ok_scoped = False
                        else:
                            substr_baseline_issues += 1
                    if (v is None) != (sy is None):
                        if touched:
                            pairing_ok_scoped = False
                        else:
                            pairing_baseline_issues += 1
                pred = ex.get("predicate")
                if pred:
                    a, b = pred["char_start"], pred["char_end"]
                    if text[a:b] != pred["form"]:
                        pred_offsets_ok = False
    check("REALIZATION_SUBSTRING_MODIFIED_FILES", substr_ok_scoped)
    check("REALIZATION_SYNTAX_NULL_PAIRING_MODIFIED_FILES", pairing_ok_scoped)
    check("PREDICATE_OFFSETS_MATCH_TEXT", pred_offsets_ok)
    print(f"  (informational, pre-existing/out-of-scope: substring issues in "
          f"untouched files = {substr_baseline_issues}, null-pairing issues = "
          f"{pairing_baseline_issues} — see tools/preexisting_corpus_issues.tsv)")

    # ---- Site checks ----
    html_files = {p.stem: p for p in SITE_DIR.glob("*.html")}
    count_match = 0
    for lemma, d in docs.items():
        n = sum(len(s["examples"]) for s in d["senses"])
        p = html_files.get(lemma)
        if not p:
            continue
        h = p.read_text(encoding="utf-8")
        rows = len(re.findall(r'<tr data-instance-id="[^"]*"', h))
        if rows == n:
            count_match += 1
    check("HTML_JSON_COUNT_MATCH", count_match == 145, f"{count_match}/145")

    # proposta is now pinned at 8 by the legacy authority (PROPOSTA_RECON_STATUS
    # = CLOSED; enforced above by PROPOSTA_LEGACY_RECONCILED_8). This check
    # additionally requires the rendered HTML to agree with the JSON at
    # whatever that pinned cardinality is — that invariant is already covered
    # by HTML_JSON_COUNT_MATCH above.
    proposta_html = html_files.get("proposta")
    proposta_rows = len(re.findall(r'<tr data-instance-id="[^"]*"',
                                    proposta_html.read_text(encoding="utf-8"))) if proposta_html else -1
    print(f"PROPOSTA_HTML_ROWS = {proposta_rows}  (must equal "
          f"PROPOSTA_JSON_INSTANCES={proposta_n}, pinned at 8)")
    # HTML and JSON must agree with EACH OTHER at the pinned cardinality.
    check("PROPOSTA_HTML_MATCHES_JSON_CARDINALITY", proposta_rows == proposta_n,
          f"html={proposta_rows} json={proposta_n}")

    # all rows carry data-instance-id, none collapsed for same sent_ID
    rows_have_iid = True
    for lemma, p in html_files.items():
        h = p.read_text(encoding="utf-8")
        m = re.search(r'<table id="relations-table">.*?<tbody>(.*?)</tbody>\s*</table>', h, re.S)
        if not m:
            rows_have_iid = False
            continue
        tbody = m.group(1)
        n_tr = len(re.findall(r"<tr(?:\s|>)", tbody))
        n_tr_iid = len(re.findall(r'<tr data-instance-id="[^"]*"', tbody))
        if n_tr != n_tr_iid:
            rows_have_iid = False
    check("ALL_ROWS_HAVE_INSTANCE_ID", rows_have_iid)

    # known multi-instance validation cases
    cases = [
        ("carteira", "dante_01_461258410596368384l", ["carteiras", "carteiras"]),
        ("carteira", "dante_01_443409354381750273l", ["carteiras", "carteira"]),
        ("descoberta", "dante_01_469952216032620544l", ["descobertas", "descoberta"]),
        ("comparação", "dante_01_443438866146807809l", ["comparação", "comparação"]),
        ("compra", "dante_01_453631123914899457l", ["compras", "compra"]),
    ]
    cases_ok = True
    for lemma, sid, expected_forms in cases:
        h = html_files[lemma].read_text(encoding="utf-8")
        found = []
        for m in re.finditer(r'<tr data-instance-id="([^"]*)"[^>]*>(.*?)</tr>', h):
            iid, row = m.groups()
            if iid.startswith(sid):
                relm = re.search(r'<span class="rel">([^<]*)</span>', row)
                found.append(relm.group(1) if relm else None)
        if found != expected_forms:
            cases_ok = False
            print(f"  case mismatch {lemma} {sid}: expected {expected_forms}, got {found}")
    check("KNOWN_MULTI_INSTANCE_REL_CASES", cases_ok)

    # no HTML references a nonexistent JSON download link
    dl_ok = True
    for lemma, p in html_files.items():
        h = p.read_text(encoding="utf-8")
        m = re.search(r'href="\.\./jsons/([^"]+)" download', h)
        if not m or not (JSON_DIR / m.group(1)).exists():
            dl_ok = False
    check("JSON_DOWNLOAD_LINKS_VALID", dl_ok)

    # ---- Front-end sanity ----
    scripts_js = Path("scripts.js")
    check("SCRIPTS_JS_EXISTS", scripts_js.exists())

    print()
    print("OVERALL =", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
