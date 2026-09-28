import html, json, re
from pathlib import Path
from collections import defaultdict

ROOT=Path("."); JD=ROOT/"jsons"; PD=ROOT/"site_pages"
manifest=json.loads((JD/"_manifest.json").read_text(encoding="utf-8"))["lemmas"]

def esc(x): return html.escape("" if x is None else str(x), quote=True)
def role_sig(s):
    return tuple((r.get("id"), r.get("desc")) for r in (s.get("roles") or []))
def role_class(r): return str(r or "").lower()

def group_senses(senses):
    groups=[]
    for s in senses:
        sig=role_sig(s)
        found=None
        for g in groups:
            if g["sig"]==sig:
                found=g; break
        if found is None:
            found={"sig":sig,"senses":[]}; groups.append(found)
        found["senses"].append(s)
    return groups

def source_link(src):
    if not src: return None
    frame=re.sub(r"^verb-","",src)
    frame=re.sub(r"\.[0-9]+$","",frame)
    return f'<a href="https://verbs.colorado.edu/propbank/framesets-english-aliases/{esc(frame)}.html">{esc(src)}</a>'

def aggregate_examples(group):
    ex=[]
    for s in group["senses"]:
        ex.extend(s.get("examples") or [])
    return ex

def aggregate_profile(examples, rids):
    deps=sorted({v for e in examples for v in (e.get("syntax") or {}).values() if v})
    return deps

def marked_from_existing_html(text):
    return text

# We preserve the currently-correct static highlighting by extracting each example row from the existing HTML
# keyed by instance-id where possible; if missing, use public JSON text.
def existing_example_map(lemma):
    p=PD/f"{lemma}.html"
    if not p.exists(): return {}
    t=p.read_text(encoding="utf-8")
    m={}
    for mm in re.finditer(r'<h3 data-instance-id="([^"]*)">\d+: (.*?)</h3>',t,re.S):
        m[mm.group(1)]=mm.group(2)
    for mm in re.finditer(r'<tr[^>]*data-instance-id="([^"]*)"[^>]*>.*?<td class="texto">(.*?)</td></tr>',t,re.S):
        m.setdefault(mm.group(1),mm.group(2))
    return m

for item in manifest:
    lemma=item["lemma"]; letter=lemma[0].lower()
    data=json.loads((JD/item["filename"]).read_text(encoding="utf-8"))
    oldmap=existing_example_map(lemma)
    groups=group_senses(data.get("senses") or [])
    body=[]
    body.append(f'<h1>Nome predicador: <i style="color: red;">{esc(lemma)}</i>{" <sup class=\"new-float\">NEW</sup>" if item.get("new") else ""}</h1>')

    for gi,g in enumerate(groups):
        if gi:
            body.append('<div class="sense-divider" aria-hidden="true"></div>')

        senses=g["senses"]
        pt=", ".join(esc(s.get("pt_roleset")) for s in senses)
        mappings=[]
        for s in senses:
            er=s.get("english_roleset"); nb=s.get("nombank_url")
            if er:
                mappings.append(f'<a href="{esc(nb)}">{esc(er)}</a>' if nb else esc(er))
            else:
                mappings.append('<span class="pending-label">Aguardando resolução</span>')
        mappings=", ".join(mappings)

        sources=[]
        for s in senses:
            src=s.get("english_roleset_source")
            if src and src not in sources:sources.append(src)
        source_html=""
        if sources:
            links=[source_link(x) for x in sources]
            source_html=", source = "+", ".join(x for x in links if x)

        body.append(f'<p class="roleset-line"><strong>Roleset id:</strong> {pt}, Mapeamento para o inglês: {mappings}{source_html}</p>')

        roles=(senses[0].get("roles") or []) if senses else []
        rids=[r["id"] for r in roles if r.get("id")]
        body.append('<h2>Roles:</h2>')
        if roles:
            body.append('<ul>'+''.join(
                f'<li class="{role_class(r.get("id"))}">{esc(str(r.get("id","")).replace("Arg","Arg "))}: {esc(r.get("desc") or "")}</li>'
                for r in roles if r.get("id")
            )+'</ul>')
        else:
            body.append('<p class="muted">Inventário de papéis aguardando resolução.</p>')

        examples=aggregate_examples(g)
        body.append('<h2>Exemplos:</h2>')
        for i,e in enumerate(examples[:2],1):
            iid=e.get("instance_id","")
            rendered=oldmap.get(iid, esc(e.get("text","")))
            body.append(f'<h3 data-instance-id="{esc(iid)}">{i}: {rendered}</h3>')
            body.append('<ul>')
            body.append(f'<li class="rel">rel: {esc((e.get("predicate") or {}).get("form") or lemma)}</li>')
            for r in rids:
                val=(e.get("realization") or {}).get(r)
                body.append(f'<li class="{role_class(r)}">{esc(r.replace("Arg","Arg "))}: {esc(val) if val else "-"}</li>')
            body.append('</ul>')
        body.append('<br><br>')

        if examples and rids:
            body.append('<h2>Realização sintática da estrutura de argumentos</h2>')
            body.append(f'<div class="argument-table-scroll" tabindex="0" aria-label="Realização sintática"><table class="expanded-arguments" style="--arg-count:{len(rids)}">')
            body.append('<colgroup><col class="numcol">'+''.join('<col class="argcol">' for _ in rids)+'<col class="textcol"></colgroup>')
            body.append('<thead><tr><th>#</th>'+''.join(f'<th class="{role_class(r)}">{esc(r.replace("Arg","Arg "))}</th>' for r in rids)+'<th>Texto</th></tr></thead><tbody>')
            for i,e in enumerate(examples,1):
                iid=e.get("instance_id","")
                rendered=oldmap.get(iid, esc(e.get("text","")))
                cells=''.join(f'<td class="{role_class(r)}">{esc((e.get("realization") or {}).get(r)) if (e.get("realization") or {}).get(r) else "-"}</td>' for r in rids)
                body.append(f'<tr data-instance-id="{esc(iid)}"><td>{i}</td>{cells}<td class="texto">{rendered}</td></tr>')
            body.append('</tbody></table></div>')

            deps=aggregate_profile(examples,rids)
            if deps:
                body.append('<div class="statistics-table-container"><h2>Frequência das realizações sintáticas</h2>')
                body.append('<table class="stats-table"><thead><tr><th>Relações de dependência - <i><a href="https://universaldependencies.org/u/dep/">Universal Dependencies</a></i></th>'+''.join(f'<th class="{role_class(r)}">{esc(r.replace("Arg","Arg "))}</th>' for r in rids)+'</tr></thead><tbody>')
                for dep in deps:
                    body.append('<tr><td>'+esc(dep)+'</td>'+''.join(f'<td>{sum(1 for e in examples if (e.get("syntax") or {}).get(r)==dep)}</td>' for r in rids)+'</tr>')
                body.append('</tbody></table></div>')

    pend=data.get("pending_instances") or []
    if pend:
        body.append('<div class="sense-divider" aria-hidden="true"></div><section class="pending-section"><h2>Aguardando resolução de sense/roleset</h2>')
        for i,e in enumerate(pend[:2],1):
            iid=e.get("instance_id","")
            rendered=oldmap.get(iid,esc(e.get("text","")))
            body.append(f'<h3 data-instance-id="{esc(iid)}">{i}: {rendered}</h3><ul><li class="rel">rel: {esc((e.get("predicate") or {}).get("form") or lemma)}</li></ul>')
        body.append('</section>')

    page=f'''<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(lemma)} - NounBank.DS Expanded</title>
<link rel="stylesheet" href="../styles.css">
<style>
:root{{--header-h:56px}}body{{margin:0}}
.site-header{{position:sticky;top:0;z-index:1000;background:rgba(20,20,20,.70);transition:background .2s ease,backdrop-filter .2s ease}}
.site-header.scrolled{{background:rgba(20,20,20,.40);backdrop-filter:blur(6px)}}
.site-nav{{height:var(--header-h);display:flex;align-items:center;justify-content:space-between;padding:0 16px}}
.site-nav .home-link{{color:#cfe3ff;text-decoration:none;font-weight:600;padding:8px 12px;border-radius:10px;background:rgba(84,102,170,.25)}}
.site-nav .page-title{{color:#cfd8ff;opacity:.75;font-weight:600;text-align:center;margin:0 12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.site-nav .download-json{{display:inline-block;text-decoration:none;font-weight:700;padding:10px 14px;border-radius:12px;color:#fff;background:#2e7d32;box-shadow:0 4px 14px rgba(0,0,0,.25)}}
.back-floating{{position:fixed;right:20px;bottom:20px;z-index:980;background:#2b2b2b;color:#cfe3ff;padding:10px 12px;border-radius:12px;box-shadow:0 8px 22px rgba(0,0,0,.35);text-decoration:none}}
</style>
</head>
<body>
<header class="site-header"><nav class="site-nav">
<a class="home-link" href="../index.html?letter={esc(letter)}">Home</a>
<span class="page-title">{esc(lemma)}</span>
<a class="download-json" href="../jsons/{esc(item["filename"])}" download="{esc(item["filename"])}">JSON download</a>
</nav></header>
<script>(function(){{const h=document.querySelector('.site-header');if(!h)return;const f=()=>h.classList.toggle('scrolled',window.scrollY>16);f();window.addEventListener('scroll',f,{{passive:true}})}})();</script>
<div class="content">{"".join(body)}</div>
<a class="back-link back-floating" href="../index.html?letter={esc(letter)}" title="Voltar para letra {esc(letter.upper())}">← Voltar para {esc(letter.upper())}</a>
</body></html>'''
    (PD/f"{lemma}.html").write_text(page,encoding="utf-8")

assert len(list(PD.glob("*.html")))==494
print("PAGES=494")

# trigger
