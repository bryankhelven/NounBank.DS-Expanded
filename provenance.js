(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const fold = value => String(value ?? '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
  let data, filtered = [], glossary;
  const groupLabels = {
    origem: row => row.origem_pt,
    tratamento: row => row.tratamento_pt,
    referencia: row => row.referencia_nombank ? `NomBank · ${row.referencia_nombank}` : 'Sem referência inglesa do NomBank',
    antecedente: row => ({verbal:'NomBank com antecedente verbal declarado',sem_verbal:'NomBank sem antecedente verbal declarado',nao_aplicavel:'Sem frame inglês associado'})[row.antecedente_id],
    nome: row => row.nome
  };
  const evidenceBlock = row => `<details class="evidence"><summary>Conferir a evidência e os identificadores</summary><p><strong>Chave da ficha:</strong> <code>${escape(row.record_id)}</code></p><p><strong>Fonte publicada:</strong> ${escape(row.fonte_publicada.path)} · posição <code>${escape(row.fonte_publicada.json_pointer)}</code> · commit <code>${escape(row.fonte_publicada.commit || row.fonte_publicada.release)}</code></p><p><strong>SHA256 da fonte:</strong> <code>${escape(row.fonte_publicada.sha256)}</code></p><p>Os identificadores e os textos desta ficha estão no <a href="data/provenance/human_pt/rolesets_pt.json">JSON legível</a>. Os registros de origem estão no <a href="data/provenance/orch279/rolesets.jsonl.gz" download>JSONL histórico dos rolesets</a>, na chave histórica indicada pela evidência de cada ficha.</p><ul>${row.evidencias.map(e => `<li><a href="data/provenance/human_pt/${escape(e.arquivo)}">Arquivo de evidência</a> · <code>${escape(e.json_pointer)}</code></li>`).join('')}</ul>${row.planilhas_recuperadas.length ? `<p><strong>Planilhas recuperadas:</strong></p><ul>${row.planilhas_recuperadas.map(w => `<li>${escape(w.path)} · ${w.corresponde_ao_inventario_publicado ? 'cabeçalhos correspondem às descrições publicadas' : 'evidência histórica; correspondência ao inventário atual não afirmada'} · folha ${escape(w.sheet)}<br><code>${escape(w.sha256)}</code></li>`).join('')}</ul>` : ''}</details>`;
  function roleTable(row) {
    if (!row.papeis.length) return row.roleset_criado_no_projeto ? '<p>O roleset foi criado no projeto. As descrições individuais de papéis não constam do arquivo recuperado. A ausência dessas descrições não permite concluir que o sentido tenha valência zero.</p>' : '<p>O registro não enumera descrições individuais de papéis.</p>';
    return `<p>Descrições da fonte e da publicação aparecem no idioma original. Elas não foram substituídas por uma tradução. “Campo vazio” é preenchimento do formato, não um papel criado.</p><div class="role-table-wrap"><table class="role-table"><thead><tr><th>Papel</th><th>Descrição publicada</th><th>Descrição na fonte</th><th>Origem / o que mudou</th></tr></thead><tbody>${row.papeis.map(p => `<tr${p.descricao_publicada == null ? ' class="padding"' : ''}><td>${escape(p.id)}</td><td>${p.descricao_publicada == null ? 'Campo vazio' : escape(p.descricao_publicada)}</td><td>${p.descricao_fonte == null ? 'Não há descrição comparável neste registro' : escape(p.descricao_fonte)}</td><td>${escape(p.origem_pt)}<br>${escape(p.transformacao_pt)}${p.referencia_fonte ? `<br>Referência: ${escape(p.referencia_fonte)}` : ''}</td></tr>`).join('')}</tbody></table></div>`;
  }
  function creationBlock(row) {
    const c = row.criacao_local;
    if (!c) return '';
    return `<section class="local-creation"><h4>Sentido e roleset criados no projeto</h4><p><strong>Sentido:</strong> ${escape(c.sentido)}</p><p><strong>Roleset criado:</strong> <code>${escape(c.identificador)}</code></p><p><strong>Origem:</strong> ${escape(c.origem)}</p><p><strong>Como e por que foi criado:</strong> ${escape(row.por_que)}</p><h4>Papéis definidos para esse sentido</h4><ul>${c.papeis.map(p=>`<li><strong>${escape(p.id)}</strong>: ${escape(p.descricao_pt)}</li>`).join('')}</ul><p>Essas definições descrevem funções dos participantes. Um papel pode estar implícito ou não aparecer em determinada ocorrência.</p></section>`;
  }
  function body(row, creationView) {

    return `<div class="explanation-grid"><section class="explanation-block"><h4>De onde veio?</h4><p>${escape(row.de_onde_veio)}</p><p class="source-line">${escape(row.antecedente_explicacao_pt)}</p></section><section class="explanation-block"><h4>O que foi feito?</h4><p>${escape(row.o_que_foi_feito)}</p></section><section class="explanation-block"><h4>Foi criado? Como?</h4><p>${escape(row.foi_criado)}</p></section><section class="explanation-block"><h4>Por que essa escolha?</h4><span class="decision-label">${escape(row.justificativa_tipo_pt)}</span><p>${escape(row.por_que)}</p></section></div>${row.documentacao_posterior_pt ? `<h4>O que foi documentado depois, durante a revisão</h4><p>${escape(row.documentacao_posterior_pt)}</p>` : ''}${row.correcoes_de_ocorrencias_pt ? `<h4>Correções das ocorrências</h4><ul>${row.correcoes_de_ocorrencias_pt.map(x=>`<li>${escape(x)}</li>`).join('')}</ul>` : ''}${creationBlock(row)}${row.criacao_local ? `<details class="evidence"><summary>Inventário anterior usado para comparação</summary>${roleTable({...row,papeis:row.criacao_local.inventario_anterior})}</details>` : `<h4>Papéis: publicação e fonte lado a lado</h4>${roleTable(row)}`}${row.exemplos.length ? `<h4>Exemplos que sustentam a consulta</h4>${row.exemplos.map(x => `<blockquote>${escape(x.texto)}</blockquote>`).join('')}<p class="source-line">${row.total_ocorrencias} ocorrência(s) · ${row.total_marcacoes} marcação(ões) neste sentido.</p>` : ''}<h4>De onde vieram as marcações?</h4><p>${escape(row.origem_historica_de_cada_marcacao_pt)}</p><p><a href="data/provenance/human_pt/marcacoes_pt.jsonl.gz" download>Consultar cada marcação, seu valor e sua localização exata</a></p>${row.candidatos_rejeitados.length ? `<details class="evidence"><summary>Quais referências foram rejeitadas, e por quê?</summary><ul>${row.candidatos_rejeitados.map(x => `<li><strong>${escape(x.candidato)}</strong>: ${escape(x.motivo)}</li>`).join('')}</ul></details>` : ''}<h4>O que não podemos concluir deste registro</h4><ul>${row.limites_pt.map(x => `<li>${escape(x)}</li>`).join('')}</ul>${row.historico.length ? `<details class="evidence"><summary>Ver o histórico documental</summary><ul>${row.historico.map(h => `<li>${escape((h.data || '').slice(0,10))} · ${escape(h.recurso)}: ${escape(h.explicacao_pt)}<br><code>${escape(h.commit)}</code></li>`).join('')}</ul></details>` : ''}${evidenceBlock(row)}<div class="record-links">${row.url_entrada ? `<a href="${escape(row.url_entrada)}">Ver a entrada no recurso</a>` : ''}<a href="${escape(row.fonte_publicada.path)}">Ver o JSON científico publicado</a>${row.fontes_nombank_urls.map(url => `<a href="${escape(url)}">Ver a fonte do NomBank</a>`).join('')}<button class="download-record" type="button" data-download-record="${escape(row.record_id)}">Baixar esta ficha (JSON)</button></div>`;
  }
  function download(value, filename) {
    const blob = new Blob([JSON.stringify(value, null, 2) + '\n'], {type:'application/json;charset=utf-8'});
    const url = URL.createObjectURL(blob);const link = document.createElement('a');link.href = url;link.download = filename;link.click();setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function render() {
    if (!data) return;
    const creationView = $('record-view').value === 'creations';
    const source = $('source-filter').value, query = fold($('provenance-search').value);
    const exactRoleset = data.registros.some(row => fold(row.roleset) === query);
    filtered = data.registros.filter(row => (!creationView || row.origem_id === 'local') && (source === 'all' || row.origem_id === source) && (!query || (exactRoleset ? fold(row.roleset) === query : fold([row.nome,row.roleset,row.referencia_nombank,row.origem_pt,row.de_onde_veio,row.o_que_foi_feito,row.por_que,row.criacao_local?.como].join(' ')).includes(query))));
    const key = $('group-by').value;
    const groups = new Map();filtered.forEach(row => {const label = groupLabels[key](row);if (!groups.has(label)) groups.set(label, []);groups.get(label).push(row);});
    $('creations-note').hidden = !creationView;
    $('result-count').textContent = `${filtered.length} / ${creationView ? data.grupos_origem.find(g=>g.id==='local').total : data.registros.length} ${creationView ? 'sentidos e rolesets criados' : 'fichas'} · ${groups.size} grupo(s)`;
    $('provenance-results').innerHTML = [...groups].map(([label, rows]) => `<section class="provenance-group"><div class="group-heading"><h3>${escape(label)}</h3><span>${rows.length} ${creationView ? 'criação(ões)' : 'ficha(s)'}</span></div>${rows.map(row => `<details class="record" data-record-id="${escape(row.record_id)}"><summary><div><div class="record-title"><strong>${escape(row.nome)}</strong><small>${escape(row.roleset)}</small></div><div class="record-subtitle">${escape(creationView && row.criacao_local ? row.criacao_local.sentido : row.origem_id === 'nombank' ? `Referência publicada: NomBank · ${row.referencia_nombank}` : row.origem_id === 'local' ? 'Sentido, roleset ou papéis criados no projeto' : 'Registro sem descrições individuais de papéis')}</div></div></summary><div class="record-body"></div></details>`).join('')}</section>`).join('') || '<p class="empty">Nenhuma ficha corresponde aos filtros. Limpe a busca ou escolha outra origem.</p>';
    $('download-filtered').disabled = filtered.length === 0;
    document.querySelectorAll('.source-card').forEach(button => button.classList.toggle('selected', button.dataset.origin === source));
    $('provenance-results').querySelectorAll('.record').forEach(detail => detail.addEventListener('toggle', () => {
      if (detail.open && !detail.dataset.loaded) {const row = filtered.find(x => x.record_id === detail.dataset.recordId);detail.querySelector('.record-body').innerHTML = body(row, creationView);detail.dataset.loaded = 'true';}
    }));
  }
  function reset() {$('provenance-search').value='';$('source-filter').value='all';$('record-view').value='published';render();}
  $('provenance-search').addEventListener('input', render);
  ['source-filter','group-by','record-view'].forEach(id => $(id).addEventListener('change', render));
  $('reset-filters').addEventListener('click', reset);
  $('download-filtered').addEventListener('click', () => download({idioma:'pt-BR',agrupamento:$('group-by').value,consulta:$('record-view').value,total:filtered.length,registros:filtered}, 'provenance_agrupada_pt.json'));
  $('provenance-results').addEventListener('click', event => {const button = event.target.closest('[data-download-record]');if (button) {const row=data.registros.find(x=>x.record_id===button.dataset.downloadRecord);download(row, `provenance_${row.roleset}.json`);}});
  Promise.all([fetch('data/provenance/human_pt/rolesets_pt.json?v=32').then(r=>{if(!r.ok)throw Error('Dados indisponíveis');return r.json();}),fetch('data/provenance/human_pt/glossario_pt.json?v=32').then(r=>{if(!r.ok)throw Error('Glossário indisponível');return r.json();})]).then(([result,terms])=>{
    data=result;glossary=terms;
    $('source-cards').innerHTML=data.grupos_origem.map(group=>`<button class="source-card" type="button" data-origin="${escape(group.id)}"><strong>${group.total}</strong><span>${escape(group.rotulo)}</span></button>`).join('');
    $('source-cards').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{$('source-filter').value=button.dataset.origin;$('record-view').value='published';$('provenance-search').value='';render();$('explorer-title').scrollIntoView({behavior:'smooth'});}));
    data.grupos_origem.forEach(group=>{const option=document.createElement('option');option.value=group.id;option.textContent=`${group.rotulo} (${group.total})`;$('source-filter').append(option);});
    const termLabels={roleset:'Roleset',frame_nominal:'Frame nominal',antecedente_verbal:'Antecedente verbal',justificativa_retrospectiva:'Justificativa retrospectiva',padding:'Campo vazio (padding)',Arg0_Arg1:'Arg0, Arg1 e seguintes',PtArg0:'PtArg0',fonte_publicada:'Fonte publicada',record_id:'Chave de ligação',origem_documental_e_historica:'Origem documental × origem histórica'};
    $('glossary').innerHTML='<dl>'+Object.entries(glossary).map(([key,value])=>`<div><dt>${escape(termLabels[key] || key)}</dt><dd>${escape(value)}</dd></div>`).join('')+'</dl>';
    function openLinkedRecord() {
      let hash;try {hash=decodeURIComponent(location.hash.slice(1));}catch {return;}
      const row=data.registros.find(x=>x.roleset===hash);if(!row)return;
      $('source-filter').value='all';$('record-view').value='published';$('provenance-search').value=row.roleset;render();
      const detail=$('provenance-results').querySelector('.record');if(!detail)return;
      detail.querySelector('.record-body').innerHTML=body(row,false);detail.dataset.loaded='true';detail.open=true;
      detail.scrollIntoView({block:'start'});
    }
    render();openLinkedRecord();window.addEventListener('hashchange',openLinkedRecord);
  }).catch(error=>{$('result-count').textContent='As fichas não puderam ser carregadas.';$('load-error').hidden=false;$('load-error').textContent='Tente recarregar a página. Os arquivos para download continuam disponíveis abaixo.';console.error(error);});
})();
