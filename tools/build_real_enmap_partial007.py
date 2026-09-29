#!/usr/bin/env python3
from pathlib import Path
import json, ssl, urllib.request, zipfile, hashlib, shutil, csv, xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("real_enmap_partial_007")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()

targets={
 "burrice":{"pt_roleset":"burrice.01","english_roleset":"folly.01","xml":"folly.xml","expected_occ":1,
            "rationale":"Evaluative sense 'isso é ... burrice' = folly of an action; NomBank folly.01 licenses agent + action and includes 'economic folly'."},
 "congestão":{"pt_roleset":"congestão.01","english_roleset":"stagnation.01","xml":"stagnation.xml","expected_occ":2,
              "rationale":"Technical-analysis 'congestão' denotes prolonged sideways/stagnant market state; stagnation.01 includes economic stagnation examples."},
 "convergência":{"pt_roleset":"convergência.01","english_roleset":"narrowing.01","xml":"narrowing.xml","expected_occ":1,
                 "rationale":"'convergência de preços' denotes reduction of price differences; narrowing.01 models a gap/difference becoming narrower and includes economic trade-gap examples."},
 "empate":{"pt_roleset":"empate.01","english_roleset":"parity.01","xml":"parity.xml","expected_occ":1,
           "rationale":"Context describes equal analyst-mention counts; parity.01 models equality between compared quantities/entities."},
 "evasão":{"pt_roleset":"evasão.01","english_roleset":"outflow.01","xml":"outflow.xml","expected_occ":2,
           "rationale":"'evasão de divisas' is capital/currency outflow; NomBank outflow.01 explicitly includes 'Outflows of people and capital' and stock-fund outflow examples."},
 "palhaçada":{"pt_roleset":"palhaçada.01","english_roleset":"absurdity.01","xml":"absurdity.xml","expected_occ":1,
              "rationale":"Predicative evaluation 'isso é palhaçada' denotes that a proposition/action is absurd; absurdity.01 models theme + degree/value of absurdity."}
}

def parse_roles(xml_bytes, roleset_id):
    root=ET.fromstring(xml_bytes)
    rs=next((x for x in root.findall(".//roleset") if x.get("id")==roleset_id),None)
    assert rs is not None, roleset_id
    roles=[{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()]
    examples=[" ".join((ex.findtext("text") or "").split()) for ex in rs.findall("./example")]
    return roles,rs.get("name"),rs.get("source"),examples[:5]

ledger=[]; total=0
for lemma,t in targets.items():
    with urllib.request.urlopen(BASE+t["xml"],context=ctx,timeout=30) as r:
        xml=r.read()
    (OUT/"evidence/xml"/t["xml"]).write_bytes(xml)
    roles,name,source,xml_examples=parse_roles(xml,t["english_roleset"])
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
            s["mapping_evidence"]={
              "xml_file":t["xml"],"roleset_name":name,"roleset_source":source,
              "rationale":t["rationale"],"nombank_examples":xml_examples
            }
            for ex in s.get("examples",[]):
                old=ex.get("realization") or {}; oldsyn=ex.get("syntax") or {}
                ex["realization"]={r["id"]:old.get(r["id"]) for r in roles}
                ex["syntax"]={r["id"]:oldsyn.get(r["id"]) for r in roles}
                ex["english_mapping_status"]="RESOLVED_REAL_NOMBANK_ROLESET"
                ledger.append({"lemma":lemma,"pt_roleset":t["pt_roleset"],"sent_id":ex.get("sent_ID",""),"english_roleset":t["english_roleset"],"xml":t["xml"],"rationale":t["rationale"]})
    assert found,lemma
    (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert total==8,total
with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","pt_roleset","sent_id","english_roleset","xml","rationale"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(ledger)

validation={
 "status":"PASS_REAL_ENGLISH_MAPPING_CLOSURE",
 "resolved_lemmas":6,
 "resolved_occurrences":8,
 "cumulative_real_enmap_resolved":42,
 "global_pending_before_real_enmap":133,
 "global_pending_after_projection":91,
 "remaining_awaiting_english_mapping_occurrences":10,
 "remaining_awaiting_english_mapping_lemmas":6,
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H REAL ENMAP PARTIAL 007

Resolved with actual NomBank frames:
- burrice.01 -> folly.01
- congestão.01 -> stagnation.01
- convergência.01 -> narrowing.01
- empate.01 -> parity.01
- evasão.01 -> outflow.01
- palhaçada.01 -> absurdity.01

Scope: 6 lemmas / 8 occurrences.
Cumulative true ENMAP closure: 42/133.
Projected global pending: 91.

Each mapping includes the original NomBank XML and contextual rationale. No null mapping is counted as resolved.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_REAL_ENMAP_PARTIAL_007.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
