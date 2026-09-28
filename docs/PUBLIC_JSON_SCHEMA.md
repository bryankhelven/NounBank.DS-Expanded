# Formato dos dados

Os JSONs públicos do NounBank.DS Expanded seguem a organização da versão original: `lemma`, `lemma_base` e `senses`. Cada sense reúne `pt_roleset`, `english_roleset` quando resolvido, `roles`, `examples`, `realization`, `syntax`, `predicate` e `syntactic_profile`.

Durante esta etapa de revisão, `pending_instances` preserva apenas ocorrências já identificadas como predicadoras que ainda aguardam resolução manual de sense e/ou roleset.

Ocorrências não predicadoras e metadados internos de construção não são publicados.
