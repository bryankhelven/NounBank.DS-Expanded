#!/usr/bin/env python3
"""Apply the explicitly decided PARTE C semantic/textual fixes.

Every ArgN value written here is verified to be a literal substring of the
example's text before being written. Deprels were recovered from the gold
treebank (not guessed) — see the report for the token-level evidence per fix.
Normative source (canonical): ~/workspace/nounbank_ds_authority/DANTEStocks_legacy_v1/corpus/
  DANTEStocks-train.conllu, DANTEStocks-dev.conllu, DANTEStocks-test.conllu
An independent audit confirmed factual equivalence with the original working
copy (/home/bryan/workspace/lais/dante.conllu) for the 22 sentences touched
here, but the legacy trio above is the authoritative reference going forward.
"""
import json

JSON_DIR = "jsons"


def load(lemma):
    with open(f"{JSON_DIR}/{lemma}.json", encoding="utf-8") as f:
        return json.load(f)


def save(lemma, doc):
    with open(f"{JSON_DIR}/{lemma}.json", "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")


def find_example(doc, sent_id, ordinal=1):
    seen = 0
    for sense in doc["senses"]:
        for ex in sense["examples"]:
            if ex["sent_ID"] == sent_id:
                seen += 1
                if seen == ordinal:
                    return sense, ex
    raise KeyError(f"{sent_id} ordinal {ordinal} not found")


def set_arg(ex, arg, value, deprel):
    if value is not None:
        assert value in ex["text"], f"{value!r} not substring of {ex['text']!r}"
    ex["realization"][arg] = value
    ex["syntax"][arg] = deprel


def recompute_profile(sense):
    profile = {}
    for ex in sense["examples"]:
        syn = ex.get("syntax") or {}
        for arg, dep in syn.items():
            if dep is None:
                continue
            profile.setdefault(arg, {})
            profile[arg][dep] = profile[arg].get(dep, 0) + 1
    sense["syntactic_profile"] = profile


applied = []
blocked = []

# ---- C1: carteira 56% ----
doc = load("carteira")
_, ex = find_example(doc, "dante_01_452088399588249600l")
set_arg(ex, "Arg2", "56 %", "nmod")
for sense in doc["senses"]:
    recompute_profile(sense)
save("carteira", doc)
applied.append("C1 carteira 56% Arg2=56 % / nmod")

# ---- C2/C3/C4: compra ----
doc = load("compra")
_, ex = find_example(doc, "dante_01_449147872840548353l")
set_arg(ex, "Arg1", "PETR4", "nsubj")
applied.append("C2 compra PETR4(nao compra) Arg1=PETR4 / nsubj")

_, ex = find_example(doc, "dante_01_448289071920472064l")
set_arg(ex, "Arg1", "de #JBSS3", "nmod")
applied.append("C3 compra JBSS3 Arg1=de #JBSS3 / nmod")

_, ex = find_example(doc, "dante_01_454284964583190528l")
set_arg(ex, "Arg1", "em PETR4", "nmod")
applied.append("C4 compra call PETR4 Arg1=em PETR4 / nmod")

for sense in doc["senses"]:
    recompute_profile(sense)
save("compra", doc)

# ---- C5: reunião literal fix ----
doc = load("reunião")
_, ex = find_example(doc, "dante_01_443463813623738368l")
set_arg(ex, "Arg2", "de o conselho de administração", "nmod")
for sense in doc["senses"]:
    recompute_profile(sense)
save("reunião", doc)
applied.append("C5 reuniao Arg2 literal fix (com->de) / nmod")

# ---- C6: cara role shift ----
doc = load("cara")
sense = doc["senses"][0]
for role in sense["roles"]:
    if role["id"] == "Arg0":
        role["desc"] = None
    elif role["id"] == "Arg1":
        role["desc"] = "theme"
    elif role["id"] == "Arg2":
        role["desc"] = "value"
for ex in sense["examples"]:
    real = ex["realization"]
    syn = ex["syntax"]
    new_real = dict(real)
    new_syn = dict(syn)
    new_real["Arg2"] = real["Arg1"]
    new_real["Arg1"] = real["Arg0"]
    new_real["Arg0"] = None
    new_syn["Arg2"] = syn["Arg1"]
    new_syn["Arg1"] = syn["Arg0"]
    new_syn["Arg0"] = None
    ex["realization"] = new_real
    ex["syntax"] = new_syn
recompute_profile(sense)
save("cara", doc)
applied.append("C6 cara role shift Arg0->Arg1->Arg2 (6 examples)")

# ---- C7: comparação split ----
doc = load("comparação")
_, ex = find_example(doc, "dante_01_443438866146807809l", ordinal=1)
set_arg(ex, "Arg1", "#PETR4", "nmod")
set_arg(ex, "Arg2", "#SPX", "conj")
for sense in doc["senses"]:
    recompute_profile(sense)
save("comparação", doc)
applied.append("C7 comparacao split instance1 Arg1=#PETR4/nmod Arg2=#SPX/conj")

# ---- C8: oferta ex2/ex3 ----
doc = load("oferta")
_, ex = find_example(doc, "dante_01_443125288709279744l")
set_arg(ex, "Arg0", "Petrobras", "nsubj")
set_arg(ex, "Arg1", "bônus", "nmod")
set_arg(ex, "Arg2", "US$ 8,5 bilhões", "nmod")
set_arg(ex, "Arg3", None, None)

_, ex = find_example(doc, "dante_01_443546558307778560l")
set_arg(ex, "Arg0", "Petrobras", "nsubj")
set_arg(ex, "Arg1", "bônus", "nmod")
set_arg(ex, "Arg2", "US$ 8,5 bi", "nmod")
set_arg(ex, "Arg3", None, None)

for sense in doc["senses"]:
    recompute_profile(sense)
save("oferta", doc)
applied.append("C8 oferta ex2/ex3 Arg0/Arg1/Arg2 fix, Arg3 cleared")

print("APPLIED:")
for a in applied:
    print(" -", a)
print("BLOCKED:")
for b in blocked:
    print(" -", b)
