#!/usr/bin/env python3
import ssl, urllib.request, xml.etree.ElementTree as ET, json
from pathlib import Path

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
candidates={
 "antecipação":["anticipation.xml"],
 "aviso":["notice.xml","warning.xml","announcement.xml"],
 "concentração":["concentration.xml"],
 "cura":["cure.xml"],
 "decolagem":["takeoff.xml","departure.xml"],
 "desmoralização":["demoralization.xml"],
 "empate":["tie.xml","draw.xml"],
 "estrangulamento":["strangulation.xml","choking.xml"],
 "evasão":["evasion.xml","escape.xml"],
 "exceção":["exception.xml"],
 "gripe":["flu.xml"],
 "impulso":["impulse.xml","push.xml"],
 "retração":["retraction.xml","contraction.xml"]
}
ctx=ssl._create_unverified_context()
out={}
Path("enmap_xml").mkdir(exist_ok=True)
for lemma,files in candidates.items():
    out[lemma]=[]
    for fn in files:
        rec={"file":fn,"exists":False}
        try:
            with urllib.request.urlopen(BASE+fn,context=ctx,timeout=30) as r:
                data=r.read()
            p=Path("enmap_xml")/fn
            p.write_bytes(data)
            root=ET.fromstring(data)
            rolesets=[]
            for rs in root.findall(".//roleset"):
                roles=[]
                for role in rs.findall("./roles/role"):
                    roles.append({"n":role.get("n"),"descr":role.get("descr")})
                rolesets.append({
                    "id":rs.get("id"),
                    "name":rs.get("name"),
                    "source":rs.get("source"),
                    "roles":roles
                })
            rec.update({"exists":True,"rolesets":rolesets})
        except Exception as e:
            rec["error"]=str(e)
        out[lemma].append(rec)
Path("ENMAP_CANDIDATE_FRAMES.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
