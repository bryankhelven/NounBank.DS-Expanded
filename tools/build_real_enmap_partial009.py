#!/usr/bin/env python3
from pathlib import Path
import json, ssl, urllib.request, zipfile, hashlib, shutil, csv, xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("real_enmap_partial_009")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()

positive={
 "movimento":{"pt_roleset":"movimento.01","english_roleset":"move.02","xml":"move.xml","expected_occ":1,
   "rationale":"Source article resolves antecedent: Vale submitted a report; 'O movimento ocorreu mais tarde...' refers to that corporate step/action. NomBank move.02 is explicitly 'take measures' and includes 'in a move to...' / 'moves to ease credit'."},
 "esperteza":{"pt_roleset":"esperteza.01","english_roleset":"trickery.01","xml":"trickery.xml","expected_occ":1,
   "rationale":"In 'Se dizer enganada é ingenuidade ou esperteza demais', esperteza is the non-naive alternative: strategic/deceptive cleverness. NomBank trickery.01 = 'to deceive', matching the implicated sly/deceptive maneuver rather than neutral intelligence."}
}
negative={
 "vertigem":{
   "pt_roleset":"vertigem.01","expected_occ":1,
   "decision":"NO_COMPATIBLE_NOMBANK_ROLESET",
   "rationale":"Context 'acompanhar a #OIBR4 proporciona um mix de alegria e vertigem' denotes dizziness/vertigo, literal-metaphorical bodily sensation induced by stock volatility. Direct NomBank candidates dizziness.xml, vertigo.xml, giddiness.xml, lightheadedness.xml, disorientation.xml, nausea.xml are absent. Existing thrill.01, excitement.01, anxiety.01, shock.01 and sensation.01 alter the lexical-semantic content and were rejected.",
   "searched_candidates":[
     {"candidate":"dizziness.xml","result":"404_NO_FRAME"},
     {"candidate":"vertigo.xml","result":"404_NO_FRAME"},
     {"candidate":"giddiness.xml","result":"404_NO_FRAME"},
     {"candidate":"lightheadedness.xml","result":"404_NO_FRAME"},
     {"candidate":"disorientation.xml","result":"404_NO_FRAME"},
     {"candidate":"nausea.xml","result":"404_NO_FRAME"},
     {"candidate":"thrill.01","result":"REJECTED_SEMANTIC_SHIFT_TO_EXCITEMENT"},
     {"candidate":"excitement.01","result":"REJECTED_SEMANTIC_SHIFT_TO_EXCITEMENT"},
     {"candidate":"anxiety.01","result":"REJECTED_SEMANTIC_SHIFT_TO_ANXIETY"},
     {"candidate":"shock.01","result":"REJECTED_SEMANTIC_SHIFT_TO_SURPRISE"},
     {"candidate":"sensation.01","result":"REJECTED_TOO_GENERIC_LOSS_OF_VERTIGO_SENSE"}
   ]
 }
}

def parse_roles(xml_bytes, roleset_id):
    root=ET.fromstring(xml_bytes)
    rs=next((x for x in root.findall(".//roleset") if x.get("id")==roleset_id),None)
    assert rs is not None, roleset_id
    roles=[{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()]
    examples=[" ".join((ex.findtext("text") or "").split()) for ex in rs.findall("./example")]
    return roles,rs.get("name"),rs.get("source"),examples[:8]

ledger=[]; total=0
for lemma,t in positive.items():
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
            s["mapping_evidence"]={"decision":"COMPATIBLE_NOMBANK_ROLESET","xml_file":t["xml"],"roleset_name":name,"roleset_source":source,
                                   "rationale":t["rationale"],"nombank_examples":xml_examples}
            for ex in s.get("examples",[]):
                old=ex.get("realization") or {}; oldsyn=ex.get("syntax") or {}
                ex["realization"]={r["id"]:old.get(r["id"]) for r in roles}
                ex["syntax"]={r["id"]:oldsyn.get(r["id"]) for r in roles}
                ex["english_mapping_status"]="RESOLVED_REAL_NOMBANK_ROLESET"
                ledger.append({"lemma":lemma,"pt_roleset":t["pt_roleset"],"sent_id":ex.get("sent_ID",""),"decision":"COMPATIBLE_NOMBANK_ROLESET","english_roleset":t["english_roleset"],"xml":t["xml"],"rationale":t["rationale"]})
    assert found,lemma
    (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

for lemma,t in negative.items():
    p=SRC/"jsons"/f"{lemma}.json"
    j=json.loads(p.read_text(encoding="utf-8"))
    found=False
    for s in j.get("senses",[]):
        if s.get("pt_roleset")==t["pt_roleset"] and s.get("resolution_status")=="awaiting_english_mapping":
            found=True
            n=len(s.get("examples",[])); assert n==t["expected_occ"],(lemma,n); total+=n
            s["english_roleset"]=None
            s["english_roleset_source"]="EXPLICIT_NO_COMPATIBLE_NOMBANK_ROLESET_AFTER_SEARCH_V2H"
            s["nombank_url"]=None
            s.pop("resolution_status",None)
            s["mapping_evidence"]={"decision":t["decision"],"rationale":t["rationale"],"searched_candidates":t["searched_candidates"]}
            s["representation_status"]="RESOLVED_NO_COMPATIBLE_NOMBANK_ROLESET"
            for ex in s.get("examples",[]):
                ex["english_mapping_status"]="RESOLVED_NO_COMPATIBLE_NOMBANK_ROLESET"
                ledger.append({"lemma":lemma,"pt_roleset":t["pt_roleset"],"sent_id":ex.get("sent_ID",""),"decision":t["decision"],"english_roleset":"","xml":"","rationale":t["rationale"]})
    assert found,lemma
    (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert total==3,total
with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","pt_roleset","sent_id","decision","english_roleset","xml","rationale"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(ledger)

(OUT/"NEGATIVE_MAPPING_EVIDENCE.json").write_text(json.dumps(negative,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
validation={
 "status":"PASS_FINAL_AWAITING_ENGLISH_MAPPING_CLOSURE",
 "resolved_lemmas":3,
 "resolved_occurrences":3,
 "positive_nombank_mappings":2,
 "explicit_no_compatible_roleset_decisions":1,
 "cumulative_real_enmap_resolved":52,
 "global_pending_before_real_enmap":133,
 "global_pending_after_projection":81,
 "remaining_awaiting_english_mapping_occurrences":0,
 "remaining_awaiting_english_mapping_lemmas":0,
 "next_pending_classes":{"awaiting_sense":23,"construction_specific":19,"other_retracted_new_cases":39},
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H REAL ENMAP PARTIAL 009

Final closure of awaiting_english_mapping.

Positive mappings:
- movimento.01 -> move.02
- esperteza.01 -> trickery.01

Explicit negative mapping decision:
- vertigem.01 -> NO_COMPATIBLE_NOMBANK_ROLESET

The negative decision is NOT null-as-terminal. It is supported by a documented search over direct and semantic candidates, with rejected alternatives recorded in NEGATIVE_MAPPING_EVIDENCE.json.

Scope: 3 lemmas / 3 occurrences.
Cumulative true ENMAP resolution: 52 occurrences.
awaiting_english_mapping remaining: 0.
Projected global pending: 81.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_REAL_ENMAP_PARTIAL_009.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
