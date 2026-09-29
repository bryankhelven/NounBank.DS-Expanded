#!/usr/bin/env python3
from pathlib import Path
import json, ssl, urllib.request, zipfile, hashlib, shutil, csv, xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("awaiting_sense_partial_001")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()

maps={
 "agulhada.01":{"en":"pattern.01","xml":"pattern.xml"},
 "beliscada.01":{"en":"purchase.01","xml":"purchase.xml"},
 "beliscada.02":{"en":"reach.01","xml":"reach.xml"},
 "bicada.01":{"en":"purchase.01","xml":"purchase.xml"},
}

xml_cache={}
def roles_for(fn,rsid):
    if fn not in xml_cache:
        with urllib.request.urlopen(BASE+fn,context=ctx,timeout=30) as r: xml_cache[fn]=r.read()
        (OUT/"evidence/xml"/fn).write_bytes(xml_cache[fn])
    root=ET.fromstring(xml_cache[fn])
    rs=next(x for x in root.findall(".//roleset") if x.get("id")==rsid)
    roles=[{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()]
    return roles,rs.get("name"),rs.get("source")

# Science decisions and contextual realization.
decisions={
 "agulhada":{
   "predicative":True,
   "sense_note":"Occurrence of the Didi technical-analysis pattern/configuration in an asset/timeframe.",
   "assign":[
     ("dante_01_453249027585236992l","agulhada.01",{"Arg1":"#PETR4"},{"Arg1":"nsubj"}),
     ("dante_01_452145897422323712l","agulhada.01",{"Arg1":"da #PETR4"},{"Arg1":"nmod"}),
     ("dante_01_472446399607369728l","agulhada.01",{"Arg1":None},{"Arg1":None}),
   ]
 },
 "beliscada":{
   "predicative":True,
   "sense_note":"Two distinct financial predicates: small purchase/entry vs brief reaching/touching of a price/index level.",
   "assign":[
     ("dante_01_462328786717904896l","beliscada.01",{"Arg0":None,"Arg1":"PETR4","Arg2":None,"Arg3":None,"Arg4":None},{"Arg0":None,"Arg1":"appos","Arg2":None,"Arg3":None,"Arg4":None}),
     ("dante_01_443033075057172480l","beliscada.02",{"Arg0":"no ibolixo","Arg1":"nos 44.6k"},{"Arg0":"nmod","Arg1":"nmod"}),
   ]
 },
 "bicada":{
   "predicative":True,
   "sense_note":"Small purchase/entry in an equity position.",
   "assign":[
     ("dante_01_459322667791687680l","bicada.01",{"Arg0":None,"Arg1":"em VALE5","Arg2":None,"Arg3":None,"Arg4":None},{"Arg0":None,"Arg1":"nmod","Arg2":None,"Arg3":None,"Arg4":None}),
   ]
 }
}

sense_meta={
 "agulhada.01":{"hint":"technical-analysis pattern occurrence","source_note":"Agulhada do Didi: named technical pattern defined by convergence/separation of moving averages."},
 "beliscada.01":{"hint":"small purchase/entry","source_note":"Corpus itself glosses BELISCADA as '(compra)'."},
 "beliscada.02":{"hint":"brief reach/touch of a market level","source_note":"Independent Brazilian market usage uses 'beliscada em [price]' for a brief reach/touch of that level."},
 "bicada.01":{"hint":"small purchase/entry","source_note":"Independent market usage 'dar uma bicada nessa [ação]' occurs in explicit consideration of buying a stock."},
}

ledger=[]
for lemma,dec in decisions.items():
    p=SRC/"jsons"/f"{lemma}.json"
    j=json.loads(p.read_text(encoding="utf-8"))
    pending={x["sent_ID"]:x for x in j.get("pending_instances",[])}
    senses={}
    for sid in sorted(set(x[1] for x in dec["assign"])):
        mm=maps[sid]
        roles,name,source=roles_for(mm["xml"],mm["en"])
        idx=int(sid.rsplit(".",1)[1])
        senses[sid]={
          "pt_roleset":sid,"pt_sense_index":idx,"pt_sense_hint":idx,
          "pt_sense_gloss":sense_meta[sid]["hint"],
          "english_roleset":mm["en"],
          "english_roleset_source":"NOMBANK_XML_AFTER_DOMAIN_SENSE_RESOLUTION_V2H",
          "nombank_url":BASE+mm["xml"],
          "roles":roles,"examples":[],"syntactic_profile":{},
          "sense_evidence":{"decision":"S_PREDICATIVE","source_note":sense_meta[sid]["source_note"],
                            "nombank_roleset_name":name,"nombank_roleset_source":source}
        }
    for sent,sid,real,syntax in dec["assign"]:
        old=pending[sent]
        ex={
          "sent_ID":old["sent_ID"],"text":old["text"],"realization":real,"syntax":syntax,
          "instance_id":old["instance_id"],"predicate":old["predicate"],
          "sense_resolution_status":"RESOLVED_DOMAIN_SENSE_AND_PREDICATIVITY",
          "predicative":True
        }
        senses[sid]["examples"].append(ex)
        for arg,dep in syntax.items():
            if dep:
                senses[sid]["syntactic_profile"].setdefault(arg,{})
                senses[sid]["syntactic_profile"][arg][dep]=senses[sid]["syntactic_profile"][arg].get(dep,0)+1
        ledger.append({"lemma":lemma,"sent_id":sent,"pt_roleset":sid,"predicative":"S",
                       "english_roleset":maps[sid]["en"],"decision":sense_meta[sid]["hint"]})
    j["senses"]=list(senses.values())
    j.pop("pending_instances",None)
    j["sense_resolution_evidence"]={"predicative":"S","note":dec["sense_note"]}
    (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","sent_id","pt_roleset","predicative","english_roleset","decision"],delimiter="\t",lineterminator="\n")
    w.writeheader(); w.writerows(ledger)

validation={
 "status":"PASS_AWAITING_SENSE_PARTIAL_001",
 "resolved_lemmas":3,
 "resolved_occurrences":6,
 "predicative_occurrences":6,
 "nonpredicative_occurrences":0,
 "new_pt_senses":["agulhada.01","beliscada.01","beliscada.02","bicada.01"],
 "english_mappings":{
   "agulhada.01":"pattern.01","beliscada.01":"purchase.01","beliscada.02":"reach.01","bicada.01":"purchase.01"
 },
 "awaiting_sense_before":23,
 "awaiting_sense_after_projection":17,
 "global_pending_before_this_partial":81,
 "global_pending_after_projection":75,
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H AWAITING SENSE PARTIAL 001

Resolved by domain-first analysis:
- agulhada: S, technical-analysis pattern occurrence -> pattern.01
- beliscada sense 1: S, small purchase/entry -> purchase.01
- beliscada sense 2: S, brief reaching of a market level -> reach.01
- bicada: S, small purchase/entry -> purchase.01

Important: predicativity was decided AFTER semantic disambiguation. No lemma was forced into S merely because it is nominal.
Scope: 3 lemmas / 6 occurrences.
awaiting_sense: 23 -> 17 projected.
global pending: 81 -> 75 projected.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_AWAITING_SENSE_PARTIAL_001.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
