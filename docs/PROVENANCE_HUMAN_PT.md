# Provenance e inventários atuais

A versão corretiva V28 materializa os inventários locais nos JSONs científicos, no JSONL, no ZIP e nas páginas. A consulta usa os mesmos textos e definições da vista computacional.

São 518 nomes, 576 sentidos e 3.693 ocorrências. Todos os 576 sentidos têm inventário com pelo menos uma descrição de papel. 567 têm referência inglesa verificada no XML nativo NomBank 1.0; 9 têm rolesets locais, com 22 papéis definidos. Os três inventários antes vazios — freio.01, show.06 e vertigem.01 — foram definidos a partir dos contextos portugueses. Os quatro desenhos anteriores de alta, ameaça, quebra e vergonha foram materializados. Razão e esquartejador conservam suas definições locais, agora explicitamente documentadas.

Alta.02 distingue a recuperação figurada na expressão “recebeu alta, saiu da UTI” de alta.01, subida de preço. Uma ocorrência mantém ID, texto, REL, spans e sintaxe, passando a alta.02. Carteira.01 tem sua referência corrigida de portfolio.04, inexistente, para portfolio.01. Nenhum nome ou ocorrência foi acrescentado.

A origem dos papéis, a base contextual e o motivo da criação estão em cada ficha e no JSON. Dicionários foram consultados apenas para confirmar o domínio lexical de freio e vertigem. Eles não fornecem os inventários criados: a interpretação contextual e os papéis são decisões do projeto.

A vista efetiva fica em data/provenance/v28. Os registros registro documental e seus snapshots de origem conservam a evidência histórica. As 36.983 marcações preservam valores e IDs, com ponteiros atualizados para os JSONs atuais e referências históricas disponíveis para comparação. Definições novas não são apresentadas como intenção original recuperada de anotadores.

Há 2.079 registros de definição de papel: 1.821 descrições semânticas e 258 campos vazios de preenchimento. O número de papéis descritos não afirma realização obrigatória em todas as ocorrências. Não foram acrescentados spans ou relações sintáticas; a revalidação independente de todos os bindings semânticos antigos é um escopo distinto da cobertura de inventários aqui verificada.

A correção científica foi solicitada explicitamente pelo usuário após identificar os vazios da publicação V27. Sua autoridade de release é USER_DIRECTED_LOCAL_ROLESET_CORRECTION_20261004_V28, com base histórica registro documental. Não se declara um novo ACK do orquestrador.
