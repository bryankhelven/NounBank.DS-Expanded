document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('.letter-button');
  const contentBox = document.getElementById('content-box');

  // === Config ===
  const PAGES_BASE = 'site_pages/';   // .html
  const JSON_BASE  = 'jsons/';        // .json (usado só na busca)
  const TARGET = '_self';
  const LETTER_PARAM = 'letter';

  // ---- Estilos da busca ----
  (function injectSearchStyles() {
    const css = `
      :root{
        --nbds-bg:#3A404C;
        --nbds-border:#525B6B;
        --nbds-text:#F3F5F8;
        --nbds-placeholder:#CDD4E1;
        --nbds-active:#444B58;
        --nbds-focus:rgba(130,170,255,.18);
      }
      #nbds-search-wrap{
        width:100%;
        display:flex;
        flex-direction:column;
        align-items:center;
        gap:8px;
        margin:16px 0;
      }
      #nbds-search{
        width:100%;
        max-width:640px;
        padding:10px 12px;
        border:1px solid var(--nbds-border);
        border-radius:8px;
        background:var(--nbds-bg);
        color:var(--nbds-text);
        caret-color:var(--nbds-text);
        font-size:16px;
        outline:none;
        box-shadow:inset 0 1px 0 rgba(255,255,255,0.03);
      }
      #nbds-search::placeholder{ color:var(--nbds-placeholder); }
      #nbds-search:focus{
        border-color:#7EA6FF;
        box-shadow:0 0 0 3px var(--nbds-focus);
      }
      #nbds-suggestions{
        width:100%;
        max-width:640px;
      }
      #nbds-suggestions .nbds-sugg{
        background:var(--nbds-bg);
        border:1px solid var(--nbds-border);
        border-top:none;
        padding:8px 10px;
        cursor:pointer;
      }
      #nbds-suggestions .nbds-sugg strong { color: #C8D6FF; }
      #nbds-suggestions .nbds-sugg { color: #C8D6FF; }
      #nbds-suggestions .nbds-sugg:first-child{
        border-top:1px solid var(--nbds-border);
      }
      #nbds-suggestions .nbds-sugg.active,
      #nbds-suggestions .nbds-sugg:hover{
        background:var(--nbds-active);
      }
      #nbds-suggestions .nbds-sugg a{
        color:#C8D6FF; text-decoration:none;
      }
      #nbds-suggestions .nbds-sugg a:hover{ text-decoration:underline; }
    `;
    const tag = document.createElement('style');
    tag.id = 'nbds-search-styles';
    tag.textContent = css;
    document.head.appendChild(tag);
  })();

  // === Dicionário ===
  const wordsDict = {
    'a': ["abastecimento", "acesso", "administração", "ajuste", "aliança", "aquisição", "ataque", "acordo", "alienação", "apreensão", "antro", "amor", "atestado", "avaliação", "aditivo", "assinatura", "alteração"],
    'b': ["briga"],
    'c': ["caminho", "cenário", "compartilhamento", "confirmação", "construção", "controle", "conversa", "coordenador", "conversão", "custódia", "convocação", "curiosidade", "comparação", "coragem", "comissão", "causa", "cara", "contrato", "cotação", "carteira", "compra"],
    'd': ["deliberação", "demanda", "diretor", "divergência", "descolamento", "discussão", "desova", "daytrade", "declaração", "divisão", "denúncia", "decisão", "descoberta", "divulgação", "distribuição"],
    'e': ["eleição", "extensão", "exploração", "estimativa", "encerramento", "entendimento", "exemplo", "expectativa", "entrada", "esclarecimento"],
    'f': ["fruto", "fusão", "falta"],
    'g': ["gestor"],
    'h': ["homem", "hora"],
    'i': ["importação", "indicador", "instauração", "inscrição", "incorporação", "indicação", "investimento"],
    'l': ["licença", "locação", "leilão"],
    'm': ["medo", "membro", "mix", "mudança", "meio", "monte"],
    'n': ["necessidade", "negociação", "notícia", "número"],
    'o': ["obrigação", "oferta", "outorga", "olhada", "olho"],
    'p': ["post", "postagem", "procura", "projeto", "projeção", "proposta", "pagador", "pedido", "perspectiva", "posição", "pagamento"],
    'r': ["relação", "resolução", "responsabilidade", "rateio", "retorno", "reeleição", "redução", "renúncia", "racionamento", "risco", "reapresentação", "reunião", "recomendação", "relatório", "recompra", "resistência"],
    's': ["solicitação", "sugestão", "spread"],
    't': ["transferência", "transporte", "troca", "teste", "taxação", "tendência", "trade"],
    'v': ["vendedor", "visão", "volta", "venda"],
    'z': ["zona"]
  };

  // ==== Helpers ====
  const isHttpLike = () => location.protocol === 'http:' || location.protocol === 'https:';
  function asciiFold(str){ return str.normalize('NFD').replace(/\p{Diacritic}/gu,''); }
  function toSlugDash(str){
    return asciiFold(str).toLowerCase().replace(/[()]/g,'').replace(/[^a-z0-9\s_-]+/g,'').replace(/\s+/g,'-');
  }
  function getParam(n){ return new URLSearchParams(location.search).get(n); }
  function setParam(n,v,replace=false){
    const url=new URL(location.href);
    if(v==null) url.searchParams.delete(n); else url.searchParams.set(n,v);
    replace ? history.replaceState({},'',url) : history.pushState({},'',url);
  }

  function candidateNames(word, ext){
    const encOriginal = encodeURIComponent(word)+ext;
    const encAscii    = encodeURIComponent(asciiFold(word))+ext;
    const slugDash    = toSlugDash(word)+ext;
    const slugTight   = slugDash.replace(/-/g,'');
    const uniq=[]; [encOriginal,encAscii,slugDash,slugTight].forEach(n=>{ if(!uniq.includes(n)) uniq.push(n);});
    return uniq;
  }
  const candidatePageNames = (w)=>candidateNames(w,'.html');
  const candidateJsonNames = (w)=>candidateNames(w,'.json');

  const existsCache=new Map();
  async function urlExists(url){
    if(existsCache.has(url)) return existsCache.get(url);
    if(!isHttpLike()){ existsCache.set(url,true); return true; }
    let ok=false;
    try{
      let r=await fetch(url,{method:'HEAD',cache:'no-store'});
      if(!r.ok){ r=await fetch(url,{method:'GET',cache:'no-store'}); }
      ok = r.ok || r.type==='opaque' || r.status===0;
    }catch{ ok=true; }
    existsCache.set(url,ok); return ok;
  }
  async function resolveExistingUrl(base,cands){ for(const n of cands){ const u=base+n; if(await urlExists(u)) return u;} return null; }
  async function resolveExistingPageUrl(word){ return resolveExistingUrl(PAGES_BASE, candidatePageNames(word)); }
  async function resolveExistingJsonUrl(word){ return resolveExistingUrl(JSON_BASE,  candidateJsonNames(word)); }

  // ====== BUSCA ======
  const alphabetBar = document.querySelector('.alphabet-buttons');
  const searchWrap = document.createElement('div');
  searchWrap.id = 'nbds-search-wrap';
  searchWrap.innerHTML = `
    <label for="nbds-search" style="width:100%; max-width:640px; font-weight:600;"></label>
    <input id="nbds-search" type="search" placeholder="Entre o nome para busca ou encontre-o abaixo (atalho: /)">
    <div id="nbds-suggestions" role="listbox"></div>
  `;
  if (alphabetBar) alphabetBar.parentNode.insertBefore(searchWrap, alphabetBar);
  else if (contentBox && contentBox.parentNode) contentBox.parentNode.insertBefore(searchWrap, contentBox);

  const searchInput = document.getElementById('nbds-search');
  const suggestions = document.getElementById('nbds-suggestions');

  const ALL_WORDS = Object.keys(wordsDict).sort().flatMap(letter => wordsDict[letter].map(w => ({ letter, word: w })));

  function scoreMatch(q, w){
    const s=asciiFold(q.trim().toLowerCase()); if(!s) return 0;
    const t=asciiFold(w.toLowerCase());
    if(t.startsWith(s)) return 100-(t.length-s.length);
    const idx=t.indexOf(s); return idx>=0 ? 50-idx : -1;
  }

  let activeIndex=-1, currentResults=[];
  function renderSuggestions(list){
    const max=10, top=list.slice(0,max);
    currentResults=top; activeIndex=top.length?0:-1;
    suggestions.innerHTML = top.map((item,i)=>`
      <div class="nbds-sugg ${i===activeIndex?'active':''}" role="option" data-idx="${i}">
        <div style="display:flex; align-items:center; gap:8px; justify-content:space-between;">
          <span><strong>${item.word}</strong>
            <span style="opacity:.6; font-size:12px;">(letra ${item.letter.toUpperCase()})</span>
          </span>
          <span style="display:flex; gap:10px;">
            <a class="nbds-open" href="#" data-word="${encodeURIComponent(item.word)}">Abrir</a>
            <a class="nbds-json" href="#" data-word="${encodeURIComponent(item.word)}">JSON</a>
          </span>
        </div>
      </div>`).join('');

    // Hover (seleção visual)
    suggestions.querySelectorAll('.nbds-sugg').forEach(div=>{
      div.addEventListener('mouseenter', ()=>{
        suggestions.querySelectorAll('.nbds-sugg').forEach(x=>x.classList.remove('active'));
        div.classList.add('active'); activeIndex=parseInt(div.dataset.idx,10);
      });
      // Clique no card (mas NÃO quando o alvo é um <a> interno)
      div.addEventListener('click', async (ev)=>{
        if (ev.target.closest('a')) return; // evita navegação dupla
        const idx=parseInt(div.dataset.idx,10);
        await openResult(top[idx]);
      });
    });

    // Ações dos links internos (sem propagar p/ o card)
    suggestions.querySelectorAll('.nbds-open').forEach(a=>{
      a.addEventListener('click', async ev=>{
        ev.preventDefault();
        ev.stopPropagation();
        const word=decodeURIComponent(a.dataset.word);
        await openResult({word,letter:getLetterOf(word)});
      });
    });
    suggestions.querySelectorAll('.nbds-json').forEach(a=>{
      a.addEventListener('click', async ev=>{
        ev.preventDefault();
        ev.stopPropagation();
        const word=decodeURIComponent(a.dataset.word);
        const jsonUrl=await resolveExistingJsonUrl(word);
        if(jsonUrl){
          const link=document.createElement('a');
          link.href=jsonUrl;
          link.download='';
          link.click();
        } else {
          alert('JSON não encontrado.');
        }
      });
    });
  }

  function getLetterOf(word){
    const ch=asciiFold(word).charAt(0).toLowerCase();
    return wordsDict[ch] ? ch : 'a';
  }

  async function openResult(item){
    if(!item) return;
    const found=await resolveExistingPageUrl(item.word);
    if(found){
      // usa location.href (mantém /<repo>/ no GitHub Pages)
      const url=new URL(found, location.href);
      url.searchParams.set(LETTER_PARAM, item.letter);
      location.assign(url.toString());
    } else {
      alert('Página em construção.');
    }
  }

  function updateSuggestions(){
    const q=searchInput.value;
    if(!q || !q.trim()){ suggestions.innerHTML=''; return; }
    const scored = ALL_WORDS.map(x=>({...x,score:scoreMatch(q,x.word)}))
      .filter(x=>x.score>=0)
      .sort((a,b)=> b.score-a.score || a.word.localeCompare(b.word,'pt'));
    renderSuggestions(scored);
  }

  // atalhos de teclado (foco na busca com '/')
  document.addEventListener('keydown', (e)=>{
    if(e.key==='/' && document.activeElement!==searchInput){ e.preventDefault(); searchInput.focus(); searchInput.select(); }
  });
  searchInput.addEventListener('input', updateSuggestions);
  searchInput.addEventListener('keydown', async (e)=>{
    const n=currentResults.length;
    if(e.key==='Escape'){ searchInput.value=''; suggestions.innerHTML=''; return; }
    if(!n) return;
    if(e.key==='ArrowDown'){ e.preventDefault(); activeIndex=(activeIndex+1)%n; renderSuggestions(currentResults); }
    else if(e.key==='ArrowUp'){ e.preventDefault(); activeIndex=(activeIndex-1+n)%n; renderSuggestions(currentResults); }
    else if(e.key==='Enter'){ e.preventDefault(); await openResult(currentResults[activeIndex]||currentResults[0]); }
  });

  // ===== Lista por letra com TOGGLE =====
  const btnsArr = Array.from(buttons);
  function selectButton(letter){
    btnsArr.forEach(b=>b.classList.toggle('selected', b.textContent.trim().toLowerCase()===letter));
  }
  function clearSelection(){
    btnsArr.forEach(b=>b.classList.remove('selected'));
  }

  async function renderLetter(letter){
    const words=wordsDict[letter]||[];
    const sorted=[...words].sort((a,b)=>a.localeCompare(b,'pt'));

    contentBox.innerHTML='';
    contentBox.style.display='block';

    if(sorted.length===0){
      contentBox.innerHTML = `<p>Conteúdo em construção para a letra ${letter.toUpperCase()}</p>`;
      return;
    }

    const frag=document.createDocumentFragment();
    for(const word of sorted){
      const line=document.createElement('div');
      const a=document.createElement('a');
      a.className='content-link';
      a.textContent=word;
      a.href='#';
      a.target=TARGET;
      a.dataset.pending='1';

      (async()=>{
        const found=await resolveExistingPageUrl(word);
        a.removeAttribute('data-pending');
        if(found){
          // usa location.href (mantém /<repo>/ no GitHub Pages)
          const url=new URL(found, location.href);
          url.searchParams.set(LETTER_PARAM, letter);
          a.href=url.toString();
          a.classList.add('ready');
        }else{
          a.addEventListener('click',(ev)=>{ ev.preventDefault(); alert('AVISO: EM CONSTRUÇÃO'); },{once:true});
          a.classList.add('missing');
        }
      })();

      line.appendChild(a);
      frag.appendChild(line);
    }
    contentBox.appendChild(frag);
  }

  // eventos (com toggle)
  btnsArr.forEach(btn=>{
    btn.addEventListener('click', async function(){
      const letter=this.textContent.trim().toLowerCase();
      const alreadySelected = this.classList.contains('selected');

      if(alreadySelected){
        // desmarca e fecha
        clearSelection();
        contentBox.innerHTML='';
        contentBox.style.display='none';
        setParam(LETTER_PARAM, null, false);
      }else{
        selectButton(letter);
        await renderLetter(letter);
        setParam(LETTER_PARAM, letter, false);
      }
    });
  });

  // ===== Init =====
  (function init(){
    // por padrão, NÃO abre nenhuma letra
    if (contentBox) {
      contentBox.style.display='none';
    }

    const q=(getParam(LETTER_PARAM)||'').toLowerCase();
    if(q && wordsDict[q]){
      // se veio com ?letter=, abre essa
      selectButton(q);
      if (contentBox) renderLetter(q);
    } else {
      // sem letra selecionada
      clearSelection();
    }
  })();

  // popstate (voltar/avançar): respeita ?letter=, senão fecha
  window.addEventListener('popstate', ()=>{
    const q=(getParam(LETTER_PARAM)||'').toLowerCase();
    if(q && wordsDict[q]){
      selectButton(q);
      if (contentBox) renderLetter(q);
    }else{
      clearSelection();
      if (contentBox) {
        contentBox.innerHTML='';
        contentBox.style.display='none';
      }
    }
  });

  // ====== DOWNLOAD DE TODOS OS JSONs ======
(() => {
  const btnDownloadAll = document.getElementById('download-all-json');
  if (!btnDownloadAll) return;

  const ZIP_URL = 'jsons/nounbank.ds_all_jsons.zip';

  // Aponta o botão diretamente para o ZIP estático
  btnDownloadAll.href = ZIP_URL;
  btnDownloadAll.setAttribute('download', 'nounbank.ds_all_jsons.zip');

  // (Opcional) fallback: se o ZIP não existir (404), avisa.
  btnDownloadAll.addEventListener('click', async (ev) => {
    try {
      const r = await fetch(ZIP_URL, { method: 'HEAD', cache: 'no-store' });
      if (!r.ok) {
        ev.preventDefault();
        alert('Arquivo ZIP ainda não está publicado. Gere os JSONs novamente para criar o bundle.');
      }
    } catch {
      // Em ambientes sem HEAD, deixamos seguir (o navegador tentará baixar).
    }
  }, { once: true });
})();
});
