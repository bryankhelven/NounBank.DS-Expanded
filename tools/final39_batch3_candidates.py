#!/usr/bin/env python3
import ssl,urllib.request,xml.etree.ElementTree as ET,json
from pathlib import Path
BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
cands={
 "show":["show.xml","performance.xml","spectacle.xml","display.xml","demonstration.xml"],
 "rumo":["direction.xml","course.xml","path.xml","trend.xml","movement.xml","move.xml"],
 "cacador":["hunter.xml","hunt.xml","killer.xml"],
 "queridinho":["favorite.xml","darling.xml","preference.xml","choice.xml"],
 "adversario":["opponent.xml","adversary.xml","rival.xml","enemy.xml"],
 "requerimento":["request.xml","petition.xml","requirement.xml","motion.xml"],
 "esquartejador":["dismemberment.xml","dismemberer.xml","butcher.xml","killer.xml","cutting.xml","cut.xml"]
}
ctx=ssl._create_unverified_context()
out={};Path("batch3_xml").mkdir(exist_ok=True)
for k,files in cands.items():
 out[k]=[]
 for fn in files:
  rec={"file":fn,"exists":False}
  try:
   with urllib.request.urlopen(BASE+fn,context=ctx,timeout=30) as r:data=r.read()
   (Path("batch3_xml")/fn).write_bytes(data)
   root=ET.fromstring(data); rss=[]
   for rs in root.findall(".//roleset"):
    rss.append({
      "id":rs.get("id"),"name":rs.get("name"),"source":rs.get("source"),
      "roles":[{"n":x.get("n"),"descr":x.get("descr")} for x in rs.findall("./roles/role")],
      "examples":[" ".join((e.findtext("text") or "").split()) for e in rs.findall("./example")[:8]]
    })
   rec.update({"exists":True,"rolesets":rss})
  except Exception as e: rec["error"]=str(e)
  out[k].append(rec)
Path("FINAL39_BATCH3_CANDIDATES.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
