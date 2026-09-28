import html, json, re, subprocess
from pathlib import Path

ROOT=Path("."); JD=ROOT/"jsons"; PD=ROOT/"site_pages"
SURFACE_COMMIT="74f24bce020caa68b19252f2d0593763adf6db24"
manifest=json.loads((JD/"_manifest.json").read_text(encoding="utf-8"))["lemmas"]

def esc(x): return html.escape("" if x is None else str(x), quote=True)
def rc(r): return str(r or "").lower()
def role_sig(s): return tuple((r.get("id"),r.get("desc")) for r in (s.get("roles") or []))
def group_senses(senses):
    groups=[]
    for s in senses:
        sig=role_sig(s)
        g=next((x for x in groups if x["sig"]==sig),None)
        if g is None:
            g={"sig":sig,"senses":[]}; groups.append(g)
        g["senses"].append(s)
    return groups
def source_link(src):
    if not src:return None
    frame=re.sub(r"^verb-","",src); frame=re.sub(r"\.[0-9]+$","",frame)
    return f'<a href="https://verbs.colorado.edu/propbank/framesets-english-aliases/{esc(frame)}.html">{esc(src)}</a>'

def old_rendered_examples(lemma):
    raw=subprocess.check_output(["git","show",f"{SURFACE_COMMIT}:site_pages/{lemma}.html"]).decode("utf-8")
    return [m.group(1) for m in re.finditer(r'<h3(?:\s+data-instance-id="[^"]*")?>(?:\d+):\s*(.*?)</h3>',raw,re.S)]

def all_examples(data):
    arr=[]
    for s in data.get("senses") or []: arr.extend(s.get("examples") or [])
    arr.extend(data.get("pending_instances") or [])
    return arr

for item in manifest:
    lemma=item["lemma"]; letter=lemma[0].lower()
    data=json.loads((JD/item["filename"]).read_text(encoding="utf-8"))
    rendered=old_rendered_examples(lemma)
    ex_all=all_examples(data)
    if len(rendered)!=len(ex_all):
        raise RuntimeError(f"{lemma}: rendered={len(rendered)} json={len(ex_all)}")
    render_by_obj={id(e):rendered[i] for i,e in enumerate(ex_all)}

    body=[f'<h1>Nome predicador: <i style="color: red;">{esc(lemma)}</i>{" <sup class=\"new-float\">NEW</sup>" if item.get("new") else ""}</h1>']
    groups=group_senses(data.get("senses") or [])

    for gi,g in enumerate(groups):
        if gi: body.append('<div class="sense-divider" aria-hidden="true"></div>')
        senses=g["senses"]
        pt=", ".join(esc(s.get("pt_roleset")) for s in senses)
        mappings=[]
        for s in senses:
            er=s.get("english_roleset"); nb=s.get("nombank_url")
            mappings.append(f'<a href="{esc(nb)}">{esc(er)}</a>' if er and nb else (esc(er) if er else '<span class="pending-label">Aguardando resolução</span>'))
        sources=[]
        for s in senses:
            src=s.get("english_roleset_source")
            if src and src not in sources:sources.append(src)
        source_html=""
        if sources: source_html=", source = "+", ".join(source_link(x) for x in sources)
        body.append(f'<p class="roleset-line"><strong>Roleset id:</strong> {pt}, Mapeamento para o inglês: {", ".join(mappings)}{source_html}</p>')

        roles=(senses[0].get("roles") or []) if senses else []
        rids=[r["id"] for r in roles if r.get("id")]
        body.append('<h2>Roles:</h2>')
        if roles:
            body.append('<ul>'+''.join(f'<li class="{rc(r.get("id"))}">{esc(str(r.get("id","")).replace("Arg","Arg "))}: {esc(r.get("desc") or "")}</li>' for r in roles if r.get("id"))+'</ul>')
        else:
            body.append('<p class="muted">Inventário de papéis aguardando resolução.</p>')

        examples=[]
        for s in senses: examples.extend(s.get("examples") or [])

        body.append('<h2>Exemplos:</h2>')
        for i,e in enumerate(examples[:2],1):
            shown=render_by_obj[id(e)]
            body.append(f'<h3>{i}: {shown}</h3><ul><li class="rel">rel: {esc((e.get("predicate") or {}).get("form") or lemma)}</li>')
            for r in rids:
                v=(e.get("realization") or {}).get(r)
                body.append(f'<li class="{rc(r)}">{esc(r.replace("Arg","Arg "))}: {esc(v) if v else "-"}</li>')
            body.append('</ul>')
        body.append('<br><br>')

        if examples and rids:
            body.append('<h2>Realização sintática da estrutura de argumentos</h2>')
            body.append(f'<div class="argument-table-scroll" tabindex="0"><table class="expanded-arguments" style="--arg-count:{len(rids)}"><colgroup><col class="numcol">'+''.join('<col class="argcol">' for _ in rids)+'<col class="textcol"></colgroup><thead><tr><th>#</th>'+''.join(f'<th class="{rc(r)}">{esc(r.replace("Arg","Arg "))}</th>' for r in rids)+'<th>Texto</th></tr></thead><tbody>')
            for i,e in enumerate(examples,1):
                cells=''.join(f'<td class="{rc(r)}">{esc((e.get("realization") or {}).get(r)) if (e.get("realization") or {}).get(r) else "-"}</td>' for r in rids)
                body.append(f'<tr><td>{i}</td>{cells}<td class="texto">{render_by_obj[id(e)]}</td></tr>')
            body.append('</tbody></table></div>')

            deps=sorted({v for e in examples for v in (e.get("syntax") or {}).values() if v})
            if deps:
                body.append('<div class="statistics-table-container"><h2>Frequência das realizações sintáticas</h2><table class="stats-table"><thead><tr><th>Relações de dependência - <i><a href="https://universaldependencies.org/u/dep/">Universal Dependencies</a></i></th>'+''.join(f'<th class="{rc(r)}">{esc(r.replace("Arg","Arg "))}</th>' for r in rids)+'</tr></thead><tbody>')
                for dep in deps:
                    body.append('<tr><td>'+esc(dep)+'</td>'+''.join(f'<td>{sum(1 for e in examples if (e.get("syntax") or {}).get(r)==dep)}</td>' for r in rids)+'</tr>')
                body.append('</tbody></table></div>')

    pend=data.get("pending_instances") or []
    if pend:
        body.append('<div class="sense-divider" aria-hidden="true"></div><section class="pending-section"><h2>Aguardando resolução de sense/roleset</h2>')
        for i,e in enumerate(pend[:2],1): body.append(f'<h3>{i}: {render_by_obj[id(e)]}</h3>')
        body.append('</section>')

    page=f'''<!DOCTYPE html>
<html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(lemma)} - NounBank.DS Expanded</title><link rel="stylesheet" href="../styles.css">
<style>:root{{--header-h:56px}}body{{margin:0}}.site-header{{position:sticky;top:0;z-index:1000;background:rgba(20,20,20,.70);transition:background .2s ease,backdrop-filter .2s ease}}.site-header.scrolled{{background:rgba(20,20,20,.40);backdrop-filter:blur(6px)}}.site-nav{{height:var(--header-h);display:flex;align-items:center;justify-content:space-between;padding:0 16px}}.site-nav .home-link{{color:#cfe3ff;text-decoration:none;font-weight:600;padding:8px 12px;border-radius:10px;background:rgba(84,102,170,.25)}}.site-nav .page-title{{color:#cfd8ff;opacity:.75;font-weight:600;text-align:center;margin:0 12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.site-nav .download-json{{display:inline-block;text-decoration:none;font-weight:700;padding:10px 14px;border-radius:12px;color:#fff;background:#2e7d32;box-shadow:0 4px 14px rgba(0,0,0,.25)}}.back-floating{{position:fixed;right:20px;bottom:20px;z-index:980;background:#2b2b2b;color:#cfe3ff;padding:10px 12px;border-radius:12px;box-shadow:0 8px 22px rgba(0,0,0,.35);text-decoration:none}}</style>
</head><body><header class="site-header"><nav class="site-nav"><a class="home-link" href="../index.html?letter={esc(letter)}">Home</a><span class="page-title">{esc(lemma)}</span><a class="download-json" href="../jsons/{esc(item["filename"])}" download>JSON download</a></nav></header><script>(function(){{const h=document.querySelector('.site-header');if(!h)return;const f=()=>h.classList.toggle('scrolled',window.scrollY>16);f();window.addEventListener('scroll',f,{{passive:true}})}})();</script><div class="content">{"".join(body)}</div><a class="back-link back-floating" href="../index.html?letter={esc(letter)}">← Voltar para {esc(letter.upper())}</a></body></html>'''
    (PD/f"{lemma}.html").write_text(page,encoding="utf-8")

assert len(list(PD.glob("*.html")))==494
print("PAGES=494")
print("ACORDO_GROUPS=",len(group_senses(json.loads((JD/"acordo.json").read_text())["senses"])))
