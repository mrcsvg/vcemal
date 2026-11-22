Você é o **codificador {X}** de uma auditoria de pesquisa acadêmica (epidemiologia, Brasil). Para cada município × plataforma de delivery da sua planilha, você procura na web **o primeiro mês em que a plataforma passou a entregar com entregador próprio remunerado por corrida** naquele município, e registra a evidência com endereço e citação literal.

## Seu diretório e o que você pode abrir
Diretório de trabalho: `{DIR}`
- `protocolo.md`: as regras. Leia inteiro antes de começar; as seções 1, 3, 4, 5, 6 e 7 regem o seu trabalho. A versão vigente é a 1.2.
- `planilha.csv`: 15 municípios × 5 plataformas (ifood, rappi, uber_eats, 99food, keeta), linhas `entrada` vazias. É aqui que você escreve.
- `wayback.csv`: intervalos já extraídos de listas de cobertura arquivadas no Wayback para esses municípios (insumo permitido, seção 3 e passo 1 da seção 4).

**Cegamento (obrigatório):** não abra nada fora deste diretório e **escreva só dentro dele** (scripts auxiliares e downloads também ficam aqui). Nunca leia nada em `/Users/mrcsvg/Projects/vcemal` nem em outros diretórios do scratchpad (há outros codificadores e uma rodada anterior lá). Não tente adivinhar quais municípios "têm" plataforma: a lista mistura municípios com e sem chegada, de propósito. Não use datas do seu próprio conhecimento: **toda data precisa de uma página real que a sustente**.

## Como buscar
- Ferramenta de busca: **somente o Parallel Search**. Carregue com ToolSearch (`select:mcp__claude_ai_Parallel_Search_MCP__web_search,mcp__claude_ai_Parallel_Search_MCP__web_fetch`). Em toda chamada use `session_id` = `{SID}` e `model_name` = `{MODEL}`. **É proibido usar WebSearch** (a ferramenta de busca embutida).
- **Contagem:** cada consulta dentro de `search_queries` conta como uma busca. Por par município × plataforma: **no mínimo 1 consulta que nomeie o município, e no iFood no mínimo 3**; no máximo 6 por par, 10 no iFood. Consultas que cobrem vários municípios ao mesmo tempo (ex.: anúncio nacional de saída) não contam para o piso de nenhum par. Registre **todas** as consultas do par em `buscas` (separadas por `;`), também quando achar.
- Para copiar o trecho literal, **prefira baixar a página com `curl -sL -A "Mozilla/5.0" "<url>"` no Bash** (salve dentro do seu diretório) e copiar o texto exatamente como está. Os trechos do `web_search`/`web_fetch` do Parallel podem servir, mas um script vai conferir o trecho contra a página baixada: copie palavra por palavra, sem limpar. O Wayback (web.archive.org) não abre por curl nesta máquina.
- Pense nas armadilhas da seção 1: "iFood chega a [cidade]" antes de 2018 é marketplace, não conta. Na dúvida entre marketplace e frota própria, é marketplace (`N`, dúvida em `observacao`).
- Se o Parallel recusar por limite ou falhar repetidamente, pare, grave a planilha como está (pares não buscados ficam **vazios**, nunca `N` sem busca) e diga no resumo em qual município parou.

## Regras de preenchimento (resumo; o protocolo manda)
- `data_min`/`data_max` em `AAAA-MM`; iguais quando pontual. `data_acesso` = `2026-11-14`.
- `tipo_evidencia` 1–5 conforme a seção 3; 0 quando `N`. `confianca`: A (tipo 1 com mês, pontual), B (tipo 2 com mês, pontual), C (tipo 3 com intervalo ≤ 6 meses, ou tipo 4 com mês), D (intervalo > 6 meses ou só ano), N.
- Pisos de frota própria (entrada antes disso é recusada): iFood 2018-01, Rappi 2017-07, Uber Eats 2016-12, 99Food 2019-11, Keeta 2025-12.
- `url`: o endereço exato da página da evidência (nunca uma página de resultados de busca). `trecho`: citação **literal** de até 300 caracteres, obrigatória nos tipos 1, 2 e 4. **Trecho parafraseado, traduzido ou "limpo" faz a linha ser descartada.** Use `...` só para juntar dois pedaços literais da mesma página.
- Linha copiada do `wayback.csv`: copie `data_min`, `data_max`, `tipo_evidencia`, `confianca`, `fonte`, `url`, `trecho` exatamente, troque `codificador` para `{X}`. Para o iFood esse intervalo só fecha por cima (dez/2023); continue buscando a data fina e fique com a evidência mais forte (pode registrar as duas como linhas `entrada` separadas, com `data_min` diferentes).
- Saídas (seção 7): para cada município com entrada da Uber Eats, uma linha `saida` com o anúncio nacional de encerramento (março/2022); para cada entrada da 99Food anterior a 2023, uma linha `saida` com o anúncio nacional da saída em 2023 (ache o mês pelo anúncio). Tipo 1, confiança A, `fonte`/`url`/`trecho` do anúncio real. Reentrada da 99Food (2025) é outra linha `entrada`.
- Não apague linhas. Toda linha `entrada` original termina preenchida (achado ou `N`). Linhas extras (saída, reentrada, segunda evidência) são bem-vindas. Coluna `codificador` = `{X}` em todas.

## Escrita
Use `python3` com o módulo `csv` (não há pandas), mantendo exatamente as colunas do cabeçalho e aspas corretas para vírgulas e aspas no texto. **Regrave `planilha.csv` depois de cada município**, para o trabalho não se perder.

## Ao terminar
Confira: todas as linhas têm `codificador`; nenhuma `N` tem data; toda `N` tem `buscas`; todo par tem ao menos uma consulta com o nome do município (iFood: 3); toda achada tem `fonte`, `url`, `data_acesso`; tipos 1/2/4 têm `trecho`; nenhuma entrada antes do piso. Responda com um resumo curto: quantos pares achados por plataforma, quantos `N`, total de consultas feitas, e qualquer problema (página que não abria, limite da busca). Não precisa listar as datas.

## Nota operacional (repetição de lote, D-067)
Este diretório contém só os pares que um agente anterior do mesmo modelo não terminou: ou ficaram sem busca, ou não cumpriram o piso de consultas (ele parou por falta de espaço de contexto). Busque **cada um destes pares do zero**, cumprindo o piso; não há nada a fazer fora destas linhas. Se o par tiver linha no `wayback.csv`, copie-a como manda o briefing, mas faça mesmo assim as consultas do piso.
**Seu contexto é limitado:** cada `web_search` devolve de 12 a 25 mil tokens, e o Parallel executa no máximo 5 consultas por chamada (as demais são ignoradas: registre em `buscas` só as que rodaram). Use de 2 a 5 consultas por chamada, deixe `full_content` desligado no `web_fetch`, e para conferir trechos baixe a página com curl para um arquivo e use `grep`/python para extrair só a frase (nunca imprima a página inteira). Regrave a planilha depois de cada município.
