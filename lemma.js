document.addEventListener("DOMContentLoaded", async function () {
  const url = document.body.dataset.json;
  const root = document.getElementById("lemma-root");
  const d = await fetch(url).then(function (r) { return r.json(); });
  const x = d.expanded_v2 || {};
  const cur = x.current_record || {};
  const instances = cur.instances || [];
  const inherited = x.lineage && x.lineage.inventory_partition === "INHERITED_V1_145";
  const pred = instances.filter(function (i) { return i.contextual_predicativity === "S"; });
  const nonpred = instances.filter(function (i) { return i.contextual_predicativity === "N"; });
  const legacySenses = Array.isArray(d.senses) ? d.senses : [];

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"]/g, function (c) {
      return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];
    });
  }
  function roleClass(role) { return String(role || "").toLowerCase(); }
  function rolesOf(i) {
    return i.argument_resource && Array.isArray(i.argument_resource.roles) ? i.argument_resource.roles : [];
  }
  function yesRoles(i) { return rolesOf(i).filter(function (r) { return r.status === "YES"; }); }
  function englishRoleset(i) {
    const a = i.english_alignment || {};
    return a.english_nombank_roleset || a.english_roleset || i.english_roleset || "";
  }
  function replaceOnce(haystack, needle, replacement) {
    if (!needle) return haystack;
    const e = esc(needle);
    const p = haystack.indexOf(e);
    if (p < 0) return haystack;
    return haystack.slice(0,p) + replacement + haystack.slice(p + e.length);
  }
  function markedText(i) {
    let out = esc(i.sentence_text || i.sentence || "");
    const args = yesRoles(i).slice().sort(function (a,b) {
      return String(b.span_text || "").length - String(a.span_text || "").length;
    });
    args.forEach(function (r) {
      if (!r.span_text) return;
      const dep = r.head_deprel ? '<sub class="deprel">' + esc(r.head_deprel) + '</sub>' : "";
      out = replaceOnce(out, r.span_text, '<span class="' + roleClass(r.role) + '">' + esc(r.span_text) + '</span>' + dep);
    });
    out = replaceOnce(out, i.form, '<span class="rel">' + esc(i.form) + '</span>');
    return out;
  }

  const allRoles = new Set();
  pred.forEach(function (i) { rolesOf(i).forEach(function (r) { if (/^ARG[0-9]+$/i.test(r.role || "")) allRoles.add(r.role.toUpperCase()); }); });
  const roleOrder = Array.from(allRoles).sort(function (a,b) { return Number(a.slice(3)) - Number(b.slice(3)); });

  const frames = new Map();
  pred.forEach(function (i) {
    const er = englishRoleset(i);
    if (!er) return;
    if (!frames.has(er)) frames.set(er, new Map());
    rolesOf(i).forEach(function (r) {
      if (!frames.get(er).has(r.role)) frames.get(er).set(r.role, r.description || "");
    });
  });

  let frameHtml = "";
  if (legacySenses.length) {
    frameHtml = legacySenses.map(function (s) {
      const roles = (s.roles || []).filter(function (r) { return r && r.id && r.desc; });
      return '<div class="frame-card"><p><strong>Roleset id:</strong> ' + esc(s.pt_roleset || "") +
        (s.english_roleset ? ' · <strong>Mapeamento para o inglês:</strong> <span class="english-role">' + esc(s.english_roleset) + '</span>' : "") +
        '</p><h3>Roles</h3><ul class="roles-list">' +
        roles.map(function (r) { return '<li class="' + roleClass(r.id) + '">' + esc(r.id.replace("Arg","Arg ")) + ': ' + esc(r.desc) + '</li>'; }).join("") +
        '</ul></div>';
    }).join("");
  } else if (frames.size) {
    frameHtml = Array.from(frames.entries()).map(function (entry) {
      const er = entry[0], roles = entry[1];
      return '<div class="frame-card"><p><strong>Mapeamento para o inglês:</strong> <span class="english-role">' + esc(er) + '</span></p><h3>Roles</h3><ul class="roles-list">' +
        Array.from(roles.entries()).filter(function (r) { return r[1]; }).map(function (r) {
          return '<li class="' + roleClass(r[0]) + '">' + esc(r[0].replace("ARG","Arg ")) + ': ' + esc(r[1]) + '</li>';
        }).join("") + '</ul></div>';
    }).join("");
  } else {
    frameHtml = '<p class="muted">Não há mapeamento nominal para o inglês apresentado para esta entrada.</p>';
  }

  const examplesHtml = pred.length ? pred.map(function (i, idx) {
    const byRole = new Map(yesRoles(i).map(function (r) { return [String(r.role).toUpperCase(), r]; }));
    return '<article class="example-card"><h3>' + (idx+1) + ': ' + markedText(i) + '</h3><ul class="example-role-list">' +
      '<li class="rel">REL: ' + esc(i.form || d.lemma) + '</li>' +
      roleOrder.map(function (role) {
        const r = byRole.get(role);
        return '<li class="' + roleClass(role) + '">' + esc(role.replace("ARG","Arg ")) + ': ' + (r && r.span_text ? esc(r.span_text) : "-") + '</li>';
      }).join("") + '</ul></article>';
  }).join("") : '<p class="muted">Nenhuma ocorrência predicadora foi identificada para este lema no conjunto analisado.</p>';

  const tableHtml = pred.length && roleOrder.length ? '<div class="argument-table-scroll"><table class="expanded-arguments"><thead><tr><th>#</th>' +
    roleOrder.map(function (r) { return '<th class="' + roleClass(r) + '">' + esc(r.replace("ARG","Arg ")) + '</th>'; }).join("") +
    '<th>Texto</th></tr></thead><tbody>' +
    pred.map(function (i, idx) {
      const byRole = new Map(yesRoles(i).map(function (r) { return [String(r.role).toUpperCase(), r]; }));
      return '<tr><td>' + (idx+1) + '</td>' + roleOrder.map(function (role) {
        const r = byRole.get(role);
        return '<td class="' + roleClass(role) + '">' + (r && r.span_text ? esc(r.span_text) : "-") + '</td>';
      }).join("") + '<td class="texto">' + markedText(i) + '</td></tr>';
    }).join("") + '</tbody></table></div>' : "";

  const depCounts = {};
  pred.forEach(function (i) {
    yesRoles(i).forEach(function (r) {
      if (!r.head_deprel || !/^ARG[0-9]+$/i.test(r.role || "")) return;
      const dep = r.head_deprel;
      const role = r.role.toUpperCase();
      if (!depCounts[dep]) depCounts[dep] = {};
      depCounts[dep][role] = (depCounts[dep][role] || 0) + 1;
    });
  });
  const depNames = Object.keys(depCounts).sort();
  const depHtml = depNames.length ? '<div class="statistics-table-container"><h2>Frequência das realizações sintáticas</h2><table class="stats-table"><thead><tr><th>Relação de dependência — Universal Dependencies</th>' +
    roleOrder.map(function (r) { return '<th class="' + roleClass(r) + '">' + esc(r.replace("ARG","Arg ")) + '</th>'; }).join("") +
    '</tr></thead><tbody>' + depNames.map(function (dep) {
      return '<tr><td>' + esc(dep) + '</td>' + roleOrder.map(function (role) { return '<td>' + (depCounts[dep][role] || 0) + '</td>'; }).join("") + '</tr>';
    }).join("") + '</tbody></table></div>' : "";

  const nonPredHtml = nonpred.length ? '<section><h2>Ocorrências não predicadoras</h2><p class="muted">Nestes contextos, o lema ocorre no corpus, mas não realiza uma estrutura predicativa nominal.</p><ol class="nonpred-list">' +
    nonpred.map(function (i) { return '<li>' + esc(i.sentence_text || i.sentence || "") + '</li>'; }).join("") + '</ol></section>' : "";

  document.title = d.lemma + " — NounBank.DS Expanded";
  root.innerHTML =
    '<div class="lemma-heading"><div><h1>Nome predicador: <i class="lemma-red">' + esc(d.lemma) + '</i>' +
    (inherited ? "" : '<sup class="new-float lemma-new">NEW</sup>') + '</h1></div><a class="json-link" href="' + url + '" download>JSON download</a></div>' +
    '<section><h2>Roleset e papéis semânticos</h2>' + frameHtml + '</section>' +
    '<section><h2>Exemplos</h2>' + examplesHtml + '</section>' +
    (tableHtml ? '<section><h2>Realização sintática da estrutura de argumentos</h2>' + tableHtml + '</section>' : "") +
    depHtml + nonPredHtml;
});
