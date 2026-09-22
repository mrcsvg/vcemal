# Anexo A — Inventário de fontes de dados

**Projeto:** Remuneração por peça e externalidade fiscal — plataformas de entrega, internações de motociclistas e gasto público
**Versão:** 0.1 — setembro de 2026
**Escopo:** fontes candidatas, dicionários, cobertura temporal, granularidade e status de acesso

---

## Legenda de status

| Símbolo | Significado |
|---|---|
| **A** | Aberto — microdado baixável sem pedido, sem cadastro |
| **A-** | Aberto, mas agregado (não é microdado) ou com supressão de campos |
| **R** | Restrito — exige pedido formal (LAI), convênio ou sala segura |
| **F** | Fechado — dado privado, sem via pública |
| **N** | Não existe compilado — precisa ser construído |

---

## Bloco 1 — Desfecho de saúde

### 1.1 SIH/SUS — Sistema de Informações Hospitalares · **A**

A espinha dorsal do projeto.

| Dimensão | Valor |
|---|---|
| Órgão | Ministério da Saúde / DATASUS |
| Unidade | AIH (internação individual, não nominal) |
| Granularidade geográfica | Município de residência (`MUNIC_RES`) e de internação (`MUNIC_MOV`) |
| Granularidade temporal | Competência mensal; datas de internação e saída no registro |
| Cobertura | Layout atual desde 2008; série anterior desde 1992 com menos campos |
| Formato | `.dbc` (DBF comprimido), um arquivo por UF × mês — `RD<UF><AAMM>.dbc` |
| Acesso | FTP `ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/` |
| Latência | ~2 a 3 meses para dado preliminar; consolidação em ~6 meses |
| Dicionário | "Estrutura dos arquivos SIHSUS — RD", distribuído junto ao FTP e na documentação do TabWin |

**Campos que interessam:** `DIAG_PRINC` e `DIAG_SECUN` (CID-10), `IDADE`/`COD_IDADE`, `SEXO`, `DT_INTER`, `DT_SAIDA`, `DIAS_PERM`, `UTI_MES_TO`, `MORTE`, `VAL_TOT`, `VAL_SH`, `VAL_SP`, `CAR_INT`, `CNES`.

**O campo decisivo é o `CAR_INT` (caráter da internação).** Ele distingue:
- `03` — acidente no local de trabalho ou a serviço da empresa
- `04` — acidente no trajeto para o trabalho
- `05` — outros tipos de acidente de trânsito
- `06` — outros tipos de lesões e envenenamentos

É o único campo do SIH que marca nexo ocupacional. **Também é notoriamente mal preenchido**, e essa má qualidade é a H4 do pré-projeto — trate como achado, não como defeito. Medir a taxa de `CAR_INT` = 03/04 entre motociclistas com CID V20–V29 já é resultado publicável por si só.

**Filtro de caso:** CID-10 V20 a V29 (motociclista traumatizado em acidente de transporte), com o quarto dígito distinguindo condutor de passageiro.

**⚠️ Em qual campo.** O código V **não está no `DIAG_PRINC`**. A norma do SIH manda o diagnóstico principal trazer o *tipo de traumatismo* (capítulo XIX, S/T) e o secundário trazer a *origem* da causa (capítulo XX). Medido: filtrar `DIAG_PRINC` devolve **zero** AIH de motociclista em todo ano de 2016 a 2023, contra 107–145 mil por ano no campo certo. Na prática o código vive em `DIAGSEC1`, com cauda em `DIAGSEC2`–`DIAGSEC9`. Ver D-017.

**Armadilhas:**
- `VAL_TOT` é o valor pago pelo SUS, não o custo econômico. Deflacione e diga explicitamente que é limite inferior.
- Município de residência ≠ município do acidente. Para entregador urbano isso costuma bater, mas em região metropolitana não.
- Cobertura hospitalar muda ao longo do tempo. Controle por leitos SUS (CNES).

**Ferramentas:** `PySUS` 2.x (Python — `pysus.ftp.sih`, com cache em `~/pysus/`; ver D-034), `microdatasus` (R), `read.dbc`.

**Base dos Dados (BigQuery) — segunda fonte, testada.** `basedosdados.br_ms_sih.aihs_reduzidas`: 212,8 milhões de AIH, particionada por `ano` (2008–2024), 129,6 GB. Precisa de um projeto GCP só para faturar; o free tier de 1 TB/mês cobre a série inteira (cada ano sai em ~1–2 GB com seleção de coluna). Implementado em `vcemal.extract.bigquery`.

**O espelho não é o arquivo RD.** Cinco divergências medidas, todas produzindo erro silencioso — não exceção — se ignoradas: `carater_internacao` vem `1`–`6` e não `01`–`06`; `sexo_paciente` vem decodificado (`Masculino`); o CID vem partido em `_categoria` (3 caracteres) e `_subcategoria` (4); `sigla_uf` é INTEGER e está inteiramente nula; e `carater_internacao` aparece **100% preenchido, sem um único nulo**, quando o RD cru tem branco. A última é a que contamina resultado: **a taxa de preenchimento desta fonte não serve para reportar**. Tabela completa em D-018.

---

### 1.2 SIM — Sistema de Informações sobre Mortalidade · **A**

Captura quem morre antes de internar — sem isso, o SIH subestima a severidade.

| Dimensão | Valor |
|---|---|
| Órgão | DATASUS |
| Unidade | Declaração de óbito |
| Granularidade | Município de residência e de ocorrência; data do óbito |
| Cobertura | Desde 1979; layout atual desde 1996 (CID-10) |
| Formato | `.dbc`, `DO<UF><AAAA>.dbc`, anual por UF |
| Latência | Preliminar em ~8 meses, definitivo em ~18 meses |
| Dicionário | Manual do SIM / "Estrutura do arquivo DO", DATASUS |

Campo `ACIDTRAB` indica óbito relacionado a acidente de trabalho — mesmo problema de preenchimento do `CAR_INT`, e por isso mesmo útil para triangular a subnotificação.

---

### 1.3 SINAN — Acidente de Trabalho Grave (ACGR) · **A**

| Dimensão | Valor |
|---|---|
| Órgão | Ministério da Saúde / SVS |
| Unidade | Ficha de notificação individual |
| Granularidade | Município de notificação e de residência |
| Cobertura | 2007 em diante |
| Formato | `.dbc` via DATASUS / TabNet |
| Dicionário | "DIC_DADOS_DRT_Acidente_Trabalho_grave" (SINAN NET v5.0), em `portalsinan.saude.gov.br` |

**Duas ressalvas graves, ambas documentadas na literatura:**
1. **Espírito Santo sai da série a partir de 2019**, porque o estado migrou para o e-SUS Vigilância em Saúde. Exclua ou trate separadamente.
2. **Completude de CBO e CNAE é ruim na maioria das UFs.** Se o desenho depender de identificar a ocupação "entregador", o SINAN não sustenta sozinho.

Vantagem: ao contrário da CAT, o SINAN **não exige vínculo empregatício** — a notificação é do sistema de saúde. É a única base pública que, em tese, enxerga o entregador informal. Na prática, depende de busca ativa municipal, então a cobertura é heterogênea entre cidades. Isso é confundidor sério num painel município × mês; use como fonte descritiva e de validação, não como desfecho principal.

---

### 1.4 CNES — Cadastro Nacional de Estabelecimentos de Saúde · **A**

Leitos SUS, leitos de UTI e habilitação em trauma por município-mês. Serve de controle de oferta. `.dbc` mensal no FTP do DATASUS.

---

## Bloco 2 — Previdência e trabalho formal

### 2.1 INSS — Benefícios concedidos (SUIBE) · **A**

Isto é microdado aberto. Não precisa de LAI.

| Dimensão | Valor |
|---|---|
| Órgão | INSS / Dataprev |
| Unidade | Benefício concedido |
| Campos | Competência da concessão, espécie, CID e nome CID-10, despacho, data de nascimento, sexo, clientela, **município de residência**, UF, vínculo dependentes, forma de filiação, qtd. de salários mínimos na RMI, ramo de atividade, DIB, DDB, DCB |
| Granularidade temporal | Mensal (competência) |
| Cobertura | Série sob o PDA atual desde jun/2023, atualizada mensalmente; séries anteriores no portal legado da Dataprev — **confirmar o encadeamento entre as duas** |
| Formato | CSV |
| Acesso | `dadosabertos.inss.gov.br` (espelhado em `dados.gov.br`) |
| Dicionário | Publicado como recurso do próprio conjunto no CKAN |

**Uso no projeto:** contar concessões por CID S/T e V20–V29, por município-mês, separando espécie 31 (auxílio por incapacidade temporária **previdenciário**) de 91 (**acidentário**). A RMI em salários mínimos permite estimar o custo previdenciário direto.

**O que se achou ao integrar (set/2026, D-030).** São três conjuntos no CKAN, não um: `inss-beneficios-concedidos` (dez/2018 a mai/2023), `beneficios-concedidos-plano-de-dados-abertos-jun-2023-a-jun-2025` (jun/2023 em diante, apesar do nome) e um terceiro com um ZIP por ano de 2012 a 2018, **não integrado**. O layout muda quatro vezes: CSV `;` latin-1 com CID em duas colunas (2019); CSV UTF-8 com BOM e `CID_1` (2020 a abr/2021); ZIP com CSV latin-1 e CID e nome numa coluna só (mai/2021 a mai/2023); XLSX com linha de título, cabeçalhos duplicados e, só aí, o **código numérico** da espécie (jun/2023 em diante). Nos CSVs de 2020 e 2021 a coluna `UF` **não corresponde** ao município de residência — a UF é lida do campo `Mun Resid`, consistente em todos os anos. O município vem em código próprio do INSS, não IBGE: a integração fica em UF. A busca do CKAN (`package_search`) estava quebrada no servidor; `package_show` funciona. O XLSX leva cerca de um minuto por mês para abrir. Tudo isso mora em `vcemal.transform.inss`.

**Conjuntos irmãos no mesmo portal:** benefícios cessados/suspensos, benefícios indeferidos (com motivo do indeferimento), benefícios emitidos. Os indeferidos são interessantes — negativa de nexo é parte da história.

**A ressalva estrutural (importante).** A espécie 91 pressupõe vínculo formal. O entregador de app é MEI ou contribuinte individual; quando muito, cai na 31. E a PNAD indica que só cerca de 36% dos plataformizados contribuem para a previdência, com informalidade acima de 84% entre motociclistas. **Logo, a base previdenciária é aberta e ao mesmo tempo cega para a população de interesse.** A lacuna entre o volume do SIH e o volume do INSS, por município e por ano, é a medida direta do custo não internalizado — é o segundo resultado do paper, não um obstáculo.

---

### 2.2 INSS — Comunicação de Acidente de Trabalho (CAT) · **A**

| Dimensão | Valor |
|---|---|
| Unidade | CAT registrada no CATWEB, ou gerada na concessão de benefício acidentário |
| Campos | Agente causador, data do acidente, **CBO (código e nome)**, CID-10 (código e nome), **CNAE 2.0 do empregador**, emitente da CAT, espécie do benefício, filiação do segurado, indicador de óbito, **município do empregador**, natureza da lesão, origem do cadastramento, parte do corpo atingida, sexo, tipo de acidente, UF do município do acidente, UF do município do empregador, data de afastamento, DDB, data do acidente, data de nascimento, data de emissão |
| Granularidade temporal | Arquivo mensal (série atual desde jun/2023); série trimestral no portal legado da Dataprev cobrindo anos anteriores |
| Formato | CSV em ZIP |
| Base legal | Decreto 8.777/2016 e LAI 12.527/2011 |
| Dicionário | "Dicionário de dados da CAT", recurso do conjunto |

**Atenção à geografia:** há município do **empregador**, mas do acidente só a **UF**. Isso quebra qualquer painel município × mês construído sobre a CAT. Use no máximo em nível de UF.

**E a ressalva de sempre:** CAT pressupõe empregador. O CBO de motociclista de entrega vai aparecer com números irrisórios. Isso não mede risco — mede invisibilidade. Vale como numerador de uma razão de subnotificação contra o SIH.

---

### 2.3 AEAT e AEPS — anuários estatísticos · **A-**

Tabelas agregadas por UF, CNAE, CID e município, com séries longas e consistentes. Edição mais recente do AEAT: 2024, publicada em dez/2025, primeira a trazer recorte por raça/cor e escolaridade. Serve para validar a agregação dos microdados e para citar número oficial no texto. **Não use como fonte primária** quando o microdado existe.

Tabulador: AEAT Infologo.

---

### 2.4 RAIS e Novo CAGED · **A**

Microdado de vínculo formal, anual (RAIS) e mensal (CAGED), por município e CNAE. No projeto serve para dois papéis: denominador de emprego formal em transporte/entrega (CNAE 5320-2, 4930-2, 5229-0) e controle de choque econômico local. Acesso via `pdet.mte.gov.br`. Dicionário publicado com o layout anual.

---

## Bloco 3 — Trânsito, frota e sinistralidade

### 3.1 RENAEST — Registro Nacional de Sinistros e Estatísticas de Trânsito · **A-**

| Dimensão | Valor |
|---|---|
| Órgão | Senatran / Ministério dos Transportes |
| Natureza | **Agregado**, não microdado |
| Granularidade | UF e município; perfil dos envolvidos, tipo de veículo, gravidade |
| Formato | ZIP com arquivos separados (Sinistros, Localidade, Veículos, Pessoas, etc.) |
| Acesso | `dados.transportes.gov.br/dataset/renaest` — atualizado recentemente |
| Cobertura | Série desde 2018; **confirmar o ano final e a completude por UF** |

Serve como desfecho alternativo e como placebo. O RENAEST depende de alimentação pelos Detrans estaduais, e a cobertura é desigual entre estados e ao longo do tempo — o que o torna perigoso como desfecho principal num painel de efeitos fixos. Use como robustez.

### 3.2 RENAVAM — frota de veículos · **A-**

Frota por UF, município e tipo de veículo, mensal. É o **denominador correto** para taxa de internação de motociclista — usar população em vez de frota é o caminho mais rápido de confundir o efeito com o crescimento da motorização.

**Atenção: são duas fontes diferentes com o mesmo nome, e só uma serve.**

| | Portal de dados abertos | Página de estatísticas do Senatran |
|---|---|---|
| Onde | `dados.transportes.gov.br`, dataset `registro-nacional-de-veiculos-automotores-renavam` | `gov.br/transportes/.../frota-de-veiculos-<ano>`, link "Frota por Município e Tipo" |
| Colunas | UF; Município; **Marca Modelo**; Ano Fabricação; Qtd. | UF; Município; TOTAL; uma coluna **por tipo** (MOTOCICLETA, MOTONETA, CICLOMOTOR, SIDE-CAR, TRICICLO…) |
| Tamanho | ~136 MB/mês (ZIP e RAR) | ~1,2 MB/mês (XLS/XLSX) |
| Cobertura | maio/2013 → | **julho/2016** → |
| Serve? | **Não** — sem coluna de tipo; derivar "motocicleta" exigiria classificar dezenas de milhares de strings de marca/modelo, com erro entrando direto no denominador | **Sim** |

Implementado em `vcemal.extract.senatran`. O nome do arquivo não é chave estável — o rótulo do link é. Ver D-016.

**Município vem por nome, não por código IBGE**, e o nome carrega grafia divergente, truncamento em 30 caracteres e município renomeado. A ponte está em `vcemal.municipios`, com tabela revisada a mão; ver D-014 para por que fuzzy match não serve aqui.

**Cobertura é a limitação real:** a série municipal começa em julho/2016. Antes disso o Senatran só publica por UF (D-015).

### 3.3 PRF — acidentes em rodovias federais · **A**

Microdado por ocorrência e por pessoa, CSV anual, desde 2007. Cobre só rodovia federal, o que é pouco relevante para entrega urbana — mas serve de placebo geográfico limpo (entrega de app não acontece em BR).

### 3.4 SPVAT / ex-DPVAT · **R**

Indenizações por morte, invalidez e DAMS. Historicamente havia boletim estatístico da Seguradora Líder com recorte por UF e tipo de veículo. Com a transição para o SPVAT o regime de divulgação mudou — **verificar o que ainda é público antes de contar com isso**.

**Por que importa para o argumento (P3).** Até 2020, 45% da arrecadação do DPVAT era vinculada ao custeio do atendimento a vítimas de trânsito no SUS. O seguro foi suspenso em 2021 e o SUS deixou de receber cerca de **R$ 580 milhões por ano** (Ipea, 2025) — no mesmo período em que a frota de entrega se expandiu. É a fonte de financiamento que existia para esta conta e foi extinta; o "repasse por corrida" da tabela de políticas em `docs/pre-projeto.md` é o seu substituto natural.

---

## Bloco 4 — Exposição à plataforma (o gargalo)

### 4.1 PNAD Contínua — módulo Trabalho por meio de plataformas digitais · **A**

| Dimensão | Valor |
|---|---|
| Órgão | IBGE, em parceria com Unicamp e MPT |
| Status | **Experimental** |
| Rodadas | 4º trimestre de 2022 e 3º trimestre de 2024, divulgadas em out/2025; rodada de 2025 anunciada, incluindo plataformas de comércio eletrônico |
| Granularidade geográfica | Brasil, grandes regiões, UF, RM e capitais — **não desce a município** |
| Formato | Microdado em `.txt` de largura fixa + input SAS/R, no FTP do IBGE |
| Dicionário | Dicionário de variáveis da PNADC + Nota Técnica 04/2025 sobre o módulo |

**O que dá:** 1,7 milhão de plataformizados em 2024 (contra 1,3 milhão em 2022, alta de 25,4%), 86,1% por conta própria, 83,9% homens, informalidade de 71,1% no conjunto e 84,3% entre motociclistas, cobertura previdenciária de 35,9%. Entregadores com jornada média de 46,4 h semanais.

**O que se achou ao integrar (set/2026, D-031).** O microdado com o suplemento **não** está em `Trimestral/Microdados/`, e sim em `Anual/Microdados/Trimestre/Trimestre_<t>/Dados/`, um ZIP por ano com data de divulgação no nome, dicionário único por trimestre (`.xls`, com posição e largura) e deflator por ano-trimestre. O `.txt` de largura fixa tem 1,9 GB (3T) a 3,5 GB (4T2022); `vcemal.transform.pnad` fatia só as 16 variáveis necessárias em ~5 s. A variável que reproduz o informativo é a derivada **`SD14001`**, não o quesito bruto `S14009`: com o bruto o total sai 1,79 milhão em 2024; com a derivada, os 1,65 milhão oficiais. Rendimento-hora publicado é razão de médias com 4,345 semanas por mês. `make pnad` reproduz cada número do informativo de 2024 com erro de arredondamento — e é a primeira leitura da rodada de 2025 no recorte de motociclista.

**O que não dá:** granularidade municipal. Serve como teto independente e para calibrar denominadores, **não** como variável de tratamento no painel.

Cuidado com a comparação temporal: houve renovação da amostra mestra em 2025 e reponderação da série. Leia a Nota Técnica 02/2025 antes de encadear.

### 4.2 Portal de Dados iFood · **A-**

Painel público lançado em set/2024, com horas em rota, ganho médio por hora, entregadores cadastrados e ativos, velocidade média em grandes cidades, volume de pedidos e presença geográfica. Números de 2025: ganho médio de R$ 29,65/hora na modalidade nuvem, mais de 600 mil cadastrados e 460 mil ativos no ano.

**Natureza:** agregado nacional ou por grandes cidades, publicado pela parte interessada, restrito à modalidade "nuvem". É insumo de contexto e de contraste retórico — **não é dado de pesquisa**. Se usar, cite como fonte da empresa e discuta o viés de seleção da modalidade.

Registre também a camada de impacto econômico calculada pela FIPE via matriz insumo-produto — é o número que a empresa usa publicamente, e o paper vai precisar dialogar com ele.

### 4.3 Volume de pedidos por município · **F**

iFood, 99Food e Keeta não publicam. Não há LAI que alcance — é dado privado.

Vias possíveis, em ordem de viabilidade:
1. Convênio acadêmico com o MPT, aproveitando a parceria já existente no módulo da PNAD.
2. Os dados que a liminar da Bahia obrigou a preservar, via MPT.
3. Acordo direto com plataforma, com as implicações óbvias de independência a declarar.

**Sem isto, a H2 fica parcialmente identificada.** O proxy por entregadores cadastrados é fraco e o sinal do viés precisa ser discutido explicitamente.

### 4.4 Cronologia de entrada das plataformas por município · **N**

Não está fechado — simplesmente não existe compilado. É o F3 do cronograma, 4 a 6 semanas de trabalho de arquivo com dupla codificação independente e cálculo de concordância entre codificadores. Fontes: releases das empresas, imprensa local, Wayback Machine sobre as páginas de cobertura, registros na Junta Comercial, prefeituras.

**Protocolo pronto (set/2026, D-033):** `docs/protocolo-cronologia-entrada.md`. Universo de 1.710 municípios (20 mil habitantes ou mais, Censo 2022) em `docs/fontes/cronologia/universo.csv`; planilhas-modelo, validação com data-piso por plataforma, kappa e concordância de data por bloco, desempate por regra e adjudicação versionada, tudo em `scripts/cronologia.py` e `make cronologia`. A codificação em si não começou.

**A data a codificar é a da frota própria, não a do aplicativo.** O iFood foi marketplace de 2011 a 2017 (entrega pelo motoboy do restaurante) e só passou a entregar com entregador da plataforma em 2018 — por declaração da própria empresa. Remuneração por corrida, que é o tratamento, começa aí. Um release de 2016 dizendo "iFood chega a [cidade]" **não é** tratamento. Ver D-020.

**Marcos conhecidos, para ancorar a codificação:**

| Plataforma | Entrada com frota própria | Saída |
|---|---|---|
| iFood | 2018 (nacional); ~900 municípios em 2019, ~1.500 em 2023, ~1.700 em 2026 | — |
| Rappi | ~2017 | — |
| Uber Eats | ~2016 | **março/2022** |
| 99Food | **novembro/2019**, estreia em Belo Horizonte; 59 cidades em jan/2022 | 2023; retomou ago/2025 |
| Keeta (Meituan) | dezembro/2025 | — |

De 5.570 municípios, ~1.700 têm iFood hoje: a maioria do país nunca foi tratada, e o rollout é escalonado ao longo de mais de cinco anos. **As saídas são tratamento reverso** e devem ser codificadas como evento próprio.

**Continua sendo o caminho crítico do projeto.**

---

## Bloco 5 — Denominadores, controles e parâmetros de custo

| Fonte | Órgão | Granularidade | Temporalidade | Status |
|---|---|---|---|---|
| Estimativas populacionais municipais | IBGE | Município | Anual — **sem 2022 e 2023** (D-015) | **A** |
| Censo 2022 | IBGE | Setor censitário | Decenal | **A** |
| PIB municipal | IBGE | Município | Anual, ~2 anos de defasagem | **A** |
| Dados meteorológicos (chuva) | INMET | Estação | Diária/horária | **A** |
| Custo econômico de acidente de trânsito | Ipea, TD 2565 (Carvalho, 2016) e Ipea/Cepal 2020 | Parâmetro nacional | Pontual | **A-** |
| Finanças municipais e de saúde | Siops / Finbra | Município | Anual | **A** |

Os parâmetros do Ipea entram na camada F6 para converter internações em custo econômico total (perda de produção + custo médico + custo material). São estimativas antigas — atualize por deflator e declare a fonte do fator.

**Referências externas para conferir a série própria:** o SUS gastou R$ 449 milhões com vítimas de trânsito em 2024 (Ipea sobre DATASUS); só internações de motociclista, R$ 233,3 milhões de janeiro a novembro de 2024 e R$ 221,5 milhões em 2023, com média de R$ 1.561 por AIH (Abramet sobre SIH). O pipeline precisa reproduzir esses números antes de somar qualquer coisa a eles.

---

## Bloco 6 — Resultados das plataformas (o contraste)

É a perna P1 do argumento (`docs/pre-projeto.md`): a série de receita e lucro que vai ao lado da série de custo público, no mesmo eixo temporal. Nenhuma dessas fontes é dado de pesquisa — são demonstrações publicadas pela parte interessada, e é assim que devem ser citadas.

### 6.1 Prosus — relatórios anuais e semestrais (iFood) · **A-**

| Dimensão | Valor |
|---|---|
| Órgão | Prosus N.V. (controladora do iFood), listada em Amsterdã e Joanesburgo |
| Unidade | Segmento de *food delivery* e, a partir de FY24, iFood destacado |
| Granularidade | Nacional (Brasil), sem abertura por município |
| Temporalidade | Ano fiscal de **abril a março**; resultados anuais em junho, semestrais em novembro |
| Formato | PDF (`prosus.com` → *results, reports and events*) |
| Cobertura | FY2019– com iFood identificável; antes disso, agregado em *food delivery* |

**Marcos:** FY2025 (abril/2024–março/2025): receita do iFood de R$ 7,5 bilhões (relatório de sustentabilidade do próprio iFood), EBIT ajustado +178%. FY2026 (encerrado em março/2026): receita de US$ 1,87 bilhão, +40% em dólar e +28% em moeda local sem aquisições; EBITDA ajustado do ecossistema Prosus de US$ 1,3 bilhão.

**Armadilhas:** o ano fiscal não bate com o calendário do SIH — converter para ano civil por interpolação declarada ou alinhar a série de custo ao ano fiscal. A moeda de reporte é dólar; usar a taxa média do período que a própria Prosus informa. Mudança de reconhecimento de receita em FY24 (nota da Prosus) quebra a série — reportar as duas bases.

**O que se achou ao integrar (set/2026, D-032).** A fonte primária não é o relatório anual, é a **planilha de KPI** (`KPI datasheet`, XLSX; PDF em FY2021) que acompanha cada resultado anual e semestral na página de resultados da Prosus. Cada planilha traz três anos fiscais com o iFood aberto como subsidiária: pedidos, GMV, receita, resultado, entregadores ativos, estabelecimentos e cidades no Brasil. A série FY2019–FY2026 está transcrita em `docs/fontes/ifood_prosus.csv` com documento, URL, data de acesso e nota por célula — o único CSV versionado do projeto, porque é citação, não dado. Regra de transcrição: a publicação mais recente que cobre o ano; o valor anterior vai na nota quando difere (pedidos de FY2022: 758 → 733; *trading profit* de FY2023: −79 → −65; EBIT de FY2025: 226 → 230 com a Zoop dentro do iFood). Dois cortes: receita muda de regra em FY2024 (pro-forma de FY2023 na regra nova: US$ 905 mi contra 1.371 publicados) e a métrica de resultado muda de *trading profit* para EBIT ajustado em FY2025, com FY2023–FY2024 nas duas. O GMV total do iFood deixou de ser publicado em FY2026 (só o do *core*). Câmbio: média mensal do BCB, SGS 3698, sobre os doze meses do ano fiscal (`vcemal.extract.bcb`) — FY2025 fecha em R$ 7,49 bilhões, contra os R$ 7,5 bilhões do relatório de sustentabilidade. Tudo em `make lucro`.

### 6.2 Demais plataformas · **A-** / **F**

| Plataforma | Controladora | O que publica |
|---|---|---|
| 99Food | DiDi Global | Segmento internacional agregado; sem abertura de Brasil nem de entrega |
| Keeta | Meituan | Segmento "novas iniciativas"; entrou no Brasil em dezembro/2025 |
| Rappi | Capital fechado | Nada auditado; só declarações à imprensa |

Para essas, a série de contraste fica restrita ao iFood, que é líder de mercado — declarar como limitação, não interpolar.

### 6.3 Estudo de impacto econômico do iFood (FIPE) · **A-**

Matriz insumo-produto encomendada pela empresa. É o número que o iFood usa publicamente para a contribuição ao PIB e à renda dos entregadores; o paper precisa dialogar com ele e com o Portal de Dados (4.2), em especial a diferença entre **hora em rota** e hora trabalhada.

---

## Tabela consolidada

| # | Fonte | Microdado? | Geografia | Temporal | Cobertura | Status | Papel |
|---|---|---|---|---|---|---|---|
| 1.1 | SIH/SUS | Sim | Município | Mensal | 2008– | A | **Desfecho principal** |
| 1.2 | SIM | Sim | Município | Anual | 1996– | A | Severidade / óbito pré-hospitalar |
| 1.3 | SINAN ACGR | Sim | Município | Contínuo | 2007– | A | Nexo ocupacional (frágil) |
| 1.4 | CNES | Sim | Estabelecimento | Mensal | 2005– | A | Controle de oferta |
| 2.1 | INSS benefícios concedidos | Sim | UF (município em código próprio) | Mensal | dez/2018– mensal; 2012–2018 anual | A | **Lacuna SIH × INSS (P3b)** — `make lacuna` |
| 2.2 | INSS CAT | Sim | UF (acidente) | Mensal | jun/2023– (legado antes) | A | Subnotificação |
| 2.3 | AEAT / AEPS | Não | Município | Anual | Longa | A- | Validação |
| 2.4 | RAIS / CAGED | Sim | Município | Anual / mensal | Longa | A | Denominador formal |
| 3.1 | RENAEST | Não | Município | Anual | 2018– | A- | Desfecho alternativo |
| 3.2 | RENAVAM frota | Não | Município | Mensal | Longa | A- | **Denominador** |
| 3.3 | PRF | Sim | Trecho | Anual | 2007– | A | Placebo |
| 3.4 | SPVAT | ? | UF | ? | ? | R | Verificar |
| 4.1 | PNAD módulo plataformas | Sim | UF / RM | 4T2022, 3T2024, 3T2025 | Experimental | A | **Precariedade (P2)** — `make pnad` |
| 4.2 | Portal iFood | Não | Nacional / capitais | Anual | 2022– | A- | Contexto |
| 4.3 | Volume de pedidos | — | — | — | — | **F** | **Lacuna da H2** |
| 4.4 | Datas de entrada | — | Município | Mensal | 2016– | **N** (protocolo pronto) | **Tratamento — caminho crítico** — `make cronologia` |
| 6.1 | Prosus / iFood KPI datasheets | Não | Nacional | Anual (abr–mar) | FY2019– | A | **Contraste de lucro (P1)** — `make lucro` |

---

## As três lacunas que realmente importam

1. **Volume de pedidos por município (F).** Sem isso, você mede o efeito da presença da plataforma, não da intensidade. A H1 sobrevive; a H2 fica capenga. É o único item da lista onde vale gastar capital institucional.

2. **Nexo ocupacional individual (parcialmente A, na prática ruim).** Nenhuma base pública liga uma internação a "trabalhava para plataforma X". O `CAR_INT` do SIH e o CBO do SINAN são as únicas aproximações, e ambas têm preenchimento sofrível. Converta a limitação em resultado: quantificar a cegueira do sistema é parte da tese.

3. **Datas de entrada (N).** Nada de estimação principal começa sem isso.

Note que **nenhuma delas se resolve com LAI.** O pedido ao INSS que eu tinha colocado como prioridade de semana 1 pode sair da rota crítica — o portal de dados abertos entrega quase tudo. Se houver um pedido a fazer, que seja estreito: encadeamento da série pré-2023 e confirmação de que município de residência não vem suprimido em municípios pequenos por sigilo estatístico.

---

## Ordem de ataque sugerida

**Semana 1**
- Baixar SIH-RD de 3 UFs de perfil distinto (SP, BA, PR), 24 meses, e validar o dicionário campo a campo — em especial o preenchimento do `CAR_INT`.
- Baixar um mês de INSS benefícios concedidos e um de CAT, e conferir se município e CID vêm mesmo abertos ou agregados.
- Pré-registro do plano de análise (OSF), **antes** de qualquer cruzamento tratamento × desfecho.

**Semana 2 a 4**
- Pipeline completo do SIH: `.dbc` → Parquet particionado por ano/mês → DuckDB. Painel município × mês replicável.
- Frota RENAVAM e população IBGE como denominadores.
- Iniciar F3, a codificação das datas de entrada.

**Paralelo, sem bloquear nada**
- Sondar MPT sobre convênio de dados.
- Baixar e explorar o módulo da PNAD para calibrar denominadores.

---

## Fontes consultadas

- DATASUS — `datasus.saude.gov.br/informacoes-de-saude-tabnet` e FTP `ftp.datasus.gov.br`
- Portal SINAN — `portalsinan.saude.gov.br` (dicionário DRT Acidente de Trabalho Grave, v5.0)
- Portal de Dados Abertos do INSS — `dadosabertos.inss.gov.br`
- Portal Brasileiro de Dados Abertos — `dados.gov.br`
- Dados Abertos do Ministério dos Transportes — `dados.transportes.gov.br/dataset/renaest`
- Estatísticas Senatran — `gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/estatisticas-senatran`
- IBGE — PNAD Contínua, notas técnicas e microdados
- PDET / MTE — microdados RAIS e CAGED
- Portal de Dados iFood — `institucional.ifood.com.br/portal-de-dados-ifood/`
- Lima et al., "Completude das notificações de acidentes de trabalho no SINAN, Brasil, 2007–2022", *Rev. Bras. Saúde Ocupacional*
