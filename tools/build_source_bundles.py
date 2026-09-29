#!/usr/bin/env python3
from pathlib import Path
import json, shutil, hashlib, urllib.request, zipfile, csv, ssl

ROOT=Path.cwd()
V1=ROOT/"v1repo"
EXP=ROOT/"exprepo"
UD=ROOT/"udrepo"
OUT=ROOT/"artifact_out"
OUT.mkdir(exist_ok=True)

def load_manifest_v1():
    m=json.loads((V1/"jsons/_manifest.json").read_text(encoding="utf-8"))
    return [Path(x).stem for x in m if x.endswith(".json") and not x.startswith("_")]

def load_manifest_exp():
    m=json.loads((EXP/"jsons/_manifest.json").read_text(encoding="utf-8"))
    # population at pre-V2H authority: exclusive Expanded, already closed then
    return [x["lemma"] for x in m["lemmas"] if x.get("new") is True and x.get("pending") is False]

def parse_jsons(repo, lemmas):
    docs={}
    sent_ids=set()
    xml_rows=[]
    for lemma in lemmas:
        p=repo/"jsons"/f"{lemma}.json"
        j=json.loads(p.read_text(encoding="utf-8"))
        docs[lemma]=(p,j)
        for s in j.get("senses",[]):
            url=s.get("nombank_url")
            xml_rows.append({
                "lemma":lemma,
                "pt_roleset":s.get("pt_roleset",""),
                "english_roleset":s.get("english_roleset") or "",
                "nombank_url":url or ""
            })
            for ex in s.get("examples",[]):
                sid=ex.get("sent_ID")
                if sid: sent_ids.add(sid)
        for ex in j.get("pending_instances",[]):
            sid=ex.get("sent_ID")
            if sid: sent_ids.add(sid)
    return docs,sent_ids,xml_rows

def load_conllu():
    sents={}
    order=[]
    files=["pt_dantestocks-ud-train.conllu","pt_dantestocks-ud-dev.conllu","pt_dantestocks-ud-test.conllu"]
    for fn in files:
        text=(UD/fn).read_text(encoding="utf-8")
        block=[]
        for line in text.splitlines()+[""]:
            if line.strip()=="":
                if block:
                    sid=None
                    for x in block:
                        if x.startswith("# sent_id = "):
                            sid=x.split(" = ",1)[1].strip(); break
                    if sid:
                        if sid in sents:
                            raise RuntimeError(f"duplicate sent_id {sid}")
                        sents[sid]="\n".join(block)+"\n\n"
                        order.append(sid)
                    block=[]
            else:
                block.append(line)
    return sents,order

def safe(s):
    return s.replace("/","_").replace("\\","_")

def download_xmls(pkg, xml_rows):
    unique_dir=pkg/"xml"/"unique_frames"; by_dir=pkg/"xml"/"by_lemma"
    unique_dir.mkdir(parents=True); by_dir.mkdir(parents=True)
    cache={}
    missing=[]
    seen_rows=[]
    for row in xml_rows:
        url=row["nombank_url"]
        if not url:
            missing.append(row); continue
        name=url.rsplit("/",1)[-1]
        if not name.endswith(".xml"):
            missing.append(row); continue
        if name not in cache:
            target=unique_dir/name
            urls=[url]
            if url.startswith("http://"):
                urls.insert(0,"https://"+url[len("http://"):])
            ok=False
            err=""
            for u in urls:
                try:
                    ctx=ssl._create_unverified_context()\n                    with urllib.request.urlopen(u,timeout=30,context=ctx) as resp:
                        data=resp.read()
                    if b"<" not in data:
                        raise RuntimeError("not xml-like")
                    target.write_bytes(data); ok=True; break
                except Exception as e:
                    err=str(e)
            if not ok:
                cache[name]=None
                rr=dict(row); rr["error"]=err; missing.append(rr)
                continue
            cache[name]=target
        src=cache.get(name)
        if src is None: continue
        ld=by_dir/safe(row["lemma"]); ld.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,ld/name)
        rr=dict(row); rr["xml_file"]=name
        seen_rows.append(rr)
    with open(pkg/"xml"/"XML_MAPPING.tsv","w",encoding="utf-8",newline="") as f:
        fields=["lemma","pt_roleset","english_roleset","nombank_url","xml_file"]
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n"); w.writeheader()
        for r in seen_rows: w.writerow({k:r.get(k,"") for k in fields})
    with open(pkg/"xml"/"NO_XML_MAPPING.tsv","w",encoding="utf-8",newline="") as f:
        fields=["lemma","pt_roleset","english_roleset","nombank_url","error"]
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n"); w.writeheader()
        for r in missing: w.writerow({k:r.get(k,"") for k in fields})
    return len(cache)-sum(v is None for v in cache.values()),len(missing)

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def build(label, repo, lemmas, docs, target_ids, xml_rows, all_sents, sent_order, authority):
    pkg=OUT/label
    if pkg.exists(): shutil.rmtree(pkg)
    (pkg/"jsons").mkdir(parents=True)
    for lemma,(p,j) in docs.items():
        shutil.copy2(p,pkg/"jsons"/p.name)
    missing_ids=sorted(target_ids-set(all_sents))
    if missing_ids:
        raise RuntimeError(f"{label}: {len(missing_ids)} missing sent_ids: {missing_ids[:20]}")
    with open(pkg/f"{label}_sentences.conllu","w",encoding="utf-8",newline="\n") as f:
        for sid in sent_order:
            if sid in target_ids: f.write(all_sents[sid])
    xml_unique,xml_missing=download_xmls(pkg,xml_rows)
    (pkg/"sentence_ids.txt").write_text("\n".join(sorted(target_ids))+"\n",encoding="utf-8")
    with open(pkg/"population.tsv","w",encoding="utf-8",newline="") as f:
        f.write("lemma\n")
        for x in sorted(lemmas,key=str.casefold): f.write(x+"\n")
    meta={
        "label":label,"authority":authority,
        "lemmas":len(lemmas),"json_files":len(docs),
        "unique_sentence_ids":len(target_ids),
        "conllu_missing_sentence_ids":len(missing_ids),
        "unique_xml_frames_downloaded":xml_unique,
        "xml_mapping_rows_without_downloadable_xml":xml_missing
    }
    (pkg/"MANIFEST.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    readme=f"""# {label}\n\nAuthority: {authority}\n\n- lemmas: {len(lemmas)}\n- JSONs: {len(docs)}\n- unique DANTEStocks sentences: {len(target_ids)}\n- unique NomBank XML frames downloaded: {xml_unique}\n- mapping rows without downloadable XML: {xml_missing}\n\nThe CoNLL-U contains each referenced DANTEStocks sentence once, filtered from UD_Portuguese-DANTEStocks commit 4268e8e1b2c95708136e34f38b8e8af96de86dd2.\n"""
    (pkg/"README.md").write_text(readme,encoding="utf-8")
    files=sorted(p for p in pkg.rglob("*") if p.is_file())
    (pkg/"SHA256SUMS.txt").write_text("\n".join(f"{sha256(p)}  {p.relative_to(pkg).as_posix()}" for p in files)+"\n",encoding="utf-8")
    z=OUT/f"{label}.zip"
    with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
        for p in sorted(pkg.rglob("*")):
            if p.is_file(): zz.write(p,arcname=f"{label}/{p.relative_to(pkg).as_posix()}")
    return meta,z

v1_lemmas=load_manifest_v1()
exp_lemmas=load_manifest_exp()
assert len(v1_lemmas)==145, len(v1_lemmas)
assert len(exp_lemmas)==299, len(exp_lemmas)
assert not (set(v1_lemmas)&set(exp_lemmas))

v1_docs,v1_ids,v1_xml=parse_jsons(V1,v1_lemmas)
ex_docs,ex_ids,ex_xml=parse_jsons(EXP,exp_lemmas)
all_sents,sent_order=load_conllu()

m1,z1=build("NOUNBANK_DS_V1_SOURCE_BUNDLE",V1,v1_lemmas,v1_docs,v1_ids,v1_xml,all_sents,sent_order,
 "bryankhelven/NounBank.DS main; 145-entry V1")
m2,z2=build("NOUNBANK_DS_EXPANDED_PREV_CLOSED_SOURCE_BUNDLE",EXP,exp_lemmas,ex_docs,ex_ids,ex_xml,all_sents,sent_order,
 "NounBank.DS-Expanded commit 7a8d6ad22d176b2b208405153740250a6b2a408a; new=true,pending=false")

print(json.dumps({"v1":m1,"expanded_previously_closed":m2},ensure_ascii=False,indent=2))
