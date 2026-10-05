import json,re,html,unicodedata,subprocess,hashlib
from decimal import Decimal,InvalidOperation
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'data/provenance/v32'
OUTPUT.mkdir(exist_ok=True)
CONTR={'do':['de','o'],'da':['de','a'],'dos':['de','os'],'das':['de','as'],'no':['em','o'],'na':['em','a'],'nos':['em','os'],'nas':['em','as'],'ao':['a','o'],'aos':['a','os'],'pelo':['por','o'],'pela':['por','a'],'pelos':['por','os'],'pelas':['por','as'],'neles':['em','eles'],'nelas':['em','elas']}
TR=re.compile(r'[#@]?[\w]+(?:[.,]\d+)*|[%$€£]',re.UNICODE)
def norm(s):
 s=''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if not unicodedata.combining(c)).lstrip('#@')
 if re.fullmatch(r'\d+[.,]\d+',s):
  try:s=str(Decimal(s.replace(',','.')).normalize())
  except InvalidOperation:pass
 return s
def tokens(s):
 return [(v,m.start(),m.end()) for m in TR.finditer(s) for v in CONTR.get(norm(m.group()),[norm(m.group())])]
def find(text,value,prefer=None):
 st=tokens(text);tt=[x[0] for x in tokens(value)];hits=[]
 if not tt:return None
 for i in range(len(st)-len(tt)+1):
  if [x[0] for x in st[i:i+len(tt)]]==tt:hits.append((st[i][1],st[i+len(tt)-1][2]))
 if not hits:return None
 return min(hits,key=lambda x:abs(x[0]-(prefer or 0)))
def esc(s):return html.escape(str(s if s is not None else ''),quote=True)
def label(r):return re.sub(r'^Arg(\d+)$',r'Arg \1',r)
def cls(r):return r.lower()
report={'version':'V32','pages':0,'senses':0,'occurrences':0,'illustrative_examples':0,'realized_arguments':0,'highlighted_arguments':0,'surface_alignment_notes':[],'arguments_without_surface_match':[],'REL_without_surface_match':[]}
alignment=[]
predicate_forms=json.loads((OUTPUT/'predicate_forms.json').read_text())['predicate_forms']
def argument_hit(text,value):
 hit=find(text,value)
 if hit:return hit,'canonical_surface'
 # Display-only orthographic variants; published annotation values stay intact.
 variants={'exemplo':'ex','de nova jazida de #propina':'d nova jazida d #propina','em o pré-sal':'n pré-sal','de o fisiologismo em a bacia de as almas':'d fisiologismo n bacia d almas','da Ibovespa':'de o Ibovespa','com o conselho de administração':'o conselho de administração','com a dasa':'com a #DASA3','rompimento':'rompimrnto','Jean Willis':'Jean Willas','US$ 8,5 bihões':'US$ 8,5 bilhões','De Particiacao Acionaria':'De Participacao Acionaria','de desabar - acl':'de desabar','para a AGO':'para AGO'}
 if value in variants:
  hit=find(text,variants[value])
  if hit:return hit,'documented_orthographic_surface'
 # Literal prefixes preserve glued tokens and annotation strings cut mid-word.
 fold_surface=lambda x:''.join(c for c in unicodedata.normalize('NFD',x.casefold()) if not unicodedata.combining(c))
 value_fold=fold_surface(value);text_fold=fold_surface(text)
 start=text_fold.find(value_fold)
 if start>=0:return (start,start+len(value)),'literal_fragment_in_surface'
 # A truncated sentence may retain only the beginning of its annotated span.
 ts=tokens(value)
 for length in range(len(ts)-1,0,-1):
  prefix=value[:ts[length-1][2]];hit=find(text,prefix)
  if hit and ('…' in text or '...' in text):return hit,'partial_span_in_truncated_sentence'
 return None,'no_surface_match'
def render_sentence(ex,lemma,source_form):
 text=ex['text'];vals={**ex.get('realization',{}),**ex.get('pt_local_realization',{})};syntax={**ex.get('syntax',{}),**ex.get('pt_local_syntax',{})};marks=[];notes={}
 pred=ex.get('predicate') or {};rel=ex.get('rel') or {};form=rel.get('form') or pred.get('form') or source_form or lemma
 ph=find(text,form)
 if ph is None:
  # Explicit historical abbreviations/misspellings of the predicate.
  for variant in {'acordo':['acrodo'],'exemplo':['ex'],'compra':['cp'],'descoberta':['dscberta'],'exploração':['exploraç']}.get(lemma,[]):
   ph=find(text,variant)
   if ph:break
 if ph is None:
  m=re.search(re.escape(form),text,re.IGNORECASE)
  if m:ph=m.span()
 if ph is None and lemma=='daytrade':ph=find(text,'day trade')
 if ph:marks.append((*ph,'REL',None));prefer=ph[0]
 else:prefer=None;report['REL_without_surface_match'].append({'lemma':lemma,'sent_ID':ex['sent_ID'],'form':form})
 for r,v in vals.items():
  if not v:continue
  report['realized_arguments']+=1;hit,method=argument_hit(text,v)
  if v=='de pensar em a PETR4' and ex['sent_ID']=='dante_01_443052651430031360l':
   segments=[find(text,'de pensar'),find(text,'em a PETR4')]
   assert all(segments)
   marks.extend((*h,r,syntax.get(r)) for h in segments);report['highlighted_arguments']+=1
   alignment.append({'lemma':lemma,'sent_ID':ex['sent_ID'],'role':r,'value':v,'method':'discontinuous_surface','segments':[{'start':h[0],'end':h[1],'surface':text[h[0]:h[1]]} for h in segments]})
   continue
  item={'lemma':lemma,'sent_ID':ex['sent_ID'],'role':r,'value':v,'method':method}
  if hit:
   marks.append((*hit,r,syntax.get(r)));report['highlighted_arguments']+=1
   alignment.append({**item,'start':hit[0],'end':hit[1],'surface':text[hit[0]:hit[1]]})
   if method!='canonical_surface':report['surface_alignment_notes'].append({**item,'surface':text[hit[0]:hit[1]]})
   if method=='partial_span_in_truncated_sentence':notes[r]='A frase publicada está truncada; o destaque cobre o trecho disponível.'
  else:
   report['arguments_without_surface_match'].append({**item,'text':text});notes[r]='O trecho anotado não corresponde ao texto publicado desta ocorrência.'
 # Split overlapping spans so every role is represented, including nested REL.
 points=sorted({0,len(text),*[p for m in marks for p in m[:2]]});parts=[]
 for a,b in zip(points,points[1:]):
  active=[m for m in marks if m[0]<=a and m[1]>=b];piece=esc(text[a:b])
  for _,_,r,_ in sorted(active,key=lambda m:m[2]=='REL'):
   piece='<span class="'+('rel' if r=='REL' else cls(r))+'" data-role="'+esc(r)+'">'+piece+'</span>'
  parts.append(piece)
  for _,end,r,dep in marks:
   if end==b and r!='REL' and dep:parts.append('<sub class="deprel">'+esc(dep)+'</sub>')
 return ''.join(parts),vals,syntax,notes,form
manifest=json.loads((ROOT/'jsons/_manifest.json').read_text())['lemmas']
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'jsons').iterdir()}
for item in manifest:
 lemma=item['lemma'];data=json.loads((ROOT/'jsons'/item['filename']).read_text());source={}
 source=predicate_forms.get(lemma,{})
 body=['<h1>Nome predicador: <i class="lemma-red">'+esc(lemma)+'</i>'+(' <sup class="new-float">NEW</sup>' if item['new'] else '')+'</h1>']
 for sense in data['senses']:
  rid=sense['pt_roleset'];roles=sense['roles'];ids=list(dict.fromkeys([r['id'] for r in roles]+[r['id'] for r in sense.get('pt_local_roles',[])]+[k for ex in sense['examples'] for k in {**ex.get('realization',{}),**ex.get('pt_local_realization',{})}]))
  body.append('<section class="sense-section"><p class="roleset-line"><strong>Roleset id:</strong> '+esc(rid)+'<br>')
  if sense.get('english_roleset'):body.append('Mapeamento para o inglês: <a href="'+esc(sense['nombank_url'])+'">'+esc(sense['english_roleset'])+'</a>')
  else:body.append('<strong>Procedência:</strong> <a href="../provenance.html?v=32#'+esc(rid)+'">Criação do projeto NounBank.DS-Expanded</a>')
  body.append('</p><h2>Papéis semânticos</h2><ul class="roles-list">'+''.join('<li class="'+cls(r['id'])+'">'+esc(label(r['id']))+': '+esc(r['desc'])+'</li>' for r in roles if r.get('desc'))+'</ul><h2>Exemplos</h2>')
  rendered=[];counts={}
  for i,ex in enumerate(sense['examples'],1):
   markup,vals,syntax,notes,form=render_sentence(ex,lemma,source.get(ex['sent_ID']));rendered.append((markup,vals,syntax,notes))
   if i<=2:
    body.append('<article class="lemma-example"><h3>'+str(i)+': '+markup+'</h3><ul class="example-role-list"><li class="rel">rel: '+esc(form)+'</li>'+''.join('<li class="'+cls(r)+'">'+esc(label(r))+': '+esc(vals.get(r) or '—')+(' <sub class="deprel">'+esc(syntax[r])+'</sub>' if syntax.get(r) else '')+'</li>' for r in ids)+'</ul></article>');report['illustrative_examples']+=1
   for r in ids:
    if vals.get(r) and syntax.get(r):counts.setdefault(syntax[r],Counter())[r]+=1
  body.append('<h2>Realização sintática da estrutura de argumentos</h2><div class="argument-table-scroll" tabindex="0" aria-label="Todas as ocorrências de '+esc(rid)+'"><table class="expanded-arguments"><caption>Todas as ocorrências desta acepção ('+str(len(rendered))+')</caption><thead><tr><th scope="col">#</th>'+''.join('<th scope="col" class="'+cls(r)+'">'+esc(label(r))+'</th>' for r in ids)+'<th scope="col">Texto</th></tr></thead><tbody>')
  for i,(markup,vals,syntax,notes) in enumerate(rendered,1):
   body.append('<tr><td>'+str(i)+'</td>'+''.join('<td class="'+cls(r)+'">'+esc(vals.get(r) or '—')+('<small class="surface-note">'+esc(notes[r])+'</small>' if r in notes else '')+'</td>' for r in ids)+'<td class="texto">'+markup+'</td></tr>')
  body.append('</tbody></table></div><div class="statistics-table-container"><h2>Frequência das realizações sintáticas</h2><div class="argument-table-scroll"><table class="stats-table syntax-table"><thead><tr><th scope="col">Relação de dependência — <a href="https://universaldependencies.org/u/dep/">Universal Dependencies</a></th>'+''.join('<th scope="col" class="'+cls(r)+'">'+esc(label(r))+'</th>' for r in ids)+'</tr></thead><tbody>')
  if counts:
   for dep,values in sorted(counts.items()):body.append('<tr><th scope="row">'+esc(dep)+'</th>'+''.join('<td>'+str(values[r])+'</td>' for r in ids)+'</tr>')
  else:body.append('<tr><td colspan="'+str(len(ids)+1)+'">Nenhuma relação sintática anotada para os papéis deste sentido.</td></tr>')
  body.append('</tbody></table></div></div></section><div class="sense-divider" aria-hidden="true"></div>');report['senses']+=1;report['occurrences']+=len(rendered)
 letter=lemma[0].lower();page='<!DOCTYPE html>\n<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(lemma)+' - NounBank.DS Expanded</title><link rel="stylesheet" href="../styles.css?v=32"></head><body class="lemma-page"><header class="site-header"><nav class="site-nav"><a class="home-link" href="../index.html?letter='+esc(letter)+'">Home</a><span class="page-title">'+esc(lemma)+'</span><a class="download-json" href="../jsons/'+esc(item['filename'])+'" download>Download JSON</a></nav></header><main class="content">'+''.join(body)+'</main><a class="back-link back-floating" href="../index.html?letter='+esc(letter)+'">← Voltar para '+esc(letter.upper())+'</a></body></html>\n'
 (ROOT/'site_pages'/f'{lemma}.html').write_text(page);report['pages']+=1
after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'jsons').iterdir()};assert before==after
report['scientific_files_byte_unchanged']=True
(OUTPUT/'interface_build_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUTPUT/'display_alignment.json').write_text(json.dumps(alignment,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if not isinstance(v,list)}));print('Argument surface gaps',len(report['arguments_without_surface_match']),'REL gaps',len(report['REL_without_surface_match']))
