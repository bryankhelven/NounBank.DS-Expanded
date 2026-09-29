#!/usr/bin/env python3
from pathlib import Path
import json, ssl, urllib.request, zipfile, hashlib, shutil, csv, xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("real_enmap_partial_002")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()

targets={
 "acomodação":{"pt_roleset":"acomodação.01","english_roleset":"stabilization.01","xml":"stabilization.xml","expected_occ":1,
          "rationale":"Trading context: price action 'encontrou uma acomodação' denotes stabilization, not lodging/accommodation."},
 "animada":{"pt_roleset":"animada.01","english_roleset":"rally.02","xml":"rally.xml","expected_occ":1,
          "rationale":"Market context: 'dá uma animadinha e depois se enterra' denotes a brief rally/recovery in price performance."},
 "concentração":{"pt_roleset":"concentração.01","english_roleset":"merger.01","xml":"merger.xml","expected_occ":2,
          "rationale":"Brazilian antitrust 'ato de concentração' in both examples denotes a corporate combination/merger transaction."},
 "impulso":{"pt_roleset":"impulso.01","english_roleset":"momentum.01","xml":"momentum.xml","expected_occ":1,
          "rationale":"Technical-analysis context: 'figura de impulso' denotes price momentum, not a physical push or psychological impulse."}
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
            s["mapping_evidence"]={"xml_file":t["xml"],"roleset_name":name,"roleset_source":source,"rationale":t["rationale"]}
            for ex in s.get("examples",[]):
                old=ex.get("realization") or {}
                oldsyn=ex.get("syntax") or {}
                ex["realization"]={r["id"]:old.get(r["id"]) for r in roles}
                ex["syntax"]={r["id"]:oldsyn.get(r["id"]) for r in roles}
                ex["english_mapping_status"]="RESOLVED_REAL_NOMBANK_ROLESET"
                ledger.append({"lemma":lemma,"pt_roleset":t["pt_roleset"],"sent_id":ex.get("sent_ID",""),"english_roleset":t["english_roleset"],"xml":t["xml"],"rationale":t["rationale"]})
    assert found, lemma
    (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert total==5,total
with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","pt_roleset","sent_id","english_roleset","xml","rationale"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(ledger)

validation={
 "status":"PASS_REAL_ENGLISH_MAPPING_CLOSURE",
 "resolved_lemmas":4,
 "resolved_occurrences":5,
 "cumulative_real_enmap_resolved":20,
 "global_pending_before_real_enmap":133,
 "global_pending_after_projection":113,
 "rule":"Actual NomBank XML + selected compatible roleset required; english_roleset=null never closes a case.",
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H REAL ENMAP PARTIAL 002

Resolved with real NomBank frames:
- acomodação.01 -> stabilization.01
- animada.01 -> rally.02
- concentração.01 -> merger.01
- impulso.01 -> momentum.01

Scope: 4 lemmas / 5 occurrences.
Cumulative true ENMAP closure: 20 occurrences.
Projected global pending: 133 -> 113.

Every mapping has its original NomBank XML in evidence/xml.
No null mapping is counted as resolved.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_REAL_ENMAP_PARTIAL_002.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
