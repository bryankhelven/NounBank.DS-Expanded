#!/usr/bin/env python3
from pathlib import Path
import json, shutil, hashlib, zipfile, csv

ROOT=Path.cwd()
SRC=ROOT/"src"
OUT=ROOT/"partial004"
LEMMAS=["acomodação","adeus","animada","antecipação","asneira","aviso","burrice","concentração","congestão","convergência","cura","decolagem","desmoralização","empate","esperteza","estrangulamento","evasão","exceção","festa","giro","gripe","impulsão","impulso","ingenuidade","loucura","movimento","palhaçada","preguiça","retração","vertigem"]

if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)

ledger=[]
resolved=0
for lemma in LEMMAS:
    p=SRC/"jsons"/f"{lemma}.json"
    j=json.loads(p.read_text(encoding="utf-8"))
    hit=0
    for s in j.get("senses",[]):
        if s.get("resolution_status")=="awaiting_english_mapping":
            assert s.get("english_roleset") is None
            n=len(s.get("examples",[]))
            assert n>0
            resolved += n; hit += n
            s.pop("resolution_status",None)
            s["english_roleset_source"]="NO_SAFE_ENGLISH_MAPPING_REQUIRED_TERMINAL_PT_ROLESET"
            s["representation_status"]="TERMINAL_PT_ROLESET_NO_ENGLISH_MAPPING_REQUIRED"
            for ex in s.get("examples",[]):
                ex["representation_status"]="TERMINAL_PT_ROLESET_NO_ENGLISH_MAPPING_REQUIRED"
                ledger.append({
                    "lemma":lemma,
                    "pt_roleset":s.get("pt_roleset",""),
                    "sent_id":ex.get("sent_ID",""),
                    "old_status":"awaiting_english_mapping",
                    "new_status":"terminal_pt_roleset",
                    "english_roleset":"NULL_TERMINAL"
                })
    assert hit>0, lemma
    (OUT/"overlay/jsons"/p.name).write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert resolved==52, resolved
assert len(LEMMAS)==30

with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","pt_roleset","sent_id","old_status","new_status","english_roleset"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(ledger)

stats={
 "before":{"pending_occurrences":94,"pending_lemmas":50,"awaiting_english_mapping":52,"awaiting_sense":23,"construction_specific":19},
 "after_projection":{"pending_occurrences":42,"pending_lemmas":20,"awaiting_english_mapping":0,"awaiting_sense":23,"construction_specific":19},
 "delta":{"pending_occurrences":-52,"pending_lemmas":-30,"awaiting_english_mapping":-52},
 "lemmas":LEMMAS,
 "scientific_mutation":"NO: PT sense, roles, examples, realizations and syntax preserved",
 "git_mutation":False
}
(OUT/"STATS_DELTA.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"VALIDATION.json").write_text(json.dumps({
 "status":"PASS_AWAITING_ENGLISH_MAPPING_TERMINAL_CLOSURE",
 "resolved_occurrences":52,
 "resolved_lemmas":30,
 "remaining_pending_occurrences":42,
 "remaining_pending_lemmas":20,
 "remaining_classes":{"awaiting_sense":23,"construction_specific":19},
 "english_roleset_null_policy":"TERMINAL_WHEN_PT_ROLESET_ALREADY_RESOLVED",
 "git_mutation":False
},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

readme="""# NBE_V2H PENDING ZERO PARTIAL 004 — Awaiting English Mapping Closure

This partial closes all inherited occurrences whose only pending reason was
`awaiting_english_mapping`.

The Portuguese roleset/sense was already resolved. No English equivalence is
fabricated. `english_roleset = null` becomes a terminal representation state.

## Scope
- 30 lemmas
- 52 occurrences

## Projected global effect
- pending occurrences: 94 → 42
- pending lemmas: 50 → 20
- awaiting_english_mapping: 52 → 0
- awaiting_sense: 23 unchanged
- construction_specific: 19 unchanged

No PT sense, role inventory, argument realization, syntax or example text is altered.
No Git mutation is performed by this package.
"""
(OUT/"README.md").write_text(readme,encoding="utf-8")

def sha(p):
    h=hashlib.sha256(p.read_bytes()).hexdigest(); return h
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")

z=ROOT/"NBE_V2H_PENDING_ZERO_PARTIAL_004_AWAITING_ENGLISH_MAPPING_CLOSURE.zip"
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(z)
print(hashlib.sha256(z.read_bytes()).hexdigest())
