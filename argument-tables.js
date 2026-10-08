/* Presentation only: the existing tables remain the complete source of each view. */
(() => {
  const element = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  };
  const groupOf = th => /^(?:ARGM-|ArgM$)/i.test(th.textContent.trim())
    ? 'argm' : /^(?:Pt)?Arg\s*\d/i.test(th.textContent.trim()) ? 'core' : null;
  document.querySelectorAll('.sense-section').forEach(section => {
    const main = section.querySelector('.expanded-arguments');
    if (!main) return;
    const wrap = main.closest('.argument-table-scroll');
    const tables = [...section.querySelectorAll('.expanded-arguments,.syntax-table')];
    const columns = [];
    tables.forEach(table => {
      if (table === main) {
        [...table.rows].forEach(row => {
          const text = row.querySelector('.texto') || (row.parentElement.tagName === 'THEAD' && [...row.cells].find(c => c.textContent.trim() === 'Texto'));
          if (text) row.insertBefore(text, row.cells[1] || null);
        });
      }
      const headers = [...table.querySelectorAll('thead tr:first-child > th')];
      headers.forEach((th, i) => {
        const group = groupOf(th);
        if (!group) return;
        const cells = [...table.querySelectorAll('tbody > tr')].map(row => row.cells[i]).filter(Boolean);
        const empty = cells.every(cell => table === main ? !cell.textContent.trim() : !Number(cell.textContent.trim()));
        const column = {label: th.textContent.trim(), group, empty, cells: [th, ...cells]};
        column.cells.forEach(cell => { cell.dataset.argumentGroup = group; });
        columns.push(column);
      });
      table.classList.add('interactive-argument-table');
    });
    const controls = element('fieldset', 'argument-view-controls');
    controls.append(element('legend', '', 'Exibir argumentos'));
    const checks = {};
    for (const [key, label] of [['core', 'Argumentos numerados'], ['argm', 'ARG-M'], ['empty', 'Colunas vazias']]) {
      const host = element('label', 'argument-view-check');
      const input = element('input'); input.type = 'checkbox'; input.checked = key !== 'empty';
      input.dataset.view = key;
      if (key !== 'empty' && !columns.some(c => c.group === key)) { input.disabled = true; input.checked = false; }
      host.append(input, document.createTextNode(label)); controls.append(host); checks[key] = input;
    }
    const shortcuts = element('div', 'argument-view-shortcuts');
    for (const [label, core, argm] of [['Todos', true, true], ['Só ArgN', true, false], ['Só ARG-M', false, true]]) {
      const button = element('button', '', label); button.type = 'button';
      if ((label === 'Só ARG-M' && checks.argm.disabled) || (label === 'Só ArgN' && checks.core.disabled)) button.disabled = true;
      button.addEventListener('click', () => { checks.core.checked = core && !checks.core.disabled; checks.argm.checked = argm && !checks.argm.disabled; update(); });
      shortcuts.append(button);
    }
    controls.append(shortcuts);
    const status = element('p', 'argument-view-status'); status.setAttribute('role', 'status');
    const note = element('p', 'argument-view-note', 'Os controles também se aplicam à frequência sintática. As marcações na frase permanecem visíveis. Colunas vazias indicam ausência de realização nesta acepção.');
    controls.append(status, note);
    wrap.before(controls);
    wrap.classList.add('instance-table-desktop');
    const mobile = element('div', 'instance-list-mobile');
    mobile.setAttribute('aria-label', main.caption ? main.caption.textContent : 'Todas as instâncias');
    if (main.caption) mobile.append(element('p', 'argument-view-note', main.caption.textContent));
    [...main.querySelectorAll('tbody > tr')].forEach((row, rowIndex) => {
      const details = element('details', 'instance-detail');
      const argmCount = new Set([...row.querySelectorAll('.texto [data-annotation-id]')].map(e => e.dataset.annotationId)).size;
      details.append(element('summary', '', 'Instância ' + (rowIndex + 1) + (argmCount ? ' · ' + argmCount + ' ARG-M' : ' · Sem ARG-M')));
      const sentence = element('p', 'instance-sentence');
      const textCell = row.querySelector('.texto');
      if (textCell) sentence.append(...[...textCell.childNodes].map(n => n.cloneNode(true)));
      details.append(sentence);
      const list = element('dl', 'instance-argument-list');
      columns.filter(c => c.cells[0].closest('table') === main).forEach(c => {
        const source = c.cells[rowIndex + 1];
        if (!source || !source.textContent.trim()) return;
        const pair = element('div', 'instance-argument'); pair.dataset.argumentGroup = c.group;
        const dt = element('dt', source.className, c.label);
        const dd = element('dd', source.className); dd.append(...[...source.childNodes].map(n => n.cloneNode(true)));
        pair.append(dt, dd); list.append(pair);
      });
      details.append(list); mobile.append(details);
    });
    wrap.after(mobile);
    function update() {
      columns.forEach(c => {
        const hidden = !checks[c.group].checked || (c.empty && !checks.empty.checked);
        c.cells.forEach(cell => { cell.hidden = hidden; });
      });
      mobile.querySelectorAll('[data-argument-group]').forEach(e => { e.hidden = !checks[e.dataset.argumentGroup].checked; });
      const mainColumns = columns.filter(c => c.cells[0].closest('table') === main);
      const hidden = mainColumns.filter(c => c.cells[0].hidden);
      status.textContent = hidden.length ? 'Colunas ocultas: ' + hidden.map(c => c.label).join(', ') + '.' : 'Todas as colunas de argumentos estão visíveis.';
      shortcuts.querySelectorAll('button').forEach(button => {
        const active = button.textContent === 'Todos' ? checks.core.checked && (checks.argm.checked || checks.argm.disabled)
          : button.textContent === 'Só ArgN' ? checks.core.checked && !checks.argm.checked : checks.argm.checked && !checks.core.checked;
        button.setAttribute('aria-pressed', String(active));
      });
    }
    Object.values(checks).forEach(input => input.addEventListener('change', update));
    update();
  });
})();
