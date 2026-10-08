import('./provenance-view.js').then(()=>Promise.all([fetch('historical-argm-provenance.json').then(r=>r.json()),window.NBDSHistory])).then(([data,history])=>{
 const H=window.NBDSProvenance,input=document.getElementById('historical-argm-search');
 if(location.hash&&input){const id=decodeURIComponent(location.hash.slice(1)),row=data.find(x=>x.instance_id===id);if(row)input.value=row.lemma;}
 const origins={REPOSITORIO_ISABELLA_PRESERVADO:'Mantido do repositório original',REPOSITORIO_ISABELLA_NORMALIZADO_POR_NOS:'Rótulo original normalizado pelo projeto',ADICIONADO_POR_NOS_NAO_HERDADO_DAS_MARCAS_REPO:'Acrescentado pelo projeto',PROPOSTA_NOSSA_EM_CELULA_COM_MARCAS_REPO:'Revisado ou acrescentado pelo projeto'};
 H.render('historical-argm-search','historical-argm-results',data,x=>{
  const a=H.card(x.lemma+' ('+(x.group==='OLD'?'nome herdado':'nome da expansão')+')',x.text);a.id=x.instance_id;
  H.add(a,'Sentido publicado',x.published_roleset||x.source_roleset_reviewed);
  H.marks(a,'Como estava no repositório original',x.original_marks);
  H.marks(a,'Como ficou após nossa revisão',x.effective_marks);
  for(const m of x.effective_marks){a.append(H.el('h4',H.value(m)));H.add(a,'O que fizemos',origins[m.annotation_origin]||'Revisão do projeto');H.add(a,'Por que',m.reason);H.technical(a,{'Arquivo de origem':m.source_file,'Sentença':m.source_sentence_key,'Token do trecho':m.source_argument_token_id,'Token do predicador':m.source_predicate_token_id,'Revisão do repositório':m.source_commit,'Marca original':(m.original_annotation_refs||[]).join(', ')});}
  const removed=(x.original_marks||[]).filter(o=>!(x.effective_marks||[]).some(m=>m.label===o.label&&m.realization===o.realization));
  for(const o of removed){a.append(H.el('h4','Marca original que não permanece nesta instância: '+H.value(o)));const change=history.find(m=>m.sentence.endsWith(x.instance_id.split('::')[0])&&String(m.token_id)===String(o.source_token_id)&&m.reason);H.add(a,'Por que mudou',change?.reason||x.disposition||'A marca não integra o resultado desta instância. Não há uma justificativa individual recuperada para esta associação.');if(change){H.add(a,'Antes',H.value(change.before));H.add(a,'Após a revisão',H.value(change.after));}}
  if(!x.effective_marks.length)H.add(a,'Resultado',x.disposition||'Nenhum ARG-M permanece nesta instância após a revisão.');
  H.add(a,'Atribuição da fonte','A origem documental é o repositório de Isabella. A autoria individual de cada célula não foi estabelecida.');
  return a;
 });
});
