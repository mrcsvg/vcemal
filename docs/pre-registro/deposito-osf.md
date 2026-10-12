# Texto para o depósito no OSF

> **Como usar.** Modelo: **OSF Preregistration** (OSF Registries → "Add new" →
> "OSF Preregistration"). Cada seção abaixo corresponde a um campo do formulário,
> na ordem dele; o texto é para colar. O documento normativo é o
> `plano-de-analise.md`, anexado ao depósito — este texto o resume e aponta para
> ele, e onde os dois divergirem vale o plano.
>
> **Antes de depositar**, falta só uma coisa: o hash do commit depositado, no
> campo Descrição (⚠️). As decisões que o formulário exigia e o plano não tinha
> estão no D-043 e já constam do plano.
>
> **Embargo:** o OSF permite até 4 anos. O timestamp vale do mesmo jeito.

---

## Título

Remuneração por corrida e internações de motociclistas no SUS: chegada de
entregadores de plataforma e incidência de internações em municípios
brasileiros, 2017–2025

## Descrição

Estudo observacional em painel município × mês. Estima o efeito da chegada de
entregadores remunerados por corrida (plataformas de entrega com frota própria)
sobre a incidência de internações de motociclistas por acidente de transporte
no SUS. O tratamento é datado pela quebra estrutural nas aberturas de MEI com
CNAE 5320-2/02 ("serviços de entrega rápida") no Cadastro Nacional da Pessoa
Jurídica, por regra congelada antes de qualquer cruzamento com o desfecho. O
desfecho vem do SIH/SUS (AIH reduzida), com denominador de frota de motocicletas
do Senatran. Estimador de diferenças em diferenças com adoção escalonada
(Callaway & Sant'Anna, 2021). Plano completo, protocolo de auditoria do
tratamento e log de decisões em anexo e no repositório
`github.com/mrcsvg/vcemal`, commit `⚠️ preencher com o hash do commit depositado`.

## Hipóteses

- **H1 (confirmatória).** A chegada de entregadores de plataforma a um município
  eleva a taxa de internações de motociclistas por acidente de transporte em
  trânsito (CID-10 V20–V29) por 100 mil motocicletas da frota. Direção prevista:
  positiva.
- **H2 (secundária).** O efeito cresce com a intensidade da operação. Volume de
  pedidos por município é dado privado; a proxy é o número de aberturas de MEI
  5320-2/02 por mil habitantes nos 12 meses a partir da quebra, em tercis entre
  os tratados da janela balanceada. Previsão: efeito monotonicamente crescente nos tercis. Viés
  declarado: o MEI cobre a minoria dos entregadores (D-031), então a proxy mede
  intensidade com erro, o que achata o gradiente — o teste é conservador.
- **H3 (teste do mecanismo).** O efeito se concentra em homens de 18 a 39 anos,
  o perfil do trabalho de entrega. Efeito de magnitude semelhante no complemento
  indica tendência geral de trânsito dentro do grupo motociclista, não
  plataformização.
- **H4 (descritiva, fora do desenho causal).** O nexo ocupacional é
  sistematicamente sub-registrado no SIH (campo `CAR_INT`).

## Design Plan

### Study type

Observational Study — dados administrativos secundários.

### Blinding

No blinding is involved in this study.

### Is there any additional blinding in this study?

Sim, na construção do tratamento. (1) A regra de quebra do MEI e seus
parâmetros foram escolhidos só contra um placebo pré-plataforma (jan–jun/2016) e
contra datas de entrada observadas no Wayback Machine (Rappi e Uber Eats), sem
consulta às internações; o arquivo de tratamento foi congelado com hash SHA-256
`128999bd21de00854c717e181657f5d1832ce78222ec9ef6dd99a3bd8a7654a2`. (2) Uma
auditoria por busca independente (75 municípios) é feita depois deste depósito
por dois codificadores cegos ao SIH, à data da quebra e ao grupo de cada
município (a lista inclui iscas sem quebra); a consequência de cada veredito
está declarada no plano antes da busca.

### Study design

Diferenças em diferenças com adoção escalonada. Unidade município × mês, de
jan/2015 a dez/2025 (taxa por frota a partir de jul/2016, início da série
municipal de frota). Tratamento absorvente: o município passa a tratado no mês
da quebra. Universo: os 1.710 municípios com 20 mil habitantes ou mais no Censo
2022, divididos em três grupos pela regra congelada:

- `datado` (640): abaixo de 100 mil habitantes, com quebra — os tratados, com
  `mes_tratamento` de 2017-01 a 2025-06;
- `sem_quebra` (751): abaixo de 100 mil, sem quebra — não tratados até onde o
  MEI vê; entram no grupo de comparação;
- `coorte_precoce` (319): 100 mil habitantes ou mais — fora da estimação
  principal (a quebra não os data: o placebo dispara em um quarto deles).

Grupo de comparação: not-yet-treated (incluindo `sem_quebra`). Janela de evento
`e ∈ [−12, +24]` meses, balanceada: entram as coortes de 2017-07 a 2023-12 (478
municípios). Detalhes e justificativas: seções 4 e 5 do plano.

### Randomization

No randomization. (A única aleatorização é o sorteio da amostra de auditoria do
tratamento, com semente fixa 20261011, já executado e versionado.)

## Sampling Plan

### Existing Data

Registration prior to analysis of the data.

### Explanation of existing data

Todos os dados existem e foram baixados. O que já foi feito com eles, e o que
não foi:

- **SIH (desfecho).** Baixado e agregado em painel município × mês. Foram feitas
  e publicadas no repositório análises **descritivas** nacionais e por UF: custo
  deflacionado das internações, lacuna entre SIH e benefícios do INSS,
  preenchimento do `CAR_INT`, série nacional ao lado do resultado do iFood.
  Nenhuma delas usa a cronologia de entrada.
- **CNPJ (tratamento).** Baixado e processado; regra de quebra aplicada e
  congelada. Validada contra placebo de 2016 e contra o Wayback, nunca contra o
  SIH (código e saídas em `scripts/mei.py`, decisão D-040).
- **Nunca feito:** nenhum cruzamento de tratamento com desfecho, em tabela,
  modelo ou gráfico exploratório (regra D-006, em vigor desde 12/09/2026). O
  script de estimação ainda não existe.

### Data collection procedures

Fontes públicas, reconstruídas pelo código do repositório (`Makefile`):

- SIH/SUS, AIH reduzida (RD), FTP do DATASUS via PySUS, com recuperação do FTP
  para competências ausentes do espelho (D-034 a D-036). Caso: código V20–V29
  em qualquer diagnóstico secundário ou principal, quarto dígito de trânsito
  pela tabela da categoria (D-010, D-017); município de residência.
- Frota: Senatran, frota municipal mensal, tipos que correspondem a V20–V29
  (D-013), desde jul/2016.
- População: IBGE (Censo 2022 para o universo; estimativas anuais como controle).
- Tratamento: dados abertos do CNPJ, publicação de set/2026, estabelecimentos-
  matriz com CNAE principal 5320-2/02, inclusive os baixados (D-040).

### Sample size

1.391 municípios na estimação principal (640 `datado` + 751 `sem_quebra`),
132 meses (jan/2015–dez/2025). Na janela balanceada, 478 municípios tratados.

### Sample size rationale

Não há escolha de tamanho: é o universo de municípios com 20 mil habitantes ou
mais em que a regra de quebra é válida (abaixo de 100 mil). Não foi feito
cálculo de poder.

### Stopping rule

Não se aplica: dados administrativos com período fechado (fim do painel em
dez/2025, fixado antes do depósito).

## Variables

### Manipulated variables

Nenhuma (estudo observacional). O tratamento observado é o mês da quebra nas
aberturas de MEI de entrega: o primeiro mês candidato `t` (2017-01 a 2025-06) em
que as aberturas de `[t, t+5]` são ao menos 5, ao menos o dobro da linha de base
dos 24 meses anteriores e improváveis sob ela (Poisson, p < 0,01); a quebra é o
primeiro mês dessa janela com abertura. Código: `src/vcemal/mei.py`.

### Measured variables

- **Desfecho principal:** 100.000 × internações de motociclista em trânsito
  (V20–V29, `internacoes_transito`) / frota de motos do município no mês
  (`frota_moto`). Não é a coluna `taxa_por_frota` do painel, que usa todas as
  internações do grupo, inclusive as de não-trânsito.
- **Recortes e testes:** internações de homens de 18 a 39 anos e do complemento
  (H3); de condutor homem 18–39 (secundário, poder baixo, D-023); ciclista
  V10–V19, em contagem (mecanismo); ocupante de automóvel V40–V49 (placebo);
  `frota_moto` como desfecho (teste de denominador endógeno).
- Dicionário completo: `docs/dicionario-painel.md`.

### Indices

Nenhum índice composto.

## Analysis Plan

### Statistical models

Callaway & Sant'Anna (2021), grupo de comparação not-yet-treated, efeitos de
grupo × tempo agregados em estudo de evento `e ∈ [−12, +24]`, balanceado.
Erros-padrão agrupados em região imediata do IBGE; agrupamento em município
reportado lado a lado na tabela principal. Sun & Abraham (2021) como robustez.

Estimando principal de H1: a média simples dos ATT(e) para `e ∈ [0, +24]` na
janela balanceada, sem covariáveis (tendências paralelas incondicionais),
reportada também em % da média pré-tratamento dos tratados. H2: o mesmo
estimando, por tercil da proxy de intensidade.

### Transformations

Taxa por 100 mil motocicletas, em nível. Internações de ciclista em contagem
(bicicleta não tem denominador). Na versão de contagem, efeito fixo de
município.

### Inference criteria

H1 é testada com teste bilateral a 5% e intervalo de 95%; é sustentada se o
estimando principal for positivo e o intervalo excluir zero. H1 é a única
hipótese confirmatória, sem correção para comparações múltiplas; H2, H3, o
teste do mecanismo e o placebo são lidos pelos critérios pré-declarados no
plano, com intervalos de 95%.

Testes pré-declarados de falha do desenho (seção 6 do plano):

1. Efeito sobre ocupante de automóvel indistinguível do efeito sobre
   motociclista → o desenho capta tendência geral de trânsito.
2. Pré-tendências não paralelas em `e ∈ [−12, −1]` → reportar e não interpretar
   causalmente.
3. Denominador endógeno: se o efeito sobre `frota_moto` for distinguível de zero
   **e** de ao menos metade do efeito percentual sobre as internações, o
   resultado principal passa a ser a contagem com efeito fixo de município.

### Data exclusion

- Municípios abaixo de 20 mil habitantes (fora do universo) e a `coorte_precoce`
  (100 mil ou mais): fora da estimação principal.
- Consequências da auditoria, aplicadas mecanicamente (seção 4 do plano): falha
  no estrato `2017` ou `2021-2025` retira essas quebras da estimação principal;
  falha em `2018-2020` mantém a estimação mas retira a leitura "efeito da
  plataforma"; falha nas capitais cancela a robustez com a `coorte_precoce`.
- Saídas de plataforma (tratamento reverso) não são observáveis no CNPJ e não
  entram (D-041).

### Missing data

Município-mês sem frota tem taxa `NaN` e sai da estimação por taxa; na janela
balanceada, coorte com algum tempo de evento sem desfecho sai inteira. Nada é
imputado (D-015): denominador ausente fica ausente.

### Exploratory analysis

Declaradas como exploratórias (seção 7 do plano): distribuição horária dos
sinistros no RENAEST; preenchimento do `CAR_INT`; transbordamento para o
controle (excluindo not-yet-treated na região imediata de um tratado);
antecipação em `e = −1, −2, −3`; mudança de codificação coincidente perto de
2018. Robustez pré-declarada: sem os `sem_quebra` no controle; sem as quebras
anteriores a 2018-01; sem as posteriores a 2020-12; versão não balanceada;
contagem no lugar da taxa.

## Other

**Por que o coeficiente é piso:** o desenho é ecológico (tratamento no
município, desfecho em todos os motociclistas), o pré-período está parcialmente
contaminado pelo marketplace (D-021), e frota que cresce com o tratamento atenua
a taxa (D-027). As três razões serão reportadas separadas.

**Desvios** deste plano depois do depósito vão para `docs/decisoes.md` com data e
motivo, e as análises afetadas passam a exploratórias declaradas.

**Anexos:** `plano-de-analise.md`; `protocolo-cronologia-entrada.md` (versão
1.1); `tratamento_mei_municipio.csv` (hash acima); `auditoria_municipios.csv`;
`decisoes.md`.
