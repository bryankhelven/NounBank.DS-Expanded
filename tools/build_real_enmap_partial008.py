#!/usr/bin/env python3
from pathlib import Path
import json, ssl, urllib.request, zipfile, hashlib, shutil, csv, xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("real_enmap_partial_008")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()

targets={
 "antecipação":{"pt_roleset":"antecipação.01","english_roleset":"acceleration.01","xml":"acceleration.xml","expected_occ":1,
   "rationale":"In 'Antecipação do debate político', the event is made to occur earlier/faster. NomBank acceleration.01 explicitly includes 'acceleration of planned tariff cuts', a close planned-event temporal advancement use."},
 "estrangulamento":{"pt_roleset":"estrangulamento.01","english_roleset":"constraint.01","xml":"constraint.xml","expected_occ":1,
   "rationale":"Financial 'estrangulamento $$$ da Petrobras' denotes a hindering resource/financial constraint. NomBank constraint.01 = prevent/hinder and includes 'a constraint to the market'."},
 "exceção":{"pt_roleset":"exceção.01","english_roleset":"deviation.01","xml":"deviation.xml","expected_occ":5,
   "rationale":"All examples mark an item/event as an exception to a prevailing rule or pattern. NomBank deviation.01 models departure from a path/pattern and includes 'deviation from our past growth patterns'."}
}

def parse_roles(xml_bytes, roleset_id):
    root=ET.fromstring(xml_bytes)
    rs=next((x for x in root.findall(".//roleset") if x.get("id")==roleset_id),None)
    assert rs is not None, roleset_id
    roles=[{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()]
    examples=[" ".join((ex.findtext("text") or "").split()) for ex in rs.findall("./example")]
    return roles,rs.get("name"),rs.get("source"),examples[:8]

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
            s["mapping_evidence"]={"xml_file":t["xml"],"roleset_name":name,"roleset_source":source,
                                  "rationale":t["rationale"],"nombank_examples":xml_examples}
            for ex in s.get("examples",[]):
                old=ex.get("realization") or {}; oldsyn=ex.get("syntax") or {}
                ex["realization"]={r["id"]:old.get(r["id"]) for r in roles}
                ex["syntax"]={r["id"]:oldsyn.get(r["id"]) for r in roles}
                ex["english_mapping_status"]="RESOLVED_REAL_NOMBANK_ROLESET"
                ledger.append({"lemma":lemma,"pt_roleset":t["pt_roleset"],"sent_id":ex.get("sent_ID",""),
                               "english_roleset":t["english_roleset"],"xml":t["xml"],"rationale":t["rationale"]})
    assert found,lemma
    (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert total==7,total
with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","pt_roleset","sent_id","english_roleset","xml","rationale"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(ledger)

validation={
 "status":"PASS_REAL_ENGLISH_MAPPING_CLOSURE",
 "resolved_lemmas":3,
 "resolved_occurrences":7,
 "cumulative_real_enmap_resolved":49,
 "global_pending_before_real_enmap":133,
 "global_pending_after_projection":84,
 "remaining_awaiting_english_mapping_occurrences":3,
 "remaining_awaiting_english_mapping_lemmas":3,
 "remaining_awaiting_english_mapping":["esperteza","movimento","vertigem"],
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H REAL ENMAP PARTIAL 008

Resolved with actual NomBank frames:
- antecipação.01 -> acceleration.01
- estrangulamento.01 -> constraint.01
- exceção.01 -> deviation.01

Scope: 3 lemmas / 7 occurrences.
Cumulative true ENMAP closure: 49/133.
Projected global pending: 84.
Remaining awaiting_english_mapping: 3 occurrences / 3 lemmas:
esperteza, movimento, vertigem.

Every mapping includes the original NomBank XML and contextual evidence.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_REAL_ENMAP_PARTIAL_008.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
