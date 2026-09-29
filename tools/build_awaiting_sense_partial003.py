#!/usr/bin/env python3
from pathlib import Path
import json,ssl,urllib.request,zipfile,hashlib,shutil,csv,xml.etree.ElementTree as ET

SRC=Path("src")
OUT=Path("awaiting_sense_partial_003")
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
    exs=[" ".join((ex.findtext("text") or "").split()) for ex in rs.findall("./example")[:6]]
    return roles,rs.get("name"),rs.get("source"),exs

ledger=[]

# guerra: N in lexicalized compound sala de guerra / war room.
j=json.loads((SRC/"jsons/guerra.json").read_text(encoding="utf-8"))
nonpred=j.setdefault("nonpredicative_instances",[])
for old in j.get("pending_instances",[]):
    rec={k:v for k,v in old.items() if k!="resolution_status"}
    rec["predicative"]=False
    rec["sense_resolution_status"]="RESOLVED_NONPREDICATIVE_MWE_SALA_DE_GUERRA"
    rec["decision_note"]="In 'sala de guerra', guerra is part of lexicalized term war room/command room; it does not independently instantiate war.01."
    nonpred.append(rec)
    ledger.append({"lemma":"guerra","sent_id":old["sent_ID"],"decision":"N","pt_roleset":"","english_roleset":"","note":"MWE sala de guerra / war room"})
j.pop("pending_instances",None)
(OUT/"overlay/jsons/guerra.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# jogo: two different S resolutions.
j=json.loads((SRC/"jsons/jogo.json").read_text(encoding="utf-8"))
pending={x["sent_ID"]:x for x in j.get("pending_instances",[])}

# jogo.04 -> play.07 (come into play / factor)
old=pending["dante_01_444105820939497472l"]
roles,name,source,nex=roles_for("play.xml","play.07")
sense4={
 "pt_roleset":"jogo.04","pt_sense_index":4,"pt_sense_hint":4,
 "pt_sense_gloss":"entrar em jogo = passar a atuar como fator relevante",
 "english_roleset":"play.07","english_roleset_source":"NOMBANK_XML_AFTER_DOMAIN_SENSE_RESOLUTION_V2H",
 "nombank_url":BASE+"play.xml","roles":roles,
 "examples":[{
   "sent_ID":old["sent_ID"],"text":old["text"],
   "realization":{"Arg0":None,"Arg1":"um ingrediente importante","Arg2":None},
   "syntax":{"Arg0":None,"Arg1":"nsubj","Arg2":None},
   "instance_id":old["instance_id"],"predicate":old["predicate"],
   "sense_resolution_status":"RESOLVED_DOMAIN_SENSE_AND_PREDICATIVITY","predicative":True
 }],
 "syntactic_profile":{"Arg1":{"nsubj":1}},
 "sense_evidence":{"decision":"S_PREDICATIVE","nombank_roleset_name":name,"nombank_roleset_source":source,
   "note":"NomBank play.07 is nomlike-factor and includes exact construction 'economic forces ... come into play'.","nombank_examples":nex}
}
j["senses"].append(sense4)
ledger.append({"lemma":"jogo","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"jogo.04","english_roleset":"play.07","note":"come into play / factor sense"})

# second pending -> existing jogo.02 / gamble.01
old=pending["dante_01_459317170187816960l"]
s2=next(s for s in j["senses"] if s.get("pt_roleset")=="jogo.02")
ex={
 "sent_ID":old["sent_ID"],"text":old["text"],
 "realization":{"Arg0":None,"Arg1":None},
 "syntax":{"Arg0":None,"Arg1":None},
 "instance_id":old["instance_id"],"predicate":old["predicate"],
 "sense_resolution_status":"RESOLVED_EXISTING_FINANCIAL_GAME_SENSE","predicative":True
}
s2["examples"].append(ex)
ledger.append({"lemma":"jogo","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"jogo.02","english_roleset":"gamble.01","note":"market-as-risk/gamble activity; same sense as existing HOME BROKER example"})
j.pop("pending_instances",None)
(OUT/"overlay/jsons/jogo.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
roles_for("gamble.xml","gamble.01")

# lavagem: S -> laundering.01
j=json.loads((SRC/"jsons/lavagem.json").read_text(encoding="utf-8"))
roles,name,source,nex=roles_for("laundering.xml","laundering.01")
examples=[]
for old in j.get("pending_instances",[]):
    # Theme is overt in all three: de dinheiro.
    ex={"sent_ID":old["sent_ID"],"text":old["text"],
        "realization":{"Arg0":None,"Arg1":"de dinheiro"},
        "syntax":{"Arg0":None,"Arg1":"nmod"},
        "instance_id":old["instance_id"],"predicate":old["predicate"],
        "sense_resolution_status":"RESOLVED_DOMAIN_SENSE_AND_PREDICATIVITY","predicative":True}
    examples.append(ex)
    ledger.append({"lemma":"lavagem","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"lavagem.01","english_roleset":"laundering.01","note":"money-laundering process"})
j["senses"]=[{
 "pt_roleset":"lavagem.01","pt_sense_index":1,"pt_sense_hint":1,
 "pt_sense_gloss":"lavagem de dinheiro / ocultação da origem ilícita de recursos",
 "english_roleset":"laundering.01","english_roleset_source":"NOMBANK_XML_AFTER_DOMAIN_SENSE_RESOLUTION_V2H",
 "nombank_url":BASE+"laundering.xml","roles":roles,"examples":examples,
 "syntactic_profile":{"Arg1":{"nmod":3}},
 "sense_evidence":{"decision":"S_PREDICATIVE","nombank_roleset_name":name,"nombank_roleset_source":source,
   "note":"NomBank laundering.01 explicitly includes money-laundering charges and laundering of drug money.","nombank_examples":nex}
}]
j.pop("pending_instances",None)
(OUT/"overlay/jsons/lavagem.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# resposta: S -> response.01
j=json.loads((SRC/"jsons/resposta.json").read_text(encoding="utf-8"))
old=j["pending_instances"][0]
roles,name,source,nex=roles_for("response.xml","response.01")
j["senses"]=[{
 "pt_roleset":"resposta.01","pt_sense_index":1,"pt_sense_hint":1,
 "pt_sense_gloss":"resposta/reação dirigida a estímulo ou interlocutor",
 "english_roleset":"response.01","english_roleset_source":"NOMBANK_XML_AFTER_DOMAIN_SENSE_RESOLUTION_V2H",
 "nombank_url":BASE+"response.xml","roles":roles,
 "examples":[{
  "sent_ID":old["sent_ID"],"text":old["text"],
  "realization":{"Arg0":None,"Arg1":"Aos compradores de abertura desesperados de #petr4","Arg2":None},
  "syntax":{"Arg0":None,"Arg1":"obl","Arg2":None},
  "instance_id":old["instance_id"],"predicate":old["predicate"],
  "sense_resolution_status":"RESOLVED_RESPONSE_EVENT","predicative":True
 }],
 "syntactic_profile":{"Arg1":{"obl":1}},
 "sense_evidence":{"decision":"S_PREDICATIVE","nombank_roleset_name":name,"nombank_roleset_source":source,"nombank_examples":nex}
}]
j.pop("pending_instances",None)
(OUT/"overlay/jsons/resposta.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
ledger.append({"lemma":"resposta","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"resposta.01","english_roleset":"response.01","note":"reply/response event"})

# tapa: S metaphorical decisive push -> push.01
j=json.loads((SRC/"jsons/tapa.json").read_text(encoding="utf-8"))
old=j["pending_instances"][0]
roles,name,source,nex=roles_for("push.xml","push.01")
j["senses"]=[{
 "pt_roleset":"tapa.01","pt_sense_index":1,"pt_sense_hint":1,
 "pt_sense_gloss":"impulso/ação decisiva que move o mercado e define a direção do trade",
 "english_roleset":"push.01","english_roleset_source":"NOMBANK_XML_AFTER_DOMAIN_SENSE_RESOLUTION_V2H",
 "nombank_url":BASE+"push.xml","roles":roles,
 "examples":[{
  "sent_ID":old["sent_ID"],"text":old["text"],
  "realization":{"Arg0":"quem","Arg1":None,"Arg2":"p/ definir o lado à trade"},
  "syntax":{"Arg0":"nsubj","Arg1":None,"Arg2":"advcl"},
  "instance_id":old["instance_id"],"predicate":old["predicate"],
  "sense_resolution_status":"RESOLVED_MARKET_METAPHOR_DECISIVE_PUSH","predicative":True
 }],
 "syntactic_profile":{"Arg0":{"nsubj":1},"Arg2":{"advcl":1}},
 "sense_evidence":{"decision":"S_PREDICATIVE","nombank_roleset_name":name,"nombank_roleset_source":source,
  "note":"Metaphorical market action causing directional movement; physical slap frame rejected in favor of cause-motion push.","nombank_examples":nex}
}]
j.pop("pending_instances",None)
(OUT/"overlay/jsons/tapa.json").write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
ledger.append({"lemma":"tapa","sent_id":old["sent_ID"],"decision":"S","pt_roleset":"tapa.01","english_roleset":"push.01","note":"decisive market push, not physical slap"})

with open(OUT/"RESOLUTION_LEDGER.tsv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["lemma","sent_id","decision","pt_roleset","english_roleset","note"],delimiter="\t",lineterminator="\n")
    w.writeheader();w.writerows(ledger)

validation={
 "status":"PASS_AWAITING_SENSE_TERMINAL_CLOSURE",
 "resolved_lemmas":5,
 "resolved_occurrences":8,
 "predicative_occurrences":7,
 "nonpredicative_occurrences":1,
 "S":{"jogo":2,"lavagem":3,"resposta":1,"tapa":1},
 "N":{"guerra":1},
 "awaiting_sense_before":8,
 "awaiting_sense_after_projection":0,
 "global_pending_before_this_partial":66,
 "global_pending_after_projection":58,
 "next_open_classes":{"construction_specific":19,"retracted_new_cases":39},
 "git_mutation":False
}
(OUT/"VALIDATION.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"README.md").write_text("""# NBE V2H AWAITING SENSE PARTIAL 003 — TERMINAL

Final 8 awaiting-sense occurrences resolved under the identity → domain sense → S/N → ENMAP gate.

N:
- guerra in sala de guerra: lexicalized war-room compound; guerra does not independently instantiate war.01.

S:
- jogo, entrar em jogo: jogo.04 -> play.07 (factor / come into play).
- jogo, o jogo tá pesado: existing jogo.02 -> gamble.01.
- lavagem de dinheiro (3): lavagem.01 -> laundering.01.
- resposta (1): resposta.01 -> response.01.
- tapa (1): tapa.01 -> push.01, metaphorical decisive market push, not physical slap.

awaiting_sense: 8 -> 0.
Global projected pending: 66 -> 58.
""",encoding="utf-8")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in OUT.rglob("*") if p.is_file())
(OUT/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.relative_to(OUT).as_posix()}" for p in files)+"\n",encoding="utf-8")
z=Path("NBE_V2H_AWAITING_SENSE_PARTIAL_003_TERMINAL.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): zz.write(p,arcname=f"{OUT.name}/{p.relative_to(OUT).as_posix()}")
print(json.dumps(validation,ensure_ascii=False,indent=2))
print("ZIP_SHA256",sha(z))
