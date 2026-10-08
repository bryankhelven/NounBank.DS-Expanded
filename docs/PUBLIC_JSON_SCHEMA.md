# Formato dos dados

Cada JSON de lema contém `lemma` e `senses`. Cada acepção reúne seu roleset, os papéis semânticos, os exemplos, suas realizações e relações sintáticas e o perfil de frequência. O campo `lemma_base`, que repetia `lemma` em todos os arquivos, foi retirado.

## Predicador de cada exemplo

Todos os exemplos têm `sent_ID`, `text` e `predicate`, inclusive quando o nome aparece apenas uma vez.

```json
{
  "sent_ID": "dante_01_464089901571788800l",
  "predicate": {
    "form": "desova",
    "char_start": 17,
    "char_end": 23,
    "occurrence_index": 1,
    "occurrence_count": 1
  }
}
```

- `form` reproduz literalmente a forma em `text`, incluindo abreviações e truncamentos.
- `char_start` começa em zero e inclui o primeiro caractere; `char_end` é o limite exclusivo. Os índices contam caracteres Unicode (pontos de código). Esta convenção vale para todos os exemplos e é definida aqui, sem um campo repetido em cada predicador. Em Python, `text[char_start:char_end]` deve ser igual a `form`.
- `occurrence_index` começa em 1 e identifica a aparição nominal do lema pela ordem no texto, considerando suas formas flexionadas e todas as acepções reconhecidas na sentença.
- `occurrence_count` informa o total dessas aparições reconhecidas. Uma aparição única recebe índice 1 e total 1. A contagem é feita sobre o texto da própria instância; versões textuais diferentes mantêm seus respectivos limites e contagens.

O predicador é identificado uma única vez, em `predicate`. `source_token_id` é preservado quando disponível; predicadores com vários tokens mantêm `source_token_ids`. `source_form` e `lemma` aparecem apenas quando diferem da forma publicada e do lema da entrada, respectivamente. O token deve ser interpretado na versão de corpus que o produziu.

Este recurso publica apenas usos predicadores nominais. Por isso, não repete `predication: Predicador`, `predicative: true` nem um bloco `rel` equivalente. A cópia de identificação do corpus `source_identity` foi retirada do JSON de consulta; o corpus e o histórico do repositório permanecem disponíveis. `argm_review`, suas referências de página e as listas de ARG-M vazias foram retirados. Sem `argm_annotations`, a instância não contém marcações ARG-M publicadas.

`source_commit`, `provenance_ref` e convenções de caracteres repetidas não fazem parte dos JSONs de lemas. As anotações preservam sua origem, relação com as marcações anteriores, justificativa, tokens e evidência sintática. Os arquivos separados de histórico de proveniência permanecem intactos.

Os exemplos públicos não precisam de um ID artificial de instância. A combinação de sentença e posição do predicador permite distinguir nomes repetidos. Os campos `instance_id`, `native_instance_id` e o bloco de operação técnica `instance_identity_provenance` foram retirados dos JSONs de lemas e dos downloads agregados. A proveniência científica dos sentidos, papéis e modificadores permanece preservada. Os arquivos de histórico mantêm seus vínculos anteriores para recuperar a origem e as alterações efetivamente feitas.

Na página, REL aponta para a posição literal do predicador. Seu título informa a aparição e o total na frase.

## JSON e JSONL

Cada página oferece o JSON do lema e o JSONL correspondente. O JSONL por lema contém o mesmo objeto em uma única linha, terminada por uma quebra de linha. Mantém todos os sentidos e exemplos do lema, sem perda de informação, e segue o mesmo formato do JSONL global: um lema por linha.

O ZIP global contém todos os JSONs individuais. O JSONL global contém os mesmos lemas, na ordem do inventário.

Antes de publicar novos exemplos ou regenerar os downloads, execute `python3 tools/validate_predicate_anchors.py`. A verificação exige os limites literais em todos os predicadores e compara os dados individuais, o JSONL global e o ZIP.
