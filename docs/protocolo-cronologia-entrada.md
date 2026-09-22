# Protocolo de codificação — cronologia de entrada das plataformas (F3)

**Versão 1.0 · 2026-09-20 · estado: aguardando piloto.** Este documento é
congelado antes da primeira linha codificada. Toda mudança depois disso vira
versão nova, com a data e o motivo registrados na seção 14, e a concordância
é recalculada a partir do bloco em que a mudança entrou. As regras
verificáveis daqui vivem em `src/vcemal/cronologia.py` e são testadas sem dado;
onde o texto e o código divergirem, o código é o que vale e o texto está errado.

## 0. Em uma frase

Para cada município do universo e cada plataforma, dois codificadores procuram,
sem se falar e sem olhar o SIH, **o primeiro mês em que a plataforma passou a
entregar com entregador próprio remunerado por corrida** naquele município, e
registram a evidência com endereço; o que os dois concordam entra, o que
discordam é resolvido por regra escrita antes, e o que sobra vai para um
terceiro, com justificativa gravada.

## 1. O que é o evento, e o que não é

O tratamento do V2 é **remuneração por corrida**, e ela só existe quando a
plataforma opera frota própria (D-020). O iFood foi marketplace de 2011 a 2017:
pedido pelo aplicativo, entrega pelo motoboy do restaurante. Isso **não é
tratamento**, e é exatamente o que a imprensa local noticia como "iFood chega a
[cidade]". Dois codificadores podem concordar, com kappa alto, sobre o evento
errado. Por isso a regra é explícita, e a validação recusa qualquer entrada do
iFood anterior a janeiro/2018.

| Conta como entrada (frota própria) | Não conta (marketplace ou irrelevante) |
|---|---|
| "entregadores parceiros do iFood começam a operar", "Entrega iFood", "modalidade nuvem/OL" no município | "restaurante X agora está no iFood", "o app chega a [cidade]" sem menção a entregador da plataforma |
| abertura de cadastro de entregadores **para aquele município** na página da plataforma | "entrega própria" **do restaurante** pelo app |
| release, blog ou rede social da plataforma anunciando operação logística na cidade | notícia sobre o **aplicativo de mobilidade** (99, Uber) sem o serviço de comida |
| Rappi, Uber Eats, 99Food e Keeta em qualquer modalidade: essas plataformas sempre operaram com entregador próprio | aiqfome, Delivery Much e similares: marketplace, entrega do restaurante — fora do escopo |
| relato de entregador com data ("comecei a rodar de iFood aqui em agosto de 2019") só como evidência tipo 4, confiança C | Loggi, Lalamove, Zé Delivery: logística B2B ou bebidas — fora do escopo |

**Quando houver dúvida entre marketplace e frota própria, é marketplace.** A
dúvida vai para `observacao`, a linha fica como `N` com as buscas registradas, e
o município reaparece no próximo bloco de revisão se surgir evidência melhor.

## 2. Unidade, universo e escopo

- **Unidade:** município (código IBGE de 7 dígitos) × plataforma × evento
  (`entrada` ou `saida`). Reentrada (99Food em 2025) é uma segunda linha de
  `entrada`, com a `saida` entre as duas.
- **Universo:** os **1.710 municípios com 20 mil habitantes ou mais no Censo
  2022** (`docs/fontes/cronologia/universo.csv`, gerado por
  `scripts/cronologia.py universo`). O iFood atendia 1.638 cidades em março/2026
  (D-032): o corte cobre o rollout inteiro com folga. Municípios menores que
  aparecerem em evidência encontrada de passagem entram como linha extra, com
  `observacao = "fora do universo"`; todos os outros são nunca tratados **por
  hipótese declarada**, não por codificação.
- **Plataformas:** iFood, Rappi, Uber Eats, 99Food, Keeta. As datas-piso
  nacionais e as saídas nacionais estão em `vcemal.cronologia.PLATAFORMAS`.
  James Delivery (GPA, frota própria, encerrada em 2022) é candidata a entrar
  depois do piloto; decidir na versão 1.1.
- **Período:** janeiro/2016 a setembro/2026.
- **Ordem de trabalho:** a planilha sai de `scripts/cronologia.py planilha` em
  ordem **sorteada com semente fixa**, a mesma para os dois codificadores. O
  trabalho anda em **blocos de 100 municípios** na ordem da planilha, e a
  concordância é calculada ao fim de cada bloco. Isso evita que os dois
  codifiquem capitais primeiro e treinem só no caso fácil.

## 3. Fontes e hierarquia

Do mais forte para o mais fraco. O número é o `tipo_evidencia` da planilha.

| Tipo | O que é | O que prova | Armadilha |
|---|---|---|---|
| 1 | Declaração da plataforma com data: release, blog, post oficial, página de cobertura com data visível | Entrada com mês | "Chegada a [cidade]" antes de 2018 no iFood é marketplace |
| 2 | Imprensa com data e **menção explícita a entregadores da plataforma** | Entrada com mês | Matéria sobre o app, não sobre a frota, é tipo 0 |
| 3 | Snapshots do Wayback Machine da página de cobertura ou de cadastro de entregadores: último snapshot sem a cidade, primeiro com | **Intervalo** `[data_min, data_max]` | Snapshot esparso vira intervalo longo (confiança D); página que carrega a lista por JavaScript pode não ser arquivada |
| 4 | Rede social da plataforma ou grupo de entregadores, com data do post | Entrada com mês, mas testemunho | Post de recrutamento pode anteceder a operação em semanas |
| 5 | Registro administrativo: prefeitura, alvará, filial no CNPJ, junta comercial | Presença institucional, não operação | Filial pode ser escritório; usar só para bordar intervalo |

**Método a testar no piloto, antes de tudo:** a página de cadastro de
entregadores do iFood (`entregador.ifood.com.br`) e as páginas de "cidades
atendidas" das demais plataformas listam os municípios em que a operação
própria recruta. Se o Wayback guardou a lista ao longo dos anos, a série de
snapshots data a entrada de centenas de municípios de uma vez, como intervalo
(tipo 3). Esse é o caminho escalável; a busca município a município (tipos 1, 2
e 4) serve para **apertar o intervalo** e para os municípios que a lista não
resolve.

## 4. Roteiro de busca

Por município e plataforma, nesta ordem, com **limite de 15 minutos** por
par (anotar em `observacao` se estourou):

1. Lista de cobertura da plataforma nos snapshots já baixados (seção 3).
2. Busca na web, entre aspas, registrando cada consulta em `buscas` quando o
   resultado for `N`:
   - `"iFood" "entregadores" "<município>"`
   - `"entrega iFood" "<município>"` · `"iFood" "cadastro" entregador "<município>"`
   - `"Rappi" chega "<município>"` · `"Uber Eats" "<município>"` · `"99Food" "<município>"` · `"Keeta" "<município>"`
   - o mesmo em portais locais (`site:` do jornal da cidade, quando houver)
3. Redes sociais da plataforma e grupos locais de entregadores (tipo 4).
4. Se nada: `confianca = N`, `tipo_evidencia = 0`, `buscas` preenchido.

**Nunca:** abrir o painel do SIH ou qualquer tabela de internação; consultar o
outro codificador; usar a planilha do outro; "corrigir" uma linha depois de
ver a comparação do bloco (a correção é feita na adjudicação, com registro).

## 5. Campos da planilha

`docs/fontes/cronologia/modelo.csv` tem três linhas de exemplo (uma A, uma C,
uma N) que devem ser apagadas antes de começar.

| Campo | Regra |
|---|---|
| `municipio_ibge`, `uf`, `municipio` | Do universo; não editar |
| `plataforma` | `ifood`, `rappi`, `uber_eats`, `99food`, `keeta` |
| `evento` | `entrada` ou `saida` |
| `data_min`, `data_max` | `AAAA-MM`. Iguais quando a data é pontual. Vazias quando `N` |
| `tipo_evidencia` | 1 a 5 (seção 3); 0 quando `N` |
| `confianca` | A, B, C, D ou N (seção 6) |
| `fonte` | Nome legível: veículo e data, ou "Wayback: <página>, snapshots <data> e <data>" |
| `url` | Endereço exato. Para Wayback, a URL com timestamp do snapshot decisivo |
| `data_acesso` | `AAAA-MM-DD` |
| `trecho` | Citação literal de até 300 caracteres que sustenta a data. Obrigatório em tipos 1, 2 e 4 |
| `buscas` | Consultas feitas, separadas por `;`. Obrigatório em `N` |
| `observacao` | Dúvida marketplace × frota, tempo estourado, fora do universo |
| `codificador` | A ou B |

## 6. Graus de confiança

| Grau | Quando | Intervalo admitido |
|---|---|---|
| **A** | Tipo 1 com mês | pontual |
| **B** | Tipo 2 com mês, ou tipo 1 sem dia mas com mês inequívoco | pontual |
| **C** | Tipo 3 com intervalo de até 6 meses; tipo 4 com mês | até 6 meses |
| **D** | Tipo 3 ou 5 com intervalo maior que 6 meses, ou só o ano | qualquer |
| **N** | Procurado e não encontrado, com `buscas` registrado | — |

A validação (`scripts/cronologia.py validar`) recusa grau incompatível com a
largura do intervalo, data antes da frota própria nacional da plataforma, `N`
sem buscas e linha sem `url`.

## 7. Saídas

- **Saída nacional** (Uber Eats, março/2022; 99Food, 2023 — mês a codificar
  uma vez, a partir do anúncio nacional, e aplicado a todos os municípios com
  entrada): o codificador registra uma linha de `saida` por município com
  entrada, `tipo_evidencia = 1`, `fonte` = o anúncio nacional. Evidência local
  de saída **anterior** substitui a nacional, com a fonte local.
- **Saída local** (plataforma encerra a operação só naquele município): mesma
  regra de evidência da entrada.
- Saída só interessa ao V2 quando deixa o município **sem nenhuma** plataforma
  com frota própria (`mes_saida_total` na tabela de tratamento): é tratamento
  reverso, raro e valioso, e por isso codificado, não ignorado.

## 8. Concordância

Ao fim de cada bloco, `scripts/cronologia.py comparar A.csv B.csv` calcula:

- **kappa de Cohen** sobre "encontrou / não encontrou" por município × plataforma;
- **% de datas concordantes** entre os pares em que os dois encontraram:
  concordante quando as datas distam no máximo **1 mês** ou os intervalos se
  cruzam;
- a lista de discordâncias com o motivo (`existencia` ou `data`).

**Piloto:** o primeiro bloco tem 60 municípios (os 30 primeiros da planilha
com 100 mil habitantes ou mais e os 30 primeiros entre 20 e 50 mil). Segue
para o bloco 2 só com **kappa ≥ 0,70 e ≥ 80% de datas concordantes**. Abaixo
disso, os dois codificadores e o adjudicador revisam as discordâncias juntos,
o protocolo sobe de versão com a regra que faltava, e o piloto é refeito com
outros 60 municípios. Kappa alto não protege contra viés comum (seção 1): o
adjudicador relê, no piloto, **todas** as linhas A e B do iFood datadas antes
de julho/2018, que é onde o marketplace mais se disfarça de frota.

## 9. Desempate

Regras aplicadas por `scripts/cronologia.py consolidar`, nesta ordem, sem
exceção e sem média de datas (D-033):

| Regra | Situação | Resultado |
|---|---|---|
| **R1** | Os dois encontraram e concordam | Fica o registro de maior confiança; empate, o de data mais antiga |
| **R1** | Nenhum encontrou | `N` |
| **R2** | Um encontrou, o outro não | Vale o achado se for **A ou B**. Se for C ou D, vai para adjudicação |
| **R3** | Os dois encontraram e discordam | Maior confiança vence. Empate em A/B: adjudicação. Empate em C/D: **união dos intervalos**, confiança D |
| **R0** | Linha em `desempates.csv` | Vence qualquer regra acima |

**Adjudicação:** um terceiro codificador, também cego ao SIH, vê os dois
registros e procura evidência nova por até 30 minutos. Escreve em
`desempates.csv`: `escolha` (`a`, `b`, `propria` com datas e grau novos, ou
`nenhum`), `justificativa` (uma frase com a fonte) e `adjudicador`. O arquivo
é versionado: cada decisão fica auditável no diff. `pendentes.csv` lista o que
ainda falta; a cronologia só está fechada quando ele fica vazio.

## 10. Do consolidado ao tratamento

`tratamento_municipio.csv`, uma linha por município do universo:

- `mes_tratamento` = `data_max` da entrada mais antiga de qualquer plataforma:
  **o primeiro mês em que se tem certeza de frota própria operando**. Escolha
  conservadora: erra para depois, nunca para antes, então contamina o "antes"
  em vez de inventar um "depois".
- `incerteza_meses` = largura do intervalo dessa entrada. A análise principal
  usa todos; a robustez pré-declarada exclui `incerteza_meses > 3`.
- `plataformas` presentes e `mes_saida_total` (seção 7).
- Municípios fora do universo são nunca tratados por hipótese (seção 2).

Robustez por plataforma (só iFood) sai do mesmo consolidado filtrando
`plataforma`.

## 11. Validação externa, antes de fechar

- `scripts/cronologia.py prosus` conta os municípios com entrada do iFood até
  março de cada ano fiscal e põe ao lado das cidades que a Prosus publica
  (D-032: 500, 975, 1.258, 1.780, 1.486, 1.530, 1.581, 1.638). Codificado
  **acima** da Prosus é erro certo; muito abaixo é cobertura incompleta.
- 99Food: 59 cidades em janeiro/2022 (D-020).
- Marcos nacionais de `vcemal.cronologia.PLATAFORMAS` batem com a entrada mais
  antiga codificada de cada plataforma.

## 12. Cegamento e pré-registro

Ninguém que codifica ou adjudica abre o SIH, o painel ou qualquer tabela de
internação até a cronologia estar fechada. A cronologia fechada
(`cronologia_entrada.csv` e `tratamento_municipio.csv`) é copiada para
`docs/fontes/cronologia/`, versionada, e seu hash entra no depósito do plano
de análise (D-006). Depois do depósito, nenhuma data muda: correção vira
análise exploratória declarada em `docs/decisoes.md`.

## 13. Arquivos e comandos

```
docs/fontes/cronologia/universo.csv          1.710 municípios (gerado, versionado)
docs/fontes/cronologia/modelo.csv            três linhas de exemplo
docs/fontes/cronologia/desempates_modelo.csv uma decisão de exemplo
docs/fontes/cronologia/codificador_a.csv     planilha do codificador A (planilha --codificador A)
docs/fontes/cronologia/codificador_b.csv     planilha do codificador B
docs/fontes/cronologia/desempates.csv        decisões do adjudicador
output/tabelas/cronologia_entrada.csv        consolidado (make cronologia)
output/tabelas/tratamento_municipio.csv      tratamento do V2
output/tabelas/pendentes.csv                 o que ainda exige adjudicação
```

```bash
python scripts/cronologia.py universo                  # uma vez; usa a API do IBGE
python scripts/cronologia.py planilha --codificador A  # e B
python scripts/cronologia.py validar docs/fontes/cronologia/codificador_a.csv
python scripts/cronologia.py comparar docs/fontes/cronologia/codificador_a.csv docs/fontes/cronologia/codificador_b.csv
make cronologia                                        # consolida, escreve pendentes
python scripts/cronologia.py prosus output/tabelas/cronologia_entrada.csv
```

**Esforço estimado.** 8.550 pares município × plataforma por codificador. Se
as listas de cobertura arquivadas resolverem Rappi, Uber Eats, 99Food e Keeta
(poucas centenas de cidades cada) e derem o intervalo de partida do iFood, a
busca fina fica em torno de 1.700 pares de iFood: a 15 minutos cada, cerca de
430 horas por codificador, 8 a 11 semanas de uma pessoa. Sequência
recomendada: bloco piloto; depois os 657 municípios com 50 mil habitantes ou
mais (as coortes mais antigas e mais intensas, onde a evidência existe);
depois os 1.053 entre 20 e 50 mil, com o intervalo do Wayback como resposta
aceitável (C/D) quando a busca fina não render nada em 15 minutos.

## 14. Histórico de versões

| Versão | Data | Mudança |
|---|---|---|
| 1.0 | 2026-09-20 | Versão inicial, antes do piloto |
