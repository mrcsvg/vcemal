# Plano de análise — pré-registro

> **Não depositar ainda.** Este arquivo é o esqueleto. Preencher as seções marcadas
> com `[ ]` e só então depositar no OSF. Depois do depósito, este arquivo fica
> congelado — qualquer mudança vai para `docs/decisoes.md` como análise exploratória
> declarada.

## 1. Pergunta e hipóteses

- **H1** — a entrada de plataforma de entrega em um município eleva a incidência
  de internações de motociclistas por acidente de transporte.
- **H2** — o efeito é crescente na intensidade de operação. `[ ]` **Parcialmente
  identificada**: volume de pedidos por município é dado privado. Declarar o proxy
  usado e o sinal esperado do viés.
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
- **H4** — o nexo ocupacional é sistematicamente subregistrado no SIH.

## 2. Dados

Ver `docs/anexo-a-inventario-fontes-de-dados.md`. Fontes da estimação principal:
SIH/SUS (desfecho), RENAVAM (denominador), IBGE (população), cronologia de entrada
por município (tratamento, construída — ver seção 4).

## 3. Definição de caso

| Grupo | CID-10 | Papel |
|---|---|---|
| Motociclista | V20–V29 **em trânsito** (`internacoes_transito`) | Desfecho |
| Ciclista | V10–V19 | Teste do mecanismo |
| Ocupante de automóvel | V40–V49 | Placebo |

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

**O evento é a entrada da logística própria, não a do aplicativo.** O iFood
operou como marketplace de 2011 a 2017 — pedido pelo app, entrega pelo motoboy
do restaurante — e só passou a entregar com frota própria em 2018. Remuneração
por corrida, que é a hipótese do projeto, só existe a partir daí. Ver D-020.

`[x]` Data de início de **operação de frota própria** de cada plataforma em cada
município, pelo protocolo `docs/protocolo-cronologia-entrada.md` (versão 1.0,
D-033): universo dos 1.710 municípios com 20 mil habitantes ou mais no Censo
2022; dois codificadores independentes e cegos ao SIH; evidência com endereço e
grau de confiança A–D/N; kappa e concordância de data por bloco; desempate por
regra (`vcemal.cronologia.consolidar`) e adjudicação registrada em arquivo
versionado. Tratamento = `data_max` da entrada mais antiga; robustez exclui
`incerteza_meses > 3`. O hash da cronologia fechada entra neste depósito.
`[ ]` Codificação executada e cronologia fechada (`pendentes.csv` vazio).

**⚠️ Risco específico deste desenho:** a imprensa local noticia a chegada do
*aplicativo*, não a da frota. "iFood chega a [cidade]" em 2016 é marketplace.
Dois codificadores podem concordar — com kappa alto — sobre o evento errado.
O protocolo precisa de regra explícita para distinguir os dois e de critério de
desempate declarado antes da codificação; kappa alto não protege contra viés
comum aos dois codificadores.

`[x]` **Saídas também são evento.** Uber Eats saiu do Brasil em março/2022 e a
99Food em 2023. Onde a saída deixou o município sem operação própria, é
tratamento reverso — variação rara e valiosa, a codificar, não a ignorar.
Regra na seção 7 do protocolo; `mes_saida_total` na tabela de tratamento.

## 5. Especificação

Diferenças em diferenças com adoção escalonada. Estimador de Callaway &
Sant'Anna (2021) como principal, dada a heterogeneidade de timing e a conhecida
inconsistência do TWFE nesse caso. Sun & Abraham como robustez.

- Unidade: município × mês
- Efeitos fixos: município e mês-calendário
- Grupo de comparação: **not-yet-treated** (D-022). Os ~3.900 municípios nunca
  tratados existem, mas são pequenos e rurais por construção — é o porte que
  determina a entrada da plataforma. Compará-los aos tratados compara
  urbanização, não plataforma, e urbanização move motorização, tráfego e oferta
  hospitalar de uma vez. Never-treated volta como robustez, pareado por porte e
  frota; divergência entre os dois é diagnóstico de seleção urbana, não fracasso.
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
  **Por que exatamente −12:** é a janela mais larga que custa zero município. O
  denominador de frota começa em julho/2016 (D-015) e a coorte mais antiga é
  janeiro/2018 (D-020); para ela, `e = −12` cai em janeiro/2017, com **seis
  meses de folga**. Em `e = −18` a folga é zero — a coorte inicial dependeria do
  primeiro mês de denominador existente e cairia inteira a qualquer revisão de
  cobertura do Senatran.
  **Por que preservar as coortes iniciais importa:** são as maiores cidades, onde
  a operação é mais intensa e o tratamento mais forte. Uma janela que as descarta
  troca precisão por um estimando diferente.
  **Robustez:** versão não balanceada, usando todo período disponível por coorte,
  acompanhada da tabela de quais coortes contribuem em cada tempo de evento.

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
   ordem comparável à das internações, a taxa não é interpretável. Nesse caso o
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
