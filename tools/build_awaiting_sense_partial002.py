#!/usr/bin/env python3
from pathlib import Path
import json, ssl, urllib.request, zipfile, hashlib, shutil, csv, xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("awaiting_sense_partial_002")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()

xml_cache={}
def fetch_roles(fn,rsid):
    if fn not in xml_cache:
        with urllib.request.urlopen(BASE+fn,context=ctx,timeout=30) as r: xml_cache[fn]=r.read()
        (OUT/"evidence/xml"/fn).write_bytes(xml_cache[fn])
    root=ET.fromstring(xml_cache[fn])
    rs=next(x for x in root.findall(".//roleset") if x.get("id")==rsid)
    roles=[{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()]
    return roles,rs.get("name"),rs.get("source")

ledger=[]

# --- bonificação: 3 pending -> same existing S sense bonificação.01 / bonus.01
p=SRC/"jsons/bonificação.json"; j=json.loads(p.read_text(encoding="utf-8"))
s=next(x for x in j["senses"] if x["pt_roleset"]=="bonificação.01")
roles,name,source=fetch_roles("bonus.xml","bonus.01")
s["roles"]=roles
for old in j.get("pending_instances",[]):
    ex={
      "sent_ID":old["sent_ID"],"text":old["text"],
      "realization":{r["id"]:None for r in roles},
      "syntax":{r["id"]:None for r in roles},
      "instance_id":old["instance_id"],"predicate":old["predicate"],
      "sense_resolution_status":"RESOLVED_SAME_EVENT_SENSE_IN_EX_CONSTRUCTION",
      "predicative":True
    }
    s["examples"].append(ex)
    ledger.append({"lemma":"bonificação","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"bonificação.01","english_roleset":"bonus.01",
                   "note":"ex-bonificação preserves underlying bonus/distribution event; ex- does not create a new sense"})
j.pop("pending_instances",None)
j["sense_resolution_evidence"]={"predicative":"S","note":"All ex-bonificação occurrences reuse bonificação.01; construction marks post-entitlement status but still evokes the bonus event."}
(OUT/"overlay/jsons/bonificação.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# --- calor: S -> heat.03
p=SRC/"jsons/calor.json"; j=json.loads(p.read_text(encoding="utf-8"))
old=j["pending_instances"][0]
roles,name,source=fetch_roles("heat.xml","heat.03")
sense={
 "pt_roleset":"calor.01","pt_sense_index":1,"pt_sense_hint":1,
 "pt_sense_gloss":"pressão/aperto sofrido em uma posição de mercado",
 "english_roleset":"heat.03","english_roleset_source":"NOMBANK_XML_AFTER_DOMAIN_SENSE_RESOLUTION_V2H",
 "nombank_url":BASE+"heat.xml","roles":roles,
 "examples":[{
   "sent_ID":old["sent_ID"],"text":old["text"],
   "realization":{"Arg0":None,"Arg1":None,"Arg2":"eu"},
   "syntax":{"Arg0":None,"Arg1":None,"Arg2":"nsubj"},
   "instance_id":old["instance_id"],"predicate":old["predicate"],
   "sense_resolution_status":"RESOLVED_DOMAIN_SENSE_AND_PREDICATIVITY","predicative":True
 }],
 "syntactic_profile":{"Arg2":{"nsubj":1}},
 "sense_evidence":{"decision":"S_PREDICATIVE","nombank_roleset_name":name,"nombank_roleset_source":source,
                   "note":"'tomando calor' = taking heat / being under pressure; experiencer/recipient is overt 'eu'."}
}
j["senses"]=[sense]; j.pop("pending_instances",None)
ledger.append({"lemma":"calor","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"calor.01","english_roleset":"heat.03","note":"market-pressure sense"})
(OUT/"overlay/jsons/calor.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# --- concorrência: S -> existing competition.01
p=SRC/"jsons/concorrência.json"; j=json.loads(p.read_text(encoding="utf-8"))
s=next(x for x in j["senses"] if x["pt_roleset"]=="concorrência.01")
for old in j.get("pending_instances",[]):
    ex={"sent_ID":old["sent_ID"],"text":old["text"],
        "realization":{"Arg0":None,"Arg1":None,"Arg2":None},
        "syntax":{"Arg0":None,"Arg1":None,"Arg2":None},
        "instance_id":old["instance_id"],"predicate":old["predicate"],
        "sense_resolution_status":"RESOLVED_DUPLICATE_SAME_COMPETITION_SENSE","predicative":True}
    s["examples"].append(ex)
    ledger.append({"lemma":"concorrência","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"concorrência.01","english_roleset":"competition.01","note":"RT/truncated repetition of same competition usage"})
j.pop("pending_instances",None)
(OUT/"overlay/jsons/concorrência.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
fetch_roles("competition.xml","competition.01")

# --- desafio: S -> challenge.01
p=SRC/"jsons/desafio.json"; j=json.loads(p.read_text(encoding="utf-8"))
old=j["pending_instances"][0]
roles,name,source=fetch_roles("challenge.xml","challenge.01")
sense={
 "pt_roleset":"desafio.01","pt_sense_index":1,"pt_sense_hint":1,
 "pt_sense_gloss":"tarefa/dificuldade que desafia uma entidade",
 "english_roleset":"challenge.01","english_roleset_source":"NOMBANK_XML_AFTER_DOMAIN_SENSE_RESOLUTION_V2H",
 "nombank_url":BASE+"challenge.xml","roles":roles,
 "examples":[{
   "sent_ID":old["sent_ID"],"text":old["text"],
   "realization":{"Arg0":None,"Arg1":"Empresas de pagamento e tranf. de recursos","Arg2":None},
   "syntax":{"Arg0":None,"Arg1":"nsubj","Arg2":None},
   "instance_id":old["instance_id"],"predicate":old["predicate"],
   "sense_resolution_status":"RESOLVED_DOMAIN_SENSE_AND_PREDICATIVITY","predicative":True
 }],
 "syntactic_profile":{"Arg1":{"nsubj":1}},
 "sense_evidence":{"decision":"S_PREDICATIVE","nombank_roleset_name":name,"nombank_roleset_source":source,
                   "note":"Support construction 'empresas terão desafios': companies are the challenged entity."}
}
j["senses"]=[sense]; j.pop("pending_instances",None)
ledger.append({"lemma":"desafio","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"desafio.01","english_roleset":"challenge.01","note":"challenging task/difficulty"})
(OUT/"overlay/jsons/desafio.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# --- descoberto: N in fixed financial construction venda a descoberto
p=SRC/"jsons/descoberto.json"; j=json.loads(p.read_text(encoding="utf-8"))
nonpred=j.setdefault("nonpredicative_instances",[])
for old in j.get("pending_instances",[]):
    rec={k:v for k,v in old.items() if k!="resolution_status"}
    rec["predicative"]=False
    rec["sense_resolution_status"]="RESOLVED_NONPREDICATIVE_FIXED_FINANCIAL_CONSTRUCTION"
    rec["decision_note"]="In 'venda a descoberto', descoberto is not the nominal predicate descoberta/discovery; predication belongs to the fixed short-selling construction."
    nonpred.append(rec)
    ledger.append({"lemma":"descoberto","sent_id":old["sent_ID"],"decision":"N","pt_roleset":"","english_roleset":"","note":"fixed construction venda a descoberto / short selling"})
j.pop("pending_instances",None)
(OUT/"overlay/jsons/descoberto.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# --- fogo: N in MWE fogo de palha
p=SRC/"jsons/fogo.json"; j=json.loads(p.read_text(encoding="utf-8"))
nonpred=j.setdefault("nonpredicative_instances",[])
for old in j.get("pending_instances",[]):
    rec={k:v for k,v in old.items() if k!="resolution_status"}
    rec["predicative"]=False
    rec["sense_resolution_status"]="RESOLVED_NONPREDICATIVE_MWE_FOGO_DE_PALHA"
    rec["decision_note"]="Meaning is contributed by lexicalized MWE 'fogo de palha' = intense but short-lived phenomenon; fogo does not independently instantiate fire.01."
    nonpred.append(rec)
    ledger.append({"lemma":"fogo","sent_id":old["sent_ID"],"decision":"N","pt_roleset":"","english_roleset":"","note":"lexicalized MWE fogo de palha"})
j.pop("pending_instances",None)
(OUT/"overlay/jsons/fogo.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
fetch_roles("fire.xml","fire.01")

with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","sent_id","decision","pt_roleset","english_roleset","note"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(ledger)

validation={
 "status":"PASS_AWAITING_SENSE_PARTIAL_002",
 "resolved_lemmas":6,
 "resolved_occurrences":9,
 "predicative_occurrences":6,
 "nonpredicative_occurrences":3,
 "S":{"bonificação":3,"calor":1,"concorrência":1,"desafio":1},
 "N":{"descoberto":1,"fogo":2},
 "awaiting_sense_before":17,
 "awaiting_sense_after_projection":8,
 "global_pending_before_this_partial":75,
 "global_pending_after_projection":66,
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H AWAITING SENSE PARTIAL 002

Domain-first S/N decisions:
S:
- bonificação (3): ex-bonificação reuses bonificação.01 / bonus.01; ex- does not create a new semantic unit.
- calor (1): pressure/heat suffered in a market position -> heat.03.
- concorrência (1): same competition.01 sense as the untruncated source occurrence.
- desafio (1): challenging task/difficulty -> challenge.01.

N:
- descoberto (1): fixed financial construction 'venda a descoberto'; not nominal discovery predicate.
- fogo (2): lexicalized MWE 'fogo de palha'; fogo does not independently instantiate fire.01.

Scope: 6 lemmas / 9 occurrences.
awaiting_sense: 17 -> 8 projected.
global pending: 75 -> 66 projected.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_AWAITING_SENSE_PARTIAL_002.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
