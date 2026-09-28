document.addEventListener("DOMContentLoaded", async () => {
  const url = document.body.dataset.json;
  const root = document.getElementById("lemma-root");

  try {
    const [d, m] = await Promise.all([
      fetch(url).then(r => {
        if (!r.ok) throw new Error("JSON HTTP " + r.status);
        return r.json();
      }),
      fetch("../jsons/_manifest.json").then(r => {
        if (!r.ok) throw new Error("Manifest HTTP " + r.status);
        return r.json();
      })
    ]);

    const meta = m.lemmas.find(x => x.lemma === d.lemma) || {};
    const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;"
    })[c]);
    const rc = r => String(r || "").toLowerCase();

    function once(h, n, replacement) {
      if (!n) return h;
      const e = esc(n);
      const p = h.indexOf(e);
      return p < 0 ? h : h.slice(0, p) + replacement + h.slice(p + e.length);
    }

    function marked(ex) {
      let out = esc(ex.text || "");
      Object.entries(ex.realization || {})
        .filter(([, v]) => v)
        .sort((a, b) => String(b[1]).length - String(a[1]).length)
        .forEach(([role, value]) => {
          const dep = (ex.syntax || {})[role];
          out = once(
            out,
            value,
            '<span class="' + rc(role) + '">' + esc(value) + '</span>' +
            (dep ? '<sub class="deprel">' + esc(dep) + '</sub>' : "")
          );
        });

      const form = (ex.predicate || {}).form || d.lemma;
      return once(out, form, '<span class="rel">' + esc(form) + '</span>');
    }

    function block(s) {
      const roles = (s.roles || []).filter(r => r.id);
      const rids = roles.map(r => r.id);
      const examples = s.examples || [];

      const mapping = s.english_roleset
        ? (s.nombank_url
            ? '<a href="' + esc(s.nombank_url) + '">' + esc(s.english_roleset) + '</a>'
            : esc(s.english_roleset))
        : '<span class="pending-label">Aguardando resolução</span>';

      const status = s.resolution_status
        ? '<span class="pending-label">' +
          esc(s.resolution_status === "construction_specific"
            ? "construção específica"
            : "aguardando mapeamento") +
          '</span>'
        : "";

      const rolesHtml = roles.length
        ? '<ul>' + roles.map(r =>
            '<li class="' + rc(r.id) + '">' +
            esc(r.id.replace("Arg", "Arg ")) + ': ' + esc(r.desc || "") +
            '</li>'
          ).join("") + '</ul>'
        : '<p class="muted">Inventário de papéis aguardando resolução.</p>';

      const examplesHtml = examples.map((e, i) =>
        '<article class="example-card"><h3>' + (i + 1) + ': ' + marked(e) +
        '</h3><ul><li class="rel">REL: ' +
        esc((e.predicate || {}).form || d.lemma) + '</li>' +
        rids.map(r =>
          '<li class="' + rc(r) + '">' +
          esc(r.replace("Arg", "Arg ")) + ': ' +
          esc((e.realization || {})[r] || "-") +
          '</li>'
        ).join("") + '</ul></article>'
      ).join("");

      let table = "";
      let freq = "";

      if (examples.length && rids.length) {
        table =
          '<div class="argument-table-scroll"><table class="expanded-arguments">' +
          '<thead><tr><th>#</th>' +
          rids.map(r => '<th class="' + rc(r) + '">' + esc(r.replace("Arg", "Arg ")) + '</th>').join("") +
          '<th>Texto</th></tr></thead><tbody>' +
          examples.map((e, i) =>
            '<tr><td>' + (i + 1) + '</td>' +
            rids.map(r =>
              '<td class="' + rc(r) + '">' + esc((e.realization || {})[r] || "-") + '</td>'
            ).join("") +
            '<td class="texto">' + marked(e) + '</td></tr>'
          ).join("") +
          '</tbody></table></div>';

        const deps = [...new Set(
          examples.flatMap(e => Object.values(e.syntax || {}).filter(Boolean))
        )].sort();

        if (deps.length) {
          freq =
            '<div class="statistics-table-container">' +
            '<h3>Frequência das realizações sintáticas</h3>' +
            '<table class="stats-table"><thead><tr>' +
            '<th>Relação de dependência — Universal Dependencies</th>' +
            rids.map(r => '<th class="' + rc(r) + '">' + esc(r.replace("Arg", "Arg ")) + '</th>').join("") +
            '</tr></thead><tbody>' +
            deps.map(dep =>
              '<tr><td>' + esc(dep) + '</td>' +
              rids.map(r =>
                '<td>' + examples.filter(e => (e.syntax || {})[r] === dep).length + '</td>'
              ).join("") +
              '</tr>'
            ).join("") +
            '</tbody></table></div>';
        }
      }

      return (
        '<section class="sense-block">' +
        '<p><strong>Roleset id:</strong> ' + esc(s.pt_roleset) +
        ' · <strong>Mapeamento para o inglês:</strong> ' + mapping + ' ' + status + '</p>' +
        '<h2>Roles</h2>' + rolesHtml +
        '<h2>Exemplos</h2>' + examplesHtml +
        (table ? '<h2>Realização sintática da estrutura de argumentos</h2>' + table : "") +
        freq +
        '</section>'
      );
    }

    const pending = (d.pending_instances || []).length
      ? '<section class="pending-section">' +
        '<h2>Aguardando resolução de sense/roleset</h2>' +
        '<p class="muted">Estas ocorrências já foram identificadas como predicadoras, mas ainda exigem revisão manual.</p>' +
        d.pending_instances.map((e, i) =>
          '<article class="example-card"><h3>' + (i + 1) + ': ' + marked(e) +
          '</h3><ul><li class="rel">REL: ' +
          esc((e.predicate || {}).form || d.lemma) +
          '</li></ul></article>'
        ).join("") +
        '</section>'
      : "";

    root.innerHTML =
      '<div class="lemma-heading"><h1>Nome predicador: <i class="lemma-red">' +
      esc(d.lemma) + '</i>' +
      (meta.new ? '<sup class="new-float lemma-new">NEW</sup>' : "") +
      '</h1><a class="json-link" href="' + url + '" download>JSON download</a></div>' +
      (d.senses || []).map(block).join("") +
      pending;

  } catch (err) {
    console.error(err);
    root.innerHTML =
      '<div class="warning"><strong>Erro ao carregar esta entrada.</strong><br>' +
      'O JSON ou o script da página não pôde ser carregado.</div>';
  }
});
