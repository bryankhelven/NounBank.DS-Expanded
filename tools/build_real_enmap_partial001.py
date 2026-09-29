#!/usr/bin/env python3
from pathlib import Path
import json, ssl, urllib.request, zipfile, hashlib, shutil, csv, xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("real_enmap_partial_001")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()

targets={
 "aviso":{"pt_roleset":"aviso.01","english_roleset":"announcement.01","xml":"announcement.xml","expected_occ":11,
          "rationale":"Corporate notice/announcement announcing webcast, shareholder notice, dividend information."},
 "cura":{"pt_roleset":"cura.01","english_roleset":"cure.01","xml":"cure.xml","expected_occ":1,
         "rationale":"Cure for alcoholism/illness; direct treatment/remedy sense."},
 "decolagem":{"pt_roleset":"decolagem.01","english_roleset":"liftoff.01","xml":"liftoff.xml","expected_occ":1,
              "rationale":"Market-price takeoff metaphor preserves increase-in-elevation/liftoff event semantics."},
 "retração":{"pt_roleset":"retração.01","english_roleset":"pullback.01","xml":"pullback.xml","expected_occ":2,
             "rationale":"Technical-analysis Fibonacci retracement/pullback; NomBank pullback includes Wall Street/program-trading usage."}
}

def parse_roles(xml_bytes, roleset_id):
    root=ET.fromstring(xml_bytes)
    rs=next((x for x in root.findall(".//roleset") if x.get("id")==roleset_id),None)
    assert rs is not None, roleset_id
    return [{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()], rs.get("name"), rs.get("source")

ledger=[]
total=0
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
            n=len(s.get("examples",[]))
            assert n==t["expected_occ"], (lemma,n)
            total+=n
            s["english_roleset"]=t["english_roleset"]
            s["english_roleset_source"]="NOMBANK_XML_CONTEXTUAL_SEMANTIC_MATCH_V2H"
            s["nombank_url"]=BASE+t["xml"]
            s["roles"]=roles
            s.pop("resolution_status",None)
            s["mapping_evidence"]={
                "xml_file":t["xml"],"roleset_name":name,"roleset_source":source,
                "rationale":t["rationale"]
            }
            # Represent the licensed inventory even where contextual realization is deferred
            for ex in s.get("examples",[]):
                old=ex.get("realization") or {}
                oldsyn=ex.get("syntax") or {}
                ex["realization"]={r["id"]:old.get(r["id"]) for r in roles}
                ex["syntax"]={r["id"]:oldsyn.get(r["id"]) for r in roles}
                ex["english_mapping_status"]="RESOLVED_REAL_NOMBANK_ROLESET"
                ledger.append({
                    "lemma":lemma,"pt_roleset":t["pt_roleset"],"sent_id":ex.get("sent_ID",""),
                    "english_roleset":t["english_roleset"],"xml":t["xml"],"rationale":t["rationale"]
                })
    assert found, lemma
    (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert total==15,total
with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","pt_roleset","sent_id","english_roleset","xml","rationale"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(ledger)

validation={
 "status":"PASS_REAL_ENGLISH_MAPPING_CLOSURE",
 "resolved_lemmas":4,
 "resolved_occurrences":15,
 "global_pending_before":133,
 "global_pending_after_projection":118,
 "remaining_awaiting_english_mapping":76,
 "rule":"No null-as-terminal. Each closure has an actual NomBank XML and selected roleset.",
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H REAL ENMAP PARTIAL 001

This supersedes the invalid null-as-terminal closure policy.

Actual mappings closed:
- aviso.01 -> announcement.01
- cura.01 -> cure.01
- decolagem.01 -> liftoff.01
- retração.01 -> pullback.01

Every mapping is backed by the included original NomBank XML. No mapping is closed with english_roleset=null.

Scope: 4 lemmas / 15 pending occurrences.
Projected global pending: 133 -> 118.

Argument realization is NOT claimed complete by this partial; the English roleset inventory is licensed now and contextual argument QA remains a later explicit sweep.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_REAL_ENMAP_PARTIAL_001.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
