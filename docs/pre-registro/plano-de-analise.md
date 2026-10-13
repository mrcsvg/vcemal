# Plano de análise — pré-registro

> **Pronto para depósito (2026-10-13).** Nenhuma seção `[ ]` em aberto; o texto do
> formulário do OSF está em `deposito-osf.md`, e a tradução para o inglês deste
> plano em `plano-de-analise.en.md`. Em divergência entre os dois, vale este. Depois do depósito, este arquivo fica
> congelado — qualquer mudança vai para `docs/decisoes.md` como análise exploratória
> declarada.

## 1. Pergunta e hipóteses

- **H1** — a entrada de plataforma de entrega em um município eleva a incidência
  de internações de motociclistas por acidente de transporte.
- **H2** — o efeito é crescente na intensidade de operação. `[x]` **Parcialmente
  identificada**: volume de pedidos por município é dado privado. **Proxy
  (D-043):** aberturas de MEI 5320-2/02 por mil habitantes (Censo 2022) nos 12
  meses a partir da quebra, em tercis entre os tratados da janela balanceada; o
  estimando principal (seção 5) é estimado por tercil. **Previsão:** efeito
  monotonicamente crescente do primeiro ao terceiro tercil. **Sinal do viés:** o
  MEI cobre a minoria dos entregadores (D-031), então a proxy mede intensidade com
  erro, e erro de classificação entre tercis achata o gradiente — o teste é
  conservador. Ausência de gradiente não refuta H2; gradiente presente a sustenta.
- **H3** — o efeito se concentra no **perfil demográfico do trabalho de entrega**:
  homens de 18 a 39 anos. Se o efeito for de magnitude semelhante fora desse
  perfil, o desenho está captando tendência geral de trânsito *dentro* do grupo
  motociclista, e não plataformização.
  **Ortogonal ao placebo:** o placebo (V40–V49) testa se é tendência geral
  **entre** tipos de veículo; H3 testa se é tendência geral **dentro** de
  motociclista. Os dois podem falhar independentemente.
  **Operacionalização:** `homem_18_39` contra o complemento
  (`internacoes − homem_18_39`), ambos no painel.
  **Secundária, com poder declaradamente baixo:** o mesmo teste restrito a
  condutor (`condutor_homem_18_39`). O quarto dígito `.4` é só **9,4%** das
  internações de motociclista — `.9`, não especificado, é 69,5% —, então o
  recorte sobra com ~5% do desfecho. Pior que a perda de poder: **quem codifica
  `.4` em vez de `.9` varia por hospital e por UF**, e essa prática tende a
  acompanhar urbanização, que é o que determina a entrada da plataforma. É
  confundimento potencial, não só ruído. Reportar, não interpretar isolado.
- **H4** (descritiva, fora do desenho causal) — o nexo ocupacional é
  sistematicamente subregistrado no SIH **e no SIM**. **Operacionalização
  (D-044):** por ano e por UF, entre internações (SIH) e óbitos (SIM) de
  motociclistas em trânsito de homens de 18 a 39 anos, a fração com nexo de
  trabalho registrado — no SIH, `CAR_INT` 03 ou 04 (acidente no trabalho ou no
  trajeto, coluna `nexo_ocupacional`) sobre os registros com `CAR_INT`
  preenchido; no SIM, `ACIDTRAB = 1` sobre os registros com `ACIDTRAB`
  preenchido. O preenchimento de cada campo é reportado ao lado. Sem teste: a
  fração é descrita ao lado da participação de entregadores entre os
  motociclistas ocupados na PNAD (D-031), como ordem de grandeza, não como
  estimativa do subregistro.
- **H5** (secundária, D-044) — o efeito aparece também nas **mortes** de
  motociclistas, que o SIH vê só em parte: o SIH registra o óbito de quem foi
  internado no SUS (`obitos`), não o de quem morre na via, em casa ou em
  hospital privado. **Fonte:** SIM, causa básica V20–V29 em trânsito (mesma
  regra de quarto dígito, `src/vcemal/cid.py`), por município de residência e
  mês do óbito. Dois desfechos, ambos por 100 mil motos e com o estimando
  principal da seção 5:
  - **H5a — mortes totais.** **Previsão:** efeito positivo.
  - **H5b — mortes fora de estabelecimento de saúde** (`LOCOCOR` diferente de
    hospital e de outro estabelecimento de saúde; ignorado não conta como fora):
    quem morre sem chegar a ser internado e por isso nunca entra no SIH.
    **Previsão:** efeito positivo. Efeito em H5b é dano que o desfecho
    principal não vê por construção — mais uma razão para ler H1 como piso, ao
    lado das três da seção 6.

  **Critério:** cada uma é sustentada se o estimando for positivo e o intervalo
  de 95% excluir zero. **Poder declaradamente baixo:** abaixo de 100 mil
  habitantes, morte de motociclista por município e mês é contagem pequena, com
  muitos zeros. Ausência de efeito não refuta H5 e não pesa contra H1.
  **Versão do SIM:** a disponível na extração, registrada com data; ano ainda
  preliminar é marcado, e a robustez repete H5 só com as coortes cuja janela
  termina no último ano definitivo.

## 2. Dados

Ver `docs/anexo-a-inventario-fontes-de-dados.md`. Fontes da estimação principal:
SIH/SUS (desfecho), RENAVAM (denominador), IBGE (população), dados abertos do
CNPJ (tratamento: quebra nas aberturas de MEI de entrega — ver seção 4). Para
H4 e H5, o SIM (declarações de óbito). **O SIM ainda não foi extraído** na data
do depósito: entra depois, pelo mesmo caminho do SIH, e nunca foi cruzado com o
tratamento (D-044).

## 3. Definição de caso

| Grupo | CID-10 | Papel |
|---|---|---|
| Motociclista | V20–V29 **em trânsito** (`internacoes_transito`) | Desfecho |
| Ciclista | V10–V19 | Teste do mecanismo |
| Ocupante de automóvel | V40–V49 | Placebo |
| Motociclista, óbito | V20–V29 em trânsito como causa básica no SIM | Desfecho secundário (H5) |

**A taxa do desfecho é calculada na estimação**, como 100.000 ×
`internacoes_transito` / `frota_moto`. A coluna `taxa_por_frota` do painel usa
`internacoes`, que inclui as de não-trânsito, e não é o desfecho.

A leitura do quarto dígito não é uniforme entre as categorias: V19, V29 e V49
usam outra tabela, em que `.3` é acidente **não** de trânsito. A regra está em
`src/vcemal/cid.py` e a justificativa em D-010 (`docs/decisoes.md`).

**O desfecho não é restrito a condutor.** Uma versão anterior desta tabela dizia
"quarto dígito de condutor em trânsito", o que restringiria o desfecho principal
a `.4` — **9,4%** das internações de motociclista, porque `.9` (não especificado)
é 69,5%. Além de descartar nove décimos dos casos, condicionar em `.4` condiciona
numa prática de codificação que varia por hospital e por UF e tende a acompanhar
urbanização — o mesmo fator que determina a entrada da plataforma. Condutor entra
como recorte secundário declarado (ver H3), nunca como desfecho principal.

## 4. Construção do tratamento

**O evento é a chegada do entregador remunerado por corrida, não a do aplicativo.**
O iFood operou como marketplace de 2011 a 2017 — pedido pelo app, entrega pelo
motoboy do restaurante — e só passou a entregar com frota própria em 2018.
Remuneração por corrida, que é a hipótese do projeto, só existe a partir daí.
Ver D-020.

`[x]` **Fonte: a quebra nas aberturas de MEI de entrega (D-040).** Por município
de residência e mês, as aberturas de estabelecimento-matriz com CNAE principal
5320-2/02 nos dados abertos do CNPJ (publicação de set/2026, com os CNPJs
baixados). O tratamento é o mês da **quebra**: o primeiro mês candidato `t`, de
2017-01 a 2025-06, em que as aberturas de `[t, t+5]` são ao menos 5, ao menos o
dobro da linha de base dos 24 meses anteriores e improváveis sob ela
(Poisson, p < 0,01); a quebra é o primeiro mês da janela com abertura. Regra e
parâmetros em `vcemal.mei`, escolhidos só contra placebo de 2016 e contra o
Wayback, nunca contra internação. O que se mede é a chegada de oferta de
entregador formalizado — usa-se a data da quebra, não o nível, porque o MEI cobre
a minoria dos entregadores (D-031).

`[x]` **Arquivo congelado.** `docs/fontes/cronologia/tratamento_mei_municipio.csv`,
SHA-256 `128999bd21de00854c717e181657f5d1832ce78222ec9ef6dd99a3bd8a7654a2`,
gerado por `make mei` antes de qualquer cruzamento com o SIH (D-006, D-041).
Depois do depósito, nenhuma data muda.

**Grupos, por município do universo (1.710 com 20 mil habitantes ou mais):**

| Grupo | N | Regra | Papel |
|---|---|---|---|
| `datado` | 640 | abaixo de 100 mil habitantes, com quebra | tratados; `mes_tratamento` = mês da quebra. É daqui que vem a variação no tempo |
| `sem_quebra` | 751 | abaixo de 100 mil, sem quebra | não tratados até onde se vê — **não** "nunca tratados": pode haver plataforma com poucos entregadores MEI para o teste ver. Entram no grupo de comparação; robustez os exclui |
| `coorte_precoce` | 319 | 100 mil ou mais | fora da estimação principal. Todas tinham o app do iFood em 2019 (D-038, D-039); que a frota própria tenha chegado até 2018 é premissa, testada pelo estrato das capitais da auditoria. O placebo dispara em um quarto delas: a quebra não as data |

Municípios abaixo de 20 mil habitantes não entram: a regra não foi validada
neles.

**Riscos específicos desta fonte, e o que cada um aciona:**

- **Quebra espúria.** O placebo (quebra em jan–jun/2016, antes de qualquer
  plataforma) dispara em 0,7% dos municípios de 20–50 mil e em 3,8% dos de
  50–100 mil. A regra pega a *primeira* quebra: uma espúria precoce esconde a
  verdadeira. É o risco de **2017**: 83 quebras antes da frota própria do iFood
  (2018-01), num ano em que só Uber Eats e Rappi tinham frota, e só em capitais.
- **Contaminação tardia.** Depois de 2021 o CNAE vizinho 5320-2/01 explode com a
  entrega de comércio eletrônico; o 5320-2/02 pode ter o mesmo canal. Pesa nas
  quebras de **2021 a 2025**.
- **Não é a plataforma X.** A quebra data a chegada da oferta de entregador
  formalizado, de qualquer plataforma. Robustez por plataforma não existe nesta
  fonte.

`[x]` **Auditoria por busca independente, com consequência declarada antes
(D-041).** Uma amostra sorteada com semente fixa (`vcemal.auditoria`, semente
20261011) de 6 municípios `datado` por faixa de população (20–50 mil, 50–100
mil) em cada estrato de ano da quebra — `2017`, `2018-2020`, `2021-2025` —, 6
iscas `sem_quebra` por faixa e, obrigatoriamente, as 27 capitais: 75 municípios
misturados numa lista só (`docs/fontes/cronologia/auditoria_municipios.csv`). Dois codificadores buscam a
entrada das plataformas pelo protocolo `docs/protocolo-cronologia-entrada.md`,
versão 1.1, cegos ao SIH, à quebra e ao estrato — exceto que as 27 capitais são
reconhecíveis como tais e têm critério próprio; desempate por regra e
adjudicação como no protocolo.

- **Concordância:** a quebra cai no intervalo codificado `[data_min, data_max]`
  da entrada mais antiga, alargado 6 meses para cada lado. Nas capitais, que são
  `coorte_precoce` e não têm a quebra como data, o teste é a premissa da coorte:
  o intervalo codificado, alargado igual, começa até dez/2018. Município sem
  evidência encontrada (`N`) não conta contra nem a favor.
- **Veredito por estrato:** *passa* com ao menos 2/3 dos achados concordando;
  *falha* abaixo disso; *inconclusivo* com menos de 6 achados. O veredito é por
  estrato de ano; o resultado por faixa é reportado ao lado, sem veredito. Iscas
  são só descritas: a fração delas com plataforma encontrada é reportada.
- **Não encontrar é resultado previsto, não falha (D-045).** Em município
  pequeno a chegada de plataforma deixa pouco rastro, e muitos `N` são
  esperados. Por isso o critério é uma **taxa de coincidência** — concordantes
  sobre achados —, e não sobre a amostra sorteada. Por estrato de ano e por
  faixa são reportados três números: a **taxa de achado** (achados sobre
  sorteados), a **taxa de coincidência** (concordantes sobre achados), com
  intervalo de 95% de Wilson, e o veredito. A coincidência nos 36 `datado`
  juntos é reportada também, sem consequência.
  **Viés declarado:** os achados tendem a ser os municípios com mais rastro
  (maiores, quebras mais recentes), então a coincidência vale para eles e não
  necessariamente para os não achados. Estrato inconclusivo por falta de achados
  é dito **não auditado** — não aprovado.
- **Consequência, aplicada mecanicamente:**
  - `2017` falha → as quebras de 2017 saem da estimação principal (nem tratadas
    nem comparação) e voltam só como robustez;
  - `2021-2025` falha → idem para as quebras de 2021 em diante;
  - `2018-2020` falha → a quebra não data a chegada das plataformas onde ela
    mais importa. A estimação roda como declarada, mas o resultado é reportado
    como efeito da chegada de entregador formalizado, e a leitura "efeito da
    plataforma" é declarada não sustentada;
  - `capital` falha → a premissa "coorte precoce tratada até 2018" cai, e a
    robustez que usa a `coorte_precoce` como coorte de 2018 não é rodada;
  - inconclusivo → a regra fica como está, e o estrato é dito não auditado.
- **Robustez pré-declarada, qualquer que seja o veredito:** excluir as quebras
  anteriores a 2018-01 e, separadamente, as posteriores a 2020-12.

O plano é depositado **antes** da auditoria começar; o veredito só aplica a
consequência já escrita aqui. `make auditoria` consolida as planilhas e imprime o
veredito.

**A codificação município a município (protocolo 1.0, D-033) deixou de ser a
fonte do tratamento.** O risco que ela tinha — dois codificadores concordarem,
com kappa alto, sobre a chegada do *aplicativo* em vez da *frota* — continua
valendo dentro da auditoria, e é tratado pela seção 1 do protocolo.

**Saídas não são observáveis nesta fonte.** A quebra data entradas; a saída da
Uber Eats (março/2022) e da 99Food (2023) não aparece no CNPJ. O tratamento
reverso previsto na versão anterior deste plano sai da estimação: um município
que perdeu uma plataforma quase sempre ficou com outra, e a quebra não distingue
os dois casos. Desvio registrado em D-041.

## 5. Especificação

Diferenças em diferenças com adoção escalonada. Estimador de Callaway &
Sant'Anna (2021) como principal, dada a heterogeneidade de timing e a conhecida
inconsistência do TWFE nesse caso. Sun & Abraham como robustez.

**Estimando principal de H1 (D-043):** a média simples dos ATT(e) para
`e ∈ [0, +24]` na janela balanceada, sem covariáveis (tendências paralelas
incondicionais), reportada também em % da média pré-tratamento dos tratados
(`e ∈ [−12, −1]`).

**Critério de inferência (D-043):** teste bilateral a 5% e intervalo de 95%. H1
é sustentada se o estimando principal for positivo e o intervalo excluir zero.
H1 é a única hipótese confirmatória, sem correção para comparações múltiplas;
H2, H3, H5, o teste do mecanismo e os testes de falha da seção 6 são lidos pelos
critérios declarados em cada um, com intervalos de 95%.

- Unidade: município × mês
- Efeitos fixos: município e mês-calendário
- Grupo de comparação: **not-yet-treated** (D-022), entre os municípios
  `datado` e `sem_quebra` da seção 4. Os municípios abaixo de 20 mil habitantes
  não entram: são pequenos e rurais por construção, e compará-los aos tratados
  compararia urbanização, não plataforma — urbanização move motorização, tráfego
  e oferta hospitalar de uma vez. **Robustez:** só not-yet-treated `datado`, sem
  os `sem_quebra` (que podem ter plataforma que o MEI não viu). Divergência entre
  as duas é diagnóstico de contaminação do controle, não fracasso.
  **Reportar o tamanho do grupo de comparação por coorte**: a saturação encolhe
  o conjunto no fim da janela.
- Erros-padrão: **agrupados em região imediata do IBGE** (510 regiões, mediana
  de 9 municípios). Município entra como robustez.
  **Motivo:** o tratamento é atribuído em município, mas o entregador e o
  paciente circulam na região. O próprio dicionário do painel registra que
  `municipio_res` ≠ município do acidente e que em região metropolitana a
  divergência é material — o mesmo transbordamento que contamina a geografia do
  desfecho correlaciona os erros. Agrupar em município subestimaria o
  erro-padrão. Com 510 clusters a assintótica é confortável; wild cluster
  bootstrap fica reservado a estimativas por coorte com poucos clusters.
  **Efeito que só sobrevive com cluster em município não foi robusto** — a
  comparação entre os dois níveis entra na tabela principal, não em anexo.
- Janela de evento: **e ∈ [−12, +24] meses, balanceada** — só entram coortes
  com os 37 tempos de evento observados.
  **Quem cabe nela:** o denominador de frota começa em julho/2016 (D-015) e o
  painel do SIH termina em dezembro/2025, então a janela balanceada admite
  coortes de **2017-07 a 2023-12**: 478 dos 640 `datado`. Ficam fora 50 com
  quebra antes de 2017-07 e 112 com quebra depois de 2023-12.
  **Por que −12 e não mais:** com a quebra do MEI a coorte mais antiga é
  2017-01, não 2018-01 (como a versão anterior deste plano supunha). Alargar a
  janela para trás custa as coortes de 2017, que já são as de risco de quebra
  espúria (seção 4); estreitar para a frente custa as de 2024–2025, as de risco
  de contaminação. +24 meses é o efeito que interessa: remuneração por corrida
  age pela exposição acumulada.
  **Robustez:** versão não balanceada, usando todo período disponível por coorte,
  acompanhada da tabela de quais coortes contribuem em cada tempo de evento; e a
  contagem de internações (com efeito fixo de município) no lugar da taxa, que
  recupera as coortes anteriores a 2017-07 porque o SIH começa em 2015-01.

## 6. Testes pré-declarados de falha do desenho

1. Efeito sobre ocupante de automóvel indistinguível do efeito sobre motociclista
   → desenho captura tendência geral de trânsito.
2. Pré-tendências não paralelas na janela pré-tratamento → reportar e não
   interpretar causalmente.
3. **Denominador endógeno.** Rodar o mesmo estimador com `frota_moto` **como
   desfecho**. Se a entrada da plataforma eleva a frota de motos registradas —
   gente comprando moto para trabalhar —, numerador e denominador se movem
   juntos e a taxa deixa de medir risco.
   **Critério pré-declarado de falha:** se o efeito sobre `frota_moto` for
   estatisticamente distinguível de zero **e** sua variação percentual for de
   ordem comparável à das internações — **ao menos metade do efeito percentual
   sobre as internações** (D-043) —, a taxa não é interpretável. Nesse caso o
   resultado principal passa a ser a **contagem** de internações com efeito fixo
   de município, e a taxa vai para o anexo com a advertência.
   **O viés é signável, e isso importa:** frota subindo com o tratamento *atenua*
   a taxa. Se o teste falhar nessa direção, a estimativa por taxa é piso — o que
   soma às duas outras razões de piso já declaradas (D-001, diluição no universo
   de motociclistas; D-021, contaminação do pré-período pelo marketplace). As
   três precisam aparecer separadas.
   **É o único dos riscos levantados que destrói o estimando em vez de apenas
   enviesá-lo** — por isso é ele que vira teste pré-declarado, e não a
   antecipação ou o transbordamento, que continuam como robustez na seção 7.

## 7. Análises exploratórias (declaradas como tais)

- Deslocamento da distribuição horária dos sinistros de moto no RENAEST para as
  faixas de pico de entrega, condicional à existência do campo de hora.
- Preenchimento do `CAR_INT` por ano e por município.
- **Transbordamento para o controle.** Reestimar excluindo os *not-yet-treated*
  na mesma região imediata de algum município já tratado. Se o efeito cresce, o
  principal estava atenuado por contaminação do controle — provável, dado que
  `municipio_res` não é o município do acidente.
- **Antecipação.** Coeficientes em `e = −1, −2, −3`. Mais afiado que o teste 2
  de pré-tendências, e em boa parte redundante com ele; roda como leitura do
  mesmo gráfico de estudo de evento, não como teste separado.
- **Mudança de codificação coincidente.** Série nacional da fração de AIH com
  código V em qualquer `DIAGSEC` e da composição de `campo_causa`. Uma
  descontinuidade perto de 2018 confundiria desfecho com medida. Barato — uma
  consulta — e a ferramenta já existe em `vcemal.extract.bigquery`.

## 8. Desvios

Qualquer desvio deste plano vai para `docs/decisoes.md` com data e motivo.
