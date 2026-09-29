#!/usr/bin/env python3
from pathlib import Path
import json, ssl, urllib.request, zipfile, hashlib, shutil, csv, xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("real_enmap_partial_004")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()

targets={
 "ingenuidade":{"pt_roleset":"ingenuidade.01","english_roleset":"innocence.01","xml":"innocence.xml","expected_occ":1,
                "rationale":"Context contrasts 'ingenuidade' with 'esperteza'; denotes innocence/naivety attributed to an agent through the act of claiming deception. innocence.01 licenses agent and action."},
 "loucura":{"pt_roleset":"loucura.01","english_roleset":"frenzy.01","xml":"frenzy.xml","expected_occ":1,
            "rationale":"After-market context with abrupt -5.39% move uses 'loucura' for a frenzied market state; frenzy.01 is the closest compatible nominal state frame."}
}

def parse_roles(xml_bytes, roleset_id):
    root=ET.fromstring(xml_bytes)
    rs=next((x for x in root.findall(".//roleset") if x.get("id")==roleset_id),None)
    assert rs is not None, roleset_id
    roles=[{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()]
    return roles,rs.get("name"),rs.get("source")

ledger=[]; total=0
for lemma,t in targets.items():
    with urllib.request.urlopen(BASE+t["xml"],context=ctx,timeout=30) as r:
        xml=r.read()
    (OUT/"evidence/xml"/t["xml"]).write_bytes(xml)
    roles,name,source=parse_roles(xml,t["english_roleset"])
    p=SRC/"jsons"/f"{lemma}.json"
    j=json.loads(p.read_text(encoding="utf-8"))
    found=False
    for s in j.get("senses",[]):
        if s.get("pt_roleset")==t["pt_roleset"] and s.get("resolution_status")=="awaiting_english_mapping":
            found=True
            n=len(s.get("examples",[])); assert n==t["expected_occ"],(lemma,n); total+=n
            s["english_roleset"]=t["english_roleset"]
            s["english_roleset_source"]="NOMBANK_XML_CONTEXTUAL_SEMANTIC_MATCH_V2H"
            s["nombank_url"]=BASE+t["xml"]
            s["roles"]=roles
            s.pop("resolution_status",None)
            s["mapping_evidence"]={"xml_file":t["xml"],"roleset_name":name,"roleset_source":source,"rationale":t["rationale"]}
            for ex in s.get("examples",[]):
                old=ex.get("realization") or {}; oldsyn=ex.get("syntax") or {}
                ex["realization"]={r["id"]:old.get(r["id"]) for r in roles}
                ex["syntax"]={r["id"]:oldsyn.get(r["id"]) for r in roles}
                ex["english_mapping_status"]="RESOLVED_REAL_NOMBANK_ROLESET"
                ledger.append({"lemma":lemma,"pt_roleset":t["pt_roleset"],"sent_id":ex.get("sent_ID",""),"english_roleset":t["english_roleset"],"xml":t["xml"],"rationale":t["rationale"]})
    assert found,lemma
    (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert total==2
with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","pt_roleset","sent_id","english_roleset","xml","rationale"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(ledger)
validation={
 "status":"PASS_REAL_ENGLISH_MAPPING_CLOSURE",
 "resolved_lemmas":2,
 "resolved_occurrences":2,
 "cumulative_real_enmap_resolved":26,
 "global_pending_before_real_enmap":133,
 "global_pending_after_projection":107,
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H REAL ENMAP PARTIAL 004

Resolved with actual NomBank frames:
- ingenuidade.01 -> innocence.01
- loucura.01 -> frenzy.01

Scope: 2 lemmas / 2 occurrences.
Cumulative true closure: 26/133.
Projected pending: 107.

Not closed in this round: adeus, palhaçada, empate, vertigem and other candidates whose available NomBank frames do not adequately match the DANTE sense.
""",encoding="utf-8")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_REAL_ENMAP_PARTIAL_004.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
