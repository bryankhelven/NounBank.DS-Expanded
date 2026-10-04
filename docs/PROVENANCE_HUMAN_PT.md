# Provenance para leitura humana

A página `provenance.html` usa diretamente `data/provenance/human_pt/rolesets_pt.json`. Seus textos em português e seus grupos são a mesma vista disponível para processamento computacional. Não há um segundo conjunto independente de explicações no HTML.

Cada ficha responde à origem, ao que foi materializado/publicado, à criação local e à justificativa documentada. A referência inglesa, o identificador português, a descrição do papel e a origem histórica da marcação são eixos distintos. Um identificador português sem correspondente inglês não é automaticamente um frame local com papéis.

Os grupos de origem têm partição exclusiva: 570 registros com referência ao NomBank, 2 com papéis locais publicados e 3 sem equivalente inglês e sem inventário de papéis. A consulta também agrupa por tratamento do inventário, referência do NomBank, antecedente verbal declarado e nome português. As 4 propostas locais não ativadas aparecem em uma consulta separada e não aumentam o total de 575 sentidos publicados.

`papeis_pt.json` conserva 2.068 chaves de registros de papel: 1.810 descrições semânticas e 258 campos vazios de preenchimento. `marcacoes_pt.jsonl.gz` conserva 36.983 chaves, valores e localizadores, acrescentando o significado do tipo de campo e explicando a limitação da origem histórica individual. `schema_pt.json` e `glossario_pt.json` explicam os campos e as ligações.

As justificativas retrospectivas aceitas são distinguidas de explicações já presentes no sentido e de sínteses editoriais em português. Traduções ou resumos de evidência não constituem nova adjudicação. Quando a justificativa histórica não foi recuperada, isso permanece explícito. Descrições de papéis na fonte e na publicação são mostradas literalmente no idioma original, sem substituir os rótulos científicos por tradução.

Os excertos Q177 (freio) e Q292 (razão) reproduzem literalmente registros do histórico estruturado recuperado, com hashes dos arquivos de origem. Em show.06 a evidência atual que rejeita performance prevalece sobre o registro anterior favorável a essa associação; a ficha conserva essa distinção. Em carteira.01 a correção histórica documentada para portfolio.01 não é confundida com o mapping ainda publicado portfolio.04.

Os arquivos originais em `data/provenance/orch279` permanecem intactos. As sínteses editoriais têm indicadores e localizadores para a evidência original. A correção da interface foi solicitada pelo usuário após ORCH283; a ciência continua sob ORCH279. Nenhum nome, mapping, gold, inventário científico ou marcação foi alterado.
