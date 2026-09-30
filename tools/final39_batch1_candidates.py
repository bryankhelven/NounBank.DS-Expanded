#!/usr/bin/env python3
import ssl,urllib.request,xml.etree.ElementTree as ET,json
from pathlib import Path
BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
cands={
 "administrador":["administrator.xml","administration.xml","manager.xml","management.xml","operator.xml"],
 "agente_fiduciario":["trustee.xml","fiduciary.xml","agent.xml","representative.xml"],
 "dono":["owner.xml","ownership.xml","proprietor.xml"],
 "controlador":["controller.xml","control.xml","owner.xml","ownership.xml","shareholder.xml"],
 "especialista":["expert.xml","specialist.xml","expertise.xml"],
 "construtor":["builder.xml","construction.xml","constructor.xml","developer.xml"]
}
ctx=ssl._create_unverified_context()
out={};Path("final39_xml").mkdir(exist_ok=True)
for k,files in cands.items():
 out[k]=[]
 for fn in files:
  rec={"file":fn,"exists":False}
  try:
   with urllib.request.urlopen(BASE+fn,context=ctx,timeout=30) as r:data=r.read()
   (Path("final39_xml")/fn).write_bytes(data)
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
Path("FINAL39_BATCH1_CANDIDATES.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
