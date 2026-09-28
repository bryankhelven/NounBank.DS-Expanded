from __future__ import annotations
import json,re,zipfile
from pathlib import Path
from collections import defaultdict,Counter

jd=Path("jsons"); pd=Path("site_pages")
files=sorted(p for p in jd.glob("*.json") if p.name not in {"_manifest.json","statistics.json"})
assert len(files)==709

def nr(r):
    m=re.fullmatch(r"(?i)arg([0-9]+)",str(r or ""))
    return f"Arg{int(m.group(1))}" if m else str(r or "")
def eng(i): return (i.get("english_alignment") or {}).get("english_nombank_roleset")
def sid(i): return (i.get("wsd") or {}).get("semantic_unit_id")
def rows(i): return (i.get("argument_resource") or {}).get("roles") or []
def regular(i): return (i.get("argument_resource") or {}).get("status")=="REGULAR_ARGUMENT_RESOURCE"
def nb(er): return None if not er else "https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"+re.sub(r"\.[0-9]+$","",er)+".xml"
def omap(xs):
    g=defaultdict(list);o={}
    for i in xs:g[i.get("sent_id")].append(i)
    for rs in g.values():
        rs.sort(key=lambda x:int(x.get("token_id") or 10**9))
        for n,i in enumerate(rs,1):o[id(i)]=n
    return o
def ex(i,l,n,rids,args=True):
    y={nr(q.get("role")):q for q in rows(i) if q.get("status")=="YES"} if args else {}
    return {"sent_ID":i.get("sent_id"),"text":i.get("sentence_text",""),
            "realization":{r:(y[r].get("span_text") if r in y else None) for r in rids},
            "syntax":{r:(y[r].get("head_deprel") if r in y else None) for r in rids},
            "instance_id":f"{i.get('sent_id')}::{l}::{n}","predicate":{"form":i.get("form") or l}}
def prof(es,rids):
    o={}
    for e in es:
        for r in rids:
            d=(e.get("syntax") or {}).get(r)
            if d:o.setdefault(r,{})[d]=o.setdefault(r,{}).get(d,0)+1
    return o

man=[]; removed=[]; pending=set(); C=Counter(); P=Counter(); A=Counter()
for p in files:
    raw=json.loads(p.read_text(encoding="utf-8"))
    x=raw.get("expanded_v2") or {}; cur=x.get("current_record") or {}
    inst=cur.get("instances") or []; S=[i for i in inst if i.get("contextual_predicativity")=="S"]
    inherited=((x.get("lineage") or {}).get("inventory_partition")=="INHERITED_V1_145")
    if not S:
        removed.append(raw["lemma"]); p.unlink()
        hp=pd/(raw["lemma"]+".html")
        if hp.exists(): hp.unlink()
        continue
    l=raw["lemma"]; om=omap(S)
    if inherited:
        senses=json.loads(json.dumps(raw.get("senses") or [],ensure_ascii=False)); by=defaultdict(list)
        for s in senses: by[s.get("english_roleset")].append(s)
        for i in [z for z in S if "NEW_38" in str((z.get("argument_resource") or {}).get("lane",""))]:
            q=by.get(eng(i),[]); assert len(q)==1,(l,eng(i))
            s=q[0]; rids=[r["id"] for r in s.get("roles",[]) if r.get("id")]
            s.setdefault("examples",[]).append(ex(i,l,om[id(i)],rids))
        for s in senses:
            rids=[r["id"] for r in s.get("roles",[]) if r.get("id")]
            s["syntactic_profile"]=prof(s.get("examples") or [],rids)
        out={"lemma":l,"lemma_base":raw.get("lemma_base",l),"senses":senses}
        C["v1"]+=1; C["regular"]+=len(S)
    else:
        obs={u.get("semantic_unit_id"):u for u in (cur.get("observed_semantic_units") or []) if u.get("semantic_unit_id")}
        rg=[i for i in S if regular(i)]; tm=[i for i in S if not regular(i)]
        g=defaultdict(list); te=defaultdict(list); non=[]
        for i in rg:g[sid(i)].append(i)
        for i in tm:
            if sid(i):te[sid(i)].append(i)
            else: non.append(i)
        senses=[]
        for j,k in enumerate(sorted(set(g)|set(te)),1):
            rr=g.get(k,[])+te.get(k,[]); meta=obs.get(k,{})
            ers={eng(i) for i in rr if eng(i)}; er=next(iter(ers)) if len(ers)==1 else meta.get("english_nombank_roleset")
            inv=meta.get("licensed_role_inventory") or []
            roles=[{"id":nr(q.get("role_label")),"desc":q.get("description") or None}
                   for q in sorted(inv,key=lambda z:int(z.get("role_number") or 999))
                   if re.fullmatch(r"Arg[0-9]+",nr(q.get("role_label")))]
            if not roles and any(regular(i) for i in rr):
                seen={}
                for i in rr:
                    for q in rows(i):
                        rid=nr(q.get("role"))
                        if re.fullmatch(r"Arg[0-9]+",rid) and rid not in seen:seen[rid]=q.get("description") or None
                roles=[{"id":r,"desc":seen[r]} for r in sorted(seen,key=lambda q:int(q[3:]))]
            rids=[r["id"] for r in roles]; es=[ex(i,l,om[id(i)],rids,regular(i)) for i in rr]
            s={"pt_roleset":f"{l}.{j:02d}","pt_sense_index":j,"pt_sense_hint":j,
               "english_roleset":er or None,"english_roleset_source":None,"nombank_url":nb(er),
               "roles":roles,"examples":es,"syntactic_profile":prof(es,rids)}
            if te.get(k):
                sts={i.get("english_alignment",{}).get("status") for i in te[k]}
                s["resolution_status"]="construction_specific" if "CONSTRUCTION_SPECIFIC" in sts else "awaiting_english_mapping"
                pending.add(l)
                for i in te[k]:P["construction_specific" if i.get("english_alignment",{}).get("status")=="CONSTRUCTION_SPECIFIC" else "awaiting_english_mapping"]+=1
            senses.append(s)
        out={"lemma":l,"lemma_base":raw.get("lemma_base",l),"senses":senses}
        if non:
            out["pending_instances"]=[{"sent_ID":i.get("sent_id"),"text":i.get("sentence_text",""),
                "instance_id":f"{i.get('sent_id')}::{l}::{om[id(i)]}","predicate":{"form":i.get("form") or l},
                "resolution_status":"awaiting_sense_resolution"} for i in non]
            P["awaiting_sense"]+=len(non); pending.add(l)
        C["new"]+=1; C["regular"]+=len(rg); C["pending"]+=len(tm)
    txt=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
    for bad in ["expanded_v2","ORCH_RECON","adjudication_reason","head_token_id","span_token_ids","lexical_authority","current_authority"]:
        assert bad not in txt,(l,bad)
    p.write_text(txt,encoding="utf-8")
    man.append({"lemma":l,"filename":p.name,"new":not inherited,"pending":l in pending})
    C["lemmas"]+=1; C["S"]+=len(S)
    for s in out.get("senses",[]):
        for e in s.get("examples",[]):
            for r,v in (e.get("realization") or {}).items():
                if v:A[r]+=1

assert C["lemmas"]==494 and C["v1"]==145 and C["new"]==349 and len(removed)==215,C
assert C["S"]==3618 and C["regular"]==3524 and C["pending"]==94,C
assert P["awaiting_sense"]==23 and P["awaiting_english_mapping"]==52 and P["construction_specific"]==19,P
assert sum(A.values())==2669,A
man.sort(key=lambda x:x["lemma"].casefold())
(jd/"_manifest.json").write_text(json.dumps({"schema_version":"nounbank-ds-expanded-sanitized-manifest/1.0","lemmas":man},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
stats={"schema_version":"nounbank-ds-expanded-sanitized-stats/1.0",
       "inventory":{"public_lemmas":494,"original":145,"new":349,"removed_without_predicative_occurrence":215},
       "examples":{"predicative_occurrences":3618,"regular_occurrences":3524,"pending_occurrences":94},
       "pending":{"awaiting_sense":23,"awaiting_english_mapping":52,"construction_specific":19,"pending_lemmas":sorted(pending,key=str.casefold)},
       "arguments":{"total":2669,"by_role":dict(sorted(A.items()))}}
(jd/"statistics.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
zp=jd/"nounbank.ds_expanded_all_jsons.zip"
if zp.exists():zp.unlink()
with zipfile.ZipFile(zp,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for q in sorted(jd.glob("*.json")):z.write(q,arcname=q.name)
print(json.dumps({"PASS":True,"lemmas":C["lemmas"],"removed":len(removed),"S":C["S"],"regular":C["regular"],"pending":C["pending"],"args":sum(A.values())}))
