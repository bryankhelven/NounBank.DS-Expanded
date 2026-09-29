#!/usr/bin/env python3
import ssl, urllib.request, xml.etree.ElementTree as ET, json
from pathlib import Path

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
candidates={
 "antecipação":["anticipation.xml","advance.xml","advancement.xml","acceleration.xml"],
 "aviso":["notice.xml","warning.xml","announcement.xml"],
 "adeus":["farewell.xml","goodbye.xml"],
 "asneira":["nonsense.xml","remark.xml","statement.xml"],
 "burrice":["stupidity.xml","foolishness.xml"],
 "concentração":["concentration.xml","consolidation.xml","merger.xml","combination.xml"],
 "cura":["cure.xml"],
 "decolagem":["takeoff.xml","departure.xml","liftoff.xml","lift-off.xml"],
 "desmoralização":["demoralization.xml"],
 "empate":["tie.xml","draw.xml","deadlock.xml"],
 "estrangulamento":["strangulation.xml","choking.xml"],
 "evasão":["evasion.xml","escape.xml","flight.xml","outflow.xml","transfer.xml","remittance.xml"],
 "exceção":["exception.xml"],
 "gripe":["flu.xml","influenza.xml"],
 "impulso":["impulse.xml","push.xml","momentum.xml","thrust.xml","surge.xml","drive.xml"],
 "retração":["retraction.xml","contraction.xml","pullback.xml","retreat.xml","decline.xml"]
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
