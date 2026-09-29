#!/usr/bin/env python3
import ssl, urllib.request, xml.etree.ElementTree as ET, json
from pathlib import Path
BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
C={
 "festa":["party.xml","celebration.xml","festival.xml"],
 "giro":["turnover.xml","trading.xml","trade.xml","rotation.xml","volume.xml"],
 "impulsão":["momentum.xml","thrust.xml","impulse.xml","push.xml","drive.xml"],
 "movimento":["movement.xml","motion.xml","shift.xml","move.xml","event.xml"],
 "antecipação":["advance.xml","advancement.xml","acceleration.xml","preemption.xml","timing.xml"]
}
ctx=ssl._create_unverified_context(); out={}; Path("short_xml").mkdir(exist_ok=True)
for lemma,files in C.items():
 out[lemma]=[]
 for fn in files:
  rec={"file":fn,"exists":False}
  try:
   with urllib.request.urlopen(BASE+fn,context=ctx,timeout=5) as r: data=r.read()
   (Path("short_xml")/fn).write_bytes(data)
   root=ET.fromstring(data); rss=[]
   for rs in root.findall(".//roleset"):
    rss.append({"id":rs.get("id"),"name":rs.get("name"),"source":rs.get("source"),
                "roles":[{"n":x.get("n"),"descr":x.get("descr")} for x in rs.findall("./roles/role")]})
   rec.update({"exists":True,"rolesets":rss})
  except Exception as e: rec["error"]=str(e)
  out[lemma].append(rec)
Path("SHORT_ENMAP.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
