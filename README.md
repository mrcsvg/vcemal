# vcemal

Remuneração por peça em plataformas de entrega e internações de motociclistas no SUS: carga, custo público e identificação causal.

**Status:** em construção. Nada aqui foi submetido, revisado ou publicado.

---

## O objetivo

Enquanto as plataformas de entrega lucram, o trabalho do entregador se precariza, o motociclista morre ou se acidenta, e a conta chega ao SUS — pago por todos nós. O projeto mede as quatro coisas lado a lado e termina em proposta de política pública. O argumento inteiro, com fontes e o que falta, está em `docs/pre-projeto.md` (D-028).

## A pergunta causal

A remuneração por corrida cria incentivo à velocidade e ao volume. A hipótese é que a entrada e o adensamento de plataformas de entrega em um município elevam a incidência de internações de motociclistas por acidente de transporte, e que esse custo é absorvido pelo SUS sem contrapartida.

A dificuldade central é que **o trabalhador de plataforma não é registrado em nenhuma base administrativa como tal.** Nenhum registro público liga uma internação a uma plataforma específica. Isso torna o desenho necessariamente ecológico: tratamento no nível do município, desfecho no total de motociclistas internados. O coeficiente estimado é, por construção, um piso — ele dilui o efeito sobre entregadores no universo de todos os motociclistas.

## Os dois produtos

| | Escopo | Afirmação | Dependências |
|---|---|---|---|
| **V1 — descritivo** | Carga e custo das internações de motociclistas no SUS, série municipal | Nenhuma causal | SIH, SIM, frota RENAVAM, população IBGE |
| **V2 — causal** | Efeito da entrada de plataforma sobre incidência | Diferenças em diferenças com adoção escalonada | V1 + cronologia de entrada por município |

**O tratamento é a frota própria, não o aplicativo.** O iFood foi marketplace de 2011 a 2017 — entrega pelo motoboy do restaurante — e só passou a entregar com entregador da plataforma em 2018. Remuneração por corrida, que é a hipótese, começa aí. É o que torna o V2 viável: o denominador de frota existe desde julho/2016, então há pré-período (D-020).

O V1 não é piloto descartável: é onde moram três das quatro pernas do argumento (custo público, precariedade, invisibilidade do nexo) e todo artefato dele é insumo do V2. O critério de inclusão é o de `docs/pre-projeto.md`: se não sustenta uma das quatro pernas ou uma linha da tabela de políticas, não entra (D-028).

## Definição de caso

CID-10, capítulo XX. Duas coisas que parecem detalhe e não são:

**O código V não está no diagnóstico principal.** A norma do SIH põe a lesão (capítulo XIX, S/T) no principal e a causa externa no secundário. Filtrar `DIAG_PRINC` devolve zero AIH em todo ano da série — o filtro varre `DIAG_SECUN` → `DIAGSEC1..9` → `DIAG_PRINC` (D-017).

**O quarto dígito não tem a mesma tabela em todas as categorias.** As terminais (V19, V29, V49) reaproveitam `.3`, `.6` e `.8` com outro sentido, e `.3` ali é acidente *não* de trânsito. V29 sozinha é 67% do desfecho, então isso move 6,3% dos casos (D-010). Implementação em `src/vcemal/cid.py`.

| Grupo | CID-10 | Papel |
|---|---|---|
| Motociclista | V20–V29 | Desfecho principal |
| Ciclista | V10–V19 | Teste do mecanismo — entrega por bike não entra em frota nova |
| Ocupante de automóvel | V40–V49 | Placebo — se o efeito aparecer aqui, é tendência geral de trânsito |

Denominador de moto: frota RENAVAM municipal. **Bicicleta não tem denominador** — não é veículo automotor, não registra. Roda em contagem bruta com efeito fixo de município.

## Estrutura

```
docs/pre-projeto.md   o argumento em quatro pernas, o que falta e o cardápio de políticas
docs/                 inventário de fontes, dicionário do painel, log de decisões
docs/protocolo-cronologia-entrada.md  como datar a entrada das plataformas, antes de datar
docs/pre-registro/    plano de análise (depositar no OSF antes de cruzar tratamento × desfecho)
docs/fontes/          transcrições curadas de fontes publicadas — o único CSV versionado, porque é citação
src/vcemal/cid.py     definição de caso: grupos CID-10 e leitura do quarto dígito
src/vcemal/frota.py   tipos de veículo do RENAVAM que correspondem a V20–V29
src/vcemal/custo.py   parâmetros de custo social por vítima (Ipea TD 2565), com fonte e data-base
src/vcemal/inss.py    espécies do INSS, classe acidentária × previdenciária, leitura de CID e UF
src/vcemal/pnad.py    regras do módulo de plataformas da PNAD: informalidade, universo, ocupações
src/vcemal/lucro.py   série do iFood na Prosus: métricas aceitas, ano fiscal abril–março, ano civil
src/vcemal/cronologia.py  F3: esquema da planilha, validação, concordância e desempate por regra
src/vcemal/municipios.py  ponte nome ↔ código IBGE, com a tabela de apelidos revisada
src/vcemal/extract/   download das fontes — única camada que toca a rede
                      (sih.py = FTP DATASUS; bigquery.py = espelho Base dos Dados)
                      (inss.py = portal de dados abertos do INSS, via CKAN)
                      (pnad.py = FTP do IBGE, microdado trimestral com suplemento)
                      (bcb.py = câmbio médio mensal, SGS 3698)
src/vcemal/transform/ limpeza, classificação e agregação do painel
src/vcemal/analyze/   diagnóstico e estimação
scripts/              entrypoints executáveis (argumento, I/O e log — sem regra)
data/                 NÃO VERSIONADO — ver docs/anexo-a-inventario-fontes-de-dados.md
output/               tabelas e figuras geradas
tests/
```

A definição de caso mora em `src/vcemal/cid.py`, sozinha, sem pandas e sem rede.
É o artefato que um revisor precisa conseguir ler inteiro sem abrir o pipeline —
e o único lugar onde a regra existe.

## Reprodutibilidade

Nenhum dado vive neste repositório — a exceção é `docs/fontes/`, transcrição de números publicados pela Prosus com citação por célula, que é referência bibliográfica e não microdado. Todas as fontes são públicas e baixáveis; o inventário em `docs/anexo-a-inventario-fontes-de-dados.md` traz órgão, granularidade, cobertura temporal, formato, dicionário e latência de cada uma.

```bash
python -m venv .venv && source .venv/bin/activate
make setup         # instala o pacote em modo editável + pre-commit
make test          # roda sem rede e sem dado — a definição de caso é testável isolada
make painel        # baixa SIH e monta o painel município × mês  (precisa de FTP do DATASUS)
make diagnostico   # preenchimento do CAR_INT por ano, UF e município
make denominadores # frota de moto (Senatran) e população (IBGE) — só HTTPS
make custo         # o que o SUS pagou (deflacionado) e o custo social (Ipea) — só baixa o IPCA
make lacuna        # benefícios do INSS com CID V20–V29 contra internações do SIH — só HTTPS
make pnad          # módulo de plataformas da PNAD Contínua: precariedade por rodada e região — só HTTPS
make lucro         # receita e resultado do iFood (Prosus) em reais constantes — só baixa câmbio e IPCA
make contraste     # figura: resultado do iFood e valor pago pelo SUS no mesmo eixo — sem rede
make cronologia    # F3: concordância e desempate das planilhas dos codificadores — sem rede
make wayback       # F3: lista de cidades atendidas nos snapshots do Wayback — rodar fora da nuvem
```

`make diagnostico` lê o painel já montado e escreve `car_int_por_ano.csv`,
`car_int_por_uf_ano.csv` e `car_int_por_municipio.csv` em `output/tabelas/`.

`make custo` lê o mesmo painel, baixa o IPCA (SIDRA 1737) e escreve
`custo_por_ano.csv` e `custo_por_uf_ano.csv`: valor pago pelo SUS a preços
constantes (piso), custo social pelos parâmetros do Ipea (ordem de grandeza) e
perda de produção separada. Os três não se somam — ver D-029.

`make lacuna` baixa os arquivos mensais de benefícios concedidos do INSS, conta
os que têm CID V20–V29 separando espécie acidentária (nexo reconhecido) de
previdenciária, e escreve `lacuna_inss_por_uf_ano.csv` e `lacuna_inss_por_ano.csv`
com o SIH ao lado. A razão mede invisibilidade, não risco — ver D-030.

`make pnad` baixa o microdado das três rodadas do módulo de plataformas da
PNAD Contínua (4T2022, 3T2024, 3T2025) e escreve `pnad_plataformas.csv` e
`pnad_plataformas_uf.csv`: informalidade, contribuição previdenciária, jornada
e rendimento-hora, nominal e real, para plataformizados, entregadores e
motociclistas com e sem plataforma. Reproduz o informativo do IBGE antes de ir
além dele — ver D-031.

`make lucro` lê a transcrição curada das planilhas de KPI da Prosus
(`docs/fontes/ifood_prosus.csv`, FY2019–FY2026, cada célula com documento, URL
e data de acesso), baixa o câmbio médio mensal do BCB e o IPCA, e escreve
`lucro_ifood_por_ano_fiscal.csv` e `lucro_ifood_por_ano.csv`: receita, resultado
operacional, pedidos e entregadores ativos em reais constantes, no mesmo eixo
que `custo_por_ano`. É a demonstração da parte interessada, citada como tal —
ver D-032.

`make contraste` lê `lucro_ifood_por_ano.csv` e `custo_por_ano.csv` e escreve
`contraste_ifood_sus.csv` e a figura `contraste_ifood_sus.png`/`.svg`: resultado
operacional do iFood e valor pago pelo SUS com internações de motociclista, no
mesmo eixo de reais constantes. A emenda entre *trading profit* e aEBIT fica
visível, e a nota diz que o valor do SUS não é atribuição à plataforma.

`make cronologia` é o F3, o tratamento do V2: lê as planilhas dos dois
codificadores e as decisões do adjudicador em `docs/fontes/cronologia/`, calcula
kappa e concordância de data, aplica as regras de desempate e escreve
`cronologia_entrada.csv`, `tratamento_municipio.csv` e `pendentes.csv`. O
protocolo humano está em `docs/protocolo-cronologia-entrada.md`; a codificação
em si ainda não começou — ver D-033.

`make wayback` é o passo 1 do roteiro de busca do F3: baixa do Wayback os
snapshots da página de cidades atendidas do portal de entregadores, casa cada
item da lista com o universo e escreve `cronologia_wayback.csv` (entrada por
intervalo, tipo 3, no esquema da planilha), `wayback_snapshots.csv` e
`wayback_nao_casados.csv`. O Wayback recusa conexão de ambiente de nuvem: rode
na sua máquina. Confira os dois relatórios antes de entregar as linhas aos
codificadores — ver D-038.

Os alvos passam pelo interpretador ativo (`$(PYTHON)`, padrão `python`). Para
apontar outro: `make test PYTHON=python3.11`.

## Duas regras do projeto

**Nada de microdado no git.** Nem SIH, nem SIM, nem Parquet intermediário. O `.gitignore` cobre isso, mas a regra é anterior ao arquivo: o repositório carrega o código que reconstrói os dados, não os dados.

**O pré-registro vem antes do cruzamento.** Olhar a distribuição descritiva do SIH é livre. Cruzar cronologia de entrada de plataforma com internação, mesmo num gráfico exploratório, exige que o plano de análise já esteja depositado e com timestamp. Depois disso, especificação nova é análise exploratória declarada.

## Licença

Código sob MIT (`LICENSE`). Texto, figuras e documentação sob CC BY 4.0 (`LICENSE-docs`).
