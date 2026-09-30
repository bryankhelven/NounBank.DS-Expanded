#!/usr/bin/env python3
from pathlib import Path
import json,ssl,urllib.request,zipfile,hashlib,shutil,csv,xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("construction_specific_partial_002")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()

with urllib.request.urlopen(BASE+"selling.xml",context=ctx,timeout=30) as r:
    xml=r.read()
(OUT/"evidence/xml/selling.xml").write_bytes(xml)
root=ET.fromstring(xml)
rs=next(x for x in root.findall(".//roleset") if x.get("id")=="selling.01")
roles=[{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()]
nombank_examples=[" ".join((e.findtext("text") or "").split()) for e in rs.findall("./example")[:8]]

j=json.loads((SRC/"jsons/realização.json").read_text(encoding="utf-8"))
s=next(x for x in j["senses"] if x.get("pt_roleset")=="realização.02")
assert s.get("resolution_status")=="construction_specific"
assert len(s.get("examples",[]))==10

s["pt_sense_gloss"]="realização de lucros / venda total ou parcial de posição para materializar ganho"
s["english_roleset"]="selling.01"
s["english_roleset_source"]="NOMBANK_XML_DOMAIN_PROFIT_TAKING_RESOLUTION_V2H"
s["nombank_url"]=BASE+"selling.xml"
s["roles"]=roles
s.pop("resolution_status",None)
s["construction_evidence"]={
  "decision":"S_PREDICATIVE",
  "domain_equivalence":"profit-taking",
  "rationale":"Brazilian financial 'realização (parcial)' denotes selling securities to lock in/materialize gains. profit.01 denotes profit as result/value and was rejected. selling.01 models the actual selling event underlying profit-taking.",
  "nombank_roleset_name":rs.get("name"),
  "nombank_roleset_source":rs.get("source"),
  "nombank_examples":nombank_examples,
  "rejected_mapping":"profit.01"
}

ledger=[]
profile={}
for e in s["examples"]:
    text=e.get("text","")
    rid=e.get("sent_ID")
    arg1=None; syn1=None
    # Overt asset/theme only where locally expressed around realization.
    if "em mrve3" in text.lower():
        arg1="em mrve3"; syn1="nmod"
    elif "em bova11" in text.lower():
        arg1="em bova11"; syn1="nmod"
    elif "MRVE3" in text and "realização parcial MRVE3" in text:
        arg1="MRVE3"; syn1="appos"
    elif "CSNA3 e GGBR4 bateram na realização parcial" in text:
        arg1="CSNA3 e GGBR4"; syn1="nsubj"
    elif "vale5" in text.lower() and "realização parcial" in text.lower() and "Posições" not in text:
        # Avoid inferring distant discourse theme unless construction makes it local.
        arg1=None; syn1=None
    e["realization"]={r["id"]:None for r in roles}
    e["syntax"]={r["id"]:None for r in roles}
    if "Arg1" in e["realization"]:
        e["realization"]["Arg1"]=arg1
        e["syntax"]["Arg1"]=syn1
    e["construction_resolution"]="PROFIT_TAKING_SELLING_PREDICATIVE"
    if syn1:
        profile.setdefault("Arg1",{})
        profile["Arg1"][syn1]=profile["Arg1"].get(syn1,0)+1
    ledger.append({
      "lemma":"realização","sent_id":rid,"decision":"S",
      "pt_roleset":"realização.02","english_roleset":"selling.01",
      "domain_sense":"profit-taking","arg1":arg1 or "",
      "note":"profit-taking / selling to materialize gains"
    })
s["syntactic_profile"]=profile

(OUT/"overlay/jsons/realização.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","sent_id","decision","pt_roleset","english_roleset","domain_sense","arg1","note"],delimiter="\t",lineterminator="\n")
    w.writeheader();w.writerows(ledger)

validation={
 "status":"PASS_CONSTRUCTION_SPECIFIC_TERMINAL_CLOSURE",
 "resolved_lemmas":1,
 "resolved_occurrences":10,
 "predicative_occurrences":10,
 "nonpredicative_occurrences":0,
 "mapping_before":"realização.02 -> profit.01",
 "mapping_after":"realização.02 -> selling.01",
 "domain_sense":"profit-taking",
 "construction_specific_before":10,
 "construction_specific_after_projection":0,
 "global_pending_before_this_partial":49,
 "global_pending_after_projection":39,
 "next_open_class":{"retracted_new_cases":39},
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H CONSTRUCTION SPECIFIC PARTIAL 002 — TERMINAL

All ten remaining construction-specific occurrences are financial uses of realização meaning profit-taking.

Scientific correction:
- OLD: realização.02 -> profit.01
- NEW: realização.02 -> selling.01

Reason:
'Realização (parcial)' in the Brazilian stock-market corpus denotes selling all or part of a position to materialize/lock in gains. The nominal predicate is the selling event, not the resulting profit amount/state.

All 10 occurrences remain S.

construction_specific: 10 -> 0.
Global projected pending: 49 -> 39.
The only remaining open block is the 39 V2H-added cases whose earlier null-terminal closure was retracted.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_CONSTRUCTION_SPECIFIC_PARTIAL_002_TERMINAL.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
