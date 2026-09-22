# Dicionário do painel município × mês

Gerado por `scripts/sih_pipeline.py`. Uma linha por município de residência ×
ano × mês × grupo de vítima.

| Campo | Tipo | Descrição |
|---|---|---|
| `uf` | str | UF do arquivo SIH de origem |
| `ano`, `mes` | int | Competência |
| `municipio_res` | str | Código IBGE de 6 dígitos do município de residência (`MUNIC_RES`) |
| `grupo` | str | `motociclista` (V20–V29), `ciclista` (V10–V19), `auto_placebo` (V40–V49) |
| `internacoes` | int | AIH no grupo, **inclusive as de não-trânsito** — o filtro de trânsito é do desfecho, não da inclusão no painel |
| `internacoes_condutor` | int | Quarto dígito `.4` — condutor em acidente de trânsito. Vale nas duas estruturas |
| `internacoes_transito` | int | Quarto dígito indicando acidente de trânsito, **lido conforme a estrutura da categoria** (D-010) |
| `internacoes_embarque` | int | Subconjunto de `internacoes_transito`: `.3` da estrutura padrão (embarque/desembarque). Isolado para análise de sensibilidade — ver D-010 |
| `homens` | int | `SEXO` = 1 |
| `idade_media` | float | Média de idade em anos completos |
| `faixa_18_39` | int | Internações na faixa de 18 a 39 anos (marginal) |
| `homem_18_39` | int | **Cruzamento** de sexo e faixa — não é reconstruível das marginais. Perfil do H3; ~50% das internações de motociclista |
| `condutor_homem_18_39` | int | O mesmo, restrito a condutor (`.4`). Recorte **secundário**: ~5% do desfecho, e `.4` vs `.9` é prática de codificação que varia por hospital e UF — ver D-023 |
| `dias_perm_total` | int | Soma de `DIAS_PERM` |
| `internacoes_uti` | int | `UTI_MES_TO` > 0 |
| `obitos` | int | `MORTE` = 1 (óbito hospitalar; não captura óbito pré-hospitalar — ver SIM) |
| `val_tot` | float | Soma de `VAL_TOT` em reais nominais. **Deflacionar antes de usar.** Valor pago pelo SUS, não custo econômico |
| `nexo_ocupacional` | int | `CAR_INT` em {03, 04} |
| `car_int_preenchido` | int | `CAR_INT` com código do domínio (`01`–`06`). Branco e as sentinelas `00`/`99` **não** contam — ver D-011 |

## Denominadores

Vêm de `scripts/denominadores.py`, gravados em
`data/painel/denominadores_municipio_mes.parquet` e juntados ao painel com
`--painel`. Join à esquerda: o painel manda, e município-mês sem denominador
fica `NA` — a taxa sai `NaN`, de propósito.

| Campo | Tipo | Descrição |
|---|---|---|
| `frota_moto` | int | `MOTOCICLETA + MOTONETA + CICLOMOTOR + SIDE-CAR` do Senatran. **Não** é a coluna `MOTOCICLETA` sozinha — ver D-013 |
| `populacao` | int | Estimativa residente do IBGE, anual. **Sem 2022 e 2023** (D-015) |
| `taxa_por_frota` | float | `100.000 × internacoes / frota_moto`. Denominador zero vira `NaN`, nunca infinito |
| `taxa_por_populacao` | float | `100.000 × internacoes / populacao`. Controle, não desfecho principal |

**Cobertura.** Frota municipal existe a partir de **julho/2016**; população não
tem 2022 nem 2023. Os dois buracos são no denominador e estão declarados em
D-015 — não são imputados.

**Agrupamento dos erros-padrão.** A região imediata do IBGE é o nível de
cluster (D-025), disponível em `vcemal.extract.ibge.listar_municipios()` no campo
`regiao_imediata` — 510 regiões, presente nos 5.571 municípios. Não é o nível de
atribuição do tratamento (município), e isso é deliberado: o transbordamento que
faz `municipio_res` divergir do município do acidente também correlaciona os
erros entre vizinhos.

**O denominador certo é frota, não população** (D-003). Usar população confunde
o efeito da plataforma com o crescimento da motorização. `taxa_por_populacao`
existe para controle e para os grupos sem frota — ciclista não registra em
RENAVAM.

## Onde mora a causa externa

`V20–V29` **não** está no diagnóstico principal. A norma do SIH manda a lesão
(capítulo XIX, S/T) para `DIAG_PRINC` e a causa externa (capítulo XX) para o
diagnóstico secundário. O filtro varre `DIAG_SECUN` → `DIAGSEC1..9` →
`DIAG_PRINC` e fica com o primeiro código que cai na definição de caso.

No SIH de 2023, 99,6% das causas vêm de `DIAGSEC1` — mas a cauda em
`DIAGSEC2..5` é real e entra. Filtrar só `DIAG_PRINC` devolve **zero** AIH em
todo ano de 2016 a 2023. Ver D-017.

As colunas `causa_externa` e `campo_causa` acompanham cada AIH classificada,
para que a procedência seja auditável sem reprocessar.

## Leitura do quarto dígito

`internacoes_transito` não sai de uma regra única sobre o quarto dígito. As
categorias terminais — **V19, V29, V49** — reaproveitam `.3`, `.6` e `.8` com
outro sentido, e `.3` ali é acidente **não** de trânsito. A tabela completa está
em D-010 no log de decisões e a implementação em `src/vcemal/cid.py`, num lugar
só. V29 é categoria de alto volume no SIH: tratar as duas estruturas como uma
infla o desfecho.

## As duas taxas do `CAR_INT`

Não se confundem, e a segunda é a que responde à H4:

| Taxa | Fórmula |
|---|---|
| Preenchimento | `car_int_preenchido / internacoes` |
| Nexo ocupacional | `nexo_ocupacional / car_int_preenchido` |

O denominador do nexo é o preenchimento, **nunca** `internacoes`. Dividir por
`internacoes` mistura duas coisas distintas — o campo estar vazio e o campo
dizer "não foi trabalho" — e faz a subnotificação parecer menor do que é.
Ambas saem prontas de `vcemal.analyze.car_int` e de `make diagnostico`.

## Tabelas de custo (`make custo`)

Saem de `scripts/custo.py` em `output/tabelas/custo_por_ano.csv` (ano × grupo) e
`custo_por_uf_ano.csv` (UF × ano, só motociclista). Tudo em reais da competência
`base_precos`, deflacionado pelo IPCA número-índice (SIDRA 1737 / 2266).

| Campo | Descrição |
|---|---|
| `val_tot_nominal` | Soma de `val_tot` como veio do SIH, reais correntes de cada competência |
| `val_tot_real` | O mesmo, linha a linha a reais de `base_precos`. **O que o SUS pagou — piso** |
| `val_por_internacao_real` | `val_tot_real / internacoes` |
| `custo_social_real` | `(internacoes − obitos) × ferido grave + obitos × morto`, parâmetros do Ipea TD 2565 levados de dez/2014 a `base_precos`. **Ordem de grandeza, não valor pontual** — ver D-029 |
| `hospitalar_ipea_real` | Componente hospitalar do custo social. Comparar com `val_tot_real` mede quanto a tabela SUS fica abaixo do custo estimado |
| `perda_producao_real` | Componente de perda de produção. Recai sobre a família do acidentado, não sobre o SUS |
| `base_precos` | `AAAA-MM` dos reais em que a tabela está |

**Os três valores não se somam.** `val_tot_real` é o que foi pago; `custo_social_real` é uma
estimativa do que a sociedade perdeu, e já contém a parcela hospitalar.

## Benefícios do INSS e a lacuna (`make lacuna`)

`scripts/lacuna_inss.py` grava `data/painel/inss_uf_mes.parquet`, uma linha por
UF × ano × mês × grupo × classe, só para benefícios com CID nos grupos do projeto
e espécie de incapacidade (D-030):

| Campo | Descrição |
|---|---|
| `uf` | Sigla, lida do campo `Mun Resid` (`02009-AL-Belo Monte`), **não** da coluna `UF` do arquivo |
| `grupo` | `motociclista`, `ciclista`, `auto_placebo`, pela mesma regra de `src/vcemal/cid.py` |
| `classe` | `acidentario` (espécies 91–95, 5, 10: nexo com o trabalho reconhecido) ou `previdenciario` (31, 32, 36, 21, 4, 13, 30: o mesmo evento sem nexo) |
| `beneficios` | Concessões no mês |
| `sm_rmi_total` | Soma da renda mensal inicial, em salários mínimos |

As tabelas `lacuna_inss_por_uf_ano.csv` e `lacuna_inss_por_ano.csv` põem o SIH ao lado:

| Campo | Descrição |
|---|---|
| `meses_sih`, `meses_inss` | Competências que cada fonte cobre na chave. **Comparar só onde as duas cobrem 12** |
| `internacoes`, `internacoes_transito`, `obitos`, `sih_nexo_ocupacional` | Somas do painel do SIH para o grupo |
| `beneficios`, `acidentarios`, `previdenciarios` | Concessões do INSS com CID do grupo |
| `beneficios_por_mil_internacoes` | `1000 × beneficios / internacoes` |
| `acidentarios_por_mil_internacoes` | O mesmo, só com nexo reconhecido |
| `sih_nexo_por_mil_internacoes` | `1000 × sih_nexo_ocupacional / internacoes`, para pôr as duas cegueiras lado a lado |
| `pct_acidentario` | `100 × acidentarios / beneficios` |

**A razão não é cobertura.** Benefício exige contribuição e mais de 15 dias de
afastamento; a espécie acidentária exige empregador. Um entregador informal não
aparece em lado nenhum. A tabela mede quanto do que o SUS trata o sistema de
proteção enxerga — e o quanto disso ele chama de trabalho.

## PNAD Contínua, módulo de plataformas (`make pnad`)

`scripts/pnad_plataformas.py` escreve `pnad_plataformas.csv` (Brasil e grandes
regiões) e `pnad_plataformas_uf.csv`, uma linha por rodada × recorte × grupo.
Universo: pessoas de 14 anos ou mais ocupadas na semana de referência,
**exclusive setor público e militares**, trabalho principal — o mesmo do
informativo do IBGE (D-031).

| Campo | Descrição |
|---|---|
| `grupo` | `ocupados_privado`, `plataformizados` (`SD14001` = 1), `nao_plataformizados`, `app_entrega`, `entregadores` (app de entrega **e** ocupação de condutor, ciclista ou mensageiro), `motociclistas` (COD 8321), `motociclistas_plataformizados`, `motociclistas_nao_plataformizados` |
| `pessoas` | Soma dos pesos (`V1028`) |
| `amostra` | Pessoas na amostra. Abaixo de ~100, o recorte é ruído |
| `pct_informal` | Definição do IBGE: sem carteira, empregador ou conta-própria sem CNPJ, familiar auxiliar |
| `pct_contribuinte` | Contribui para previdência em qualquer trabalho (`VD4012`) |
| `pct_homens` | `V2007` = 1 |
| `horas_media` | Horas habituais por semana no trabalho principal (`V4039`), média ponderada |
| `rend_medio` | Rendimento habitual do trabalho principal (`VD4016`), reais correntes |
| `rend_hora` | `rend_medio / (horas_media × 4,345)` — razão de médias, como o IBGE publica |
| `rend_medio_real`, `rend_hora_real` | O mesmo, com o deflator do IBGE (por UF e trimestre) da rodada mais recente pedida |

## Receita e resultado do iFood (`make lucro`)

`scripts/lucro.py` lê a transcrição curada `docs/fontes/ifood_prosus.csv` (uma
linha por ano fiscal × métrica, com documento, URL, data de acesso e nota) e
escreve `lucro_ifood_por_ano_fiscal.csv` (abril–março, como a Prosus reporta) e
`lucro_ifood_por_ano.csv` (ano civil, interpolado). Tudo em reais da competência
`base_precos`, a mesma convenção de `make custo` (D-032).

| Campo | Descrição |
|---|---|
| `inicio`, `fim` | Competências `AAAA-MM` do ano fiscal: abril do ano anterior a março do ano |
| `*_usd_milhoes` | Como publicado pela Prosus, em US$ milhões: `receita`, `receita_comparavel` (pro-forma na regra de reconhecimento e composição mais recentes), `trading_profit` (até FY2024), `aebit` e `aebitda` (de FY2023), `gmv` |
| `cambio_medio` | R$/US$, média das médias mensais do BCB (SGS 3698) nos doze meses do ano fiscal |
| `receita_brl_nominal_milhoes` | `receita × cambio_medio`, reais correntes do ano fiscal |
| `*_brl_real_milhoes` | O mesmo, levado a `base_precos` pelo IPCA médio dos doze meses do ano fiscal |
| `receita_por_pedido_brl_real` | `receita_brl_real / pedidos`. **Quebra em FY2024** com a nova regra de receita — não comparar através do corte |
| `pedidos_milhoes` | Pedidos no ano fiscal, grupo iFood |
| `entregadores_brasil`, `estabelecimentos_brasil`, `cidades_brasil` | Estoques no fim do ano fiscal (março). Entregadores = contas ativas na plataforma, não pessoas em ocupação principal; não é o mesmo conceito da PNAD |
| `metodo` (tabela civil) | `0,25 × AF(t) + 0,75 × AF(t+1)`: janeiro a março do ano civil `t` estão em AF(t), abril a dezembro em AF(t+1). Só fluxos; estoques ficam na tabela fiscal |

**Resultado não é lucro líquido.** É o resultado operacional do segmento como a
controladora reporta, e a métrica muda em FY2025 (*trading profit* → EBIT
ajustado); FY2023 e FY2024 carregam as duas. A série é do iFood, líder de
mercado; 99Food, Keeta e Rappi não publicam — é piso do setor, não o setor.

## Cronologia de entrada e tratamento (`make cronologia`)

`scripts/cronologia.py consolidar` lê as planilhas dos dois codificadores e as
decisões do adjudicador (`docs/fontes/cronologia/`) e escreve
`cronologia_entrada.csv`, `tratamento_municipio.csv` e `pendentes.csv`. As regras
estão em `docs/protocolo-cronologia-entrada.md` e `src/vcemal/cronologia.py` (D-033).

| Campo | Descrição |
|---|---|
| `regra` (consolidado) | Qual regra de desempate produziu a linha: `R1-concordantes`, `R2-evidencia-forte`, `R3-maior-confianca`, `R3-uniao-dos-intervalos`, `R0-adjudicado:<escolha>` |
| `tratado` | Há entrada encontrada de alguma plataforma no município |
| `mes_tratamento` | `data_max` da entrada mais antiga: primeiro mês com certeza de frota própria. **É a variável de tratamento do V2** |
| `incerteza_meses` | `data_max − data_min` dessa entrada. Robustez pré-declarada exclui `> 3` |
| `confianca` | Grau da entrada que definiu o tratamento (A–D) |
| `plataformas` | Plataformas com entrada encontrada, separadas por `\|` |
| `mes_saida_total` | Mês em que a última plataforma presente saiu, se todas saíram — tratamento reverso |

Municípios fora do universo (menos de 20 mil habitantes no Censo 2022) não
aparecem: são nunca tratados por hipótese declarada.

## Advertências

- `municipio_res` ≠ município do acidente. Em região metropolitana a divergência
  é material.
- `val_tot` é limite inferior do custo. Não inclui pré-hospitalar, reabilitação,
  perda de produção nem custo material.
- `idade_media` trata menor de um ano (`COD_IDADE` ≠ 4) como 0. Não afeta a
  faixa de interesse do projeto, mas afeta a média.
