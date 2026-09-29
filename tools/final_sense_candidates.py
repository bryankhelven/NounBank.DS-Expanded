#!/usr/bin/env python3
import ssl,urllib.request,xml.etree.ElementTree as ET,json
from pathlib import Path

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
candidates={
 "jogo_entrar":["play.xml","game.xml","involvement.xml","participation.xml","entry.xml"],
 "jogo_pesado":["game.xml","gamble.xml","struggle.xml","contest.xml"],
 "lavagem":["laundering.xml","washing.xml","cleaning.xml"],
 "resposta":["response.xml","reply.xml","answer.xml"],
 "tapa":["slap.xml","hit.xml","push.xml","strike.xml","kick.xml"]
}
ctx=ssl._create_unverified_context()
out={}
Path("sense_xml").mkdir(exist_ok=True)
for key,files in candidates.items():
  out[key]=[]
  for fn in files:
    rec={"file":fn,"exists":False}
    try:
      with urllib.request.urlopen(BASE+fn,context=ctx,timeout=30) as r: data=r.read()
      (Path("sense_xml")/fn).write_bytes(data)
      root=ET.fromstring(data)
      rolesets=[]
      for rs in root.findall(".//roleset"):
        roles=[{"n":r.get("n"),"descr":r.get("descr")} for r in rs.findall("./roles/role")]
        examples=[" ".join((ex.findtext("text") or "").split()) for ex in rs.findall("./example")[:6]]
        rolesets.append({"id":rs.get("id"),"name":rs.get("name"),"source":rs.get("source"),"roles":roles,"examples":examples})
      rec.update({"exists":True,"rolesets":rolesets})
    except Exception as e:
      rec["error"]=str(e)
    out[key].append(rec)
Path("FINAL_SENSE_CANDIDATES.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
