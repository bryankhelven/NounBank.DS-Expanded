#!/usr/bin/env python3
"""Small heuristic Portuguese noun pluralizer, used only to generate CANDIDATE
surface forms to search for in text. Candidates are only ever accepted if they
are actually found (via regex) in the corpus text — this module never invents
text, it only proposes strings to look for.
"""
import re

VOWEL_TIL = {"ão": "ões", "ãe": "ães"}


def pluralize(word: str):
    """Return a list of plausible plural forms for a PT singular noun."""
    if not word:
        return []
    low = word
    forms = set()
    if low.endswith("ção"):
        forms.add(low[:-3] + "ções")
    elif low.endswith("são"):
        forms.add(low[:-3] + "sões")
    elif low.endswith("ão"):
        forms.add(low[:-2] + "ões")
        forms.add(low[:-2] + "ãos")
        forms.add(low[:-2] + "ães")
    elif low.endswith(("r", "z", "n")):
        forms.add(low + "es")
    elif low.endswith("m"):
        forms.add(low[:-1] + "ns")
    elif low.endswith("l"):
        forms.add(low[:-1] + "is")
    elif low.endswith(("a", "e", "o", "i", "u")):
        forms.add(low + "s")
    else:
        forms.add(low + "s")
    return sorted(forms)
