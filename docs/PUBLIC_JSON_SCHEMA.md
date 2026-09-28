# Formato dos dados

Cada arquivo JSON corresponde a um lema do NounBank.DS Expanded.

A estrutura pública foi concebida para manter compatibilidade com o NounBank.DS original e representar, de forma legível por máquina:

- o lema;
- os rolesets associados;
- o mapeamento para o NomBank em inglês, quando disponível;
- os papéis semânticos (Arg0, Arg1, ...);
- os exemplos do DANTEStocks;
- a realização textual dos argumentos;
- as relações sintáticas observadas segundo a Universal Dependencies;
- a distinção contextual entre usos predicadores e não predicadores.

Nos 145 lemas herdados, os dados da versão original são preservados.
