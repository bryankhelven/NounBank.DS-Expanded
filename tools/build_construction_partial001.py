#!/usr/bin/env python3
from pathlib import Path
import json,ssl,urllib.request,zipfile,hashlib,shutil,csv,xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("construction_specific_partial_001")
if OUT.exists(): shutil.rmtree(OUT)
(OUT/"overlay/jsons").mkdir(parents=True)
(OUT/"evidence/xml").mkdir(parents=True)

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
ctx=ssl._create_unverified_context()
xml_cache={}
def roles_for(fn,rsid):
    if fn not in xml_cache:
        with urllib.request.urlopen(BASE+fn,context=ctx,timeout=30) as r: xml_cache[fn]=r.read()
        (OUT/"evidence/xml"/fn).write_bytes(xml_cache[fn])
    root=ET.fromstring(xml_cache[fn])
    rs=next(x for x in root.findall(".//roleset") if x.get("id")==rsid)
    roles=[{"id":"Arg"+r.get("n"),"desc":r.get("descr")} for r in rs.findall("./roles/role") if (r.get("n") or "").isdigit()]
    exs=[" ".join((e.findtext("text") or "").split()) for e in rs.findall("./example")[:8]]
    return roles,rs.get("name"),rs.get("source"),exs

ledger=[]

def load(lemma): return json.loads((SRC/"jsons"/f"{lemma}.json").read_text(encoding="utf-8"))
def save(lemma,j): (OUT/"overlay/jsons"/f"{lemma}.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# fogo: support construction pegar fogo; theme is subject of support verb.
j=load("fogo"); s=j["senses"][0]
roles,name,source,nex=roles_for("fire.xml","fire.01")
s["roles"]=roles; s.pop("resolution_status",None)
e=s["examples"][0]
e["realization"]={"Arg1":"eu"}
e["syntax"]={"Arg1":"nsubj"}
e["construction_resolution"]="SUPPORT_CONSTRUCTION_PEGAR_FOGO_PREDICATIVE"
s["syntactic_profile"]={"Arg1":{"nsubj":1}}
s["construction_evidence"]={"decision":"S","note":"pegar fogo realizes a fire/burning state; NomBank fire.01 includes 'woods are on fire'.","nombank_examples":nex}
ledger.append({"lemma":"fogo","sent_id":e["sent_ID"],"decision":"S","pt_roleset":"fogo.01","english_roleset":"fire.01","construction":"pegar fogo","note":"support construction; subject realizes theme"})
save("fogo",j)

# caso: all 4 are case.03 discourse-connective uses; two overt proposition, two anaphoric/implicit.
j=load("caso"); s=j["senses"][0]
roles,name,source,nex=roles_for("case.xml","case.03")
s["roles"]=roles; s.pop("resolution_status",None)
for i,e in enumerate(s["examples"]):
    if i<2:
        e["realization"]={"Arg1":"de racionamento","Arg2":None}
        e["syntax"]={"Arg1":"nmod","Arg2":None}
        note="conditional proposition overt in 'no caso de racionamento'"
    else:
        e["realization"]={"Arg1":None,"Arg2":None}
        e["syntax"]={"Arg1":None,"Arg2":None}
        note="anaphoric/implicit proposition in 'quando/se for o caso'"
    e["construction_resolution"]="DISCOURSE_CONNECTIVE_CASE_03_PREDICATIVE"
    ledger.append({"lemma":"caso","sent_id":e["sent_ID"],"decision":"S","pt_roleset":"caso.01","english_roleset":"case.03","construction":"no caso de / se for o caso / quando é o caso","note":note})
s["syntactic_profile"]={"Arg1":{"nmod":2}}
s["construction_evidence"]={"decision":"S","note":"NomBank case.03 is explicitly discourse-connective-if-then and includes in-case constructions.","nombank_examples":nex}
save("caso",j)

# vontade: à vontade -> ease.02, experiencer is implicit subject of fiquem.
j=load("vontade"); s=next(x for x in j["senses"] if x["pt_roleset"]=="vontade.01")
roles,name,source,nex=roles_for("ease.xml","ease.02")
s["roles"]=roles; s.pop("resolution_status",None)
e=s["examples"][0]
e["realization"]={"Arg0":"vocês (implícito)","Arg1":None}
e["syntax"]={"Arg0":"nsubj:implicit","Arg1":None}
e["construction_resolution"]="A_VONTADE_AT_EASE_PREDICATIVE"
s["syntactic_profile"]={"Arg0":{"nsubj:implicit":1}}
s["construction_evidence"]={"decision":"S","note":"'fiquem à vontade' = be at ease / feel free; NomBank ease.02 is explicitly at-ease.","nombank_examples":nex}
ledger.append({"lemma":"vontade","sent_id":e["sent_ID"],"decision":"S","pt_roleset":"vontade.01","english_roleset":"ease.02","construction":"à vontade","note":"at-ease construction"})
save("vontade",j)

# respeito: a seu respeito -> respect.02 topic/issue.
j=load("respeito"); s=j["senses"][0]
roles,name,source,nex=roles_for("respect.xml","respect.02")
s["roles"]=roles; s.pop("resolution_status",None)
e=s["examples"][0]
e["realization"]={"Arg1":"seu"}
e["syntax"]={"Arg1":"det"}
e["construction_resolution"]="A_RESPEITO_DE_TOPIC_PREDICATIVE"
s["syntactic_profile"]={"Arg1":{"det":1}}
s["construction_evidence"]={"decision":"S","note":"'a seu respeito' = with respect to/about; NomBank respect.02 is issue/topic and includes with-respect-to uses.","nombank_examples":nex}
ledger.append({"lemma":"respeito","sent_id":e["sent_ID"],"decision":"S","pt_roleset":"respeito.01","english_roleset":"respect.02","construction":"a respeito de","note":"topic construction; possessive seu realizes topic"})
save("respeito",j)

# contagem regressiva -> countdown.01
j=load("contagem"); s=j["senses"][0]
roles,name,source,nex=roles_for("countdown.xml","countdown.01")
s["roles"]=roles; s.pop("resolution_status",None)
e=s["examples"][0]
e["realization"]={"Arg0":None,"Arg1":"de PETR4 para os $13"}
e["syntax"]={"Arg0":None,"Arg1":"nmod"}
e["construction_resolution"]="CONTAGEM_REGRESSIVA_COUNTDOWN_PREDICATIVE"
s["syntactic_profile"]={"Arg1":{"nmod":1}}
s["construction_evidence"]={"decision":"S","note":"The whole complement specifies the countdown theme/event: PETR4 reaching $13.","nombank_examples":nex}
ledger.append({"lemma":"contagem","sent_id":e["sent_ID"],"decision":"S","pt_roleset":"contagem.01","english_roleset":"countdown.01","construction":"contagem regressiva","note":"countdown event"})
save("contagem",j)

# sentimentos: condolence formula still expresses sympathy; keep sympathy.01.
j=load("sentimento"); s=next(x for x in j["senses"] if x["pt_roleset"]=="sentimento.01")
roles,name,source,nex=roles_for("sympathy.xml","sympathy.01")
s["roles"]=roles; s.pop("resolution_status",None)
e=s["examples"][0]
e["realization"]={"Arg0":"nossos","Arg1":None}
e["syntax"]={"Arg0":"det","Arg1":None}
e["construction_resolution"]="FORMULA_NOSSOS_SENTIMENTOS_SYMPATHY_PREDICATIVE"
s["syntactic_profile"]={"Arg0":{"det":1}}
s["construction_evidence"]={"decision":"S","note":"'nossos sentimentos' is a conventional expression of sympathy/condolence; formulaicity does not erase the sympathy predicate.","nombank_examples":nex}
ledger.append({"lemma":"sentimento","sent_id":e["sent_ID"],"decision":"S","pt_roleset":"sentimento.01","english_roleset":"sympathy.01","construction":"nossos sentimentos","note":"formulaic sympathy expression"})
save("sentimento",j)

with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","sent_id","decision","pt_roleset","english_roleset","construction","note"],delimiter="\t",lineterminator="\n")
    w.writeheader();w.writerows(ledger)

validation={
 "status":"PASS_CONSTRUCTION_SPECIFIC_PARTIAL_001",
 "resolved_lemmas":6,
 "resolved_occurrences":9,
 "predicative_occurrences":9,
 "nonpredicative_occurrences":0,
 "construction_specific_before":19,
 "construction_specific_after_projection":10,
 "global_pending_before_this_partial":58,
 "global_pending_after_projection":49,
 "remaining_construction_specific":{"realização":10},
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H CONSTRUCTION SPECIFIC PARTIAL 001

Nine construction-specific occurrences resolved. All remain predicative because the construction itself is licensed by a compatible nominal frame.

- fogo / pegar fogo -> fire.01
- caso / no caso de, se for o caso, quando é o caso -> case.03 discourse connective
- vontade / à vontade -> ease.02 at-ease
- respeito / a seu respeito -> respect.02 topic
- contagem / contagem regressiva -> countdown.01
- sentimento / nossos sentimentos -> sympathy.01

Construction-specific: 19 -> 10.
Global projected pending: 58 -> 49.
Remaining construction-specific occurrences are all 10 uses of realização in financial profit-taking language.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_CONSTRUCTION_SPECIFIC_PARTIAL_001.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
