#!/usr/bin/env python3
from pathlib import Path
import json,re,unicodedata,csv

def norm(s):
    s=(s or "").lower()
    s=unicodedata.normalize("NFD",s)
    s="".join(c for c in s if unicodedata.category(c)!="Mn")
    return re.sub(r"[^a-z0-9-]+","",s)

def simple_plural_variants(x):
    out={x}
    if x.endswith("s"): out.add(x[:-1])
    if x.endswith("es"): out.add(x[:-2])
    if x.endswith("ns"): out.add(x[:-2]+"m")
    if x.endswith("oes"): out.add(x[:-3]+"ao")
    if x.endswith("aes"): out.add(x[:-3]+"ao")
    return out

rows=[]
for p in sorted(Path("jsons").glob("*.json")):
    if p.name.startswith("_") or p.name=="statistics.json": continue
    j=json.loads(p.read_text(encoding="utf-8"))
    lemma=j.get("lemma") or p.stem
    nl=norm(lemma)
    exs=[]
    for s in j.get("senses",[]):
        for ex in s.get("examples",[]):
            exs.append(("sense",s.get("pt_roleset") or "",ex))
    for ex in j.get("pending_instances",[]): exs.append(("pending","",ex))
    for ex in j.get("nonpredicative_instances",[]): exs.append(("nonpred","",ex))
    for kind,rs,ex in exs:
        form=(ex.get("predicate") or {}).get("form")
        if not form: continue
        nf=norm(form)
        if nf==nl: continue
        # Ignore transparent plural only.
        if nl in simple_plural_variants(nf) or nf in simple_plural_variants(nl): continue
        rows.append({
          "file":p.name,"lemma":lemma,"lemma_base":j.get("lemma_base") or "",
          "kind":kind,"pt_roleset":rs,"predicate_form":form,
          "sent_ID":ex.get("sent_ID") or "","text":ex.get("text") or ""
        })

with open("LEXICAL_IDENTITY_MISMATCH_AUDIT.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["file","lemma","lemma_base","kind","pt_roleset","predicate_form","sent_ID","text"],delimiter="\t",lineterminator="\n")
    w.writeheader();w.writerows(rows)

summary={}
for r in rows:
    summary.setdefault(r["file"],set()).add(r["predicate_form"])
print("FILES",len(summary),"ROWS",len(rows))
for fn,forms in sorted(summary.items()):
    print(fn,"=>",sorted(forms))
