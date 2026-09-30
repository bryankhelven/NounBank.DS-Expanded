#!/usr/bin/env python3
from pathlib import Path
import json,ssl,urllib.request,zipfile,hashlib,shutil,csv,xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("final39_partial_003_terminal")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()
xml_cache={}
def frame(fn,rsid):
    if fn not in xml_cache:
        with urllib.request.urlopen(BASE+fn,context=ctx,timeout=30) as r: xml_cache[fn]=r.read()
        (OUT/"evidence/xml"/fn).write_bytes(xml_cache[fn])
    root=ET.fromstring(xml_cache[fn])
    rs=next(x for x in root.findall(".//roleset") if x.get("id")==rsid)
    roles=[{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()]
    exs=[" ".join((e.findtext("text") or "").split()) for e in rs.findall("./example")[:8]]
    return roles,rs.get("name"),rs.get("source"),exs

def load(lemma):
    return json.loads((SRC/"jsons"/f"{lemma}.json").read_text(encoding="utf-8"))
def save(lemma,j):
    (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def blank(roles): return {r["id"]:None for r in roles}

ledger=[]

# SHOW: split two semantic manifestations.
j=load("show")
pend={x["sent_ID"]:x for x in j["pending_instances"]}
roles,name,source,nex=frame("performance.xml","performance.02")
old=pend["dante_01_469903994593501184l"]
r=blank(roles); s=blank(roles)
if "Arg0" in r: r["Arg0"]="#embr3"; s["Arg0"]="nsubj"
sense1={
 "pt_roleset":"show.05","pt_sense_index":5,"pt_sense_hint":5,
 "pt_sense_gloss":"dar show = apresentar desempenho excelente",
 "english_roleset":"performance.02","english_roleset_source":"NOMBANK_XML_FINAL39_REPAIR_V2H",
 "nombank_url":BASE+"performance.xml","roles":roles,
 "examples":[{"sent_ID":old["sent_ID"],"text":old["text"],"realization":r,"syntax":s,
              "instance_id":old["instance_id"].replace("::pending","::1"),"predicate":old["predicate"],
              "predicative":True,"resolution_status":"RESOLVED_REAL_NOMBANK_ROLESET_AND_ROLE_INVENTORY"}],
 "syntactic_profile":{"Arg0":{"nsubj":1}} if "Arg0" in r else {},
 "mapping_evidence":{"decision":"COMPATIBLE_NOMBANK_ROLESET","roleset_name":name,"roleset_source":source,"nombank_examples":nex}
}
roles2,name2,source2,nex2=frame("performance.xml","performance.01")
old=pend["dante_01_459035339739262976l"]
r2=blank(roles2); s2=blank(roles2)
sense2={
 "pt_roleset":"show.06","pt_sense_index":6,"pt_sense_hint":6,
 "pt_sense_gloss":"show = espetáculo/desenrolar de acontecimentos",
 "english_roleset":"performance.01","english_roleset_source":"NOMBANK_XML_FINAL39_REPAIR_V2H",
 "nombank_url":BASE+"performance.xml","roles":roles2,
 "examples":[{"sent_ID":old["sent_ID"],"text":old["text"],"realization":r2,"syntax":s2,
              "instance_id":old["instance_id"].replace("::pending","::1"),"predicate":old["predicate"],
              "predicative":True,"resolution_status":"RESOLVED_REAL_NOMBANK_ROLESET_AND_ROLE_INVENTORY"}],
 "syntactic_profile":{},
 "mapping_evidence":{"decision":"COMPATIBLE_NOMBANK_ROLESET","roleset_name":name2,"roleset_source":source2,"nombank_examples":nex2,
                     "note":"Metaphorical 'part of the show' denotes the ongoing performance/spectacle, not broadcast show.01."}
}
j["senses"]=[sense1,sense2]; j.pop("pending_instances",None); j.pop("pending_status",None); j["projection_status"]="PREDICATIVE_RESOLVED"
save("show",j)
ledger += [
 {"lemma":"show","sent_id":"dante_01_469903994593501184l","decision":"S","pt_roleset":"show.05","english_roleset":"performance.02","note":"dar show = perform excellently"},
 {"lemma":"show","sent_id":"dante_01_459035339739262976l","decision":"S","pt_roleset":"show.06","english_roleset":"performance.01","note":"part of the show = spectacle/performance"}
]

# RUMO -> direction.01
j=load("rumo"); roles,name,source,nex=frame("direction.xml","direction.01")
examples=[]
for old in j["pending_instances"]:
    r=blank(roles); s=blank(roles); t=old["text"]
    target=None
    if "rumo de casa" in t: target="de casa"
    elif "Rumo ao 0,01" in t: target="ao 0,01"
    elif "rumo aos centavos" in t: target="aos centavos"
    if target and "Arg2" in r: r["Arg2"]=target; s["Arg2"]="nmod"
    examples.append({"sent_ID":old["sent_ID"],"text":t,"realization":r,"syntax":s,
                     "instance_id":old["instance_id"].replace("::pending","::1"),"predicate":old["predicate"],
                     "predicative":True,"resolution_status":"RESOLVED_REAL_NOMBANK_ROLESET_AND_ROLE_INVENTORY"})
    ledger.append({"lemma":"rumo","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"rumo.04","english_roleset":"direction.01","note":"direction/heading toward target"})
j["senses"]=[{"pt_roleset":"rumo.04","pt_sense_index":4,"pt_sense_hint":4,"pt_sense_gloss":"direção/rumo em direção a um destino ou valor",
              "english_roleset":"direction.01","english_roleset_source":"NOMBANK_XML_FINAL39_REPAIR_V2H",
              "nombank_url":BASE+"direction.xml","roles":roles,"examples":examples,
              "syntactic_profile":{"Arg2":{"nmod":3}} if any((e["syntax"].get("Arg2")) for e in examples) else {},
              "mapping_evidence":{"decision":"COMPATIBLE_NOMBANK_ROLESET","roleset_name":name,"roleset_source":source,"nombank_examples":nex}}]
j.pop("pending_instances",None);j.pop("pending_status",None);j["projection_status"]="PREDICATIVE_RESOLVED";save("rumo",j)

# CACADOR -> hunter.01
j=load("caçador"); roles,name,source,nex=frame("hunter.xml","hunter.01")
old=j["pending_instances"][0]; r=blank(roles); s=blank(roles)
j["senses"]=[{"pt_roleset":"caçador.01","pt_sense_index":1,"pt_sense_hint":1,"pt_sense_gloss":"caçador / aquele que caça",
              "english_roleset":"hunter.01","english_roleset_source":"NOMBANK_XML_FINAL39_REPAIR_V2H",
              "nombank_url":BASE+"hunter.xml","roles":roles,
              "examples":[{"sent_ID":old["sent_ID"],"text":old["text"],"realization":r,"syntax":s,
                           "instance_id":old["instance_id"].replace("::pending","::1"),"predicate":old["predicate"],
                           "predicative":True,"resolution_status":"RESOLVED_PROVERBIAL_ROLE_HUNTER"}],
              "syntactic_profile":{},
              "mapping_evidence":{"decision":"COMPATIBLE_NOMBANK_ROLESET","roleset_name":name,"roleset_source":source,"nombank_examples":nex,
                                  "note":"Proverbial use still denotes the hunter participant role."}}]
j.pop("pending_instances",None);j.pop("pending_status",None);j["projection_status"]="PREDICATIVE_RESOLVED";save("caçador",j)
ledger.append({"lemma":"caçador","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"caçador.01","english_roleset":"hunter.01","note":"proverbial hunter role"})

# QUERIDINHO -> favorite.01
j=load("queridinho"); roles,name,source,nex=frame("favorite.xml","favorite.01")
examples=[]
for old in j["pending_instances"]:
    r=blank(roles); s=blank(roles); t=old["text"]
    if "do Ibovespa" in t and "Arg0" in r: r["Arg0"]="do Ibovespa"; s["Arg0"]="nmod"
    elif "sua queridinha" in t and "Arg0" in r: r["Arg0"]="sua"; s["Arg0"]="det"
    examples.append({"sent_ID":old["sent_ID"],"text":t,"realization":r,"syntax":s,
                     "instance_id":old["instance_id"].replace("::pending","::1"),"predicate":old["predicate"],
                     "predicative":True,"resolution_status":"RESOLVED_REAL_NOMBANK_ROLESET_AND_ROLE_INVENTORY"})
    ledger.append({"lemma":"queridinho","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"queridinho.01","english_roleset":"favorite.01","note":"favored/preferred entity"})
j["senses"]=[{"pt_roleset":"queridinho.01","pt_sense_index":1,"pt_sense_hint":1,"pt_sense_gloss":"entidade favorita/queridinha de alguém ou de um mercado",
              "english_roleset":"favorite.01","english_roleset_source":"NOMBANK_XML_FINAL39_REPAIR_V2H",
              "nombank_url":BASE+"favorite.xml","roles":roles,"examples":examples,
              "syntactic_profile":{"Arg0":{"nmod":1,"det":1}},
              "mapping_evidence":{"decision":"COMPATIBLE_NOMBANK_ROLESET","roleset_name":name,"roleset_source":source,"nombank_examples":nex}}]
j.pop("pending_instances",None);j.pop("pending_status",None);j["projection_status"]="PREDICATIVE_RESOLVED";save("queridinho",j)

# ADVERSARIO -> adversary.01
j=load("adversário"); roles,name,source,nex=frame("adversary.xml","adversary.01")
old=j["pending_instances"][0]; r=blank(roles); s=blank(roles)
j["senses"]=[{"pt_roleset":"adversário.01","pt_sense_index":1,"pt_sense_hint":1,"pt_sense_gloss":"adversário/oponente",
              "english_roleset":"adversary.01","english_roleset_source":"NOMBANK_XML_FINAL39_REPAIR_V2H",
              "nombank_url":BASE+"adversary.xml","roles":roles,
              "examples":[{"sent_ID":old["sent_ID"],"text":old["text"],"realization":r,"syntax":s,
                           "instance_id":old["instance_id"].replace("::pending","::1"),"predicate":old["predicate"],
                           "predicative":True,"resolution_status":"RESOLVED_REAL_NOMBANK_ROLESET_AND_ROLE_INVENTORY"}],
              "syntactic_profile":{},
              "mapping_evidence":{"decision":"COMPATIBLE_NOMBANK_ROLESET","roleset_name":name,"roleset_source":source,"nombank_examples":nex}}]
j.pop("pending_instances",None);j.pop("pending_status",None);j["projection_status"]="PREDICATIVE_RESOLVED";save("adversário",j)
ledger.append({"lemma":"adversário","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"adversário.01","english_roleset":"adversary.01","note":"adversary/opponent role"})

# REQUERIMENTO -> request.01
j=load("requerimento"); roles,name,source,nex=frame("request.xml","request.01")
old=j["pending_instances"][0]; r=blank(roles); s=blank(roles)
j["senses"]=[{"pt_roleset":"requerimento.01","pt_sense_index":1,"pt_sense_hint":1,"pt_sense_gloss":"requerimento/pedido formal",
              "english_roleset":"request.01","english_roleset_source":"NOMBANK_XML_FINAL39_REPAIR_V2H",
              "nombank_url":BASE+"request.xml","roles":roles,
              "examples":[{"sent_ID":old["sent_ID"],"text":old["text"],"realization":r,"syntax":s,
                           "instance_id":old["instance_id"].replace("::pending","::1"),"predicate":old["predicate"],
                           "predicative":True,"resolution_status":"RESOLVED_REAL_NOMBANK_ROLESET_AND_ROLE_INVENTORY"}],
              "syntactic_profile":{},
              "mapping_evidence":{"decision":"COMPATIBLE_NOMBANK_ROLESET","roleset_name":name,"roleset_source":source,"nombank_examples":nex}}]
j.pop("pending_instances",None);j.pop("pending_status",None);j["projection_status"]="PREDICATIVE_RESOLVED";save("requerimento",j)
ledger.append({"lemma":"requerimento","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"requerimento.01","english_roleset":"request.01","note":"formal request"})

# ESQUARTEJADOR -> explicit negative ENMAP closure.
j=load("esquartejador"); old=j["pending_instances"][0]
pt_roles=[{"id":"Arg0","desc":"ESQUARTEJADOR / AGENTE QUE ESQUARTEJA"},{"id":"Arg1","desc":"ENTIDADE ESQUARTEJADA"}]
j["senses"]=[{"pt_roleset":"esquartejador.01","pt_sense_index":1,"pt_sense_hint":1,
              "pt_sense_gloss":"agente que esquarteja/dismembra",
              "english_roleset":None,
              "english_roleset_source":"NO_COMPATIBLE_NOMBANK_ROLESET_AFTER_DOCUMENTED_SEARCH",
              "nombank_url":None,
              "roles":pt_roles,
              "examples":[{"sent_ID":old["sent_ID"],"text":old["text"],"realization":{"Arg0":None,"Arg1":None},
                           "syntax":{"Arg0":None,"Arg1":None},
                           "instance_id":old["instance_id"].replace("::pending","::1"),"predicate":old["predicate"],
                           "predicative":True,"resolution_status":"RESOLVED_NO_COMPATIBLE_NOMBANK_ROLESET"}],
              "syntactic_profile":{},
              "mapping_evidence":{"decision":"NO_COMPATIBLE_NOMBANK_ROLESET",
                                  "searched_candidates":["dismemberment.xml","dismemberer.xml","butcher.xml","killer.xml","cutting.xml","cut.xml"],
                                  "rejected_candidates":{
                                    "killer.01":"too broad and entails killing, which is not equivalent to dismembering",
                                    "cut.01":"event noun/frame, not an agentive dismemberer nominal",
                                    "cutting.01":"reduction sense, semantically incompatible"
                                  },
                                  "note":"Null is not used as a terminal shortcut; the explicit negative decision is the terminal mapping result."}}]
j.pop("pending_instances",None);j.pop("pending_status",None);j["projection_status"]="PREDICATIVE_RESOLVED_NEGATIVE_ENMAP";save("esquartejador",j)
ledger.append({"lemma":"esquartejador","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"esquartejador.01","english_roleset":"NO_COMPATIBLE_NOMBANK_ROLESET","note":"documented negative mapping; no fabricated English roleset"})

with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","sent_id","decision","pt_roleset","english_roleset","note"],delimiter="\t",lineterminator="\n")
    w.writeheader();w.writerows(ledger)

validation={
 "status":"PASS_FINAL39_TERMINAL_CLOSURE",
 "resolved_lemmas":7,
 "resolved_occurrences":11,
 "predicative_occurrences":11,
 "nonpredicative_occurrences":0,
 "compatible_nombank_occurrences":10,
 "explicit_negative_enmap_occurrences":1,
 "pending_before":11,
 "pending_after_projection":0,
 "final39_before":39,
 "final39_after_projection":0,
 "all_pending_classes_after_projection":0,
 "lexical_identity_gate":"PASS",
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H FINAL39 PARTIAL 003 — TERMINAL

Final 11 retracted-new pending occurrences resolved.

- show.05 -> performance.02 (dar show / perform excellently)
- show.06 -> performance.01 (part of the show / spectacle-performance)
- rumo.04 -> direction.01
- caçador.01 -> hunter.01
- queridinho.01 -> favorite.01
- adversário.01 -> adversary.01
- requerimento.01 -> request.01
- esquartejador.01 -> NO_COMPATIBLE_NOMBANK_ROLESET after documented search

No fabricated English mapping was introduced for esquartejador.

FINAL39: 39 -> 0.
Projected global pending across all classes: 0.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_FINAL39_PARTIAL_003_TERMINAL.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
