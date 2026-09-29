#!/usr/bin/env python3
from pathlib import Path
import json, zipfile, html, re, hashlib, shutil

ROOT=Path(".")
J=ROOT/"jsons"
P=ROOT/"site_pages"

def load(lemma):
    return json.loads((J/f"{lemma}.json").read_text(encoding="utf-8"))

def save(lemma,obj):
    (J/f"{lemma}.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def normalize_example(ex, old_lemma, new_lemma, roles):
    e=json.loads(json.dumps(ex,ensure_ascii=False))
    iid=e.get("instance_id","")
    if f"::{old_lemma}::" in iid:
        e["instance_id"]=iid.replace(f"::{old_lemma}::",f"::{new_lemma}::")
    oldr=e.get("realization") or {}
    olds=e.get("syntax") or {}
    e["realization"]={r["id"]:oldr.get(r["id"]) for r in roles}
    e["syntax"]={r["id"]:olds.get(r["id"]) for r in roles}
    return e

def dedupe_append(target_examples, additions):
    seen={(e.get("sent_ID"),e.get("instance_id"),(e.get("predicate") or {}).get("form")) for e in target_examples}
    for e in additions:
        k=(e.get("sent_ID"),e.get("instance_id"),(e.get("predicate") or {}).get("form"))
        if k not in seen:
            target_examples.append(e); seen.add(k)

ledger=[]

# 1) descoberto -> descoberta (3 wrongly grouped discovery examples); own 'venda a descoberto' is N and removed from predicative publication.
src=load("descoberto"); tgt=load("descoberta")
ss=src["senses"][0]; ts=tgt["senses"][0]
adds=[normalize_example(e,"descoberto","descoberta",ts.get("roles",[])) for e in ss.get("examples",[])]
dedupe_append(ts["examples"],adds)
ledger.append({"wrong_lemma":"descoberto","correct_lemma":"descoberta","action":"MOVE_3_PREDICATIVE_EXAMPLES_AND_REMOVE_FALSE_LEMMA","moved":len(adds),"note":"descoberta (event noun) != descoberto (form in venda a descoberto); sole verdadeiro 'descoberto' occurrence is N"})
save("descoberta",tgt)
(J/"descoberto.json").unlink()

# 2) retirado -> retirada
src=load("retirado"); tgt=load("retirada")
ss=src["senses"][0]; ts=tgt["senses"][0]
adds=[normalize_example(e,"retirado","retirada",ts.get("roles",[])) for e in ss.get("examples",[])]
dedupe_append(ts["examples"],adds)
ledger.append({"wrong_lemma":"retirado","correct_lemma":"retirada","action":"MERGE_AND_REMOVE_FALSE_LEMMA","moved":len(adds),"note":"retirada is the event noun in corpus"})
save("retirada",tgt); (J/"retirado.json").unlink()

# 3) virado -> virada
src=load("virado"); tgt=load("virada")
ss=src["senses"][0]; ts=tgt["senses"][0]
adds=[normalize_example(e,"virado","virada",ts.get("roles",[])) for e in ss.get("examples",[])]
dedupe_append(ts["examples"],adds)
ledger.append({"wrong_lemma":"virado","correct_lemma":"virada","action":"MERGE_AND_REMOVE_FALSE_LEMMA","moved":len(adds),"note":"virada is the nominal event/change noun"})
save("virada",tgt); (J/"virado.json").unlink()

# 4) alternativo -> alternativa, 1:1 lexical correction
src=load("alternativo")
src["lemma"]="alternativa"; src["lemma_base"]="alternativa"
for s in src.get("senses",[]):
    s["pt_roleset"]=s.get("pt_roleset","").replace("alternativo.","alternativa.")
    for e in s.get("examples",[]):
        iid=e.get("instance_id","")
        e["instance_id"]=iid.replace("::alternativo::","::alternativa::")
save("alternativa",src); (J/"alternativo.json").unlink()
ledger.append({"wrong_lemma":"alternativo","correct_lemma":"alternativa","action":"RENAME_LEXICAL_ENTRY","moved":1,"note":"noun in corpus is alternativa 'option', not masculine adjective alternativo"})

# 5) representação -> reapresentação.02 (restatement), preserve existing reapresentação.01 (submission/resubmission)
src=load("representação"); tgt=load("reapresentação")
ss=src["senses"][0]
roles=ss.get("roles",[])
new_sense=json.loads(json.dumps(ss,ensure_ascii=False))
new_sense["pt_roleset"]="reapresentação.02"
new_sense["pt_sense_index"]=2
new_sense["pt_sense_hint"]=2
new_sense["pt_sense_gloss"]="reapresentação/restatement de demonstrações financeiras"
new_sense["english_roleset"]="restatement.01"
new_sense["english_roleset_source"]="LEXICAL_IDENTITY_REPAIR_V2H"
new_sense["examples"]=[normalize_example(e,"representação","reapresentação",roles) for e in ss.get("examples",[])]
# avoid duplicate sense on rerun
tgt["senses"]=[s for s in tgt.get("senses",[]) if s.get("pt_roleset")!="reapresentação.02"]+[new_sense]
save("reapresentação",tgt); (J/"representação.json").unlink()
ledger.append({"wrong_lemma":"representação","correct_lemma":"reapresentação","action":"MOVE_TO_NEW_SENSE_REAPRESENTACAO_02_AND_REMOVE_FALSE_LEMMA","moved":len(new_sense["examples"]),"note":"reapresentação is a distinct prefixed noun; financial-statement uses map to restatement.01"})

# Manifest: remove four duplicate false entries, rename alternativo -> alternativa.
manifest=json.loads((J/"_manifest.json").read_text(encoding="utf-8"))
out=[]
for x in manifest["lemmas"]:
    lem=x["lemma"]
    if lem in {"descoberto","retirado","virado","representação"}:
        continue
    if lem=="alternativo":
        x=dict(x); x["lemma"]="alternativa"; x["filename"]="alternativa.json"
    out.append(x)
# stable alphabetical order
out=sorted(out,key=lambda x:x["lemma"].casefold())
manifest["lemmas"]=out
(J/"_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Stats: identity repair only, from accepted base counts.
stats=json.loads((J/"statistics.json").read_text(encoding="utf-8"))
stats["schema_version"]="nounbank-ds-expanded-sanitized-stats/1.2-lexical-identity-repair"
stats["inventory"]["public_lemmas"]=516
stats["inventory"]["original"]=145
stats["inventory"]["new"]=371
stats["inventory"]["lexical_identity_collapses_removed"]=4
stats["inventory"]["removed_without_predicative_occurrence"]=216
stats["examples"]["predicative_occurrences"]=3707
stats["examples"]["regular_occurrences"]=3575
stats["examples"]["pending_occurrences"]=132
stats["pending"]["awaiting_sense"]=22
stats["pending"]["pending_lemmas"]=[x for x in stats["pending"]["pending_lemmas"] if x!="descoberto"]
(J/"statistics.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Index counters/text.
idx=(ROOT/"index.html").read_text(encoding="utf-8")
idx=idx.replace("com 520 nomes predicadores","com 516 nomes predicadores")
idx=idx.replace("<strong>520</strong><span>nomes predicadores</span>","<strong>516</strong><span>nomes predicadores</span>")
idx=idx.replace("<strong>3.708</strong><span>ocorrências predicadoras</span>","<strong>3.707</strong><span>ocorrências predicadoras</span>")
idx=idx.replace("<strong>145 + 375</strong>","<strong>145 + 371</strong>")
idx=idx.replace("As 375 entradas acrescentadas","As 371 entradas acrescentadas")
(ROOT/"index.html").write_text(idx,encoding="utf-8")

# Simple static renderer for affected canonical pages.
def render(lemma,obj,new_flag):
    letter=lemma[0].lower()
    chunks=[]
    for s in obj.get("senses",[]):
        en=s.get("english_roleset")
        url=s.get("nombank_url")
        if en and url: map_html=f'<a href="{html.escape(url)}">{html.escape(en)}</a>'
        else: map_html=html.escape(str(en)) if en else "—"
        chunks.append(f'<p class="roleset-line"><strong>Roleset id:</strong> {html.escape(s.get("pt_roleset",""))}, Mapeamento para o inglês: {map_html}</p>')
        chunks.append("<h2>Roles:</h2><ul>")
        for r in s.get("roles",[]):
            chunks.append(f'<li class="{r["id"].lower()}">{html.escape(r["id"].replace("Arg","Arg "))}: {html.escape(str(r.get("desc","")))}</li>')
        chunks.append("</ul><h2>Exemplos:</h2>")
        for i,e in enumerate(s.get("examples",[]),1):
            text=e.get("text","")
            form=(e.get("predicate") or {}).get("form","")
            # highlight first occurrence case-insensitively
            safe=html.escape(text)
            if form:
                pat=re.compile(re.escape(html.escape(form)),re.I)
                safe=pat.sub(lambda m:f'<span class="rel">{m.group(0)}</span>',safe,count=1)
            chunks.append(f"<h3>{i}: {safe}</h3><ul><li class=\"rel\">rel: {html.escape(form)}</li>")
            for r in s.get("roles",[]):
                rid=r["id"]; val=(e.get("realization") or {}).get(rid)
                chunks.append(f'<li class="{rid.lower()}">{html.escape(rid.replace("Arg","Arg "))}: {html.escape(str(val)) if val else "-"}</li>')
            chunks.append("</ul>")
        chunks.append('<div class="sense-divider" aria-hidden="true"></div>')
    newbadge=' <sup class="new-float">NEW</sup>' if new_flag else ''
    body="".join(chunks)
    return f'''<!DOCTYPE html>
<html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(lemma)} - NounBank.DS Expanded</title><link rel="stylesheet" href="../styles.css">
<style>:root{{--header-h:56px}}body{{margin:0}}.site-header{{position:sticky;top:0;z-index:1000;background:rgba(20,20,20,.70)}}.site-nav{{height:var(--header-h);display:flex;align-items:center;justify-content:space-between;padding:0 16px}}.site-nav .home-link{{color:#cfe3ff;text-decoration:none;font-weight:600}}.site-nav .download-json{{color:#fff;background:#2e7d32;padding:10px 14px;border-radius:12px;text-decoration:none}}</style>
</head><body><header class="site-header"><nav class="site-nav"><a class="home-link" href="../index.html?letter={letter}">Home</a><span class="page-title">{html.escape(lemma)}</span><a class="download-json" href="../jsons/{html.escape(lemma)}.json" download>JSON download</a></nav></header>
<div class="content"><h1>Nome predicador: <i style="color:red;">{html.escape(lemma)}</i>{newbadge}</h1>{body}</div>
<a class="back-link back-floating" href="../index.html?letter={letter}">← Voltar para {letter.upper()}</a></body></html>'''

manifest_map={x["lemma"]:x for x in manifest["lemmas"]}
for lemma in ["descoberta","retirada","virada","alternativa","reapresentação"]:
    obj=load(lemma)
    (P/f"{lemma}.html").write_text(render(lemma,obj,manifest_map[lemma]["new"]),encoding="utf-8")

for old in ["descoberto","retirado","virado","alternativo","representação"]:
    q=P/f"{old}.html"
    if q.exists(): q.unlink()

# Rebuild aggregate zip: 516 lemma JSONs + manifest + stats = 518 entries.
z=J/"nounbank.ds_expanded_all_jsons.zip"
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
    for x in manifest["lemmas"]:
        p=J/x["filename"]
        assert p.exists(), p
        zz.write(p,arcname=p.name)
    zz.write(J/"_manifest.json",arcname="_manifest.json")
    zz.write(J/"statistics.json",arcname="statistics.json")

# Repair ledger and validation.
docs=ROOT/"docs"; docs.mkdir(exist_ok=True)
(docs/"LEXICAL_IDENTITY_REPAIR_V2H.json").write_text(json.dumps({
 "status":"CLOSED_LEXICAL_IDENTITY_REPAIR",
 "base_commit":"46c8074f1d89d86dc7a2a619f4b1147d8d046d38",
 "confirmed_collapses":ledger,
 "reviewed_mismatch_files":57,
 "confirmed_real_collapses":5,
 "other_mismatch_files_classification":"SURFACE_VARIATION_OR_INFLECTION_NOT_LEXICAL_IDENTITY_COLLAPSE",
 "inventory_before":520,"inventory_after":516,
 "new_before":375,"new_after":371,
 "predicative_occurrences_before":3708,"predicative_occurrences_after":3707,
 "pending_before":133,"pending_after":132,
 "awaiting_sense_before":23,"awaiting_sense_after":22
},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert len(manifest["lemmas"])==516
assert len({x["lemma"] for x in manifest["lemmas"]})==516
for bad in ["descoberto","retirado","virado","alternativo","representação"]:
    assert bad not in {x["lemma"] for x in manifest["lemmas"]}
    assert not (J/f"{bad}.json").exists()
    assert not (P/f"{bad}.html").exists()
for good in ["descoberta","retirada","virada","alternativa","reapresentação"]:
    assert (J/f"{good}.json").exists() and (P/f"{good}.html").exists()
with zipfile.ZipFile(z) as zz:
    assert len(zz.namelist())==518
print(json.dumps({"status":"PASS","public_lemmas":516,"new":371,"predicative_occurrences":3707,"pending":132,"zip_entries":518},indent=2))
