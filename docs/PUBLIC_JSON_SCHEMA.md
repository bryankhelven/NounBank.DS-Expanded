# Formato dos dados

Os JSONs públicos do NounBank.DS Expanded seguem a organização da versão original: `lemma`, `lemma_base` e `senses`. Cada sense reúne `pt_roleset`, `english_roleset` quando resolvido, `roles`, `examples`, `realization`, `syntax`, `predicate` e `syntactic_profile`.

Durante esta etapa de revisão, `pending_instances` preserva apenas ocorrências já identificadas como predicadoras que ainda aguardam resolução manual de sense e/ou roleset.

Ocorrências não predicadoras e metadados internos de construção não são publicados.

## Identificação obrigatória de cada instância

Todos os exemplos, tanto dos lemas herdados quanto dos novos, têm `instance_id` e `predicate`. A identificação é preenchida também quando há apenas uma aparição do nome na frase.

```json
{
  "instance_id": "dante_01_464089901571788800l::desova::1",
  "predicate": {
    "form": "desova",
    "char_start": 17,
    "char_end": 23,
    "occurrence_index": 1,
    "occurrence_count": 1,
    "char_offset_unit": "UNICODE_CODEPOINT_END_EXCLUSIVE"
  }
}
```

- `form` é a sequência literal encontrada em `text`, preservando sua grafia, inclusive abreviações, formas truncadas e espaços de expressões compostas.
- `char_start` começa em zero e inclui o primeiro caractere; `char_end` exclui o último limite. Os índices contam caracteres Unicode, não bytes nem unidades UTF-16. A expressão Python `text[char_start:char_end]` deve ser exatamente igual a `form`.
- `occurrence_index` começa em 1 e identifica a aparição do lema pela ordem no texto. A contagem reúne suas formas nominais reconhecidas na sentença, incluindo flexões, e considera todas as acepções. Não é o número da linha na tabela nem o índice da acepção.
- `occurrence_count` informa o total dessas aparições reconhecidas. Uma sentença pode conter uma aparição nominal que não esteja publicada como instância desta acepção; nesse caso o índice ainda identifica a posição na frase.
- `instance_id` é um identificador estável e opaco. Os identificadores anteriores foram preservados, inclusive aqueles com `::token=...`, para manter todos os vínculos de proveniência e de ARG-M. Não se deve extrair sua posição pelo sufixo: use `occurrence_index` e os limites do texto. Os identificadores anteriormente ausentes foram criados no formato `sent_ID::lemma::occurrence_index`.

Campos anteriores de `predicate`, como `source_token_id`, `source_form`, `lemma` e `upos`, continuam preservados quando disponíveis. Um token de origem deve ser interpretado na versão de corpus que o produziu; ele não substitui os limites no `text` publicado.

`instance_identity_provenance` documenta o método e a justificativa da recuperação, o commit anterior, o caminho e o ponteiro JSON da instância original, e informa se seu identificador foi preservado. Esses registros permitem distinguir o conteúdo herdado dos campos materializados nesta padronização. A forma literal pode ter sua capitalização ajustada para reproduzir exatamente `text`, sem alterar o texto original.

A apresentação utiliza os limites explícitos para destacar REL. Ao passar o cursor sobre o predicador, o título informa sua aparição e o total na frase. A ausência de ARG-M não implica ausência de identificador do predicador.

Antes de publicar novos exemplos ou regenerar os downloads, execute `python3 tools/validate_instance_identity.py`. O verificador rejeita qualquer exemplo sem os campos obrigatórios, identidade duplicada, limites incompatíveis com a forma literal, vínculo ARG-M quebrado ou divergência entre arquivos individuais, JSONL e ZIP.
