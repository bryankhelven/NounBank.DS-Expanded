document.addEventListener("DOMContentLoaded", async () => {
  const manifest = await fetch("jsons/_manifest.json").then(r => r.json());
  const items = manifest.lemmas || [];
  const search = document.getElementById("nbds-search");
  const suggestions = document.getElementById("nbds-suggestions");
  const alphabet = document.getElementById("alphabet-buttons");
  const box = document.getElementById("content-box");

  const fold = s => String(s || "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
  const firstLetter = lemma => fold(lemma).charAt(0);
  const letters = [...new Set(items.map(x => firstLetter(x.lemma).toUpperCase()))].sort();

  alphabet.innerHTML = letters.map(l =>
    '<button class="letter-button" data-letter="' + l.toLowerCase() + '">' + l + '</button>'
  ).join("");

  const buttons = [...alphabet.querySelectorAll(".letter-button")];

  function card(x) {
    const letter = firstLetter(x.lemma);
    return '<a class="lemma-card" href="site_pages/' + encodeURIComponent(x.lemma) + '.html?letter=' + encodeURIComponent(letter) + '">' +
      '<span class="lemma-name-row"><span>' + x.lemma + '</span>' +
      (x.new ? '<sup class="new-float">NEW</sup>' : '') +
      '</span></a>';
  }

  function selectButton(letter) {
    buttons.forEach(b => b.classList.toggle("selected", b.dataset.letter === letter));
  }

  function clearSelection() {
    buttons.forEach(b => b.classList.remove("selected"));
  }

  function setLetterParam(letter, replace = false) {
    const u = new URL(location.href);
    if (letter) u.searchParams.set("letter", letter);
    else u.searchParams.delete("letter");
    history[replace ? "replaceState" : "pushState"]({}, "", u);
  }

  function renderLetter(letter, changeUrl = true) {
    const list = items
      .filter(x => firstLetter(x.lemma) === letter)
      .sort((a, b) => a.lemma.localeCompare(b.lemma, "pt-BR"));

    if (!list.length) {
      box.innerHTML = "";
      box.style.display = "none";
      clearSelection();
      return;
    }

    box.innerHTML = list.map(card).join("");
    box.style.display = "block";
    selectButton(letter);
    if (changeUrl) setLetterParam(letter);
  }

  alphabet.addEventListener("click", e => {
    const b = e.target.closest(".letter-button");
    if (!b) return;
    const letter = b.dataset.letter;
    if (b.classList.contains("selected")) {
      clearSelection();
      box.innerHTML = "";
      box.style.display = "none";
      setLetterParam(null);
    } else {
      renderLetter(letter, true);
    }
  });

  search.addEventListener("input", () => {
    const q = fold(search.value.trim());
    if (!q) {
      suggestions.innerHTML = "";
      return;
    }
    suggestions.innerHTML = items
      .filter(x => fold(x.lemma).includes(q))
      .sort((a, b) => a.lemma.localeCompare(b.lemma, "pt-BR"))
      .slice(0, 12)
      .map(card)
      .join("");
  });

  const initial = (new URLSearchParams(location.search).get("letter") || "").toLowerCase();
  if (initial && letters.map(x => x.toLowerCase()).includes(initial)) {
    renderLetter(initial, false);
  } else {
    box.style.display = "none";
    clearSelection();
  }

  window.addEventListener("popstate", () => {
    const letter = (new URLSearchParams(location.search).get("letter") || "").toLowerCase();
    if (letter && letters.map(x => x.toLowerCase()).includes(letter)) {
      renderLetter(letter, false);
    } else {
      clearSelection();
      box.innerHTML = "";
      box.style.display = "none";
    }
  });
});
