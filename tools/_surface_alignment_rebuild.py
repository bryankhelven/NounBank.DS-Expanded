import html, json, re, subprocess, unicodedata
from pathlib import Path
from collections import defaultdict

ROOT=Path(".")
JD=ROOT/"jsons"; PD=ROOT/"site_pages"
SOURCE="4295edf3e8dc8020717506ca0d3d2d3f21c7b11d"
manifest=json.loads((JD/"_manifest.json").read_text(encoding="utf-8"))["lemmas"]

CONTR={
 "do":["de","o"],"da":["de","a"],"dos":["de","os"],"das":["de","as"],
 "no":["em","o"],"na":["em","a"],"nos":["em","os"],"nas":["em","as"],
 "ao":["a","o"],"aos":["a","os"],"pelo":["por","o"],"pela":["por","a"],
 "pelos":["por","os"],"pelas":["por","as"],"pro":["para","o"],"pra":["para","a"]
}
TOKEN_RE=re.compile(r'[#@]?[\\wÀ-ÖØ-öø-ÿ]+(?:[.,][0-9]+)*|[%$€£]|[^\\w\\s]',re.UNICODE)

def fold(s): return unicodedata.normalize("NFC",s).casefold()

def canon_tokens(text):
 out=[]
 for m in TOKEN_RE.finditer(text):
  raw=m.group(0); f=fold(raw)
  if re.fullmatch(r'[^\\wÀ-ÖØ-öø-ÿ#@%$€£]+',raw): continue
  for v in CONTR.get(f,[f]): out.append((v,m.start(),m.end()))
 return out

def target_tokens(text): return [x[0] for x in canon_tokens(text)]

def find_span(sentence,target,prefer=None):
 st=canon_tokens(sentence); tt=target_tokens(target)
 if not tt:return None
 hits=[]
 for i in range(0,len(st)-len(tt)+1):
  if [x[0] for x in st[i:i+len(tt)]]==tt:
   hits.append((st[i][1],st[i+len(tt)-1][2],i))
 if not hits:return None
 if prefer is None or len(hits)==1:return hits[0][:2]
 return min(hits,key=lambda h:abs(h[2]-prefer))[:2]

def source_json(lemma):
 raw=subprocess.check_output(["git","show",f"{SOURCE}:jsons/{lemma}.json"])
 return json.loads(raw)

def source_index(src):
 rows=(src.get("expanded_v2") or {}).get("current_record",{}).get("instances",[]) or []
 S=[r for r in rows if r.get("contextual_predicativity")=="S"]
 groups=defaultdict(list)
 for r in S: groups[r.get("sent_id")].append(r)
 for rs in groups.values(): rs.sort(key=lambda r:int(r.get("token_id") or 10**9))
 return groups

def parse_ord(instance_id):
 try:return int(str(instance_id).rsplit("::",1)[1])
 except:return 1

def esc(s): return html.escape("" if s is None else str(s),quote=True)

def annotated_html(ex,lemma,sg):
 sentence=ex.get("text","")
 sid=ex.get("sent_ID"); ordno=parse_ord(ex.get("instance_id"))
 src_rows=sg.get(sid,[]); src=src_rows[ordno-1] if 0<ordno<=len(src_rows) else None
 pref=None
 if src:
  try:pref=max(0,int(src.get("token_id") or 1)-1)
  except:pass
 marks=[]
 for role,val in (ex.get("realization") or {}).items():
  if val:
   hit=find_span(sentence,str(val),pref)
   if hit:marks.append((hit[0],hit[1],role,(ex.get("syntax") or {}).get(role)))
 form=str((ex.get("predicate") or {}).get("form") or lemma)
 hit=find_span(sentence,form,pref)
 if hit:marks.append((hit[0],hit[1],"REL",None))
 accepted=[]
 for m in sorted(marks,key=lambda x:(x[0],-(x[1]-x[0]),0 if x[2]!="REL" else 1)):
  if not any(not (m[1]<=a[0] or m[0]>=a[1]) for a in accepted):accepted.append(m)
 accepted.sort(key=lambda x:x[0])
 parts=[];pos=0
 for a,b,role,dep in accepted:
  parts.append(esc(sentence[pos:a])); surface=esc(sentence[a:b])
  if role=="REL": parts.append(f'<span class="rel">{surface}</span>')
  else:
   piece=f'<span class="{role.lower()}">{surface}</span>'
   if dep: piece+=f'<sub class="deprel">{esc(dep)}</sub>'
   parts.append(piece)
  pos=b
 parts.append(esc(sentence[pos:]))
 return "".join(parts)

colored=0; unmatched=0
for item in manifest:
 lemma=item["lemma"]
 data=json.loads((JD/item["filename"]).read_text(encoding="utf-8"))
 sg=source_index(source_json(lemma))
 body=[f'<h1>Nome predicador: <i style="color: red;">{esc(lemma)}</i>{" <sup class=\"new-float\">NEW</sup>" if item.get("new") else ""}</h1>']

 for s in data.get("senses") or []:
  er=s.get("english_roleset"); nb=s.get("nombank_url")
  mapping=f'<a href="{esc(nb)}">{esc(er)}</a>' if er and nb else (esc(er) if er else '<span class="pending-label">Aguardando resolução</span>')
  body.append(f'<p><strong>Roleset id:</strong> {esc(s.get("pt_roleset"))}, Mapeamento para o inglês: {mapping}</p>')
  roles=[r for r in (s.get("roles") or []) if r.get("id")]; rids=[r["id"] for r in roles]
  body.append('<h2>Roles:</h2>')
  body.append('<ul>'+''.join(f'<li class="{r["id"].lower()}">{esc(r["id"].replace("Arg","Arg "))}: {esc(r.get("desc",""))}</li>' for r in roles)+'</ul>' if roles else '<p class="muted">Inventário de papéis aguardando resolução.</p>')
  body.append('<h2>Exemplos:</h2>')
  examples=s.get("examples") or []
  for i,e in enumerate(examples,1):
   rendered=annotated_html(e,lemma,sg)
   if 'class="arg' in rendered: colored+=1
   for role,val in (e.get("realization") or {}).items():
    if val and f'class="{role.lower()}"' not in rendered: unmatched+=1
   body.append(f'<h3 data-instance-id="{esc(e.get("instance_id",""))}">{i}: {rendered}</h3>')
   body.append('<ul><li class="rel">rel: '+esc((e.get("predicate") or {}).get("form") or lemma)+'</li>'+''.join(f'<li class="{r.lower()}">{esc(r.replace("Arg","Arg "))}: {esc((e.get("realization") or {}).get(r)) if (e.get("realization") or {}).get(r) else "-"}</li>' for r in rids)+'</ul>')
  body.append('<br><br>')

  if examples and rids:
   body.append('<h2>Realização sintática da estrutura de argumentos</h2>')
   body.append(f'<div class="argument-table-scroll"><table class="expanded-arguments" style="--arg-count:{len(rids)}"><thead><tr><th>#</th>'+''.join(f'<th class="{r.lower()}">{esc(r.replace("Arg","Arg "))}</th>' for r in rids)+'<th>Texto</th></tr></thead><tbody>')
   for i,e in enumerate(examples,1):
    cells=''.join(f'<td class="{r.lower()}">{esc((e.get("realization") or {}).get(r)) if (e.get("realization") or {}).get(r) else "-"}</td>' for r in rids)
    body.append(f'<tr><td>{i}</td>{cells}<td class="texto">{annotated_html(e,lemma,sg)}</td></tr>')
   body.append('</tbody></table></div>')
   deps=sorted({v for e in examples for v in (e.get("syntax") or {}).values() if v})
   if deps:
    body.append('<h3>Frequência das realizações sintáticas</h3><table class="stats-table"><thead><tr><th>Relação de dependência — Universal Dependencies</th>'+''.join(f'<th class="{r.lower()}">{esc(r.replace("Arg","Arg "))}</th>' for r in rids)+'</tr></thead><tbody>')
    for dep in deps:
     body.append('<tr><td>'+esc(dep)+'</td>'+''.join(f'<td>{sum(1 for e in examples if (e.get("syntax") or {}).get(r)==dep)}</td>' for r in rids)+'</tr>')
    body.append('</tbody></table>')

 pend=data.get("pending_instances") or []
 if pend:
  body.append('<section class="pending-section"><h2>Aguardando resolução de sense/roleset</h2>')
  for i,e in enumerate(pend,1): body.append(f'<h3>{i}: {annotated_html(e,lemma,sg)}</h3><ul><li class="rel">rel: {esc((e.get("predicate") or {}).get("form") or lemma)}</li></ul>')
  body.append('</section>')

 page=f'''<!DOCTYPE html>
<html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(lemma)} - NounBank.DS Expanded</title><link rel="stylesheet" href="../styles.css">
<style>:root{{--header-h:56px}}body{{margin:0}}.site-header{{position:sticky;top:0;z-index:1000;background:rgba(20,20,20,.70)}}.site-nav{{height:var(--header-h);display:flex;align-items:center;justify-content:space-between;padding:0 16px}}.site-nav .home-link{{color:#cfe3ff;text-decoration:none;font-weight:600;padding:8px 12px;border-radius:10px;background:rgba(84,102,170,.25)}}.site-nav .page-title{{color:#cfd8ff;opacity:.75;font-weight:600}}.site-nav .download-json{{text-decoration:none;font-weight:700;padding:10px 14px;border-radius:12px;color:#fff;background:#2e7d32}}</style>
</head><body><header class="site-header"><nav class="site-nav"><a class="home-link" href="../index.html">Home</a><span class="page-title">{esc(lemma)}</span><a class="download-json" href="../jsons/{esc(item["filename"])}" download>JSON download</a></nav></header><div class="content">{"".join(body)}</div></body></html>'''
 (PD/f"{lemma}.html").write_text(page,encoding="utf-8")

assert len(list(PD.glob("*.html")))==494
print("PAGES=494")
print("EXAMPLES_WITH_COLORED_ARGS=",colored)
print("REALIZED_ARGUMENTS_UNMATCHED=",unmatched)

# trigger
