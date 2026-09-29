#!/usr/bin/env python3
from pathlib import Path
import json,re,unicodedata,csv

ROOT=Path(".")
rows=[]

def norm(s):
    s=(s or "").lower()
    s=unicodedata.normalize("NFD",s)
    s="".join(c for c in s if unicodedata.category(c)!="Mn")
    s=re.sub(r"[^a-z0-9-]+","",s)
    return s

def crude_stem(s):
    s=norm(s)
    for suf in ["ões","ães","ais","eis","is","ns","s","as","os","a","o"]:
        if len(s)>5 and s.endswith(suf):
            return s[:-len(suf)]
    return s

for p in sorted(Path("jsons").glob("*.json")):
    if p.name.startswith("_") or p.name=="statistics.json":
        continue
    j=json.loads(p.read_text(encoding="utf-8"))
    lemma=j.get("lemma") or p.stem
    forms=[]
    for s in j.get("senses",[]):
        for ex in s.get("examples",[]):
            f=(ex.get("predicate") or {}).get("form")
            if f: forms.append(("sense",s.get("pt_roleset"),f,ex.get("sent_ID"),ex.get("text")))
    for ex in j.get("pending_instances",[]):
        f=(ex.get("predicate") or {}).get("form")
        if f: forms.append(("pending",None,f,ex.get("sent_ID"),ex.get("text")))
    for ex in j.get("nonpredicative_instances",[]):
        f=(ex.get("predicate") or {}).get("form")
        if f: forms.append(("nonpred",None,f,ex.get("sent_ID"),ex.get("text")))
    for kind,rs,f,sid,text in forms:
        nl,nf=norm(lemma),norm(f)
        same = nl==nf
        stem_same = crude_stem(lemma)==crude_stem(f)
        prefix = nf.startswith(nl) or nl.startswith(nf)
        # surface mismatch worth manual review if not exact and not a likely plural/case/diacritic variant
        if not same and not stem_same:
            rows.append({
                "file":p.name,"lemma":lemma,"lemma_base":j.get("lemma_base"),
                "kind":kind,"pt_roleset":rs or "","predicate_form":f,
                "lemma_norm":nl,"form_norm":nf,"prefix_related":prefix,
                "sent_ID":sid or "","text":text or ""
            })

with open("LEXICAL_IDENTITY_MISMATCH_AUDIT.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys() if rows else ["file"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(rows)

summary={}
for r in rows:
    summary.setdefault(r["file"],set()).add(r["predicate_form"])
print("FILES",len(summary),"ROWS",len(rows))
for fn,forms in sorted(summary.items()):
    print(fn, "=>", sorted(forms))
