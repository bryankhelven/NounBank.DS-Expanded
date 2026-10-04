# Provenance de rolesets, papéis e marcações — ORCH279

A fila original de398 issues de justificativa/provenance foi aceita como fechada pelo ORCH_RECON_000279: **398/398, residual0**. Accounting:350 rationales de seleção,43 reconciliações anteriores de inventário,2 ratificações documentais novas e3 issues de carteira.

Esse fechamento é de uma fila específica. Não significa que intenção original, execução histórica do gerador ou origem histórica individual de todos os spans tenham sido recuperadas. As decisões retrospectivas são identificadas como tal; `original_annotator_intent = NOT_RECOVERED_NOT_INFERRED` permanece explícito. Conservação sob ambiguidade não certifica o fato lexical ambíguo.

## Arquivos de consulta

Os arquivos estão em [data/provenance/orch279](../data/provenance/orch279/), em JSONL gzip. Cada linha é um registro JSON; descompactar não muda seus bytes originais. O [manifest](../data/provenance/orch279/manifest.json) fornece hash comprimido, hash original, origem V23 e número de registros.

| Arquivo | Registros | Conteúdo |
|---|---:|---|
| rolesets.jsonl.gz |575| Fonte publicada, inventário, evidência e decisões aceitas por record_id |
| role_definitions.jsonl.gz |2.068| Origem documental de cada definição, comparador nativo e ressalvas |
| annotations.jsonl.gz |36.983| Literal original de cada marcação, referências ao roleset/papel e estado de origem histórica |
| occurrences.jsonl.gz |3.693| Ocorrências gold preservadas literalmente |
| issue_closures.jsonl.gz |398| Identidades físicas e autoridades de fechamento |
| accepted_selection_rationales.jsonl.gz |350| Justificativas retrospectivas criadas e aceitas, com escopo/evidência |
| accepted_inventory_documentation.jsonl.gz |45|43 reconciliações anteriores +2 ratificações documentais, com tipos distintos |

Os vínculos usam `record_id`, `occurrence_id`, `annotation_id` e `role_definition_record_id`. Os locators originais contêm commit, caminho e hash; eles se referem à fonte histórica explicitada, não a uma suposta importação direta. Evidências e antecedentes externos continuam identificados por seus locators nos literais; esta projeção não copia toda a coleção de arquivos históricos do pacote V23.

## Grupos de origem

| Grupo | Registros | Arquivo |
|---|---:|---|
| NomBank com upstream verbal declarado |475|nombank_with_verbal_upstream.jsonl.gz|
| NomBank sem upstream verbal declarado |95|nombank_without_verbal_upstream.jsonl.gz|
| Sem mapeamento inglês compatível documentado |5|no_compatible_english_mapping.jsonl.gz|
| Inventários locais existentes |2|existing_local_inventories.jsonl.gz|
| Propostas locais V20, inativas |4|inactive_local_proposals.jsonl.gz|

Os grupos locais são subconjuntos/contextos, não parcelas para somar a575. `verb-*` no NomBank é upstream interno declarado, não comprovação de importação direta do PropBank. Recursos suplementares de domínio não são automaticamente fontes de definição de papel.

## Limites científicos preservados

Aceite de rationale não substitui fonte ativa nem certifica equivalência de papéis/spans. As propostas locais permanecem inativas. Cotação/posição têm transformação ratificada documentalmente, sem prova de execução histórica. O inventário de papéis não determina aridade obrigatória; padding nulo não cria papel semântico.

Esta integração acrescenta documentação e arquivos de provenance. JSONs científicos, JSONL de distribuição, ZIP científico, argumentos, sintaxe, predicação, IDs, valência publicada e interface são preservados. Mudanças científicas ou de publicação dependem de autoridade separada. Veja POST_CLOSURE_SCOPE_LIMITS_AND_SEPARATE_GATES.json.

## Verificação

Execute `python tools/validate_provenance_orch279.py` na raiz do repositório. O validador confere hashes, população, identidades, referências e hashes das fontes publicadas. PASS de integridade não equivale a certificado de recuperação histórica ou de todos os bindings semânticos.
