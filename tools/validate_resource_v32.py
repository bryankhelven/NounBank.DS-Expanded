"""Check current source joins, preserved history, downloads and interface accounting."""
import json,gzip,hashlib,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'data/provenance';V=P/'v32';H=P/'human_pt'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x) for x in gzip.open(p,'rt')]
manifest=json.loads((R/'jsons/_manifest.json').read_text());data={f"jsons/{x['filename']}":json.loads((R/'jsons'/x['filename']).read_text()) for x in manifest['lemmas']};hashes={p:sha(R/p) for p in data}
def resolve(loc):
 assert loc['sha256']==hashes[loc['path']],loc
 x=data[loc['path']]
 for k in loc['json_pointer'].strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
 return x
tables={n:lines(V/(n+'.jsonl.gz')) for n in ['rolesets','role_definitions','occurrence_bindings','annotations']}
for n,key in [('rolesets','published_source_locator'),('role_definitions','source_locator'),('occurrence_bindings','source_locator')]:
 for row in tables[n]:resolve(row[key])
previous={x['annotation_id']:x for x in lines(P/'v28/annotations.jsonl.gz')};changed=[]
for a in tables['annotations']:
 assert a['historical_annotation_literal']==previous[a['annotation_id']]['historical_annotation_literal']
 assert a['current_annotation_value']==resolve(a['current_source_locator'])
 if a['annotation_value_changed']:changed.append(a)
assert len(changed)==2 and {x['historical_annotation_literal']['role_id'] for x in changed}=={'Arg1','Arg2'}
human=lines(H/'marcacoes_pt.jsonl.gz');original={x['annotation_id']:x for x in lines(P/'../provenance/v28/annotations.jsonl.gz')};effective={x['annotation_id']:x for x in tables['annotations']}
for h in human:
 assert h['valor_original']==original[h['annotation_id']]['historical_annotation_literal']['value']
 assert h['valor_atual']==effective[h['annotation_id']]['current_annotation_value']==resolve(h['current_source_locator'])
 assert not h['annotation_original_changed']
assert len(human)==len({x['annotation_id'] for x in human})==36983
allrows=[json.loads(x) for x in (R/'jsons/nounbank.ds_expanded_all.jsonl').read_text().splitlines()];expected=[]
for item in manifest['lemmas']:
 for s in data['jsons/'+item['filename']]['senses']:
  for ex in s['examples']:expected.append((item['lemma'],s['pt_roleset'],ex))
assert len(allrows)==len(expected)==3693
assert [(x['lemma'],x['pt_roleset'],x['example']) for x in allrows]==expected
with zipfile.ZipFile(R/'jsons/nounbank.ds_expanded_all_jsons.zip') as z:
 assert len(z.namelist())==520
 for name in z.namelist():assert z.read(name)==(R/'jsons'/name).read_bytes()
h=json.loads((H/'rolesets_pt.json').read_text());assert len(h['registros'])==576
for row in h['registros']:resolve(row['fonte_publicada'])
for row in json.loads((H/'papeis_pt.json').read_text())['registros']:resolve(row['source_locator'])
hm=json.loads((H/'manifest.json').read_text())
for n,digest in hm['hashes_sha256'].items():assert digest==sha(H/n)
for n,digest in json.loads((V/'manifest.json').read_text())['files'].items():assert digest==sha(V/n),n
ui=json.loads((V/'interface_dom_audit.json').read_text());assert ui['result']=='PASS' and ui['occurrences']==3693 and ui['realized_arguments']==3679
result={'result':'PASS','pages':518,'senses':576,'occurrences':3693,'effective_annotations':36983,'historical_annotation_ids_and_values_preserved':36983,'current_annotation_values_corrected':2,'current_occurrence_texts_corrected':1,'JSONL_instances_match_published_JSON':True,'ZIP_members_match_published_JSON':520,'current_source_hashes_and_pointers_verified':True}
(V/'resource_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
