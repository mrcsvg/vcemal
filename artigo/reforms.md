---
title: "Checklist REFORMS aplicado ao estudo"
subtitle: "Plataformas de entrega e internações de motociclistas no SUS — versão prévia"
author: "[NOMES DOS AUTORES] — UFPR"
date: "13 de outubro de 2026"
lang: pt-BR
---

Checklist REFORMS (Kapoor et al., 2024, *Science Advances* 10(18): eadk3452), 8 módulos e 32 itens, aplicado como revisão metodológica final. **Nota de adaptação:** o estudo é de inferência causal observacional (diferenças em diferenças), e o componente de “modelo” ajustado aos dados é a regra de detecção de quebra estrutural que constrói o tratamento. Os itens de ML são respondidos para essa regra; onde o item não se aplica, dizemos por quê. Status: **✓** atendido; **◐** parcial ou previsto no pré-registro; **N/A** não se aplica.

## Módulo 1 — Objetivos do estudo

| Item | Status | Resposta | Onde |
|---|---|---|---|
| 1a. População ou fenômeno de interesse | ✓ | Motociclistas internados no SUS por acidente de trânsito (CID-10 V20–V29), em municípios brasileiros de 20 mil+ habitantes, 2015–2025; tratamento: chegada do entregador remunerado por corrida | Artigo §1, §2.2; plano §1 e §3 |
| 1b. Motivação para o uso de métodos de ML/ciência de dados | ✓ | O tratamento não é observado em nenhuma base; precisa ser inferido de um sinal ruidoso (aberturas de MEI) por regra de detecção de quebra calibrada. Estimação causal por DiD escalonado porque TWFE é inconsistente com adoção escalonada | Artigo §2.3–2.4 |
| 1c. População-alvo da inferência | ✓ | Municípios de 20–100 mil habitantes (onde a regra é validada); 100 mil+ como coorte precoce; < 20 mil fora | Artigo Tabela 3; plano §4 |

## Módulo 2 — Reprodutibilidade computacional

| Item | Status | Resposta | Onde |
|---|---|---|---|
| 2a. Dataset utilizado | ✓ | Todas as fontes públicas, com órgão, URL, cobertura e formato. Microdado não versionado por volume; reconstruído por código | `docs/anexo-a-…md`; artigo §2.1 |
| 2b. Código | ✓ | Repositório público `github.com/mrcsvg/vcemal`, MIT | README |
| 2c. Infraestrutura computacional | ✓ | Python ≥ 3.11, CPU comum; série SIH ~3.564 arquivos; CNPJ ~6 GB | `pyproject.toml`; README |
| 2d. README com instruções | ✓ | Passo a passo por alvo de `make` | `README.md` |
| 2e. Script de reprodução | ✓ | `make painel`, `make mei`, `make custo` etc.; `artigo/analise_artigo.py` para as figuras desta versão (verifica o hash do tratamento) | `Makefile` |

## Módulo 3 — Qualidade dos dados

| Item | Status | Resposta | Onde |
|---|---|---|---|
| 3a. Fonte dos dados | ✓ | SIH/SUS (DATASUS, via PySUS e FTP), Senatran, IBGE, CNPJ (Receita), INSS, PNAD Contínua, Prosus, Wayback | Artigo §2.1 |
| 3b. Unidade de observação e moldura amostral | ✓ | Censo administrativo (não amostra): toda AIH do SUS, todo CNPJ. Unidade município × mês; universo de 1.710 municípios | Artigo §2.1, §2.3 |
| 3c. Adequação dos dados à pergunta | ✓ | SIH cobre só SUS (não rede privada) e município de residência; MEI cobre minoria dos entregadores — por isso usa-se a data da quebra, não o nível | Artigo §2.3, §4 |
| 3d. Variável de desfecho | ✓ | Taxa por 100 mil motos de internações V20–V29 em trânsito; leitura do 4º dígito por categoria; causa externa em campo secundário | Artigo §2.2; `src/vcemal/cid.py` |
| 3e. Tamanho da amostra | ✓ | 433.033 linhas de painel em 5.517 municípios; 640 tratados, 478 na janela balanceada; 510 clusters | Artigo §2.2, §3.4 |
| 3f. Dados faltantes | ✓ | 1 de 3.564 competências ausente (RR 2022-06, lacuna da fonte); 103 recuperadas do FTP; frota só desde jul/2016 (encurta a janela); população sem 2022–2023 (não interpolada) | Artigo §2.2; D-015, D-036 |
| 3g. Representatividade | ◐ | Universo completo de municípios ≥ 20 mil, mas desbalanço regional dos tratados (NE/N 15–20% contra S/SE 73–78%) pode refletir propensão a formalizar, não chegada da plataforma | Artigo Tabela 4, §4 |

## Módulo 4 — Pré-processamento

| Item | Status | Resposta | Onde |
|---|---|---|---|
| 4a. Exclusões | ✓ | Municípios < 20 mil (regra não validada); 100 mil+ fora da estimação principal (placebo ≈ 25%); coortes fora da janela balanceada em robustez | Artigo §3.4; plano §4–5 |
| 4b. Dados impossíveis ou corrompidos | ✓ | `CAR_INT` vazio, `00` e `99` não contam como preenchido; divergências do espelho Base dos Dados tratadas no adapter; municípios não casados reportados, nunca descartados | D-011, D-014, D-018 |
| 4c. Transformações | ✓ | Deflação pelo IPCA (R$ dez/2025); conversão USD→BRL pela média mensal do BCB; ano fiscal → civil por interpolação declarada; agregação AIH → município × mês | D-029, D-032 |

## Módulo 5 — Modelagem

| Item | Status | Resposta | Onde |
|---|---|---|---|
| 5a. Descrição do modelo | ✓ | (i) Regra de quebra: teste de Poisson sobre janelas de 6 meses contra linha de base de 24 meses; (ii) DiD escalonado Callaway & Sant'Anna, Sun & Abraham como robustez | Artigo §2.3–2.4; `src/vcemal/mei.py` |
| 5b. Justificativa da escolha | ✓ | Poisson: contagens raras; DiD-CS: heterogeneidade de timing; *not-yet-treated* evita comparar urbanização | Artigo §2.4; D-022 |
| 5c. Método de avaliação | ✓ | Regra: falso positivo em placebo pré-plataforma (2016) e atraso contra 65 datas externas (Wayback); auditoria cega de 75 municípios. DiD: pré-tendências, placebo V40–V49, teste de denominador endógeno | Artigo §2.3, §2.5; plano §6 |
| 5d. Seleção de modelo | ✓ | Grade de 9 configurações avaliada só contra placebo e Wayback, nunca contra internação | Artigo §2.3 |
| 5e. Hiperparâmetros | ✓ | *k* = 2, *N* = 5, α = 0,01, base 24 m, janela 6 m; janela de evento [−12, +24]; semente 20261011 | Artigo, Materiais complementares |
| 5f. Baselines | ◐ | Regra comparada a alternativas da grade e à fonte anterior (codificação manual/Wayback, descartada); estimador principal comparado a TWFE implicitamente e a Sun & Abraham (previsto) | D-039, D-040; plano §5 |

## Módulo 6 — Vazamento de dados (*data leakage*)

| Item | Status | Resposta | Onde |
|---|---|---|---|
| 6a. Separação entre dados de ajuste e de avaliação | ✓ | O tratamento foi ajustado sem acesso ao desfecho e congelado com SHA-256 antes de qualquer cruzamento; o plano foi depositado no OSF antes da estimação. É a forma, em inferência causal, de separar “treino” de “teste” | Artigo §2.3–2.4; D-006, D-041 |
| 6b. Dependências e duplicidades | ✓ | AIH duplicadas verificadas (impacto R$ 0,1 mi); dependência espacial tratada por cluster em região imediata | Pré-projeto; D-025 |
| 6c. Legitimidade das variáveis | ✓ | Tratamento usa só informação disponível no momento (aberturas até t+5, base passada); sem covariáveis pós-tratamento no estimando principal | Artigo §2.3–2.4 |

## Módulo 7 — Métricas e incerteza

| Item | Status | Resposta | Onde |
|---|---|---|---|
| 7a. Métricas de desempenho | ✓ | Regra: % de disparo no placebo, % de atraso contra Wayback, % de cobertura da lista do iFood, concordância na auditoria (≥ 2/3). Causal: ATT médio em [0, +24], em nível e em % | Artigo §2.3–2.5 |
| 7b. Quantificação da incerteza | ◐ | IC 95% com cluster em 510 regiões imediatas e em município, lado a lado; wild bootstrap para coortes pequenas. A ser reportado na estimação | Plano §5 |
| 7c. Adequação dos testes estatísticos | ✓ | Teste bilateral pré-declarado; H1 única confirmatória; demais com critérios próprios | Plano §5; D-043 |

## Módulo 8 — Generalização e limitações

| Item | Status | Resposta | Onde |
|---|---|---|---|
| 8a. Validade externa | ✓ | Efeito é de “chegada de entregador formalizado” em municípios de 20–100 mil; não se estende a capitais nem à plataforma X; é piso por três razões distintas (diluição, pré-período contaminado, denominador endógeno) | Artigo §4 |
| 8b. Contextos em que os resultados não se generalizam | ✓ | Municípios < 20 mil; rede privada de saúde; óbitos pré-hospitalares (SIM, fora); entregadores de bicicleta para o desfecho principal; período pós-2021 com possível contaminação por e-commerce | Artigo §4; plano §4 |

**Síntese.** 29 itens atendidos, 3 parciais (3g, 5f, 7b), nenhum não atendido. Os parciais dependem da estimação causal, que é a etapa seguinte ao pré-registro.
