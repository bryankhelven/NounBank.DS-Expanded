document.addEventListener("DOMContentLoaded",async()=>{
 const s=await fetch("jsons/statistics.json").then(r=>r.json());
 const root=document.getElementById("statistics-root");
 const fmt=n=>Number(n).toLocaleString("pt-BR");
 const pct=(a,b)=>b?100*a/b:0;
 const esc=x=>String(x??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
 const barList=(obj,total=null,labels={})=>{const vals=Object.entries(obj);const max=total||Math.max(...vals.map(([,v])=>Number(v)||0),1);return '<div class="bar-list">'+vals.map(([k,v])=>{const n=Number(v)||0,w=Math.max(1,100*n/max);return '<div class="bar-row"><div class="bar-label"><span>'+esc(labels[k]||k)+'</span><strong>'+fmt(n)+'</strong></div><div class="bar-track"><span style="width:'+w+'%"></span></div></div>'}).join("")+"</div>"};
 const card=(value,label,sub="")=>'<div class="metric metric-rich"><strong>'+value+'</strong><span>'+label+'</span>'+(sub?'<small>'+sub+'</small>':"")+'</div>';
 const donut=(a,b,labelA,labelB)=>{const total=a+b,deg=total?360*a/total:0;return '<div class="donut-wrap"><div class="donut" style="--slice:'+deg+'deg"><div><strong>'+fmt(total)+'</strong><span>total</span></div></div><div class="donut-legend"><span><i class="dot dot-a"></i>'+esc(labelA)+' <b>'+fmt(a)+'</b> ('+pct(a,total).toFixed(1)+'%)</span><span><i class="dot dot-b"></i>'+esc(labelB)+' <b>'+fmt(b)+'</b> ('+pct(b,total).toFixed(1)+'%)</span></div></div>'};
 const section=(domain,title,kicker,body)=>'<section class="stats-panel" data-domain="'+domain+'"><div class="panel-head"><div><p class="eyebrow">'+kicker+'</p><h2>'+title+'</h2></div></div>'+body+'</section>';
 const roleTotal=Object.values(s.arguments.realized_role_labels).reduce((a,b)=>a+Number(b),0);
 const growth=((s.inventory.lemmas-s.inventory.original)/s.inventory.original)*100;
 const mapLabels={
  validated:"Mapeamento validado",
  exact:"Correspondência direta",
  reviewed_approximate:"Correspondência aproximada revisada",
  without_safe_mapping:"Sem mapeamento seguro",
  without_nombank_match:"Sem correspondente no NomBank",
  construction_specific:"Dependente da construção",
  ambiguous:"Mapeamento ambíguo"
 };
 root.innerHTML=
 '<section class="stats-kpis">'+
   card(fmt(s.inventory.lemmas),"lemas","145 da versão original + 564 NEW")+
   card("+"+fmt(s.inventory.new),"novos lemas","+"+growth.toFixed(0)+"% sobre a versão original")+
   card(fmt(s.occurrences.total),"ocorrências analisadas",fmt(s.occurrences.predicative)+" predicadoras · "+fmt(s.occurrences.non_predicative)+" não predicadoras")+
   card(fmt(s.arguments.realized_total),"argumentos realizados","em "+fmt(s.arguments.regular_occurrences)+" ocorrências regulares")+
  '</section>'+
  section("lexical","NounBank.DS → Expanded","Crescimento do recurso",
    '<div class="compare-grid"><div class="compare-step"><span>NounBank.DS</span><strong>'+fmt(s.comparison_with_original.original_lemmas)+'</strong><small>lemas · '+fmt(s.comparison_with_original.original_examples)+' exemplos publicados</small></div><div class="compare-arrow">→</div><div class="compare-step expanded"><span>NounBank.DS<sup>Expanded</sup></span><strong>'+fmt(s.comparison_with_original.expanded_lemmas)+'</strong><small>lemas · '+fmt(s.occurrences.total)+' ocorrências analisadas</small></div></div>'+
     '<div class="growth-band"><div style="width:'+(100*s.inventory.original/s.inventory.lemmas)+'%">Original '+fmt(s.inventory.original)+'</div><div class="growth-new" style="width:'+(100*s.inventory.new/s.inventory.lemmas)+'%">NEW '+fmt(s.inventory.new)+'</div></div>'+
     '<p class="panel-note">As <strong>'+fmt(s.comparison_with_original.original_entries_preserved)+'</strong> entradas da versão original permanecem no recurso; a expansão acrescenta <strong>'+fmt(s.inventory.new)+'</strong> novos lemas.</p>')+
  section("semantic","Uso predicador no contexto","Nem toda ocorrência de um lema é predicadora",
    '<div class="two-col">'+donut(s.occurrences.predicative,s.occurrences.non_predicative,"Ocorrências predicadoras","Ocorrências não predicadoras")+
    '<div class="insight-box"><strong>'+fmt(s.occurrences.total)+'</strong><span>ocorrências do DANTEStocks foram analisadas para distinguir usos predicadores e não predicadores.</span></div></div>')+
  section("semantic","Identificação de sentido","Ocorrências predicadoras",
    '<div class="two-col">'+donut(s.sense_identification.exact,s.sense_identification.without_exact_identification,"Sentido identificado","Sem identificação exata")+
    '<div class="insight-box"><strong>'+fmt(s.sense_identification.exact)+'</strong><span>das '+fmt(s.sense_identification.predicative_occurrences)+' ocorrências predicadoras receberam uma identificação exata de sentido.</span></div></div>')+
  section("semantic","Mapeamento para o NomBank em inglês","Unidades semânticas novas",
    '<p class="panel-note">O mapeamento para o NomBank em inglês é apresentado quando há correspondência adequada para a leitura nominal em português.</p>'+
    barList({
      validated:s.english_nombank_mapping.validated,
      exact:s.english_nombank_mapping.exact,
      reviewed_approximate:s.english_nombank_mapping.reviewed_approximate,
      without_safe_mapping:s.english_nombank_mapping.without_safe_mapping,
      without_nombank_match:s.english_nombank_mapping.without_nombank_match,
      construction_specific:s.english_nombank_mapping.construction_specific,
      ambiguous:s.english_nombank_mapping.ambiguous
    },null,mapLabels))+
  section("arguments","Quais papéis aparecem no corpus?","Argumentos realizados",
    '<div class="role-summary">'+Object.entries(s.arguments.realized_role_labels).map(([k,v])=>'<div class="role-stat '+k.toLowerCase()+'"><strong>'+fmt(v)+'</strong><span>'+k.replace("ARG","Arg ")+'</span><small>'+(100*v/roleTotal).toFixed(1)+'%</small></div>').join("")+'</div>'+
    barList(s.arguments.realized_role_labels,null,Object.fromEntries(Object.keys(s.arguments.realized_role_labels).map(k=>[k,k.replace("ARG","Arg ")]))))+
  section("arguments","Quantos argumentos aparecem em uma ocorrência?","Realização observada",
    '<div class="two-col"><div><h3>Argumentos numerados simultâneos</h3>'+
    barList(s.arguments.numbered_arguments_per_occurrence,s.arguments.regular_occurrences,{"0":"0 argumentos","1":"1 argumento","2":"2 argumentos","3":"3 argumentos"})+
    '</div><div class="insight-box"><strong>'+fmt(s.arguments.regular_occurrences)+'</strong><span>ocorrências entram nas estatísticas regulares de realização argumental. A maior realização simultânea observada foi de <b>3</b> argumentos numerados.</span></div></div>')+
  section("arguments","Como os lemas realizam seus argumentos?","Duas perspectivas",
    '<div class="two-col"><div><h3>Máximo simultâneo por lema</h3><p class="microcopy">Maior número de argumentos numerados observado em uma única ocorrência de cada lema.</p>'+
    barList(s.arguments.maximum_numbered_arguments_per_lemma,null,{"0":"máximo 0","1":"máximo 1","2":"máximo 2","3":"máximo 3"})+
    '</div><div><h3>Papéis distintos por lema</h3><p class="microcopy">Quantidade de rótulos Arg diferentes observados pelo menos uma vez para cada lema.</p>'+
    barList(s.arguments.distinct_numbered_roles_per_lemma,null,{"0":"0 papéis","1":"1 papel","2":"2 papéis","3":"3 papéis","4":"4 papéis","5":"5 papéis"})+
    '</div></div>')+
  section("arguments","Quantos papéis os rolesets preveem?","Valência semântica",
    '<p class="panel-note">Esta distribuição mostra quantos papéis estão previstos nos rolesets das 352 unidades novas mapeadas. Um papel previsto pelo roleset pode não aparecer em todas as ocorrências.</p>'+
    barList(s.arguments.roles_per_mapped_semantic_unit,null,{"1":"1 papel","2":"2 papéis","3":"3 papéis","4":"4 papéis","5":"5 papéis","6":"6 papéis"}))+
  section("semantic","Casos fora das estatísticas argumentais regulares","Cobertura do recurso",
    '<div class="two-col"><div>'+barList({
      without_exact_sense_identification:s.outside_regular_argument_statistics.without_exact_sense_identification,
      without_regular_english_mapping:s.outside_regular_argument_statistics.without_regular_english_mapping,
      construction_specific:s.outside_regular_argument_statistics.construction_specific
    },null,{"without_exact_sense_identification":"Sem identificação exata de sentido","without_regular_english_mapping":"Sem mapeamento nominal regular para o inglês","construction_specific":"Dependentes da construção"})+
    '</div><div class="insight-box"><strong>'+fmt(s.outside_regular_argument_statistics.total)+'</strong><span>ocorrências predicadoras são preservadas no recurso, mas não entram nas estatísticas argumentais regulares porque não permitem uma comparação nominal direta e segura.</span></div></div>')+
  '<section class="stats-panel interpretation" data-domain="all"><p class="eyebrow">Como ler</p><h2>Valência não é realização</h2><p>Um roleset descreve os papéis semânticos associados a uma leitura nominal. Em uma ocorrência concreta, todos, alguns ou nenhum desses argumentos podem aparecer de forma explícita.</p><p>Da mesma forma, a presença de um lema no inventário não significa que toda ocorrência seja predicadora: a classificação depende do uso observado no contexto.</p></section>';
 const tabs=[...document.querySelectorAll(".stats-tab")];
 function setView(v){tabs.forEach(b=>b.classList.toggle("active",b.dataset.view===v));document.querySelectorAll("[data-domain]").forEach(el=>{const d=el.dataset.domain;el.hidden=!(v==="all"||d==="all"||d===v);});}
 tabs.forEach(b=>b.addEventListener("click",()=>setView(b.dataset.view)));
 setView("all");
});
