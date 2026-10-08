# Pré-projeto — o argumento

> Este documento é a espinha do projeto. Tudo que entra no repositório precisa
> servir a uma das quatro pernas abaixo. Se não serve, não entra — ver D-028.
> O título de trabalho é o do inventário de fontes: **remuneração por peça e
> externalidade fiscal**.

## O objetivo, em uma frase

Enquanto as plataformas de entrega lucram, o trabalho do entregador se
precariza, o motociclista morre ou se acidenta, e a conta chega ao SUS — que
é pago por todos nós. A partir dessa medida, propor políticas públicas que
façam quem lucra pagar pelo risco que cria.

Não é uma tese de método. O desenho causal (V2) existe porque, sem ele, o
argumento cai na primeira objeção: "internação de motociclista cresce desde
2008 por causa da frota, não da plataforma". Mas o desenho é a viga, não a
casa. As últimas semanas construíram a viga (D-020 a D-027) e deixaram as
outras três pernas sem documento. Este arquivo corrige isso.

## As quatro pernas

| # | Afirmação | O que o projeto mede | Fonte | Estado no repositório |
|---|---|---|---|---|
| **P1** | **Eles lucram.** | Receita e lucro operacional das plataformas, ano a ano, como série de contraste ao custo público | Relatórios anuais da Prosus (iFood); relatório de sustentabilidade do iFood; DiDi (99Food) e Meituan (Keeta) reportam segmento | **Existe: `make lucro` (D-032).** iFood, FY2026: receita de R$ 10,2 bi e EBIT ajustado de R$ 2,0 bi (R$ de dez/2025); 621 mil entregadores ativos |
| **P2** | **O trabalho é precário.** | Informalidade, cobertura previdenciária, jornada e renda-hora dos plataformizados | PNAD Contínua, módulo de plataformas (2022, 2024, 2025) | **Existe: `make pnad` (D-031).** Motociclistas plataformizados: 85% informais, 19% contribuem, R$ 11,4/h em 2025 |
| **P3** | **Nós pagamos.** | (a) Valor pago pelo SUS, deflacionado, por internação de motociclista, e o custo econômico via parâmetros do Ipea; (b) a lacuna entre o que o SUS interna e o que a Previdência reconhece como acidente de trabalho; (c) quanto disso é atribuível à plataforma | SIH `VAL_TOT`; Ipea TD 2565; INSS benefícios (espécies 31 × 91); o próprio estimador do V2 | **Parcial.** (a) existe: `make custo` (D-029). (b) existe: `make lacuna` (D-030). (c) é o V2 |
| **P4** | **Eles morrem ou se acidentam — e o sistema não vê.** | Internações, UTI, óbito hospitalar e pré-hospitalar; e a fração com nexo ocupacional registrado | SIH, SIM, `CAR_INT` | **É o que existe.** D-019: 965.714 internações em 2016–2023, 62 com nexo. Uma em 15.576 |

A perna P3(c) é o V2 inteiro. As outras três são descritivas e **não dependem
do pré-registro** (D-006): olhar receita da Prosus, PNAD e `VAL_TOT` não cruza
tratamento com desfecho. Podem — e devem — andar agora, em paralelo à
cronologia de entrada (F3).

## Ordens de grandeza que o argumento precisa carregar

Números de fora do projeto, para ancorar. Cada um precisa ser recalculado
pelo pipeline antes de virar tabela; aqui servem para dizer qual é o tamanho da
história e o que precisa aparecer lado a lado.

**P1 — lucro.**
- iFood, das planilhas de KPI da Prosus (D-032), em R$ de dez/2025: receita de
  R$ 10,2 bilhões e EBIT ajustado de R$ 2,0 bilhões no ano fiscal encerrado em
  março/2026; o resultado operacional cruzou o zero em FY2024 (R$ 0,5 bi) e
  quase quadruplicou em dois anos. Entregadores ativos no Brasil: 314 mil em
  março/2024, 621 mil em março/2026. Pedidos: 1,9 bilhão no ano fiscal.
- Ano civil de 2025 (interpolado): EBIT ajustado de R$ 1,8 bilhão — cerca de
  oito vezes o que o SUS pagou em 2023 por todas as internações de
  motociclista do país, e três vezes o DPVAT que o SUS deixou de receber por
  ano. R$ 0,15 por pedido cobriria a conta que o SUS paga por internação de
  motociclista. É ordem de grandeza para a linha "repasse por corrida", não
  argumento: a conta só vira política com a fração atribuível do V2.
- Validação externa: FY2025 dá R$ 7,49 bilhões nominais pelo câmbio médio do
  BCB, contra R$ 7,5 bilhões do relatório de sustentabilidade do iFood.

**P2 — precariedade.**
- 1,7 milhão de plataformizados em 2024, contra 1,3 milhão em 2022 (+25,4%).
  Só **35,9%** contribuem para a Previdência. Informalidade de **84,3%** entre
  motociclistas. Entregadores: 46,4 horas semanais. Renda-hora de R$ 15,4,
  **8,3% abaixo** dos demais ocupados (IBGE, PNAD Contínua, 17/10/2025).
- Motociclistas plataformizados, do microdado (D-031): 405 mil em 2025, 85%
  informais, 19% contribuem, R$ 11,4 por hora real contra R$ 18,4 do ocupado
  médio do setor privado, com cinco horas a mais por semana.
- O contraste com o Portal de Dados do iFood (R$ 29,65/hora "em rota",
  modalidade nuvem) é o debate que o paper precisa travar: hora em rota não é
  hora trabalhada, e a modalidade nuvem é selecionada.

**P3 — a conta pública.**
- Internações de motociclista no SUS, janeiro a novembro de 2024: 148.797,
  custando R$ 233,3 milhões (Abramet sobre SIH). Em 2023: 145.761 internações
  (nosso D-019), R$ 221,5 milhões, R$ 1.561 por AIH. Isso é **o valor pago**,
  não o custo — `VAL_TOT` é piso declarado (dicionário do painel).
- Ipea: o SUS gastou R$ 449 milhões com vítimas de trânsito em 2024, e desde
  2021 deixou de receber cerca de **R$ 580 milhões por ano** do DPVAT, cujos 45%
  eram vinculados ao custeio dessas vítimas. A fonte de financiamento que
  existia para essa conta foi extinta exatamente no período em que a frota de
  entrega se expandiu.
- Empregador formal paga a contribuição do RAT (Riscos Ambientais do
  Trabalho), de 1% a 3% da folha, que financia o benefício acidentário. A
  plataforma não tem folha: com 84% de informalidade, **ninguém paga o RAT do
  entregador**. Essa é a externalidade fiscal em uma linha, e é o que a lacuna
  SIH × INSS (espécie 91 quase vazia) vai mostrar em número.

**P4 — mortes e invisibilidade.**
- 13.477 motociclistas mortos em 2023 (Ministério da Saúde, SIM). Perfil:
  homens de 20 a 39 anos; mais de 60% dos óbitos de trânsito são de moto
  (Abramet).
- 62 internações com nexo ocupacional em 965.714 (D-019). O sistema de
  informação é cego ao trabalho — e isso é achado (D-008), não defeito.
- Do lado da Previdência, a mesma cegueira: 75 benefícios com CID V20–V29
  concedidos em janeiro/2023 no país inteiro, 15 com nexo reconhecido, contra
  ~12 mil internações no mês (D-030). Seis por mil; um a dois por mil com nexo.

## O que o desenho causal faz aqui — e o que não faz

O V2 responde a uma pergunta só: **quanto do crescimento das internações é da
plataforma.** É a fração que converte P3 de "o SUS paga por acidentes de moto"
em "o SUS paga por acidentes que a remuneração por corrida causou". Sem essa
fração, a proposta de política é uma opinião; com ela, é um número a cobrar.

O que o V2 **não** faz: não mede lucro, não mede precariedade, não mede a
lacuna previdenciária, e não propõe nada. As três razões de piso (D-001, D-021,
D-027) continuam valendo — mas o paper precisa dizê-las em uma frase, não em
três seções. **A profundidade do método vai para o anexo; o argumento vai para
o texto.**

## Políticas públicas — o cardápio a avaliar com a evidência

Candidatas, não conclusões. Cada uma se ancora numa perna, e a evidência do
projeto é o que diz se ela é proporcional. A ordem é da mais direta à mais
estrutural.

| Política | Perna | O que a evidência do projeto precisa mostrar | Onde está o debate hoje |
|---|---|---|---|
| **Contribuição acidentária das plataformas** — equivalente ao RAT, calculada sobre o valor das corridas, vinculada ao SUS e ao benefício acidentário | P3 | Custo público atribuível por município e por ano; o V2 dá a fração atribuível, a camada de custo dá o valor | O PLP 12/2024 prevê alíquota previdenciária mínima, mas cobre só motoristas de passageiros; entregadores ficaram fora do acordo |
| **Repasse por corrida ao SUS**, no molde do que o DPVAT fazia (45% ao SUS) | P3 | O buraco de R$ 580 mi/ano desde 2021 contra a curva de internações no mesmo período | DPVAT extinto em 2021; SPVAT em transição — ver anexo A, 3.4 |
| **Seguro de acidentes obrigatório**, permanente, custeado pela plataforma | P4 | Internações, UTI e óbito por município tratado; o que o seguro voluntário do iFood cobre e o que não cobre | Lei 14.297/2022 obrigou durante a emergência sanitária e caducou; PL 391/2020 no Senado |
| **Nexo ocupacional registrado na AIH e no SINAN** — campo "trabalho por plataforma" | P4 | A taxa de 1 em 15.576 (D-019) e o preenchimento do `CAR_INT` por município (`make diagnostico`) | Não existe proposta; é a mais barata e a única que faz o Estado enxergar o problema |
| **Transparência obrigatória**: volume de corridas, entregadores ativos e sinistros reportados ao regulador, por município | P1, P3 | A lacuna 4.3 do inventário — sem volume de pedidos, a H2 fica parcialmente identificada. É o dado que só a lei consegue abrir | Sem proposta federal; a liminar da Bahia obrigou preservação de dados via MPT |
| **Limite de jornada e piso por hora trabalhada** (não por hora em rota) | P2 | 46,4 h semanais e R$ 15,4/hora da PNAD contra os R$ 29,65 "em rota" da empresa | PLP 12/2024 fixa teto diário e piso, só para motoristas; Convenção 193 da OIT (12/06/2026) é o marco internacional novo |
| **Desincentivo à velocidade**: proibição de bônus por corrida rápida e de penalidade por recusa | P4 | É o mecanismo da H1. O deslocamento horário dos sinistros (RENAEST, seção 7 do plano) é a assinatura | Sem proposta; é o que a pesquisa acrescenta ao debate, que hoje é só sobre vínculo |

**Contexto de setembro de 2026.** O STF suspendeu em 24/06/2026 o julgamento
sobre vínculo empregatício (RE 1.446.336, Uber; Rcl 64.018, Rappi), a pedido da
DPU, por causa da Convenção 193 da OIT aprovada doze dias antes. O Congresso
discute o PLP 12/2024 na Câmara. **Todo o debate público é sobre vínculo.
Nenhuma das partes está discutindo quem paga a conta do SUS.** É esse o espaço
que o projeto ocupa: não precisa decidir se há vínculo para mostrar que há
externalidade.

## Critério de inclusão

Substitui o do README ("se não reaparece no paper causal, não entra"):

**Se não sustenta uma das quatro pernas ou uma linha da tabela de políticas,
não entra.** O V2 continua sendo a maior peça, mas não é o critério.

## O que falta, em ordem

1. **P3(a) — custo.** ~~Deflacionar `val_tot` (IPCA), converter em custo
   econômico com os parâmetros do Ipea (camada F6), e escrever a série
   nacional 2008– por ano.~~ **Feito: `make custo` (D-029).** ~~Falta rodar
   sobre o painel nacional completo e conferir contra as referências externas
   do anexo A, Bloco 5.~~ **Rodado (set/2026) sobre 2015–2025, 3.563 de 3.564
   competências (D-036).** Motociclista em 2023: R$ 230,1 mi nominais contra
   R$ 221,5 mi da Abramet (+3,9%); jan–nov/2024: R$ 245,0 mi contra R$ 233,3 mi
   (+5,0%). O valor médio por AIH bate (R$ 1.575 contra R$ 1.561, +0,9%), então
   a diferença está na contagem, não no valor. Não é a varredura de campos do
   D-017 (0,7% das AIH) nem AIH duplicada (R$ 0,1 mi). Hipótese não verificada:
   safra do dado — a Abramet tabulou antes de reapresentações posteriores.
2. **P3(b) — lacuna SIH × INSS.** ~~Baixar benefícios concedidos (espécies 31 e
   91) com CID V20–V29, por UF e ano, e pôr ao lado do SIH.~~ **Feito:
   `make lacuna` (D-030).** ~~Falta rodar a série 2019– inteira contra o painel
   nacional.~~ **Rodado (set/2026), 2019–2025:** de 5 a 7 benefícios com CID
   V20–V29 por mil internações até 2023, 1 a 1,3 deles acidentário; em 2024 e
   2025 a razão salta para 12,5 e 15,4 (acidentários 2,2 e 3,0). **O salto é
   quebra de série, não risco (D-037):** a partir de nov/2023 a concessão por
   análise documental (Atestmed) domina, e o atestado registra o CID V muito
   mais que a perícia. Ela responde por 65% dos benefícios de motociclista em
   2024–2025; fora dela a série fica em 853, 754 e 927 benefícios em 2023, 2024
   e 2025. `make lacuna` agora traz `documentais` e `pct_documental` ao lado do
   total — anos dos dois lados da quebra não se comparam pelo total.
3. **P1 — série de lucro.** ~~Tabela anual a partir dos relatórios da Prosus,
   em reais, no mesmo eixo temporal que a série de custo. Fonte nova no
   inventário (Bloco 6).~~ **Feito: `make lucro` (D-032).** FY2019–FY2026
   transcritos com citação em `docs/fontes/ifood_prosus.csv`, em reais
   constantes, ano fiscal e ano civil. ~~Falta pôr ao lado de `custo_por_ano`
   rodado sobre o painel nacional.~~ **As duas séries existem rodadas (set/2026)**
   em `output/tabelas/`, e `make contraste` as põe no mesmo eixo. Em 2025 o
   resultado operacional do iFood (R$ 1,8 bi) é seis vezes o que o SUS pagou
   por internações de motociclista (R$ 288 mi), em R$ de dez/2025.
4. **P2 — PNAD.** ~~Baixar o módulo de 2022, 2024 e 2025 e tirar as quatro
   estatísticas (informalidade, previdência, jornada, renda-hora) por região.~~
   **Feito: `make pnad` (D-031).** Reproduz o IBGE e traz o recorte de
   motociclista plataformizado nas três rodadas.
5. **F3 — cronologia de entrada.** Continua sendo o caminho crítico do V2.
   **Protocolo feito (D-033):** `docs/protocolo-cronologia-entrada.md`, universo
   de 1.710 municípios gerado, planilhas-modelo, validação, concordância e
   desempate por regra em `make cronologia`. **Falta a codificação em si**: dois
   codificadores, piloto de 60 municípios, 8 a 11 semanas de uma pessoa. Não é
   trabalho de sessão automática. **O passo 1 do roteiro existe (D-038):**
   `make wayback` data por intervalo os municípios que aparecem nas listas de
   cidades arquivadas no Wayback. **Rodado (out/2026), D-039:** a lista do
   iFood que se usava era do marketplace e saiu; a do entregador dá 453
   municípios com frota até dez/2023, sem datar entrada. Rappi (160 municípios,
   2019–2021) e Uber Eats (191, 2020–2022) datam por intervalo, 65 deles com
   confiança C. ~~Para o iFood, a cronologia depende da busca dos codificadores.~~
   **O tratamento passa a ser datado pelo CNPJ (D-040):** `make mei` acha a
   quebra nas aberturas de MEI de entrega (CNAE 5320-2/02) por município e mês.
   640 municípios abaixo de 100 mil habitantes ficam datados, de 2017 a 2025;
   os 319 de 100 mil+ são coorte precoce (até 2018). A codificação vira
   auditoria de 30 a 50 municípios; falta o protocolo 1.1 dizer isso.
6. Migrar aqui o documento original `pre-projeto-remuneracao-entrega-acidentes.md`
   (fases F0–F4, desenhos A e B, cronograma), que não está no repositório.
