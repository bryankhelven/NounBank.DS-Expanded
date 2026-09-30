#!/usr/bin/env python3
from pathlib import Path
import json, zipfile, shutil, re, html, hashlib, sys
from collections import Counter, defaultdict

ROOT=Path(".")
ART=ROOT/"artifacts"
J=ROOT/"jsons"
P=ROOT/"site_pages"
DOCS=ROOT/"docs"
DOCS.mkdir(exist_ok=True)

ORDER=[
 "01_real_enmap_001","02_real_enmap_002","03_real_enmap_003","04_real_enmap_004","05_real_enmap_005",
 "06_real_enmap_006","07_real_enmap_007","08_real_enmap_008","09_real_enmap_009",
 "10_awaiting_sense_001","11_awaiting_sense_002","12_awaiting_sense_003",
 "13_construction_001","14_construction_002",
 "15_final39_001","16_final39_002","17_final39_003"
]

def recursive_extract(zpath, outdir):
    outdir.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(outdir)
    changed=True
    seen=set()
    while changed:
        changed=False
        for zf in list(outdir.rglob("*.zip")):
            key=str(zf.resolve())
            if key in seen: continue
            seen.add(key)
            sub=zf.with_suffix("")
            try:
                sub.mkdir(parents=True,exist_ok=True)
                with zipfile.ZipFile(zf) as z:
                    z.extractall(sub)
                changed=True
            except zipfile.BadZipFile:
                pass

# Expand wrappers and inner package zips.
for name in ORDER:
    z=ART/f"{name}.zip"
    assert z.exists(), f"missing artifact wrapper {z}"
    recursive_extract(z, ART/f"{name}_x")

# Collect overlay files in scientific order.
overlay_by_stage={}
for name in ORDER:
    files=[]
    for p in (ART/f"{name}_x").rglob("*.json"):
        if "/overlay/jsons/" in p.as_posix():
            files.append(p)
    overlay_by_stage[name]=sorted(files)

report=[]
fogo_await=None
fogo_construct=None

for stage in ORDER:
    for src in overlay_by_stage[stage]:
        fn=src.name
        # Post-lexical-identity authority supersedes this old file entirely.
        if fn=="descoberto.json":
            report.append({"stage":stage,"file":fn,"action":"SKIP_SUPERSEDED_BY_LEXICAL_IDENTITY_REPAIR"})
            continue
        if fn=="fogo.json":
            if stage=="11_awaiting_sense_002":
                fogo_await=json.loads(src.read_text(encoding="utf-8"))
                report.append({"stage":stage,"file":fn,"action":"HOLD_FOR_EXPLICIT_MERGE"})
                continue
            if stage=="13_construction_001":
                fogo_construct=json.loads(src.read_text(encoding="utf-8"))
                report.append({"stage":stage,"file":fn,"action":"HOLD_FOR_EXPLICIT_MERGE"})
                continue
        dst=J/fn
        shutil.copy2(src,dst)
        report.append({"stage":stage,"file":fn,"action":"APPLY_OVERLAY"})

# Explicit scientific merge for fogo:
assert fogo_await and fogo_construct
merged=fogo_construct
merged.pop("pending_instances",None)
merged["nonpredicative_instances"]=fogo_await.get("nonpredicative_instances",[])
(J/"fogo.json").write_text(json.dumps(merged,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
report.append({"stage":"MERGE","file":"fogo.json","action":"S_PEGAR_FOGO_PLUS_N_FOGO_DE_PALHA_X2"})

# Lexical identity repair invariants.
for bad in ["descoberto","retirado","virado","alternativo","representação"]:
    assert not (J/f"{bad}.json").exists(), f"lexical identity regression: {bad}"
for good in ["descoberta","retirada","virada","alternativa","reapresentação"]:
    assert (J/f"{good}.json").exists(), good

manifest=json.loads((J/"_manifest.json").read_text(encoding="utf-8"))
entries=manifest["lemmas"]
manifest_names={x["lemma"] for x in entries}
assert len(entries)==516 and len(manifest_names)==516

# No superseded false lemma is public.
assert "descoberto" not in manifest_names

# Recompute pending and science totals from canonical JSON.
pending_lemmas=[]
pending_count=0
pred_count=0
arg_total=0
by_role=Counter()
null_en=[]
sense_count=0
nonpred_count=0

open_statuses={
 "construction_specific","awaiting_sense_resolution","awaiting_english_mapping",
 "ENMAP_ROLEINV_UNRESOLVED_EXPLICIT_NO_FABRICATION"
}

for ent in entries:
    lemma=ent["lemma"]
    p=J/ent["filename"]
    assert p.exists(), p
    d=json.loads(p.read_text(encoding="utf-8"))
    assert d.get("lemma")==lemma, (lemma,d.get("lemma"))
    pend=d.get("pending_instances") or []
    if pend:
        pending_lemmas.append(lemma); pending_count+=len(pend)
    assert not d.get("pending_status"), f"pending_status remains: {lemma}"
    for s in d.get("senses",[]) or []:
        sense_count+=1
        status=s.get("resolution_status")
        assert status not in open_statuses, f"open status {status}: {lemma}"
        exs=s.get("examples") or []
        pred_count+=len(exs)
        if s.get("english_roleset") is None:
            ev=s.get("mapping_evidence") or s.get("sense_evidence") or {}
            decision=ev.get("decision")
            source=s.get("english_roleset_source")
            if decision!="NO_COMPATIBLE_NOMBANK_ROLESET" and source!="NO_COMPATIBLE_NOMBANK_ROLESET_AFTER_DOCUMENTED_SEARCH":
                null_en.append((lemma,s.get("pt_roleset"),decision,source))
        for e in exs:
            for role,val in (e.get("realization") or {}).items():
                if val not in (None,"","-"):
                    arg_total+=1; by_role[role]+=1
    nonpred_count+=len(d.get("nonpredicative_instances") or [])

assert pending_count==0, (pending_count,pending_lemmas)
# Null ENMAP is allowed only for explicit documented negative closures.
assert not null_en, f"unjustified null ENMAP: {null_en[:20]}"

for ent in entries:
    ent["pending"]=False
(J/"_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

stats=json.loads((J/"statistics.json").read_text(encoding="utf-8"))
stats["schema_version"]="nounbank-ds-expanded-sanitized-stats/1.3-v2h-zero-pending"
stats["inventory"]["public_lemmas"]=516
stats["inventory"]["original"]=sum(1 for x in entries if not x.get("new"))
stats["inventory"]["new"]=sum(1 for x in entries if x.get("new"))
stats["examples"]["predicative_occurrences"]=pred_count
stats["examples"]["regular_occurrences"]=pred_count
stats["examples"]["pending_occurrences"]=0
stats["pending"]={
    "awaiting_sense":0,
    "awaiting_english_mapping":0,
    "construction_specific":0,
    "retracted_new_cases":0,
    "pending_lemmas":[]
}
stats["arguments"]={
    **{k:v for k,v in stats.get("arguments",{}).items() if k.startswith("v2h_")},
    "total":arg_total,
    "by_role":dict(sorted(by_role.items()))
}
stats["closure"]={
    "authority":"NBE_V2H_ZERO_PENDING_INTEGRATION",
    "base_commit":"df5a3ca7cbaced21f7018b60c63fcaa52615def6",
    "pending_scientific":0,
    "sense_count":sense_count,
    "nonpredicative_instances_retained_in_json":nonpred_count,
    "lexical_identity_repair_preserved":True,
    "applied_scientific_packages":len(ORDER)
}
(J/"statistics.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Rebuild all public pages from canonical JSON for zero stale pending UI.
def mark_first(text,form):
    safe=html.escape(text or "")
    if not form: return safe
    target=html.escape(form)
    return re.sub(re.escape(target),lambda m:f'<span class="rel">{m.group(0)}</span>',safe,count=1,flags=re.I)

def render_page(lemma,d,new):
    letter=lemma[0].lower()
    parts=[]
    for s in d.get("senses",[]) or []:
        pt=s.get("pt_roleset","")
        en=s.get("english_roleset")
        url=s.get("nombank_url")
        if en and url:
            enhtml=f'<a href="{html.escape(url)}">{html.escape(en)}</a>'
        elif en:
            enhtml=html.escape(str(en))
        else:
            enhtml='<span title="No compatible NomBank roleset after documented search">NO_COMPATIBLE_NOMBANK_ROLESET</span>'
        parts.append(f'<p class="roleset-line"><strong>Roleset id:</strong> {html.escape(pt)}, Mapeamento para o inglês: {enhtml}</p>')
        roles=s.get("roles") or []
        if roles:
            parts.append("<h2>Roles:</h2><ul>")
            for r in roles:
                rid=r.get("id","")
                parts.append(f'<li class="{rid.lower()}">{html.escape(rid.replace("Arg","Arg "))}: {html.escape(str(r.get("desc","")))}</li>')
            parts.append("</ul>")
        parts.append("<h2>Exemplos:</h2>")
        for i,e in enumerate(s.get("examples") or [],1):
            form=(e.get("predicate") or {}).get("form","")
            parts.append(f'<h3>{i}: {mark_first(e.get("text",""),form)}</h3><ul><li class="rel">rel: {html.escape(form)}</li>')
            for r in roles:
                rid=r.get("id",""); val=(e.get("realization") or {}).get(rid)
                syn=(e.get("syntax") or {}).get(rid)
                extra=f' <sub class="deprel">{html.escape(str(syn))}</sub>' if syn else ""
                parts.append(f'<li class="{rid.lower()}">{html.escape(rid.replace("Arg","Arg "))}: {html.escape(str(val)) if val else "-"}{extra}</li>')
            parts.append("</ul>")
        profile=s.get("syntactic_profile") or {}
        if profile:
            deps=sorted({dep for x in profile.values() for dep in x})
            parts.append('<h2>Realização sintática da estrutura de argumentos</h2><table class="stats-table"><thead><tr><th>Relação</th>')
            for r in roles: parts.append(f'<th>{html.escape(r.get("id",""))}</th>')
            parts.append('</tr></thead><tbody>')
            for dep in deps:
                parts.append(f'<tr><td>{html.escape(dep)}</td>')
                for r in roles:
                    parts.append(f'<td>{profile.get(r.get("id",""),{}).get(dep,0)}</td>')
                parts.append('</tr>')
            parts.append('</tbody></table>')
        parts.append('<div class="sense-divider" aria-hidden="true"></div>')
    badge=' <sup class="new-float">NEW</sup>' if new else ''
    return f'''<!DOCTYPE html>
<html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(lemma)} - NounBank.DS Expanded</title><link rel="stylesheet" href="../styles.css">
<style>:root{{--header-h:56px}}body{{margin:0}}.site-header{{position:sticky;top:0;z-index:1000;background:rgba(20,20,20,.70)}}.site-nav{{height:var(--header-h);display:flex;align-items:center;justify-content:space-between;padding:0 16px}}.site-nav .home-link{{color:#cfe3ff;text-decoration:none;font-weight:600}}.site-nav .page-title{{color:#cfd8ff;opacity:.75;font-weight:600}}.site-nav .download-json{{color:#fff;background:#2e7d32;padding:10px 14px;border-radius:12px;text-decoration:none}}</style>
</head><body><header class="site-header"><nav class="site-nav"><a class="home-link" href="../index.html?letter={letter}">Home</a><span class="page-title">{html.escape(lemma)}</span><a class="download-json" href="../jsons/{html.escape(ent_filename[lemma])}" download>JSON download</a></nav></header>
<div class="content"><h1>Nome predicador: <i style="color:red;">{html.escape(lemma)}</i>{badge}</h1>{''.join(parts)}</div>
<a class="back-link back-floating" href="../index.html?letter={letter}">← Voltar para {letter.upper()}</a></body></html>'''

ent_filename={x["lemma"]:x["filename"] for x in entries}
for ent in entries:
    d=json.loads((J/ent["filename"]).read_text(encoding="utf-8"))
    (P/f'{ent["lemma"]}.html').write_text(render_page(ent["lemma"],d,ent.get("new",False)),encoding="utf-8")

# Rebuild aggregate ZIP.
agg=J/"nounbank.ds_expanded_all_jsons.zip"
with zipfile.ZipFile(agg,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for ent in entries:
        p=J/ent["filename"]; z.write(p,arcname=p.name)
    z.write(J/"_manifest.json",arcname="_manifest.json")
    z.write(J/"statistics.json",arcname="statistics.json")
with zipfile.ZipFile(agg) as z:
    assert len(z.namelist())==518

# Update homepage counters robustly.
idx=(ROOT/"index.html").read_text(encoding="utf-8")
idx=re.sub(r'com \d+ nomes predicadores',f'com {len(entries)} nomes predicadores',idx)
idx=re.sub(r'<strong>[\d.]+</strong><span>nomes predicadores</span>',f'<strong>{len(entries)}</strong><span>nomes predicadores</span>',idx)
fmt_pt=lambda n:f"{n:,}".replace(",",".")
idx=re.sub(r'<strong>[\d.]+</strong><span>ocorrências predicadoras</span>',f'<strong>{fmt_pt(pred_count)}</strong><span>ocorrências predicadoras</span>',idx)
idx=re.sub(r'<strong>\d+ \+ \d+</strong>',f'<strong>{stats["inventory"]["original"]} + {stats["inventory"]["new"]}</strong>',idx)
idx=re.sub(r'As \d+ entradas acrescentadas',f'As {stats["inventory"]["new"]} entradas acrescentadas',idx)
(ROOT/"index.html").write_text(idx,encoding="utf-8")

integration={
 "status":"PASS_ZERO_PENDING_CANONICAL_INTEGRATION",
 "base_commit":"df5a3ca7cbaced21f7018b60c63fcaa52615def6",
 "packages_applied":ORDER,
 "package_count":len(ORDER),
 "overlay_report":report,
 "public_lemmas":len(entries),
 "original":stats["inventory"]["original"],
 "new":stats["inventory"]["new"],
 "predicative_occurrences":pred_count,
 "pending_occurrences":0,
 "arguments_realized":arg_total,
 "by_role":dict(sorted(by_role.items())),
 "sense_count":sense_count,
 "nonpredicative_instances_retained":nonpred_count,
 "aggregate_zip_entries":518,
 "lexical_identity_invariants":"PASS"
}
(DOCS/"NBE_V2H_ZERO_PENDING_INTEGRATION.json").write_text(json.dumps(integration,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# QA scan for stale pending strings in canonical JSON only.
for ent in entries:
    txt=(J/ent["filename"]).read_text(encoding="utf-8")
    assert '"pending_instances": [' not in txt or not (json.loads(txt).get("pending_instances") or []), ent["lemma"]

print(json.dumps(integration,ensure_ascii=False,indent=2))
