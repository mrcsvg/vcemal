# Log de decisões

Registro datado de toda escolha metodológica com mais de uma alternativa defensável. Serve para três coisas: não reabrir discussão já fechada, responder revisor com data e motivo, e distinguir o que foi decidido *antes* de ver o dado do que foi decidido depois.

**Formato:** uma entrada por decisão. Nunca editar entrada antiga — adicionar uma nova que a revise, referenciando a anterior.

---

## D-001 · Desenho é ecológico, não individual
**Data:** 2026-09-12
**Decisão:** o tratamento é medido no nível município × mês; o desfecho é o total de motociclistas internados. Não se tenta identificar o indivíduo entregador.
**Motivo:** nenhuma base administrativa pública liga uma internação a uma plataforma. O `CAR_INT` do SIH e o CBO do SINAN são as únicas aproximações e têm preenchimento sofrível.
**Consequência a declarar no paper:** o coeficiente é um piso. Ele dilui o efeito sobre entregadores no universo de todos os motociclistas. Qualquer leitura de magnitude precisa ser reescalada pela participação estimada de entregadores na frota em circulação, com o erro dessa reescala propagado.
**Alternativa rejeitada:** desenho individual via SINAN ACGR com filtro de CBO. Rejeitado por completude de CBO ruim na maioria das UFs e por cobertura heterogênea entre municípios, que é confundidor direto num painel de efeitos fixos.

## D-002 · SINAN e INSS fora do escopo inicial
**Data:** 2026-09-12
**Decisão:** V1 e a estimação principal do V2 usam apenas SIH, SIM, frota RENAVAM e população IBGE. SINAN ACGR e microdados do INSS saem da rota crítica.
**Motivo:** ambos pressupõem registro formal do trabalhador, e a população de interesse é majoritariamente informal — a PNAD indica informalidade acima de 84% entre motociclistas plataformizados e cobertura previdenciária de ~36%. As bases são abertas, mas estruturalmente cegas ao caso.
**Retorno previsto:** voltam como medida de subnotificação, comparando o volume do SIH ao volume de benefícios e CAT por UF e ano. É capítulo próprio, não insumo da estimação.

## D-003 · Denominador é frota, não população
**Data:** 2026-09-12
**Decisão:** taxa de internação de motociclista usa frota de motocicletas RENAVAM do município como denominador.
**Motivo:** usar população confunde o efeito da plataforma com o crescimento da motorização, que é forte e heterogêneo entre municípios no período.
**Exceção:** ciclista roda em contagem bruta com efeito fixo de município. Bicicleta não é veículo automotor, não registra em RENAVAM, e não existe denominador nacional. Estimativas de modal via Censo ou pesquisas OD municipais não têm cobertura nem periodicidade suficientes para um painel mensal.

## D-004 · Ciclista como teste do mecanismo, não como desfecho secundário
**Data:** 2026-09-12
**Decisão:** internações de ciclista (V10–V19) entram como teste da via causal, não como desfecho paralelo.
**Motivo:** entrega por bicicleta responde ao mesmo incentivo de remuneração por corrida e não envolve aquisição de veículo novo nem habilitação. Se o efeito estimado for pressão de entrega, deve aparecer em ciclista; se aparecer só em moto, a objeção "isto é apenas crescimento da frota" ganha força.
**Limitação:** o RENAEST praticamente não captura ciclista — o registro nasce de boletim de ocorrência e queda sem contato com veículo motorizado raramente gera BO. O teste só é viável no SIH.

## D-005 · Placebo é ocupante de automóvel
**Data:** 2026-09-12
**Decisão:** V40–V49 como grupo placebo.
**Critério de falha pré-declarado:** se o efeito estimado sobre ocupante de automóvel for estatisticamente indistinguível do efeito sobre motociclista, o desenho está capturando tendência geral de trânsito e a estimativa não sustenta interpretação causal.

## D-006 · Pré-registro antes de qualquer cruzamento tratamento × desfecho
**Data:** 2026-09-12
**Decisão:** o plano de análise é depositado com timestamp (OSF) antes de cruzar a cronologia de entrada de plataforma com as internações, inclusive em exploração gráfica.
**Motivo:** análise descritiva do SIH isolada não compromete o pré-registro; olhar a relação tratamento–desfecho compromete. Depois do depósito, especificação nova é análise exploratória declarada.

## D-007 · SIH é o desfecho, RENAEST é textura
**Data:** 2026-09-12
**Decisão:** desfecho principal vem do SIH. RENAEST entra como robustez e como fonte de características do sinistro.
**Motivo:** RENAEST é agregado e depende de alimentação pelos Detrans estaduais, com cobertura desigual entre estados e ao longo do tempo — o que o torna perigoso como desfecho num painel de efeitos fixos. O SIH captura qualquer pessoa internada no SUS, com cobertura muito mais estável.
**A verificar:** se o arquivo de Sinistros traz hora do sinistro com completude usável. Entrega tem pico de almoço e jantar; um deslocamento da distribuição horária dos sinistros de moto para 11h–14h e 18h–22h após a entrada da plataforma seria assinatura bem mais específica que o volume agregado.

## D-008 · Má qualidade do `CAR_INT` é resultado, não obstáculo
**Data:** 2026-09-12
**Decisão:** medir e reportar o percentual de internações de motociclista com `CAR_INT` em 03 (acidente no local de trabalho) ou 04 (acidente de trajeto) é um achado do V1.
**Motivo:** quantifica a cegueira do sistema de informação a uma categoria de trabalhador cujo perfil demográfico e mecanismo de lesão são conhecidos. Não é defeito de dado a corrigir — é a lacuna que o paper documenta.
**Atenção:** a tabela de domínio do `CAR_INT` mudou de versão ao longo da série. Confirmar contra a "Estrutura dos arquivos SIHSUS – RD" da competência mais antiga usada antes de encadear.

## D-009 · Microdado não é versionado
**Data:** 2026-09-12
**Decisão:** nenhum arquivo de dado no git. O repositório carrega o código que reconstrói os dados.
**Motivo:** volume, e o inventário de fontes já documenta órgão, formato e caminho de cada base — a reprodutibilidade vem de lá, não de um blob commitado.

## D-010 · O quarto dígito tem duas estruturas, não uma
**Data:** 2026-09-14
**Decisão:** a leitura do quarto caractere do CID passa a depender da categoria. Categorias de colisão e não-colisão (V10–V18, V20–V28, V40–V48) seguem a estrutura padrão; as categorias "outros e não especificados" (V19, V29, V49) seguem a estrutura terminal, que reaproveita `.3`, `.6` e `.8` com outro sentido.

| Dígito | Padrão (V20–V28) | Terminal (V29) |
|---|---|---|
| `.0` `.1` `.2` | condutor / passageiro / não esp., **não-trânsito** | idem, colisão com outro veículo a motor |
| `.3` | pessoa ao embarcar ou desembarcar | **qualquer ocupante, acidente NÃO de trânsito** |
| `.4` `.5` | condutor / passageiro, **trânsito** | idem |
| `.6` | não existe | não especificado, **trânsito** |
| `.8` | não existe | outros acidentes de transporte especificados |
| `.9` | não especificado, **trânsito** | qualquer ocupante, **trânsito** não especificado |

**Motivo:** a versão anterior aplicava uma regra única (`{3,4,5,6,7,8,9}` = trânsito) sobre o quarto dígito, independente da categoria. Isso classificava **V19.3, V29.3 e V49.3 como acidente de trânsito quando o CID-10 os define como explicitamente não-trânsito**. V29 é categoria de alto volume no SIH — é onde cai o registro sem detalhe do veículo antagonista —, então o erro não é marginal: contamina o numerador do desfecho principal e o do placebo em magnitudes diferentes, o que é pior que contaminar os dois igualmente.
**Consequência:** `internacoes_transito` cai em relação ao que a versão anterior produziria. Qualquer número gerado antes desta data está inflado e não deve ser comparado com os novos.
**Ponto em aberto — `.3` da estrutura padrão.** "Pessoa ao embarcar ou desembarcar" não traz a distinção trânsito/não-trânsito na definição da OMS. Adotamos **contar como trânsito**, seguindo a faixa `V20-V28[.3-.9]` da definição padrão do NCHS. É convenção, não definição: o painel traz `internacoes_embarque` isolando essas AIH para que a sensibilidade seja calculável sem reprocessar o SIH.
**Alternativa rejeitada:** manter a regra única e tratar a diferença como ruído. Rejeitada porque o erro é sistemático por categoria, não aleatório, e V19/V29/V49 têm peso desigual entre os três grupos do desenho.

## D-011 · `CAR_INT` em branco não é `CAR_INT` preenchido
**Data:** 2026-09-14
**Decisão:** `car_int_preenchido` conta apenas códigos do domínio (`01`–`06`). Ficam de fora string vazia e as sentinelas `00` e `99`, que circulam como "ignorado" em parte da série.
**Motivo:** a versão anterior contava `CAR_INT.notna()`, e o campo em branco no arquivo RD chega como string vazia, não como nulo — passava por preenchido. Como a taxa de nexo é `nexo / car_int_preenchido` (ver D-008 e `docs/dicionario-painel.md`), um denominador inflado por brancos **subestima a subnotificação**, que é exatamente o achado do V1. O erro empurrava o resultado na direção conveniente, o que é o pior tipo.
**A conferir antes de encadear a série:** se `00` e `99` de fato aparecem como sentinela nas competências mais antigas, ou se são código válido em alguma versão do layout. A lista está em `vcemal.cid.CAR_INT_AUSENTE`, num lugar só, e é o que os testes cobrem.

## D-012 · A lógica vive no pacote, o script é entrypoint
**Data:** 2026-09-14
**Decisão:** definição de caso em `src/vcemal/cid.py`, download em `vcemal.extract`, limpeza e agregação em `vcemal.transform`, diagnóstico em `vcemal.analyze`. `scripts/` só faz parsing de argumento, I/O e log.
**Motivo:** a definição de caso é o artefato metodológico do projeto — precisa ser testável sem rede, citável por caminho de arquivo e revisável isoladamente. Enquanto morava dentro de um script, o teste a alcançava por `sys.path.insert`, e nada impedia que uma segunda cópia da regra do quarto dígito nascesse no script seguinte.

## D-013 · A frota do denominador é a que casa com V20–V29, não a coluna `MOTOCICLETA`
**Data:** 2026-09-14
**Decisão:** o denominador de motociclista soma **`MOTOCICLETA` + `MOTONETA` + `CICLOMOTOR` + `SIDE-CAR`** do arquivo "Frota por Município e Tipo" do Senatran. `TRICICLO` e `QUADRICICLO` ficam de fora.
**Motivo:** o denominador tem que casar com o numerador, e o numerador é V20–V29. A nota de inclusão do próprio CID-10 brasileiro resolve a questão:

> **V20-V29** Motociclista traumatizado em um acidente de transporte
> *Inclui:* bicicleta motorizada · motocicleta com "side-car" · **motoneta** · patinete motorizado
> *Exclui:* **triciclo motorizado (V30-V39)** · veículo motorizado de três rodas (V30-V39)
>
> — DATASUS, CID-10 v2008

Motoneta e side-car estão nomeados; ciclomotor é a "bicicleta motorizada"/moped da mesma lista. Triciclo é mandado explicitamente para V30–V39, que não é o desfecho deste projeto.
**Magnitude, para não parecer detalhe:** em Curitiba, dezembro de 2023, `MOTOCICLETA` sozinha dá 170.754; a frota que corresponde a V20–V29 dá **204.058**. Usar a coluna óbvia inflaria a taxa em 19%, e no sentido conveniente.
**Os dois erros possíveis andam em direções opostas e nenhum aparece no resultado:** usar só `MOTOCICLETA` subestima a exposição e infla a taxa; somar triciclo e quadriciclo conta veículo cujo acidente nunca entra no numerador. A regra mora em `src/vcemal/frota.py`, num lugar só, com teste por tipo.

## D-014 · Município do Senatran casa por tabela revisada, nunca por fuzzy match
**Data:** 2026-09-14
**Decisão:** a ponte entre o nome de município do Senatran e o código IBGE usa normalização exata (caixa alta, sem acento, sem pontuação) e, para o que sobra, uma **tabela fixa e revisada a mão** em `src/vcemal/municipios.py`. Município não reconhecido é **reportado, nunca descartado nem chutado**.
**Motivo:** a normalização exata casa 5.533 de 5.572 linhas (99,3%). As 39 sobras são de três tipos: grafia divergente (`LAGEDO`/`LAJEDO`, `PARATI`/`PARATY`, e um `BARAO D0 MONTE ALTO` com zero no lugar da letra O), truncamento em 30 caracteres (`VILA BELA DA SANTISSIMA TRINDA`), e **município renomeado**, com o Senatran carregando o nome antigo.
**A evidência contra o fuzzy.** Rodamos `difflib` uma vez sobre as sobras, sob revisão, e ele **errou cinco** — todos do terceiro tipo, onde o nome novo não se parece com o velho:

| Senatran | Fuzzy sugeriu | Correto |
|---|---|---|
| `SANTAREM` (PB) | Santo André | **Joca Claudino** (2513653) |
| `SAO DOMINGOS DE POMBAL` (PB) | S. Domingos do Cariri | **São Domingos** (2513968) |
| `FORTALEZA DO TABOCAO` (TO) | Porto Alegre do Tocantins | **Tabocão** (1708254) |
| `SAO VALERIO DA NATIVIDADE` (TO) | Chapada da Natividade | **São Valério** (1720499) |
| `BOA SAUDE` (RN) | — | **Januário Cicco** (2405306) |

Um join errado num denominador não deixa rastro: a frota de um município entra na conta de outro e a taxa sai plausível e errada. Denominador que some deixa `NaN`, que se vê; denominador que casa errado, não.
**Consequência operacional:** a tabela é revisável em diff, os testes fixam cada par, e `agregar_frota` grita quando o número de não-casados passa de 20 — sinal de que o layout mudou. Com os apelidos, 2016, 2019, 2023 e 2025 casam 5.570 de 5.570 municípios reais; a única sobra é `MUNICIPIO NAO INFORMADO`, que é exclusão deliberada.

## D-015 · Cobertura dos denominadores: dois buracos a declarar
**Data:** 2026-09-14
**Decisão:** registrar como limitação, não contornar com imputação silenciosa.

**1. Frota municipal só existe a partir de julho de 2016.** A página do Senatran de 2015 publica apenas "Frota por UF e Tipo de Veículo", sem abertura municipal; 2016 tem só julho a dezembro. A janela padrão do `Makefile` começava em 2015-01, o que dá 18 meses sem denominador de frota. **Isso encurta a janela pré-tratamento disponível para o V2** e precisa entrar na escolha da janela de evento do pré-registro (seção 5).

**2. Estimativa populacional municipal não tem 2022 nem 2023.** O agregado 6579 do IBGE publica 2001–2021 e retoma em 2024: 2022 foi ano de Censo e a estimativa não foi divulgada. Quem precisar de 2022 tem que ir ao Censo, que é outra definição de população — encadear os dois sem dizer é comparar coisas diferentes. `vcemal.extract.ibge.populacao` devolve os anos que faltaram em vez de omitir linha.

**Por que não interpolar:** os dois buracos são no denominador. Interpolar população entre 2021 e 2024 embute a revisão do Censo 2022 como se fosse crescimento suave — em Curitiba a estimativa cai de 1.963.726 (2021) para 1.829.225 (2024), e essa queda é rebasing, não migração. Se a interpolação for feita depois, que seja declarada e testada contra a alternativa.

## D-016 · Frota vem da página do Senatran, não do RENAVAM de dados abertos
**Data:** 2026-09-14
**Decisão:** a frota é lida de "Frota por Município e Tipo" (`gov.br/transportes`, ~1,2 MB/mês), não do dataset `registro-nacional-de-veiculos-automotores-renavam` do portal de dados abertos.
**Motivo:** o dataset do portal traz `UF; Município; Marca Modelo; Ano Fabricação; Qtd. Veículos` — **sem coluna de tipo de veículo** — em ~136 MB por mês. Derivar "motocicleta" dali exigiria classificar dezenas de milhares de strings de marca/modelo em categorias, e o erro dessa classificação entraria direto no denominador, sem medida. O arquivo do Senatran já vem com uma coluna por tipo.
**Nota de implementação:** o nome do arquivo não é chave — o mesmo relatório aparece como `frota_por_municipio_e_tipo-dez_16.xlsx`, `frota_munic_modelo_dezembro_2019.xls`, `FrotaporMunicipioetipoDEZEMBRO2025.xlsx` e `copy2_of_Frota_por_municipio_tipo_Maro_2025.xlsx`. O **rótulo do link** é estável, e é por ele que `vcemal.extract.senatran` localiza o mês.

## D-017 · A causa externa não está no diagnóstico principal
**Data:** 2026-09-16
**Decisão:** o filtro de caso passa a procurar V10–V49 numa **união ordenada** de campos de diagnóstico — `DIAG_SECUN`, `DIAGSEC1`…`DIAGSEC9`, `DIAG_PRINC` — ficando com o **primeiro código que cai na definição de caso**, não o primeiro campo preenchido. A AIH registra de qual campo veio (`campo_causa`).
**Motivo:** a versão anterior filtrava `DIAG_PRINC`. Pela norma do próprio SIH/SUS:

> "As internações provocadas por causas externas devem ser classificadas, **no diagnóstico principal, segundo o tipo de traumatismo** (capítulo XIX, causas S e T). **No diagnóstico secundário, deve ser codificado segundo a origem da causa externa** — capítulo XX (causas V a Y). Existem situações em que é permitido que o diagnóstico principal seja classificado diretamente pelo capítulo XX."
> — DATASUS, *Morbidade Hospitalar do SUS por Causas Externas*, notas técnicas

**Isto não era imprecisão: era o desfecho inteiro.** Medido no SIH (Base dos Dados, Brasil):

| ano | motociclista na causa externa | motociclista em `DIAG_PRINC` |
|---|---|---|
| 2016 | 107.385 | **0** |
| 2019 | 117.577 | **0** |
| 2023 | 145.184 | **0** |

O pipeline produzia painel vazio em todo ano da série. Nenhum teste pegou porque as fixtures punham o código V no principal — o único lugar onde ele não está.

**Por que união e não só o secundário:** a norma permite o principal, e o dado confirma que a cauda existe. Em junho/2023, 14.235 das 14.295 AIH tiveram a causa em `DIAGSEC1`, mas **60 vieram de `DIAGSEC2`–`DIAGSEC5`** — que uma regra fixada em `DIAGSEC1` perderia.
**Por que "o primeiro que casa" e não "o primeiro preenchido":** o campo de maior precedência quase sempre traz a lesão (`S825`, `T111`). Parar no primeiro campo não nulo descartaria a AIH inteira por causa de um S no caminho.
**Precedência declarada:** `DIAG_SECUN` → `DIAGSEC1..9` → `DIAG_PRINC`. Havendo mais de um código válido, vence o de maior precedência; a regra é fixa e testada. Casos com dois códigos V distintos são raros e merecem contagem própria antes de qualquer estimação.
**Consequência:** qualquer número produzido antes desta data é vazio, não apenas enviesado.

## D-018 · Base dos Dados entra como segunda fonte, não como substituta
**Data:** 2026-09-16
**Decisão:** `vcemal.extract.bigquery` lê o SIH do espelho da Base dos Dados no BigQuery, com adapter para o domínio do arquivo RD. O caminho oficial continua sendo o `.dbc` do FTP (`vcemal.extract.sih`).
**Motivo:** o FTP do DATASUS não é alcançável de todo ambiente, e o Anexo A já previa a Base dos Dados "para conferência". Duas fontes com a mesma definição de caso tornam a divergência entre elas mensurável — e ela existe.
**Cinco divergências medidas, todas tratadas no adapter.** Cada uma produz erro silencioso, não exceção:

| # | Espelho | Arquivo RD | Efeito se ignorado |
|---|---|---|---|
| 1 | `carater_internacao` = `1`–`6` | `01`–`06` | nexo ocupacional sai **zero** |
| 2 | `sexo_paciente` = `Masculino`/`Feminino` | `1`/`3` | contagem de homens sai **zero** |
| 3 | CID partido em `_categoria` (3 car.) e `_subcategoria` (4 car.) | campo único | perde metade dos códigos, e o quarto dígito mora justamente na outra coluna |
| 4 | `sigla_uf` INTEGER e **inteiramente nula** | — | filtro por UF zera o resultado |
| 5 | `carater_internacao` **100% preenchido, sem nulos** | tem branco | infla o denominador do nexo |

**A divergência 5 é a que importa para o resultado.** A taxa de *preenchimento* desta fonte não é confiável: no RD cru há branco, aqui não há nenhum. O numerador do nexo é piso defensável; o denominador precisa vir do RD. **Reportar taxa de nexo a partir do BigQuery sem essa ressalva seria erro.**
**A conferir:** se o espelho recodificou branco para algum valor do domínio (o que empurraria AIH para `02`, a categoria dominante) ou se descartou as linhas.

## D-019 · Primeiro número do V1
**Data:** 2026-09-16
**Registro** — não é decisão, é o resultado que o V1 existe para produzir. Brasil, SIH via Base dos Dados:

**2016–2023, motociclista (V20–V29): 965.714 internações. 62 com nexo ocupacional declarado — 17 como acidente no local de trabalho, 45 como acidente de trajeto. Uma em 15.576.**

Em 2023 isoladamente: 145.761 internações de motociclista, **10** com nexo. O grupo placebo (ocupante de automóvel) teve **zero**.

**Magnitude do D-010 no dado real:** a regra achatada classificava 60.511 AIH como trânsito indevidamente em 2016–2023 (V29.3, 13.706; V29.8, 46.805) — 6,3% do desfecho. E V29 sozinha é 67% de todas as internações de motociclista, contra a expectativa de "categoria de alto volume" que o D-010 registrava sem número.

Os três números carregam a ressalva do D-018: o denominador do preenchimento vem de fonte que não tem branco. A ordem de grandeza do nexo (dezenas, em centenas de milhares) não depende disso.

## D-020 · Marketplace não é tratamento; a logística própria é
**Data:** 2026-09-17
**Decisão:** o evento de tratamento é **a data em que a plataforma passa a operar frota própria de entregadores remunerados por corrida naquele município** — não a data em que o aplicativo passou a atender a cidade.
**Motivo:** a hipótese do projeto é sobre remuneração por peça criando incentivo à velocidade e ao volume. Isso pressupõe entregador da plataforma, pago por corrida. Entre 2011 e 2017 o iFood era **marketplace**: o pedido vinha pelo app, mas quem entregava era o motoboy do restaurante, remunerado pelo restaurante. A própria empresa data a virada:

> "**It began deliveries in 2018; before then restaurants were responsible.**"
> — iFood, release institucional (`institucional.ifood.com.br/releases/brazilian-delivery-group-ifood-corners-meals-market`)

**Por que isso decide a viabilidade do V2.** O denominador de frota municipal só existe a partir de julho/2016 (D-015). Se o tratamento fosse "iFood existe na cidade", boa parte dos municípios estaria tratada antes do primeiro denominador e não haveria pré-período. Com o tratamento datado na logística própria, o marco nacional é 2018 — e o rollout municipal é escalonado:

| | municípios atendidos |
|---|---|
| 2018 | início da operação própria |
| 2019 | ~900 |
| 2023–2025 | ~1.500 |
| 2026 | ~1.700 |

De **5.570 municípios**. Para os tratados a partir de 2020, o pré-período com denominador passa de três anos.

**Variação de timing além do iFood**, com datas próprias a codificar: Rappi (~2017), Uber Eats (~2016, **saiu em março/2022**), 99Food (**novembro/2019, estreia em Belo Horizonte**; 59 cidades em janeiro/2022; saiu em 2023; retomou em agosto/2025), Keeta/Meituan (dezembro/2025), Loggi (expansão nacional 2018–2019). **As saídas são tratamento reverso** — Uber Eats e 99Food deixando municípios são variação rara e valiosa, e devem ser codificadas como evento próprio, não ignoradas.

**Consequência operacional para o F3, e é séria:** a imprensa local noticia a chegada do *aplicativo*, não a da frota. Um release de 2016 dizendo "iFood chega a [cidade]" é marketplace, não tratamento. **Dois codificadores podem concordar com kappa alto sobre o evento errado.** O protocolo de codificação precisa da distinção explícita e de um critério de desempate documentado antes de começar — ver a seção 4 do plano de análise e o item 4.4 do Anexo A.

## D-021 · O pré-período está parcialmente tratado
**Data:** 2026-09-17
**Decisão:** declarar, como limitação, que o período pré-tratamento não é livre de plataforma — apenas livre de *remuneração por corrida*.
**Motivo:** o marketplace operou de 2011 a 2017. É plausível que ele já tenha elevado o volume de entregas por moto no município, ainda que o entregador fosse do restaurante e não remunerado por corrida. Isso vaza tratamento para o "antes".
**Direção do viés:** atenuação. O contraste medido é "corrida avulsa" contra "marketplace", não contra "sem plataforma" — então o coeficiente subestima o efeito de plataformização em relação a um contrafactual sem nenhuma plataforma. **É a mesma direção do piso que o D-001 já declara, por um motivo diferente e adicional**, e as duas razões precisam aparecer separadas no paper: uma é diluição no universo de motociclistas, a outra é contaminação do período de comparação.
**O que não fazer:** tratar a entrada do marketplace como um segundo evento e estimar os dois. Sem dado de volume de pedidos (lacuna 4.3, fechada), o marketplace não tem intensidade mensurável, e um evento sem intensidade num painel escalonado adiciona ruído sem identificar nada.

## D-022 · Grupo de comparação é not-yet-treated
**Data:** 2026-09-17
**Decisão:** o grupo de comparação do estimador de Callaway & Sant'Anna é **not-yet-treated**, não never-treated. Resolve o `[ ]` da seção 5 do plano de análise.
**Motivo:** os nunca tratados existem em volume — cerca de 3.900 dos 5.570 municípios nunca receberam operação própria de plataforma. Mas não são comparáveis: os tratados são urbanos e maiores, os nunca tratados são pequenos e rurais, por construção, porque é exatamente isso que determina a entrada da plataforma. **Comparar os dois compara urbanização, não plataforma** — e urbanização move motorização, tráfego e oferta hospitalar ao mesmo tempo, todos ligados ao desfecho.
Not-yet-treated compara município tratado em `t` com município que será tratado depois, mantendo a comparação dentro da população que a plataforma considera atendível. O Callaway & Sant'Anna suporta isso nativamente e é a razão de ele ser o estimador principal.
**Custo a declarar:** com a saturação crescendo ao longo da janela, o conjunto de not-yet-treated encolhe no fim do período, e os grupos tratados tardiamente têm comparação mais fina. Reportar o tamanho do grupo de comparação por coorte de tratamento, não só o efeito agregado.
**Alternativa rejeitada:** never-treated como comparação principal. Rejeitada pelo confundimento de urbanização acima. Pode voltar como **robustez**, restrita a municípios nunca tratados pareados por porte populacional e frota — e se o resultado divergir do principal, é sinal de que a seleção urbana está ativa, o que é informação, não fracasso.

## D-023 · O desfecho não é restrito a condutor
**Data:** 2026-09-17
**Decisão:** o desfecho principal é **V20–V29 em trânsito** (`internacoes_transito`), não o recorte de condutor. O plano de análise dizia "quarto dígito de condutor em trânsito"; está corrigido.
**Motivo — medido:** o quarto dígito `.4` (condutor) é **9,4%** das internações de motociclista; `.9` (não especificado) é **69,5%** (junho/2023, Brasil, 11.936 AIH). Restringir a condutor descartaria nove décimos dos casos.
**E o problema não é só poder.** Escrever `.4` em vez de `.9` é decisão de quem codifica, e a qualidade de codificação varia por hospital e por UF — plausivelmente melhor em municípios mais urbanizados, que são exatamente os que a plataforma atende primeiro. Condicionar em `.4` condicionaria numa variável correlacionada com o tratamento: confundimento, não só ruído.
**Consequência:** condutor permanece no painel (`internacoes_condutor`) como recorte secundário declarado, nunca como desfecho.

## D-024 · H3 é o perfil demográfico, operacionalizado sem condutor
**Data:** 2026-09-17
**Decisão:** **H3** — o efeito se concentra em homens de 18 a 39 anos. Operacionalizada como `homem_18_39` contra o complemento.
**Motivo:** é ortogonal ao placebo e testa outra coisa. O placebo (V40–V49) pergunta se é tendência geral **entre** tipos de veículo; H3 pergunta se é tendência geral **dentro** de motociclista. Os dois podem falhar independentemente, e falhar em qualquer um já é informação.
**Por que sem condutor:** pela mesma medição do D-023. `homem_18_39` cobre **50,4%** do desfecho; `condutor_homem_18_39` cobre **4,7%**. O segundo fica como secundário com a limitação escrita — reportar, não interpretar isolado.
**Consequência de código:** as marginais `homens` e `faixa_18_39` não reconstroem o cruzamento. `agregar()` passou a produzir `homem_18_39` e `condutor_homem_18_39`.

## D-025 · Erros-padrão agrupados em região imediata
**Data:** 2026-09-17
**Decisão:** agrupar em **região imediata do IBGE** (510 regiões, mediana de 9 municípios, presente nos 5.571). Município entra como robustez, na tabela principal.
**Motivo:** o tratamento é atribuído em município, e a regra de manual mandaria agrupar ali. Mas o dicionário do painel já registra que `municipio_res` ≠ município do acidente e que em região metropolitana a divergência é material. O mesmo transbordamento que embaralha a geografia do desfecho correlaciona os erros entre municípios vizinhos — agrupar em município subestimaria o erro-padrão.
**Custo:** intervalos mais largos. Assumido: **efeito que só sobrevive com cluster em município nunca foi robusto.**
**Wild cluster bootstrap** fica reservado a estimativas por coorte com poucos clusters; com 510 a assintótica basta.
**Consequência de código:** `vcemal.extract.ibge.listar_municipios()` passou a devolver `regiao_imediata`.

## D-026 · Janela de evento e ∈ [−12, +24], balanceada
**Data:** 2026-09-17
**Decisão:** janela balanceada de −12 a +24 meses; só entram coortes com os 37 tempos observados. Versão não balanceada como robustez, com a tabela de quais coortes contribuem em cada tempo de evento.
**Motivo — a aritmética escolhe o número:** denominador de frota começa em julho/2016 (D-015), coorte mais antiga é janeiro/2018 (D-020). Para ela, `e = −12` cai em janeiro/2017 — **seis meses de folga**. Em `e = −18` a folga é zero, e a coorte inicial cairia inteira a qualquer revisão de cobertura do Senatran.
**Por que a folga importa mais que o pré-período extra:** as coortes iniciais são as maiores cidades, onde a operação é mais intensa. Uma janela que as descarta não é mais precisa — estima outra coisa.

## D-027 · Terceiro teste de falha: denominador endógeno
**Data:** 2026-09-17
**Decisão:** rodar o mesmo estimador com **`frota_moto` como desfecho**. Critério pré-declarado: se o efeito sobre a frota for distinguível de zero **e** sua variação percentual for de ordem comparável à das internações, a taxa não é interpretável — o resultado principal passa a ser contagem com efeito fixo de município, e a taxa vai para o anexo com a advertência.
**Motivo:** se a plataforma faz gente comprar moto para trabalhar, numerador e denominador sobem juntos e a taxa deixa de medir risco. **É o único risco levantado que destrói o estimando em vez de apenas enviesá-lo** — por isso é ele que vira teste, e não antecipação ou transbordamento, que ficam como robustez declarada na seção 7.
**O viés é signável:** frota subindo com o tratamento *atenua* a taxa. Se falhar nessa direção, a estimativa é piso — somando às duas razões de piso já declaradas (D-001, diluição; D-021, contaminação do pré). **As três precisam aparecer separadas no paper**, porque têm magnitudes e remédios diferentes.
**Riscos rejeitados como teste, mantidos como robustez:** transbordamento contaminando os *not-yet-treated* da mesma região imediata (provável, e atenua); antecipação em `e = −1, −2, −3` (redundante com o teste 2); mudança de codificação coincidente com 2018 (barata de checar, mas é ameaça à medida, não ao desenho).

## D-028 · O objetivo é o critério de inclusão, não o paper causal
**Data:** 2026-09-19
**Decisão:** o projeto tem quatro pernas — as plataformas lucram, o trabalho é precário, a conta chega ao SUS, o motociclista morre ou se acidenta sem que o sistema registre — e termina em proposta de política pública. O critério de inclusão passa a ser "sustenta uma das quatro pernas ou uma linha da tabela de políticas". Revisa o critério do README ("se não reaparece no paper causal, não entra"). Documento de referência: `docs/pre-projeto.md`.
**Motivo:** o título do inventário de fontes sempre foi "remuneração por peça e **externalidade fiscal** — gasto público". As decisões D-020 a D-027 construíram a identificação causal com o cuidado devido, mas nesse caminho três pernas ficaram sem documento, sem fonte e sem alvo de `make`: não há série de lucro das plataformas, a PNAD é nota de rodapé, e `val_tot` está no painel sem nada que o use. A lacuna SIH × INSS, que D-002 chamou de "capítulo próprio" e o inventário de "segundo resultado do paper", saiu da rota crítica e nunca voltou.
**O que não muda:** o desenho causal fica inteiro. É a fração atribuível à plataforma que converte "o SUS paga por acidentes de moto" em "o SUS paga por acidentes que a remuneração por corrida causou" — sem ela, a proposta de política é opinião. Pré-registro antes do cruzamento (D-006) continua valendo.
**Consequência:** entram na rota crítica, em paralelo à cronologia de entrada (F3) e sem depender do pré-registro: (a) custo público deflacionado e convertido pelos parâmetros do Ipea; (b) lacuna SIH × INSS por UF e ano, espécies 31 e 91; (c) série anual de receita e lucro das plataformas (Bloco 6 do anexo A); (d) as quatro estatísticas do módulo de plataformas da PNAD. A profundidade do método vai para o anexo do paper; o argumento vai para o texto.

## D-029 · Custo a preços constantes: IPCA como deflator, Ipea TD 2565 como parâmetro de custo social
**Data:** 2026-09-19
**Decisão:** `val_tot` é deflacionado linha a linha, pela competência `(ano, mes)`, com o IPCA número-índice (SIDRA, tabela 1737, variável 2266) para reais de uma `base_precos` declarada na própria tabela. O custo social usa a Tabela 1A do Ipea TD 2565 (Carvalho, 2020), em R$ de dez/2014, com mapeamento fixo: AIH = ferido grave em acidente com vítimas; AIH com `MORTE = 1` = morto em acidente com fatalidade. Os parâmetros são levados à `base_precos` pelo mesmo IPCA. Implementação em `src/vcemal/custo.py` (parâmetros, sem pandas) e `src/vcemal/analyze/custo.py`.
**Motivo:** é a perna P3 ("nós pagamos", D-028) e não dependia de nada além do painel — `val_tot` estava no painel desde o início sem nenhum alvo que o usasse. IPCA é o deflator que o próprio Ipea usa no TD 2565 para atualizar a série; qualquer outro (IGP, deflator do PIB, salário) seria escolha a defender, e o argumento não precisa dela.
**Três números, que não se somam:** `val_tot_real` é o que o SUS **pagou** e é piso; `custo_social_real` é o que a sociedade **perdeu**, estimativa; `perda_producao_real` é a parte que recai sobre a família, não sobre o SUS — e é a maior componente (99% do custo de um morto, 38% de um ferido grave).
**Ressalva a carregar no paper:** a Tabela 1A vem da pesquisa de rodovias federais (Ipea/Denatran/ANTP 2006, atualizada). O Ipea não publica abertura por pessoa para aglomerados urbanos, que é onde a entrega acontece. Custo por vítima em rodovia tende a ser maior que em área urbana. O componente hospitalar do Ipea (R$ 72,9 mil por ferido grave, dez/2014) fica **duas ordens de grandeza acima** do que o SUS paga por AIH (~R$ 1,5 mil) — parte disso é a tabela SUS abaixo do custo, parte é rodovia versus cidade. Por isso o custo social é ordem de grandeza e nunca aparece sem o piso ao lado.
**Alternativa rejeitada:** atualizar os parâmetros com o fator combinado "IPCA × variação de mortes" que o Ipea usa para o agregado nacional. Esse fator corrige *quantidade* de acidentes, não preço; nosso numerador já é a contagem observada.
**Não implementado, declarado:** óbito pré-hospitalar (SIM) não entra nesta tabela — é internação que não houve. Entra na perna P4 com custo próprio quando o SIM for integrado.

## D-030 · A lacuna SIH × INSS é medida em UF × ano, por espécie, e mede invisibilidade
**Data:** 2026-09-20
**Decisão:** os benefícios concedidos do INSS entram como numerador previdenciário contra as internações do SIH, por UF e ano, restritos a CID nos grupos do projeto (V10–V19, V20–V29, V40–V49) e a espécies de incapacidade, classificadas em **acidentárias** (91, 92, 93, 94, 95 e as rurais 5 e 10: nexo com o trabalho reconhecido) e **previdenciárias** (31, 32, 36, 21 e as rurais 4, 13, 30: o mesmo evento sem nexo). Aposentadoria por idade com CID V29 é ruído de preenchimento e fica fora. Implementação em `src/vcemal/inss.py` (tabelas e regras, sem pandas), `vcemal.extract.inss`, `vcemal.transform.inss` e `vcemal.analyze.lacuna`; alvo `make lacuna`.
**Motivo:** D-002 tirou o INSS da rota crítica e prometeu voltar com ele "como medida de subnotificação, capítulo próprio". Nunca foi agendado. É a perna P3(b) do argumento (D-028): a diferença entre o que o SUS trata e o que a Previdência reconhece como acidente de trabalho é a medida direta do custo não internalizado.
**Por que UF e não município:** o município no arquivo do INSS vem em código próprio da Previdência (`02009-AL-Belo Monte`), não IBGE. Uma tabela de correspondência é trabalho de arquivo que não muda o argumento; a UF está embutida no mesmo campo e é consistente em todos os anos. **A coluna `UF` do arquivo não é usada**: nos CSVs de 2020 e 2021 ela não corresponde ao município de residência.
**Por que espécie e não CAT:** a CAT tem CBO e CNAE, mas só UF do acidente e pressupõe empregador. A espécie do benefício é o que o INSS *decidiu* sobre o nexo — é a decisão que se quer medir. A CAT fica como robustez declarada.
**O que a razão mede.** Benefício exige contribuição e mais de 15 dias de afastamento; espécie acidentária exige empregador. O entregador informal (84% dos motociclistas plataformizados, PNAD) não aparece em lado nenhum. Por isso a tabela sai em *benefícios por mil internações*, nunca como "cobertura", e carrega `meses_sih` e `meses_inss` para que só se compare onde as duas fontes cobrem os doze meses. O SIH tem a sua própria cegueira (`CAR_INT`, D-008); as duas ficam lado a lado na mesma tabela, em `sih_nexo_por_mil_internacoes`.
**Primeiro número, de dois meses reais, nacional:** janeiro/2023, 75 benefícios com CID V20–V29, 15 acidentários (20%); fevereiro/2025, 188 e 26 (14%). Contra cerca de 12 mil internações de motociclista por mês no SIH (D-019), são **6 benefícios por mil internações e 1 a 2 acidentários por mil**. O nexo do SIH, no mesmo ano, é 0,07 por mil. As duas bases públicas que deveriam ver o trabalho por trás do acidente veem, juntas, menos de 1% dele. Números de um mês cada; a série completa é o que `make lacuna` produz.
**Não integrado, declarado:** o conjunto anual de 2012 a 2018 (um ZIP por ano, layout não verificado). A série mensal começa em dezembro/2018, dois anos depois do início do painel do SIH; a lacuna cobre 2019 em diante.

## D-031 · A precariedade é medida pela PNAD reproduzindo o IBGE, no recorte de motociclista
**Data:** 2026-09-20
**Decisão:** as quatro estatísticas da perna P2 (D-028) — informalidade, contribuição previdenciária, jornada e rendimento-hora — saem do microdado do módulo "Trabalho por meio de plataformas digitais" da PNAD Contínua, nas três rodadas (4T2022, 3T2024, 3T2025), com as definições do IBGE reproduzidas ao pé da letra: universo de ocupados no setor privado, plataformizado = `SD14001`, informalidade pela posição na ocupação e CNPJ, rendimento-hora como razão de médias com 4,345 semanas por mês, deflator do IBGE por UF e trimestre. Grupos: plataformizados, entregadores (app de entrega e ocupação compatível, nota 21 do informativo), motociclistas com e sem plataforma. Implementação em `src/vcemal/pnad.py`, `vcemal.extract.pnad`, `vcemal.transform.pnad`; alvo `make pnad`.
**Motivo:** o inventário já trazia os números do informativo como nota de rodapé. Reproduzi-los é o que autoriza o passo seguinte, que o IBGE não publicou: o recorte de **motociclista plataformizado** nas três rodadas, por região e por UF — a população do desfecho V20–V29. `make pnad` devolve cada número do informativo de 2024 (1.654 mil plataformizados; 71,1% informais; 35,9% contribuintes; 44,8 h; R$ 15,4/h; motociclistas plataformizados 351 mil, 84,3%, 21,6%, 45,2 h, R$ 10,8/h) com erro de arredondamento, e os de 2022 (1.319 mil; 211 e 751 mil motociclistas).
**Primeiro número, rodada de 2025, em R$ do 3T2025:**

| Motociclistas plataformizados | 2022 | 2024 | 2025 |
|---|---|---|---|
| Pessoas (mil) | 211 | 351 | 405 |
| Informalidade | 77,6% | 84,2% | 85,2% |
| Contribuem para a previdência | 20,8% | 21,6% | 19,4% |
| Horas por semana | 47,3 | 45,2 | 44,9 |
| Rendimento-hora real | R$ 9,6 | R$ 11,4 | R$ 11,4 |
| Rendimento-hora real, ocupados do setor privado | R$ 16,6 | R$ 17,7 | R$ 18,4 |

Em três anos o contingente quase dobrou, a informalidade subiu de 78% para 85% e a contribuição previdenciária caiu para um em cinco. Ganham por hora 62% do que ganha o ocupado médio do setor privado, com cinco horas a mais por semana. É a população que chega ao SIH como V20–V29 e não chega ao INSS (D-030).
**Ressalvas:** (1) a rodada de 2025 veio com renovação da amostra mestra e reponderação (Nota Técnica 02/2025); a comparação 2024→2025 carrega isso. (2) O recorte de motociclista plataformizado tem 324 a 734 pessoas na amostra; por região, algumas dezenas — os cortes regionais são indicativos, e por UF só as grandes sustentam leitura. (3) `SD14001` só vale para o trabalho principal; quem entrega como bico secundário (quesito 21 da rodada de 2025) não entra.
**Não é tratamento:** a PNAD não desce a município e não entra no painel do V2. É teto independente e calibração (anexo A, 4.1).

## D-032 · A série de lucro é a da Prosus, transcrita com citação, em reais constantes e ano fiscal
**Data:** 2026-09-20
**Decisão:** a perna P1 ("eles lucram", D-028) sai das planilhas de KPI que a Prosus publica com cada resultado anual, transcritas à mão em `docs/fontes/ifood_prosus.csv` — uma linha por ano fiscal × métrica, cada uma com documento, URL, data de acesso e nota. É o único CSV versionado do projeto, de propósito: não é dado, é citação. Regras em `src/vcemal/lucro.py` (sem pandas), câmbio em `vcemal.extract.bcb`, conversão em `vcemal.analyze.lucro`; alvo `make lucro`. Métricas: receita, receita comparável (pro-forma), *trading profit*, EBIT ajustado, EBITDA ajustado, GMV, pedidos, entregadores, estabelecimentos e cidades no Brasil, FY2019 a FY2026.
**Motivo:** o iFood é companhia fechada e não publica demonstração própria. O que existe é o que a controladora reporta por segmento, e as planilhas de KPI são a fonte primária — os relatórios anuais e releases citam delas. Ler o número da imprensa (como o inventário fazia) é ler de segunda mão.
**Três conversões, todas na tabela:** (1) dólar → real pela média mensal do BCB (SGS 3698) nos doze meses do ano fiscal, que é o que a nota de moedas da Prosus faz; (2) real corrente → real de `base_precos` pelo IPCA médio dos doze meses, o mesmo deflator de D-029; (3) ano fiscal (abril–março) → ano civil por `0,25 × AF(t) + 0,75 × AF(t+1)`, só para fluxos, com o método escrito na coluna. A tabela fiscal é a primária; a civil existe para sentar ao lado de `custo_por_ano`. Validação: FY2025 dá R$ 7,49 bilhões nominais, contra R$ 7,5 bilhões do relatório de sustentabilidade do próprio iFood.
**Dois cortes na série, declarados em vez de escondidos.** (a) Em FY2024 a Prosus mudou a regra de reconhecimento de receita e a composição do grupo iFood: a receita publicada cai de US$ 1.371 mi para 1.222 mi enquanto o crescimento em moeda local é de +21%. A coluna `receita_comparavel` traz o pro-forma da Prosus (FY2023 = US$ 905 mi na regra nova) e é ela que serve para taxa de crescimento; a publicada serve para nível. (b) Em FY2025 a Prosus trocou *trading profit* por EBIT ajustado. FY2023 e FY2024 têm as duas métricas na tabela (−65 e −83; 96 e 96) para mostrar a emenda. Republicações menores (pedidos de FY2022, EBIT de FY2025) ficam na coluna `nota` do CSV; a regra é usar a publicação mais recente que cobre o ano.
**Primeiro número, R$ de dezembro/2025, em milhões:**

| Ano fiscal (abr–mar) | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| Receita publicada | 1.824 | 5.407 | 6.547 | 8.110 | 6.632 | 7.875 | 10.203 |
| Receita comparável | — | — | — | 5.354 | 6.480 | 8.117 | 10.203 |
| Resultado operacional | −1.431 | −316 | −1.209 | −385 | 521 | 1.358 | 1.955 |
| Pedidos (milhões) | 276 | 553 | 733 | 832 | 981 | 1.261 | 1.877 |
| Entregadores ativos no Brasil (mil, fim do ano) | 170 | 209 | 232 | 217 | 314 | 443 | 621 |

O resultado operacional cruza o zero em FY2024 e quase quadruplica em dois anos. O número de entregadores ativos dobra em dois anos, de 314 mil para 621 mil. No ano civil de 2025 (interpolado), o EBIT ajustado é de R$ 1,8 bilhão — cerca de oito vezes o que o SUS pagou em 2023 por **todas** as internações de motociclista do país (R$ 221,5 milhões correntes, D-019), e três vezes o que o SUS deixou de receber por ano com o fim do DPVAT (Ipea). Com 1,7 bilhão de pedidos no ano civil de 2025, um repasse de R$ 0,15 por pedido cobriria a conta inteira que o SUS paga por internação de motociclista — número para dimensionar a linha "repasse por corrida" da tabela de políticas, não para defender antes que a fração atribuível (V2) exista.
**Ressalvas:** (1) é resultado operacional do segmento, não lucro líquido, e é a demonstração da parte interessada — cita-se como tal. (2) O grupo iFood na Prosus inclui Colômbia até FY2022, fintech (iFood Pago) e novas iniciativas; o Brasil e a entrega de comida são a quase totalidade, mas não são 100%. (3) "Entregadores ativos" é conta da plataforma (cadastros com atividade), não pessoas em ocupação principal: não se compara diretamente com os 405 mil motociclistas plataformizados da PNAD (D-031), que cobrem todas as plataformas e só o trabalho principal. (4) A interpolação para ano civil assume fluxo uniforme dentro do ano fiscal; com crescimento de 30% ao ano, o erro é de poucos por cento e fica na direção de subestimar o ano civil. (5) 99Food, Keeta e Rappi não têm abertura pública: a série é do líder, declarada como piso do setor, sem interpolação.

## D-033 · A cronologia de entrada é codificada por protocolo escrito antes, com desempate por regra e universo de 20 mil habitantes
**Data:** 2026-09-20
**Decisão:** o F3 segue `docs/protocolo-cronologia-entrada.md` (versão 1.0), congelado antes da primeira linha. Universo: os 1.710 municípios com 20 mil habitantes ou mais no Censo 2022; os demais são nunca tratados por hipótese declarada. Unidade: município × plataforma × evento, com intervalo `[data_min, data_max]` e grau de confiança A–D ou N (não encontrado, com as buscas registradas). Dois codificadores independentes, cegos ao SIH, na mesma ordem sorteada, em blocos de 100, com kappa e concordância de data por bloco. Desempate por quatro regras aplicadas em ordem por `scripts/cronologia.py consolidar` (R1 concordância → maior confiança; R2 um só achou → vale se A/B, senão adjudica; R3 discordância → maior confiança, empate forte adjudica, empate fraco vira união dos intervalos com grau D; R0 adjudicação registrada vence tudo). Tratamento: `data_max` da entrada mais antiga de qualquer plataforma, com a incerteza na tabela. As regras vivem em `src/vcemal/cronologia.py` e são testadas sem dado.
**Motivo:** D-020 já dizia que dois codificadores podem concordar com kappa alto sobre o evento errado, e o plano de análise pedia o critério de desempate "declarado antes da codificação". Não existia. Sem protocolo, cada divergência viraria conversa, e conversa depois de ver o dado é a porta pela qual o viés entra. Regra escrita e aplicada por código é auditável no diff: quem quiser saber por que Curitiba é setembro/2018 abre `desempates.csv`.
**Por que 20 mil:** o iFood atendia 1.638 cidades em março/2026 (D-032) e há 1.710 municípios de 20 mil ou mais — o corte cobre o rollout inteiro com folga, e abaixo dele a plataforma não entra por construção (D-022). Codificar os 5.570 custaria três vezes mais para datar municípios que o estimador não usa.
**Por que `data_max` e não o meio do intervalo:** é o primeiro mês em que há certeza de frota própria. Errar para depois contamina o pré-período (atenuação, mesma direção de D-021); errar para antes inventaria efeito onde não havia tratamento. Entre os dois erros, o desenho já convive com o primeiro.
**Por que a data-piso é validação, não aviso:** uma entrada do iFood em 2016 é marketplace com probabilidade um. Recusar a linha na validação é mais barato que descobrir na adjudicação — e é a única guarda contra o erro comum aos dois codificadores.
**Piloto e critério de continuidade:** 60 municípios; kappa ≥ 0,70 e ≥ 80% de datas concordantes para seguir; abaixo, o protocolo sobe de versão e o piloto é refeito. O adjudicador relê toda entrada do iFood datada antes de julho/2018.
**Não decidido, declarado:** James Delivery entra ou não (versão 1.1, depois do piloto); o mês da saída nacional da 99Food em 2023; se o Wayback guardou a lista de cidades da página de cadastro de entregadores do iFood — é o método escalável e o piloto começa por ele.


## D-034 · O extrator do SIH acompanha o PySUS 2.x, e competência já baixada não se rebaixa
**Data:** 2026-09-20
**Decisão:** `vcemal.extract.sih` passa a usar a API do PySUS 2.x — `pysus.ftp.sih(uf, ano, mes, group="RD", as_dataframe=True)` — e o `pyproject` fixa `pysus>=2.11`. O pipeline ganha retomada: competência já gravada em `data/raw/sih/uf=.../ano=.../mes=.../parte.parquet` é lida do disco em vez de rebaixada e reclassificada; `--refazer` ignora o que está em disco.
**Motivo:** o código anterior foi escrito contra a API 0.x (`pysus.ftp.databases.sih.SIH().load()`, `get_files`, `download`) e o docstring dizia, corretamente, "NÃO TESTADO CONTRA A BASE REAL" — o ambiente em que foi escrito não alcançava o DATASUS. Na primeira execução real ele quebrou em `No module named 'pysus.ftp.databases'; 'pysus.ftp' is not a package`: na 2.x, `pysus.ftp` é módulo, não pacote, e cada base virou uma função. O pin `pysus>=0.15` não protegia contra isso.
**O que a 2.x traz de graça, e muda a viabilidade da série nacional:** cache próprio em `~/pysus/downloads/`, então download interrompido retoma; leitura do espelho do catálogo em S3 por padrão, em vez do FTP do DATASUS (mais rápido e menos sujeito a queda), com `source="origin"` para conferir contra a fonte primária.
**Competência inexistente não é erro.** A 2.x devolve DataFrame vazio para mês não publicado; `baixar_mes` traduz isso em `None` com aviso, e **não** envolve a chamada em `try/except` largo — falha de rede tem que subir, não virar "mês sem dado" que sumiria do painel em silêncio. Há teste para as duas coisas.
**Primeira execução real (set/2026):** PR, janeiro/2023 — 74.743 AIH no arquivo, 755 de interesse, 537 de motociclista, 234 linhas de painel em 158 municípios. `CAR_INT` preenchido em 100% das AIH e **nenhum** nexo ocupacional, coerente com D-019.
**O filtro `group` do PySUS está quebrado, e o modo de falha é o pior possível.** No catálogo, o campo `group` do arquivo vem **nulo** — assim como `year`, `month` e `state` —, embora o caminho codifique tudo (`.../sih/RD/2015/08/AC/RDAC1508.parquet`). Pedir `group="RD"` compara contra campo nulo e devolve coleção vazia para parte das competências, de forma inconsistente: **73 das 216 primeiras competências da série nacional voltaram "sem arquivo RD" quando o arquivo existia** (AC 2015-08, 4.141 AIH; AL 2015-06, 14.411; e por aí). Isso não levanta erro — o pipeline registrava o aviso e seguia, e o painel sairia silenciosamente incompleto, com um viés que ninguém detectaria olhando a tabela final. Por isso `baixar_mes` consulta o catálogo com `download=False`, escolhe o RD **pelo nome do arquivo** (único sinal confiável) e baixa só ele; há teste de regressão que falha se `group` voltar a ser passado.
**Baixar só o RD não é otimização, é necessidade:** cada competência traz quatro grupos (RD, ER, RJ, SP) e baixar todos quadruplicaria a série nacional.
**Ressalva:** o teste do extrator dubla o PySUS. Ele fixa o contrato (grupo RD, `as_dataframe`, vazio → `None`, erro de rede sobe), não a compatibilidade com a biblioteca — essa só uma execução real verifica, e é por isso que a primeira competência de uma série longa deve ser conferida no log.

## D-035 · O SIH é baixado por UF-ano, não por competência
**Data:** 2026-09-21
**Decisão:** `vcemal.extract.sih.baixar_ano(uf, ano)` faz **uma** consulta ao catálogo pelos doze meses e deixa o PySUS baixar os arquivos RD concorrentemente, devolvendo os caminhos locais por mês; `scripts/sih_pipeline.py` percorre UF × ano e lê cada competência do arquivo já baixado. `baixar_mes` continua existindo para uso avulso.
**Motivo — medido na série nacional:** pedir mês a mês custa uma consulta ao catálogo por competência (~5 s × 3.564) e deixa o download **sequencial**. O servidor engasga: em 717 competências a mediana foi de 6 s, mas a média foi de **42 s**, com um arquivo travando **19 minutos** e parando a fila inteira. Nesse ritmo a série levaria cerca de dois dias. Pedindo o ano de uma vez, a concorrência do PySUS absorve as travadas: um ano do Espírito Santo (12 competências, 230 mil AIH) saiu em **1 min 48 s**, contra cerca de 8 minutos.
**Consequência para a retomada (D-034):** o ano só vai à rede se faltar alguma competência dele em disco. Uma execução sobre série já baixada não abre conexão nenhuma.
**Não resolvido, declarado:** o PySUS baixa com 4 trabalhadores fixos, sem ajuste exposto. Mais paralelismo exigiria vários processos com caches separados — cada processo trava o DuckDB de `~/pysus/config.db`, e dois processos concorrentes dão `Conflicting lock`. Fica como opção se a série precisar ser refeita com pressa.


## D-036 · O que falta no espelho do PySUS vem do FTP do DATASUS
**Data:** 2026-09-25
**Decisão:** `baixar_ano` busca no FTP do DATASUS (`/dissemin/publicos/SIHSUS/200801_/Dados/`) todo RD que o catálogo do PySUS não trouxer, converte o `.dbc` pelo próprio PySUS (`ExtensionFactory` → `DBC.to_parquet`) e guarda o parquet em `data/raw/sih_origem/`, separado do cache do PySUS para que a procedência continue visível. Só é "mês sem dado" o que também não existe no FTP (resposta 550); qualquer outro erro do servidor sobe.
**Motivo — medido na primeira série nacional completa (2015-01 a 2025-12):** **103 competências** voltaram sem RD no catálogo — PI 22, TO 19, MT 16, DF 9, SE 9, AM 6, MS 6, RN 6, PB 4, SP 3, RO 2, ES 1 — e as conferidas existem no FTP (`RDDF1604.dbc`, por exemplo). Não é o bug do `group` do D-034: o RD simplesmente não está no índice do espelho, que lista ER, RJ e SP da mesma competência. `source="origin"` não resolve, porque consulta o mesmo índice. Sem o recurso ao FTP o painel sairia com buracos concentrados em UFs pequenas — viés que a tabela final não mostra.
**Por que a conversão do PySUS e não um leitor próprio:** o parquet resultante tem as mesmas colunas e os mesmos tipos do espelho (conferido em DF 2016-03 × 2016-04), então `normalizar` e `classificar` não precisam saber de onde o arquivo veio.
**Também declarado:** na mesma execução, o download de MG falhou em 2016, 2023 e 2025 com exceção de mensagem vazia vinda do PySUS. O pipeline registra e segue (D-034); a retomada refaz só esses anos.
**Resultado da retomada:** as 103 competências vieram do FTP e os três anos de MG completaram; 3.563 das 3.564 competências estão em disco, e o painel tem 433.033 linhas em 5.517 municípios. **A que falta é RR 2022-06, e o buraco é da fonte:** o `RDRR2206.dbc` do próprio FTP tem 50 KB e 668 AIH, contra cerca de 300 KB e 4.300 AIH nos meses vizinhos, e nenhuma AIH de interesse. Não há o que recuperar; o mês entra no painel como ausente e fica declarado aqui.
