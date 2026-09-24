#!/usr/bin/env python3
"""PARTE B1 — regenerate site_pages/<lemma>.html from jsons/<lemma>.json.

This is a fork of the original generator embedded in
utils/from_table_to_site.ipynb (cell 3), kept byte-for-byte compatible in
layout/CSS/nav/footer, with two behavioral fixes to close the JSON/site
drift documented in the audit:

  1. The number of table rows / example blocks always equals the number of
     JSON examples for that lemma (no more MAX_EXAMPLES silently dropping
     rows anywhere but the small "Exemplos:" teaser section, which was
     already capped at 2 in the original and stays capped at 2 here).
  2. The REL span highlighted per row is the one computed per-instance in
     PARTE B2 (jsons/<lemma>.json examples[*].predicate), instead of the
     old "first match of the bare lemma, once per page" regex, which
     collapsed legitimate multi-instance sent_IDs onto a single occurrence
     and never matched inflected (plural) forms at all.

Each <tr>/<h3> block also carries a data-instance-id attribute so rows are
individually addressable and multi-instance groups are never visually
collapsed.

REL resolution (HOTFIX REL VISUAL): the REL predicate for a given instance
ALWAYS exists scientifically — `predicate` is only a positional anchor used
to disambiguate which textual occurrence belongs to that instance when a
sent_ID has more than one. When an instance has no exact `predicate` anchor
in the JSON, this renderer falls back to a resolution computed from the
DANTEStocks legacy CoNLL-U authority (tools/resolve_predicate_anchors.py,
cached in tools/predicate_anchor_resolutions.json) instead of ever
displaying an "REL truncado" placeholder. Nothing is ever guessed: the
fallback is only used when it was derived from token-level evidence in the
legacy corpus.
"""
import re
import html
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from predicate_anchor_cache import load_cache  # noqa: E402

escape = html.escape

JSON_DIR = Path("jsons")
HTML_DIR = Path("site_pages")
CSS_HREF = "../styles.css"
MAX_EXAMPLES_IN_SECTION = 2
DOWNLOAD_PREFIX_FROM_PAGE = "../jsons/"

PREDICATE_CACHE = load_cache()

STYLE_BLOCK = """
:root{
  --header-h: 56px;
}
body{margin:0;}
/* ===== Top bar ===== */
.site-header{
  position: sticky; top:0; z-index:1000;
  /* alpha menor -> mais transparente */
  background: rgba(20,20,20,0.70);
  transition: background .2s ease, backdrop-filter .2s ease;
}
.site-header.scrolled{
  /* ainda mais transparente quando rolar */
  background: rgba(20,20,20,0.40);
  backdrop-filter: blur(6px);
}
.site-nav{
  height: var(--header-h);
  display:flex; align-items:center; justify-content:space-between;
  padding: 0 16px;
}
.site-nav .home-link{
  color:#cfe3ff; text-decoration:none; font-weight:600;
  padding:8px 12px; border-radius:10px; background:rgba(84,102,170,.25);
}
.site-nav .home-link:hover{ background:rgba(84,102,170,.35); }
.site-nav .page-title{
  color:#cfd8ff; opacity:.75; font-weight:600;
  text-align:center; margin:0 12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}

/* ===== Botão JSON (agora dentro da header, alinhado) ===== */
.site-nav .download-json{
  display:inline-block; text-decoration:none; font-weight:700;
  padding:10px 14px; border-radius:12px; color:#fff;
  background:#2e7d32; box-shadow:0 4px 14px rgba(0,0,0,.25);
  transition:transform .08s ease, box-shadow .2s ease, opacity .2s ease;
  opacity:.95;
}
.site-nav .download-json:hover{ transform:translateY(-1px); box-shadow:0 8px 22px rgba(0,0,0,.35); opacity:1; }

/* ===== “Voltar para X” (flutuante no rodapé) ===== */
.back-link{ color:#9ecbff; text-decoration:none; font-weight:500; }
.back-link:hover{ text-decoration:underline; }
.back-floating{
  position: fixed; right: 20px; bottom: 20px; z-index: 980;
  background:#2b2b2b; color:#cfe3ff; padding:10px 12px; border-radius:12px;
  box-shadow:0 8px 22px rgba(0,0,0,.35); text-decoration:none;
}

/* ===== Tabela de realização sintática ===== */
#relations-table{ width:100%; border-collapse:collapse; }
#relations-table col.numcol{ width:3.5rem; }
#relations-table col.argcol{ width:18rem; }
#relations-table col.textcol{ width:auto; }
#relations-table thead th{
  text-align:center; padding:.45rem .6rem; white-space:nowrap;
}
#relations-table tbody td{
  padding:.45rem .6rem; vertical-align:top; border-bottom:1px solid #fff;
}
#relations-table tbody tr:last-child td{ border-bottom:none; }
#relations-table tbody td:first-child{ text-align:center; }

"""

# ---------- utils ----------
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def first_letter(lemma: str) -> str:
    s = strip_accents((lemma or "").strip()).lower()
    return s[0] if s and s[0].isalpha() else "a"


def _boundary_safe_pattern(phrase: str):
    core = re.escape(phrase)
    patt = rf"(?<![#\w])({core})(?!\w)"
    return re.compile(patt, flags=re.IGNORECASE)


def _wrap_once(colored, orig_map, phrase, cls, deprel=None):
    """Wrap the first boundary-safe occurrence of `phrase` in `colored` with
    a <span>, and extend `orig_map` (colored-index -> original-text-index,
    or None for pure markup) to cover the newly inserted characters. Returns
    the (possibly unchanged) (colored, orig_map) pair."""
    if not phrase:
        return colored, orig_map
    pat = _boundary_safe_pattern(phrase)
    m = pat.search(colored)
    if not m:
        return colored, orig_map
    s, e = m.start(1), m.end(1)
    frag = m.group(1)
    prefix = f'<span class="{cls}">'
    suffix = "</span>"
    if deprel:
        suffix += f'<sub class="deprel">{escape(deprel)}</sub>'
    esc_pieces = [escape(c) for c in frag]
    new_colored = colored[:s] + prefix + "".join(esc_pieces) + suffix + colored[e:]
    new_map = (
        orig_map[:s]
        + [None] * len(prefix)
        + [oi for oi, piece in zip(orig_map[s:e], esc_pieces) for _ in piece]
        + [None] * len(suffix)
        + orig_map[e:]
    )
    return new_colored, new_map


def resolve_rel_span(text, instance_id, sent_id, lemma, rel_predicate):
    """Return (form, char_start, char_end) for the REL occurrence belonging
    to this instance, or None. The REL scientifically always exists for
    every instance; `predicate` (or, failing that, the legacy-CoNLL-U-backed,
    schema-validated resolution cache) is only a positional anchor telling
    us *which* occurrence in the text to highlight. char_start/char_end are
    always positions in the ORIGINAL example text - they are the positional
    authority, never rediscovered by searching already-marked-up HTML
    (see _place_rel_by_offset)."""
    if rel_predicate:
        start, end = rel_predicate["char_start"], rel_predicate["char_end"]
        form = rel_predicate["form"]
        if text[start:end] == form:
            return form, start, end
    fallback = PREDICATE_CACHE.get_validated(instance_id, sent_id, lemma, text)
    if fallback:
        return fallback["form"], fallback["char_start"], fallback["char_end"]
    return None


def _place_rel_by_offset(colored, orig_map, rel_start, rel_end, instance_id):
    """Locate, within the already Arg-wrapped `colored` string, the exact
    span that renders original-text characters [rel_start, rel_end) - using
    the offset map built while wrapping Args, never a fresh text search over
    `colored` itself (BLOCKER 8: char_start/char_end is the sole positional
    authority). Raises if an ArgN wrap boundary lands strictly inside the
    REL interval (a wrap may legitimately CONTAIN the REL span - that is the
    normal nested case - but it must never CROSS it)."""
    positions = [j for j, oi in enumerate(orig_map) if oi is not None and rel_start <= oi < rel_end]
    if not positions:
        return None
    lo, hi = min(positions), max(positions) + 1
    actual = orig_map[lo:hi]
    if any(oi is None for oi in actual):
        raise RuntimeError(
            f"{instance_id}: an ArgN markup boundary crosses the REL interval "
            f"[{rel_start},{rel_end}) - refusing to render a corrupted REL span"
        )
    collapsed = []
    for oi in actual:
        if not collapsed or collapsed[-1] != oi:
            collapsed.append(oi)
    if collapsed != list(range(rel_start, rel_end)):
        raise RuntimeError(
            f"{instance_id}: REL interval [{rel_start},{rel_end}) does not map "
            f"back cleanly onto the original text after ArgN markup"
        )
    return lo, hi


def build_colored(text, real, syn, rel_predicate, order, instance_id="", sent_id="", lemma=""):
    """Wrap ArgN values first (sequential substitution, same as the original
    generator - this preserves its nested-span behavior for the rare case
    where an Arg span textually contains the REL occurrence), tracking an
    offset map back to the original text as we go. REL is then placed using
    that offset map at the *authoritative* [char_start, char_end) position
    from the JSON predicate anchor (or, when absent, the validated
    legacy-authority cache) - never by re-searching the Arg-marked-up HTML
    string to decide which occurrence is the REL.
    Returns (html_fragment, rel_found: bool).
    """
    colored = text
    orig_map = list(range(len(text)))
    for arg_id in order:
        k = int(arg_id[-1])
        val = real.get(arg_id)
        if val:
            colored, orig_map = _wrap_once(colored, orig_map, val, f"arg{k}", syn.get(arg_id))

    rel_found = False
    resolved = resolve_rel_span(text, instance_id, sent_id, lemma, rel_predicate)
    if resolved:
        _form, start, end = resolved
        span = _place_rel_by_offset(colored, orig_map, start, end, instance_id)
        if span:
            lo, hi = span
            colored = colored[:lo] + f'<span class="rel">{colored[lo:hi]}</span>' + colored[hi:]
            rel_found = True

    return colored, rel_found


def active_args(sense):
    """Arguments supported by this sense, including evidence without a role label."""
    active = {r.get("id") for r in sense.get("roles", [])
              if r.get("desc") is not None and str(r["desc"]).strip()}
    active.update(sense.get("syntactic_profile") or {})
    for ex in sense.get("examples") or []:
        for field in ("realization", "syntax"):
            active.update(arg for arg, value in (ex.get(field) or {}).items()
                          if value is not None)
    return sorted((a for a in active if re.fullmatch(r"Arg[0-4]", a or "")),
                  key=lambda a: int(a[3:]))


def highlight_order(shown_args):
    # Preserve Arg1/Arg2 before Arg0; wrap higher roles before nested Arg0 spans.
    return sorted(shown_args, key=lambda a: (a == "Arg0", int(a[3:])))


def build_roles_list(roles, shown_args):
    items = []
    for arg_id in shown_args:
        k = int(arg_id[3:])
        desc = next((r.get("desc") for r in roles if r.get("id") == arg_id), None)
        items.append(f'<li class="arg{k}">Arg {k}: {escape(str(desc)) if desc else "-"}</li>')
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def extract_counts_for(shown_args, syntactic_profile):
    ks = set()
    for arg in shown_args:
        for dep in (syntactic_profile.get(arg) or {}):
            ks.add(dep)
    rows = []
    for dep in sorted(ks):
        cells = [(syntactic_profile.get(arg) or {}).get(dep, 0) for arg in shown_args]
        rows.append((dep, cells))
    return rows


def build_examples_section(lemma, shown_args, examples, max_examples: int):
    parts = []
    subset = examples[:max_examples]
    order = highlight_order(shown_args)
    for i, ex in enumerate(subset, start=1):
        text = ex.get("text") or ""
        real = ex.get("realization") or {}
        iid = ex.get("instance_id", "")
        colored, _ = build_colored(text, real, {}, ex.get("predicate"), order,
                                    instance_id=iid, sent_id=ex.get("sent_ID", ""), lemma=lemma)
        parts.append(f'<h3 data-instance-id="{escape(iid)}">{i}: {colored}</h3>')
        items = [f'<li class="rel">rel: {escape(lemma)}</li>']
        for arg_id in shown_args:
            k = int(arg_id[-1])
            val = real.get(arg_id)
            items.append(f'<li class="arg{k}">Arg {k}: {escape(val) if val is not None else "-"}</li>')
        parts.append("<ul>\n" + "\n".join(items) + "\n</ul>")
    return "\n".join(parts)


def build_realization_table(lemma, shown_args, examples):
    colgroup = ['<col class="numcol">'] + ['<col class="argcol">' for _ in shown_args] + ['<col class="textcol">']
    ths = ['<th>#</th>'] + [f'<th class="arg{int(a[-1])}">{a.replace("Arg","Arg ")}</th>' for a in shown_args] + ['<th>Texto</th>']
    rows = []
    order = highlight_order(shown_args)
    for i, ex in enumerate(examples, start=1):
        text = ex.get("text") or ""
        real = ex.get("realization") or {}
        syn = ex.get("syntax") or {}
        iid = ex.get("instance_id", "")
        colored, rel_found = build_colored(text, real, syn, ex.get("predicate"), order,
                                            instance_id=iid, sent_id=ex.get("sent_ID", ""), lemma=lemma)
        if not rel_found:
            # HARD RULE: the REL always exists scientifically; a row must
            # never be left without its highlighted occurrence. If this
            # fires, the legacy-authority resolution cache is missing that
            # instance_id — see tools/resolve_predicate_anchors.py.
            raise RuntimeError(
                f"no REL highlight resolvable for instance {iid!r} (lemma={lemma!r}); "
                "run tools/resolve_predicate_anchors.py and re-check its residual TSV"
            )
        tds = [f"<td>{i}</td>"]
        for arg_id in shown_args:
            k = int(arg_id[-1])
            val = real.get(arg_id)
            tds.append(f'<td class="arg{k}">{escape(val) if val is not None else "-"}</td>')
        tds.append(f"<td class='texto'>{colored}</td>")
        attrs = f' data-instance-id="{escape(iid)}"'
        rows.append(f"<tr{attrs}>" + "".join(tds) + "</tr>")
    wide = len(shown_args) > 3
    opening = '<div class="argument-table-scroll" tabindex="0" aria-label="Realização sintática">' if wide else ""
    closing = "</div>" if wide else ""
    table_attrs = f' class="expanded-arguments" style="--arg-count:{len(shown_args)}"' if wide else ""
    return f"""
    {opening}<table id="relations-table"{table_attrs}>
      <colgroup>{''.join(colgroup)}</colgroup>
      <thead><tr>{''.join(ths)}</tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>{closing}
    """


def build_freq_table(shown_args, syntactic_profile):
    rows = extract_counts_for(shown_args, syntactic_profile)
    ths = ['<th>Relações de dependência - <i><a href="https://universaldependencies.org/u/dep/"> Universal Dependencies</a></i></th>'] \
          + [f'<th class="arg{int(a[-1])}">{a.replace("Arg","Arg ")}</th>' for a in shown_args]
    body = []
    for dep, cells in rows:
        body.append("<tr>" + "".join([f"<td>{escape(dep)}</td>"] + [f'<td class="{arg.lower()}">{int(v)}</td>' if arg in ("Arg3", "Arg4") else f"<td>{int(v)}</td>" for arg, v in zip(shown_args, cells)]) + "</tr>")
    if not body:
        body.append(f"<tr><td colspan='{len(shown_args)+1}'><i>Sem ocorrências</i></td></tr>")
    return f"""
    <div class="statistics-table-container">
      <h2>Frequência das realizações sintáticas</h2>
      <table id="statistics-table">
        <thead><tr>{''.join(ths)}</tr></thead>
        <tbody>{''.join(body)}</tbody>
      </table>
    </div>
    """


def render_html(doc: dict, json_filename: str) -> str:
    lemma = (doc.get("lemma") or doc.get("lemma_base") or "").strip()
    senses = doc.get("senses") or []

    if len(senses) > 1:
        # Keep each roleset's roles, examples and frequencies together.
        pages = [render_html({**doc, "senses": [sense]}, json_filename) for sense in senses]
        start = '<div class="content">'
        end = '\n</div>\n\n<a class="back-link'
        prefix = pages[0].split(start, 1)[0]
        suffix = end + pages[0].split(end, 1)[1]
        bodies = []
        for index, page in enumerate(pages, start=1):
            body = page.split(start, 1)[1].split(end, 1)[0]
            for table_id in ("relations-table", "statistics-table"):
                body = body.replace(f'id="{table_id}"', f'id="{table_id}-{index}"')
            bodies.append(body)
        for table_id in ("relations-table", "statistics-table"):
            prefix = prefix.replace(f"#{table_id}", f'[id^="{table_id}"]')
        return prefix + start + "\n<hr>\n".join(bodies) + suffix

    pt_rolesets = []
    en_links = []
    sources = []
    roles = []
    for k in range(5):
        chosen = None
        for s in senses:
            for r in (s.get("roles") or []):
                if r.get("id") == f"Arg{k}" and r.get("desc") is not None:
                    chosen = r.get("desc")
                    break
            if chosen is not None:
                break
        roles.append({"id": f"Arg{k}", "desc": chosen})

    examples = []
    for s in senses:
        examples.extend(s.get("examples") or [])

    syntactic_profile = {}
    for s in senses:
        sp = s.get("syntactic_profile") or {}
        for arg, deps in sp.items():
            syntactic_profile.setdefault(arg, {})
            for dep, cnt in deps.items():
                syntactic_profile[arg][dep] = syntactic_profile[arg].get(dep, 0) + int(cnt or 0)

    seen_pt, seen_en, seen_src = set(), set(), set()
    for s in senses:
        pr = (s.get("pt_roleset") or "").strip()
        if pr and pr not in seen_pt:
            seen_pt.add(pr)
            pt_rolesets.append(pr)
        er = (s.get("english_roleset") or "").strip()
        if er and er not in seen_en:
            seen_en.add(er)
            url = s.get("nombank_url")
            if not url:
                base_en = er.split(".")[0]
                if base_en:
                    url = f"https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/frames/{base_en}.xml"
            en_links.append((er, url))
        src = (s.get("english_roleset_source") or "").strip()
        if src and src not in seen_src:
            seen_src.add(src)
            sources.append(src)

    roleset_id_str = ", ".join(pt_rolesets) if pt_rolesets else f"{lemma}.01"
    en_map_html = ", ".join(
        (f'<a href="{url}">{escape(er)}</a>' if url else escape(er))
        for (er, url) in en_links
    ) if en_links else "-"
    if sources:
        src_links = []
        for src in sources:
            m = re.match(r"verb-([^.]+)", src, flags=re.I)
            if m:
                verb = m.group(1).lower()
                pb_url = f"https://verbs.colorado.edu/propbank/framesets-english-aliases/{verb}.html"
                src_links.append(f'<a href="{pb_url}">{escape(src)}</a>')
            else:
                src_links.append(escape(src))
        source_tail = ", source = " + ", ".join(src_links)
    else:
        source_tail = ""

    shown_args = active_args(senses[0]) if senses else []
    roles_html = build_roles_list(roles, shown_args)
    examples_html = build_examples_section(lemma, shown_args, examples, max_examples=MAX_EXAMPLES_IN_SECTION)
    table_html = build_realization_table(lemma, shown_args, examples)
    freq_html = build_freq_table(shown_args, syntactic_profile)

    letter = first_letter(lemma)
    back_href = f"../index.html?letter={letter}"
    back_label = f"← Voltar para {letter.upper()}"
    download_href = f"{DOWNLOAD_PREFIX_FROM_PAGE}{json_filename}"

    head = f"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(lemma)} - NounBank.DS</title>
<link rel="stylesheet" href="{CSS_HREF}">
<style>{STYLE_BLOCK}</style>
</head>
<body>

<header class="site-header">
  <nav class="site-nav">
    <a class="home-link" href="../index.html">Home</a>
    <span class="page-title">{escape(lemma)}</span>
    <a class="download-json" href="{download_href}" download="{escape(json_filename)}" aria-label="Baixar JSON">JSON download</a>
  </nav>
</header>

<script>
(function(){{
  const h = document.querySelector('.site-header');
  if(!h) return;
  const onScroll = () => h.classList.toggle('scrolled', window.scrollY > 16);
  onScroll(); window.addEventListener('scroll', onScroll, {{passive:true}});
}})();
</script>

<div class="content">
  """

    topo = f"""
  <h1>Nome predicador: <i style="color: red;">{escape(lemma)}</i></h1>
  <p><strong>Roleset id:</strong> {escape(roleset_id_str)}, Mapeamento para o inglês: {en_map_html}{source_tail}</p>
  <h2>Roles:</h2>
  {roles_html}
  <h2>Exemplos:</h2>
  {examples_html}
  <br><br>
"""

    tail = f"""
  <h2>Realização sintática da estrutura de argumentos</h2>
  {table_html}
  {freq_html}
</div>

<a class="back-link back-floating" href="{back_href}" title="Voltar para letra {letter.upper()}">{back_label}</a>

</body>
</html>
"""
    out = head + topo + tail
    # The f-string templates above interpolate multi-line fragments (tables,
    # example blocks) inside indented lines, which leaves indentation-only
    # ("trailing whitespace") lines behind wherever a fragment starts or
    # ends with its own newline. Strip trailing whitespace deterministically
    # rather than hand-tuning every template.
    return re.sub(r"[ \t]+$", "", out, flags=re.M)


def check_rendering(paths):
    """Read-only regression check (requires beautifulsoup4); never writes pages."""
    from bs4 import BeautifulSoup

    assert not re.search(r"range\(\s*3\s*\)", Path(__file__).read_text())
    # Each activation source works independently, without filling gaps.
    assert active_args({"roles": [{"id": "Arg1", "desc": "x"},
                                  {"id": "Arg0", "desc": " "}],
                        "examples": [{"realization": {"Arg2": "x"},
                                      "syntax": {"Arg3": "nmod"}}],
                        "syntactic_profile": {"Arg4": {}}}) == [f"Arg{k}" for k in range(1, 5)]
    assert active_args({"roles": [{"id": "Arg1", "desc": "x"},
                                  {"id": "Arg2", "desc": "y"}]}) == ["Arg1", "Arg2"]
    page_counts = dict.fromkeys(("Arg3", "Arg4"), 0)
    instance_counts = dict.fromkeys(page_counts, 0)
    checked = 0
    for path in paths:
        if path.name == "_manifest.json":
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        soup = BeautifulSoup(render_html(doc, path.name), "html.parser")
        tables = soup.select('[id^="relations-table"]')
        freqs = soup.select('[id^="statistics-table"]')
        assert len(tables) == len(doc["senses"]), path
        page_args = set()
        for sense, table, freq in zip(doc["senses"], tables, freqs):
            # Independent oracle for the four activation rules.
            expected = []
            for k in range(5):
                arg = f"Arg{k}"
                if (any(r.get("id") == arg and r.get("desc") is not None
                        and str(r["desc"]).strip() for r in sense.get("roles", []))
                    or any(ex.get(field, {}).get(arg) is not None
                           for ex in sense.get("examples", []) for field in ("realization", "syntax"))
                    or arg in sense.get("syntactic_profile", {})):
                    expected.append(arg)
            roles_list = table.find_previous("h2", string="Roles:").find_next("ul")
            assert [li.get("class", [""])[0] for li in roles_list.select("li")] == [a.lower() for a in expected], path
            for ex in (sense.get("examples") or [])[:MAX_EXAMPLES_IN_SECTION]:
                example = soup.find("h3", attrs={"data-instance-id": ex["instance_id"]})
                for arg in expected:
                    value = ex.get("realization", {}).get(arg)
                    item = example.find_next("ul").select_one("li." + arg.lower())
                    assert item.get_text() == arg.replace("Arg", "Arg ") + ": " + (value if value is not None else "-"), path
            page_args.update(expected)
            assert [th.get_text() for th in table.select("thead th")][1:-1] == [a.replace("Arg", "Arg ") for a in expected], path
            assert [th.get_text() for th in freq.select("thead th")][1:] == [a.replace("Arg", "Arg ") for a in expected], path
            rows = table.select("tbody tr")
            assert len(rows) == len(sense.get("examples", [])), path
            for ex, row in zip(sense.get("examples", []), rows):
                assert row["data-instance-id"] == ex["instance_id"], path
                for arg in expected:
                    value = ex.get("realization", {}).get(arg)
                    assert row.select_one("td." + arg.lower()).get_text() == (value if value is not None else "-"), (path, ex["instance_id"], arg)
                    if arg in instance_counts and value is not None:
                        instance_counts[arg] += 1
            for arg, deps in sense.get("syntactic_profile", {}).items():
                if arg not in expected:
                    continue
                for dep, count in deps.items():
                    row = next(r for r in freq.select("tbody tr") if r.select_one("td").get_text() == dep)
                    assert int(row.select("td")[expected.index(arg) + 1].get_text()) == count, (path, arg, dep)
        for arg in page_counts:
            page_counts[arg] += arg in page_args
        if path.stem == "desova":
            row = soup.find("tr", attrs={"data-instance-id": "dante_01_463775892947611648l::desova::1"})
            assert row.select_one(".texto .arg3").get_text() == "médio de 104,06"
            assert [li.get_text() for li in soup.select(".content > ul")[0].select("li")] == [
                "Arg 0: seller", "Arg 1: thing sold", "Arg 2: buyer", "Arg 3: price paid", "Arg 4: beneficiary"]
            assert row.select_one("td.arg4").get_text() == "-"
            assert soup.select_one("#statistics-table tbody td.arg3").get_text() == "1"
        checked += 1
    print(f"Checked {checked} pages; active pages: {page_counts}; realized instances: {instance_counts}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lemmas", nargs="*", help="Only regenerate these lemmas (default: all)")
    parser.add_argument("--check", action="store_true", help="Check rendering in memory; requires beautifulsoup4")
    args = parser.parse_args()
    paths = [JSON_DIR / f"{lemma}.json" for lemma in args.lemmas] if args.lemmas else sorted(JSON_DIR.glob("*.json"))
    if args.check:
        check_rendering(paths)
        return
    n = 0
    for path in paths:
        if path.name == "_manifest.json":
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        out_html = render_html(doc, json_filename=path.name)
        out_path = HTML_DIR / f"{path.stem}.html"
        out_path.write_text(out_html, encoding="utf-8")
        n += 1
    print(f"regenerated {n} html pages")


if __name__ == "__main__":
    main()
