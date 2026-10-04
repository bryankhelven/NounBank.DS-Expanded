#!/usr/bin/env python3
"""Validate documentary provenance without changing source annotations."""
import argparse,collections,gzip,hashlib,json,pathlib
def digest(b):return hashlib.sha256(b).hexdigest()
def validate(repo):
 root=repo/'data/provenance/orch279';m=json.loads((root/'manifest.json').read_text())
 tables={}
 for n,spec in m['files'].items():
  b=(root/n).read_bytes();assert digest(b)==spec['sha256'],n
  raw=gzip.decompress(b);assert digest(raw)==spec['uncompressed_sha256'],n
  tables[n]=[json.loads(l) for l in raw.splitlines() if l.strip()];assert len(tables[n])==spec['records'],n
 roles=tables['rolesets.jsonl.gz'];rd=tables['role_definitions.jsonl.gz'];ann=tables['annotations.jsonl.gz'];gold=tables['occurrences.jsonl.gz'];ledger=tables['issue_closures.jsonl.gz']
 rb={r['record_id']:r for r in roles};db={r['role_definition_record_id']:r for r in rd};ob={o['occurrence_id']:o for o in gold}
 assert len(rb)==len(roles)==575 and len(db)==len(rd)==2068 and len(ob)==len(gold)==3693
 assert len(ann)==len({a['annotation_id'] for a in ann})==36983
 for r in roles:
  loc=r['published_source_locator'];p=repo/loc['path']
  if digest(p.read_bytes())!=loc['sha256']:
   snapshots=json.loads((repo/'data/provenance/orch279_sources/manifest.json').read_text());spec=snapshots[loc['path']];assert spec['sha256']==loc['sha256'];p=repo/spec['snapshot']
  assert digest(p.read_bytes())==loc['sha256'],loc['path']
  assert not r['open_issue_records'] and not r['gold_changed'] and not r['publication_changed']
 for r in rd:assert r['roleset_record_id'] in rb and r['arity_obligatoriness_not_inferred']
 for a in ann:
  assert a['roleset_record_id'] in rb and a['V4_annotation_literal']['occurrence_id'] in ob
  if a['role_definition_origin_ref']:assert a['role_definition_origin_ref'] in db
  assert not a['original_annotation_changed']
 for o in gold:assert o['roleset_record_id'] in rb
 assert len(ledger)==len({(r['physical_issue_record_literal']['record_id'],r['physical_issue_record_literal']['issue']) for r in ledger})==398
 assert all(r['status']=='CLOSED' for r in ledger)
 counts=collections.Counter(r['closure_type'] for r in ledger)
 assert counts=={'RETROSPECTIVE_SELECTION_RATIONALE':350,'LEGACY_INVENTORY_RECONCILIATION':43,'RETROSPECTIVE_DOCUMENTARY_INVENTORY':2,'CARTEIRA_HISTORICALLY_EVIDENCED_CORRECTION':3}
 assert len(tables['accepted_selection_rationales.jsonl.gz'])==350 and len(tables['accepted_inventory_documentation.jsonl.gz'])==45
 return {'result':'PASS','authority':'ORCH_RECON_000279','rolesets':575,'role_definitions':2068,'annotations':36983,'gold_occurrences':3693,'closed_issue_identities':398,'remaining_issue_queue':0,'historical_pinned_source_hashes_verified':575,'role_binding_equivalence_claim':False,'full_historical_origin_completion_claim':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[1]);a=p.parse_args();print(json.dumps(validate(a.repo),ensure_ascii=False))
