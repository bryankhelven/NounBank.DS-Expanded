#!/usr/bin/env python3
import ssl, urllib.request, xml.etree.ElementTree as ET, json
from pathlib import Path

BASE="https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/"
candidates={
 "exceção3":["anomaly.xml","rarity.xml","deviation.xml","exceptional.xml","exception.xml","outlier.xml"],
 "gripe3":["infection.xml","disease.xml","illness.xml","sickness.xml","virus.xml","contagion.xml"],
 "desmoralização3":["discredit.xml","disgrace.xml","humiliation.xml","damage.xml","erosion.xml"],
 "vertigem3":["nausea.xml","illness.xml","sickness.xml","confusion.xml"],

 "adeus2":["leave.xml","leaving.xml","exit.xml","departure.xml","parting.xml"],
 "ingenuidade2":["innocence.xml","belief.xml","trust.xml","credibility.xml","credulity.xml"],
 "palhaçada2":["sham.xml","farce.xml","fraud.xml","mockery.xml","joke.xml","ridicule.xml"],
 "loucura2":["frenzy.xml","craze.xml","mania.xml","madness.xml","insanity.xml"],
 "vertigem2":["dizziness.xml","vertigo.xml","spin.xml","spinning.xml"],
 "empate2":["draw.xml","deadlock.xml","stalemate.xml","tie.xml"],

 "adeus":["farewell.xml","goodbye.xml","departure.xml","leave.xml"],
 "burrice":["stupidity.xml","foolishness.xml","mistake.xml","error.xml","blunder.xml"],
 "convergência":["convergence.xml","alignment.xml","agreement.xml","consensus.xml","convergence_point.xml"],
 "ingenuidade":["naivety.xml","naivete.xml","innocence.xml","gullibility.xml","credulity.xml"],
 "loucura":["madness.xml","insanity.xml","craziness.xml","folly.xml","mania.xml"],
 "palhaçada":["farce.xml","joke.xml","mockery.xml","charade.xml","nonsense.xml"],
 "vertigem":["dizziness.xml","vertigo.xml","giddiness.xml"],
 "gripe":["flu.xml","influenza.xml","illness.xml","sickness.xml"],
 "exceção":["exception.xml","exemption.xml","exclusion.xml"],
 "desmoralização":["demoralization.xml","discredit.xml","disgrace.xml"],
 "empate":["draw.xml","tie.xml","deadlock.xml","stalemate.xml"],

 "adeus":["farewell.xml","goodbye.xml","departure.xml"],
 "asneira":["remark.xml","statement.xml","nonsense.xml","comment.xml"],
 "burrice":["stupidity.xml","foolishness.xml","mistake.xml","error.xml"],
 "congestão":["congestion.xml","consolidation.xml","range.xml","stagnation.xml"],
 "convergência":["convergence.xml","alignment.xml","agreement.xml","consensus.xml"],
 "estrangulamento":["squeeze.xml","restriction.xml","constraint.xml","pressure.xml","choke.xml"],
 "ingenuidade":["naivety.xml","naivete.xml","innocence.xml","gullibility.xml"],
 "loucura":["madness.xml","insanity.xml","craziness.xml","folly.xml"],
 "palhaçada":["farce.xml","joke.xml","mockery.xml","charade.xml"],
 "preguiça":["laziness.xml","reluctance.xml","sloth.xml"],
 "vertigem":["dizziness.xml","vertigo.xml"],

 "acomodação":["stabilization.xml","stability.xml","consolidation.xml","pause.xml"],
 "animada":["boost.xml","pickup.xml","rally.xml","rise.xml"],
 "congestão":["congestion.xml","consolidation.xml","range.xml"],
 "convergência":["convergence.xml","alignment.xml","agreement.xml"],
 "estrangulamento":["squeeze.xml","constraint.xml","restriction.xml","pressure.xml","strangling.xml"],
 "loucura":["madness.xml","insanity.xml","craziness.xml"],
 "palhaçada":["farce.xml","joke.xml","mockery.xml"],
 "esperteza":["cleverness.xml","cunning.xml","shrewdness.xml"],
 "ingenuidade":["naivety.xml","naivete.xml","innocence.xml"],
 "preguiça":["laziness.xml","reluctance.xml"],
 "vertigem":["dizziness.xml","vertigo.xml"],

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
