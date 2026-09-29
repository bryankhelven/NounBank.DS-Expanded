#!/usr/bin/env python3
import subprocess, json, re, unicodedata, csv
from collections import defaultdict

def sh(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)

def norm(s):
    s=(s or "").lower()
    s=unicodedata.normalize("NFD",s)
    s="".join(c for c in s if unicodedata.category(c)!="Mn")
    return re.sub(r"[^a-z0-9-]+","",s)

def simple_variants(x):
    out={x}
    if x.endswith("s"): out.add(x[:-1])
    if x.endswith("es"): out.add(x[:-2])
    if x.endswith("ns"): out.add(x[:-2]+"m")
    if x.endswith("oes"): out.add(x[:-3]+"ao")
    if x.endswith("aes"): out.add(x[:-3]+"ao")
    return out

# Every commit that touched jsons, plus roots reachable from all refs.
commits=sh("git","log","--all","--format=%H","--","jsons").splitlines()
seen=set(); commits=[c for c in commits if not (c in seen or seen.add(c))]
print("COMMITS",len(commits))

pairs=defaultdict(lambda: {"commits":set(),"count":0,"examples":[],"paths":set()})

for i,commit in enumerate(commits,1):
    try:
        files=sh("git","ls-tree","-r","--name-only",commit,"jsons").splitlines()
    except Exception:
        continue
    for path in files:
        if not path.endswith(".json") or path.endswith("_manifest.json") or path.endswith("statistics.json"):
            continue
        try:
            raw=subprocess.check_output(["git","show",f"{commit}:{path}"],stderr=subprocess.DEVNULL)
            j=json.loads(raw.decode("utf-8"))
        except Exception:
            continue
        lemma=j.get("lemma") or path.rsplit("/",1)[-1][:-5]
        nl=norm(lemma)
        exs=[]
        for s in j.get("senses",[]) or []:
            for ex in s.get("examples",[]) or []:
                exs.append(ex)
        for key in ("pending_instances","nonpredicative_instances"):
            for ex in j.get(key,[]) or []:
                exs.append(ex)
        for ex in exs:
            form=((ex.get("predicate") or {}).get("form") or "").strip()
            if not form: continue
            nf=norm(form)
            if nf==nl: continue
            if nl in simple_variants(nf) or nf in simple_variants(nl): continue
            k=(lemma,form)
            d=pairs[k]
            d["commits"].add(commit)
            d["count"]+=1
            d["paths"].add(path)
            if len(d["examples"])<4:
                d["examples"].append({
                    "commit":commit,
                    "sent_ID":ex.get("sent_ID",""),
                    "text":ex.get("text","")
                })

rows=[]
for (lemma,form),d in pairs.items():
    rows.append({
        "lemma":lemma,"predicate_form":form,
        "commit_count":len(d["commits"]),"occurrence_count":d["count"],
        "first_commit":sorted(d["commits"])[0] if d["commits"] else "",
        "paths":";".join(sorted(d["paths"])),
        "example_texts":" || ".join(x["text"] for x in d["examples"])
    })
rows.sort(key=lambda r:(r["lemma"].casefold(),r["predicate_form"].casefold()))

with open("LEXICAL_IDENTITY_HISTORY_AUDIT.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys() if rows else ["lemma"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(rows)

# Heuristic shortlist: gender/derivational/prefix changes that are not mere truncations.
def suspicious(lemma,form):
    a,b=norm(lemma),norm(form)
    if len(a)<3 or len(b)<3: return False
    # exclude obvious truncation/elongation/typo-like prefix matches
    if a.startswith(b) or b.startswith(a):
        # retain full-word prefix alternations ex: representacao/reapresentacao
        if abs(len(a)-len(b))<=2: return False
    # prioritize common nominal/adjectival cross endings and prefixed forms
    endings=("ado","ada","ido","ida","ivo","iva","or","ora","cao","ção","mento","menta")
    if any(a.endswith(x) for x in endings) or any(b.endswith(x) for x in endings): return True
    if ("re"+a==b) or ("re"+b==a): return True
    return False

short=[r for r in rows if suspicious(r["lemma"],r["predicate_form"])]
with open("LEXICAL_IDENTITY_HISTORY_SHORTLIST.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys() if rows else ["lemma"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(short)

print("UNIQUE_MISMATCH_PAIRS",len(rows))
print("HEURISTIC_SHORTLIST",len(short))
for r in short[:200]:
    print(r["lemma"],"=>",r["predicate_form"],"| commits",r["commit_count"],"|",r["example_texts"][:220])
