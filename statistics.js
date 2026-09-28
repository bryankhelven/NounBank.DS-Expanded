document.addEventListener("DOMContentLoaded",async()=>{
 const s=await fetch("jsons/statistics.json").then(r=>r.json());
 const root=document.getElementById("statistics-root");
 const fmt=n=>Number(n).toLocaleString("pt-BR");
 const pct=(a,b)=>b?100*a/b:0;
 const esc=x=>String(x??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
 const pretty=k=>({"ARG0":"ARG0","ARG1":"ARG1","ARG2":"ARG2","ARG3":"ARG3","ARG4":"ARG4","ARGM":"ARGM",
 "VALIDATED_ALIGNMENT":"Alinhamento validado","APPROXIMATE_REVIEWED":"Aproximado revisado","NO_SAFE_ALIGNMENT":"Sem alinhamento seguro",
 "NO_ENGLISH_NOMBANK_MATCH":"Sem match no English NomBank","CONSTRUCTION_SPECIFIC":"Construção específica","EXACT":"Exato","AMBIGUOUS":"Ambíguo",
 "WSD_TERMINAL_NONEXACT":"WSD non-exact","ENMAP_TERMINAL_NONALIGNED":"ENMAP não alinhado"}[k]||k.replaceAll("_"," "));
 const barList=(obj,total=null)=>{const vals=Object.entries(obj);const max=total||Math.max(...vals.map(([,v])=>Number(v)||0),1);return '<div class="bar-list">'+vals.map(([k,v])=>{const n=Number(v)||0,w=Math.max(1,100*n/max);return `<div class="bar-row"><div class="bar-label"><span>${esc(pretty(k))}</span><strong>${fmt(n)}</strong></div><div class="bar-track"><span style="width:${w}%"></span></div></div>`}).join("")+"</div>"};
 const card=(value,label,sub="")=>`<div class="metric metric-rich"><strong>${value}</strong><span>${label}</span>${sub?`<small>${sub}</small>`:""}</div>`;
 const donut=(a,b,labelA,labelB)=>{const total=a+b,deg=total?360*a/total:0;return `<div class="donut-wrap"><div class="donut" style="--slice:${deg}deg"><div><strong>${fmt(total)}</strong><span>total</span></div></div><div class="donut-legend"><span><i class="dot dot-a"></i>${esc(labelA)} <b>${fmt(a)}</b> (${pct(a,total).toFixed(1)}%)</span><span><i class="dot dot-b"></i>${esc(labelB)} <b>${fmt(b)}</b> (${pct(b,total).toFixed(1)}%)</span></div></div>`};
 const section=(domain,title,kicker,body)=>`<section class="stats-panel" data-domain="${domain}"><div class="panel-head"><div><p class="eyebrow">${kicker}</p><h2>${title}</h2></div></div>${body}</section>`;
 const roleTotal=Object.values(s.arguments.realized_role_labels).reduce((a,b)=>a+Number(b),0);
 const v1=s.compatibility.canonical_v1_lemmas, expanded=s.compatibility.expanded_lemmas;
 const growth=s.compatibility.lexical_growth_percent;
 const sourceNew={"DUPB-backed":s.lexical.new_dupb_backed,"LeGOS-only":s.lexical.new_legos_only_without_dupb_backed};
 const align=s.enmap_new_units.status_counts;
 const exceptions=s.terminal_semantic_exceptions.type_counts;
 const lineage=s.arguments.argument_lineage;
 const lineageRows=Object.entries(lineage).map(([k,v])=>`<article class="lineage-card"><div class="lineage-top"><strong>${fmt(v.instances)} instâncias</strong><span>${fmt(v.role_slots)} slots</span></div><h3>${esc(v.description)}</h3><p><b>${fmt(v.YES||0)}</b> YES${v.ABSTAIN!=null?` · <b>${fmt(v.ABSTAIN)}</b> ABSTAIN`:""}</p><code>${esc(k)}</code></article>`).join("");
 root.innerHTML=
 `<section class="stats-kpis">
   ${card(fmt(s.lexical.lemmas),"lemas",`145 V1 + 564 NEW`)}
   ${card("+"+fmt(s.compatibility.added_lemmas),"novos lemas",`+${growth.toFixed(0)}% sobre a V1`)}
   ${card(fmt(s.contextual.instances),"ocorrências contextuais",`${fmt(s.contextual.S)} S · ${fmt(s.contextual.N)} N`)}
   ${card(fmt(s.arguments.YES),"argumentos realizados",`${fmt(s.arguments.licensed_role_slots)} slots licenciados`)}
  </section>
  ${section("lexical","NounBank.DS → Expanded","Crescimento com continuidade",
    `<div class="compare-grid"><div class="compare-step"><span>V1 canônica</span><strong>${fmt(v1)}</strong><small>lemas · ${fmt(s.compatibility.canonical_v1_examples)} exemplos publicados</small></div><div class="compare-arrow">→</div><div class="compare-step expanded"><span>NounBank.DS<sup>Expanded</sup></span><strong>${fmt(expanded)}</strong><small>lemas · ${fmt(s.contextual.instances)} ocorrências contextuais</small></div></div>
     <div class="growth-band"><div style="width:${100*v1/expanded}%">V1 ${fmt(v1)}</div><div class="growth-new" style="width:${100*s.compatibility.added_lemmas/expanded}%">NEW ${fmt(s.compatibility.added_lemmas)}</div></div>
     <p class="panel-note"><strong>${esc(s.compatibility.v1_payload_compatibility)}</strong>: os 145 payloads herdados foram preservados e a expansão foi adicionada em uma camada compatível.</p>`)}
  ${section("lexical","De onde vêm os 564 novos?","Proveniência lexical",
    `<div class="two-col">${donut(s.lexical.new_dupb_backed,s.lexical.new_legos_only_without_dupb_backed,"DUPB-backed","LeGOS-only sem DUPB-backed")}<div><h3>Classes de authority</h3>${barList(s.lexical.authority_class)}</div></div>`)}
  ${section("semantic","Predicatividade contextual","S e N não são propriedade automática do lema",
    `<div class="two-col">${donut(s.contextual.S,s.contextual.N,"S · predicador no contexto","N · não predicador no contexto")}<div class="insight-box"><strong>${fmt(s.contextual.instances)}</strong><span>ocorrências foram decididas contextual e independentemente da positividade lexical.</span></div></div>`)}
  ${section("semantic","WSD e alinhamento English NomBank","Cobertura sem forçar equivalência",
    `<div class="semantic-grid"><div><h3>WSD</h3>${donut(s.wsd.exact,s.wsd.terminal_nonexact,"Exact","Terminal non-exact")}</div><div><h3>ENMAP — 389 unidades novas</h3>${barList(align)}</div></div>`)}
  ${section("arguments","Quais papéis foram realizados?","2.669 YES com HEAD + SPAN",
    `<div class="role-summary">${Object.entries(s.arguments.realized_role_labels).map(([k,v])=>`<div class="role-stat ${k.toLowerCase()}"><strong>${fmt(v)}</strong><span>${k}</span><small>${(100*v/roleTotal).toFixed(1)}%</small></div>`).join("")}</div>${barList(s.arguments.realized_role_labels)}`)}
  ${section("arguments","Quantos argumentos aparecem por ocorrência?","Realização overt, não valência licenciada",
    `<div class="two-col"><div><h3>Argumentos numerados simultâneos</h3>${barList(s.arguments.numbered_overt_arguments_per_instance,s.arguments.regular_instances)}</div><div class="insight-box"><strong>${fmt(s.arguments.regular_instances)}</strong><span>instâncias regulares. A maior realização simultânea observada foi de <b>3</b> argumentos numerados.</span></div></div>`)}
  ${section("arguments","E por lema?","Duas leituras complementares",
    `<div class="two-col"><div><h3>Máximo simultâneo observado</h3><p class="microcopy">Quantos argumentos numerados um lema chega a realizar em uma única ocorrência.</p>${barList(s.arguments.lemma_max_numbered_overt_arguments)}</div><div><h3>Rótulos ARG distintos ao longo do corpus</h3><p class="microcopy">Quantos papéis numerados diferentes aparecem pelo menos uma vez para o lema.</p>${barList(s.arguments.lemma_distinct_numbered_role_labels_realized)}</div></div>`)}
  ${section("arguments","Inventários licenciados","352 unidades novas com English NomBank alinhado",
    `<p class="panel-note">Esta distribuição mede <strong>quantos papéis a unidade pode licenciar</strong>; não quantos aparecem em toda ocorrência.</p>${barList(s.arguments.licensed_role_inventory_size_new_352_units)}`)}
  ${section("arguments","Como o gold argumental foi construído?","Genealogia da anotação",
    `<div class="lineage-grid">${lineageRows}</div><p class="panel-note">As lanes V1 reutilizam gold publicado quando possível; a expansão nova é model-assisted, rule-constrained e usa abstention conservador.</p>`)}
  ${section("semantic","Exceções preservadas","Cobertura conservadora",
    `<div class="two-col"><div>${barList(exceptions)}</div><div class="insight-box"><strong>${fmt(s.terminal_semantic_exceptions.instances)}</strong><span>ocorrências ficaram explicitamente fora do pipeline argumental regular, em vez de serem forçadas a uma equivalência insegura.</span></div></div>`)}
  <section class="quality-strip" data-domain="all">
    <div><strong>145/145</strong><span>compatibilidade V1</span></div>
    <div><strong>0</strong><span>generic unresolved</span></div>
    <div><strong>2.669/2.669</strong><span>YES com HEAD+SPAN</span></div>
    <div><strong>96 + 104</strong><span>reanchors de span + HEADs V1 derivados</span></div>
    <div><strong>DANTEStocks</strong><span>único corpus row-level</span></div>
  </section>
  <section class="stats-panel interpretation" data-domain="all"><p class="eyebrow">Como ler</p><h2>Valência não é realização</h2><p>O inventário licenciado descreve os papéis disponíveis para uma unidade semântica. As estatísticas de realização mostram quais desses papéis aparecem de forma overt em cada ocorrência. Um nome pode licenciar vários papéis e realizar apenas um, ou nenhum, em um tweet específico.</p><p>Da mesma forma, <strong>S/N é contextual</strong>: pertencer ao inventário lexical não torna automaticamente toda ocorrência predicadora.</p></section>`;
 const tabs=[...document.querySelectorAll(".stats-tab")];
 function setView(v){tabs.forEach(b=>b.classList.toggle("active",b.dataset.view===v));document.querySelectorAll("[data-domain]").forEach(el=>{const d=el.dataset.domain;el.hidden=!(v==="all"||d==="all"||d===v);});}
 tabs.forEach(b=>b.addEventListener("click",()=>setView(b.dataset.view)));
 setView("all");
});
