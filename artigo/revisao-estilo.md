# Revisão de estilo do artigo

Sugestões para aproximar o `artigo.tex` do seu jeito de escrever. Usei como referência o documento da Entrega Parcial de *Ética em Experimentação Digital* e as edições que você mesmo fez no Overleaf em 13/10. Todas as sugestões já estão aplicadas no `artigo.tex` deste PR. Abaixo, cada uma aparece com o trecho original, o novo e o motivo, para que você possa recusar qualquer uma colando o original de volta.

Nenhum resultado foi alterado. As duas únicas mudanças em afirmações numéricas corrigem imprecisões do próprio texto e estão explicadas na seção 4.

## 1. O que tomei como "seu estilo"

Do documento da Entrega Parcial (sobretudo Tema, Temática, Metodologia e Previsão de resultados):

- **A frase começa enquadrando o assunto:** "Trata-se de um position paper...", "A temática central é...", "O trabalho situa-se na intersecção entre...".
- **"Se" impessoal:** "Argumenta-se que", "Espera-se demonstrar", "prevê-se", "Reforça-se ainda".
- **A causa vem com conectivo, não com dois-pontos:** "o arcabouço regulatório vigente não fecha a lacuna, pois mira os dados e o design".
- **Enumeração dentro da frase**, com (i), (ii), (iii) ou (a) a (d), e ponto e vírgula entre os itens.
- **Aposto entre vírgulas:** "as defesas usuais do status quo, consentimento via termos de serviço, trivialidade do risco, [...], não se sustentam".
- **Travessão para acrescentar, não para dramatizar:** "— exatamente o eixo do paper".
- **Nenhum negrito no meio do texto.**

Das suas edições no Overleaf (diff entre `ee8591e` e `726219f`), você:

- trocou jargão por explicação ("dois codificadores, cegos ao SIH" virou "duas pessoas, sem acesso às datas calculadas nem às internações");
- cortou frases de efeito ("correlação temporal nada prova", "inservível", "nunca contra internações");
- tirou os travessões do resumo;
- escreveu as faixas por extenso ("15% a 20%", "20 a 100 mil habitantes");
- passou a usar a 1ª pessoa do plural ("Testamos", "Sorteamos", "o nosso método");
- trocou razões de chance por algo concreto (a probabilidade numa cidade típica de 30 mil habitantes).

Por isso **mantive a 1ª pessoa do plural** que você introduziu e usei o "se" impessoal só onde ele deixa a frase mais natural ("Trata-se de", "Considera-se acerto"). Também mantive o "— exatamente os comportamentos associados ao risco" da introdução, que é a mesma construção do seu "— exatamente o eixo do paper".

## 2. Onde o texto ainda soava automático

As partes que você já tinha reescrito (introdução, 2.2, 2.5, 2.6(b), o fim da 3.4, as limitações, as implicações e a conclusão) soam como você, e mexi pouco nelas. Os padrões se concentravam no que sobrou da versão anterior: 2.3, 2.4, 2.6(a), 3.1 a 3.6 e o começo da Discussão.

| Padrão (corpo do texto, sem tabelas e legendas) | Antes | Depois |
|---|---|---|
| Travessões | 30 | 1 |
| Negrito | 40 | 16 |
| "exatamente" / "justamente" | 6 | 3 |
| Setas "→" na prosa (fora o ciclo Explore → … → Produce) | 2 | 0 |
| "pois", "porque", "já que" | 4 | 11 |

Os 16 negritos que ficaram são rótulos de parágrafo dos Métodos ("Regra de detecção.", "Desenho." etc.) e os títulos dos três itens da 2.2. O travessão que ficou é o da introdução, citado acima.

Outros padrões, sem contagem:

- **Frases de efeito:** "A Previdência repete a cegueira.", "Quando data, data bem", "Esse número dimensiona uma política, mas não a justifica", "a coorte precoce não é escolha arbitrária".
- **Frases sem verbo, em estilo de ficha:** quase toda a 2.4 ("Desenho. Diferenças em diferenças com adoção escalonada, unidade município × mês, ...").
- **Dois-pontos fazendo o papel de "porque":** "O valor pago é piso: a tabela SUS remunera abaixo do custo".
- **Títulos que parecem manchete:** "3.5 A regra simulada: calibrada onde é usada, conservadora e incapaz de datar cidades grandes".
- **Rótulos de pergunta e resposta:** "O que já se sabe." / "O que ainda não se sabe — e por que esta versão não responde."
- **Jargão de bastidor:** "safra do dado", "cluster", "rollout", `datado` e `sem_quebra` em fonte de código no meio da frase, "o sistema de informação vê", "os modelos leem".

## 3. Sugestões, trecho a trecho

Nos parágrafos longos, mostro só as frases que mudaram.

### S1. Resumo: Resultados e Conclusão

> **Antes:** Dois modelos complementares, sem uso do desfecho, avaliam o tratamento: uma simulação de Monte Carlo da regra reproduz o falso positivo observado abaixo de 100 mil habitantes (0,6% e 3,9% simulados contra 0,7% e 3,8% observados) e mostra que a regra é conservadora (detecta 22–54% dos saltos de 2 a 5 vezes em municípios de 50–100 mil); para testar o nosso método de datação, uma regressão logística (AUC de validação cruzada 0,91) estimou quais municípios a regra consegue datar e mostrou que ela identifica a chegada dos entregadores muito menos no Nordeste e no Norte: em uma cidade típica de 30 mil habitantes, a probabilidade prevista é de 9% e 5%, contra 64% no Sudeste, mesmo comparando municípios de mesmo porte e mesma formalização anterior às plataformas. *Conclusão:* a carga é grande, crescente e invisível como acidente de trabalho; o desenho causal é viável e está travado por pré-registro.

> **Depois:** O método de datação foi testado por dois modelos complementares, nenhum dos quais usa o desfecho. Uma simulação de Monte Carlo da regra reproduz o falso positivo observado abaixo de 100 mil habitantes (0,6% e 3,9% simulados, contra 0,7% e 3,8% observados) e mostra que a regra é conservadora, pois detecta apenas 22% a 54% dos saltos de 2 a 5 vezes em municípios de 50 a 100 mil habitantes. Uma regressão logística (AUC de validação cruzada de 0,91) mostra que a regra data muito menos municípios no Nordeste e no Norte: numa cidade típica de 30 mil habitantes, a probabilidade prevista de receber data é de 9% e 5%, respectivamente, contra 64% no Sudeste, mesmo comparando municípios de mesmo porte e com a mesma formalização anterior às plataformas. *Conclusão:* a carga é grande e crescente, e quase nenhuma dessas internações aparece nos registros como acidente de trabalho. O desenho causal é viável e ficou fixado no pré-registro antes de qualquer cruzamento com o desfecho.

**Por quê:** a frase original tinha cerca de 120 palavras, misturava presente e pretérito ("avaliam", "estimou", "mostrou") e só dizia que os modelos testam o método no meio do caminho. Agora isso vem primeiro, e cada modelo tem a sua frase. "Travado por pré-registro" e o trio "grande, crescente e invisível" foram trocados por formulações literais. Também abri as primeiras frases de Resultados ("entre 2016 e 2023, foram...", "desses, 478 entram...") e corrigi o espaço dentro de `\emph{ Conclusão:}`, que grudava a palavra no ponto anterior.

### S2. Introdução, 1º parágrafo

> **Antes:** ...mediada por plataformas digitais; quase o dobro dos 211 mil de 2022. [...] Em média, estes trabalhadores ganham R$ 11,4 por hora — 62% do rendimento-hora do ocupado médio do setor privado —, com cerca de cinco horas a mais de trabalho por semana.

> **Depois:** ...mediada por plataformas digitais, quase o dobro dos 211 mil de 2022. [...] Em média, estes trabalhadores ganham R$ 11,4 por hora, o equivalente a 62% do rendimento-hora do ocupado médio do setor privado, e trabalham cerca de cinco horas a mais por semana.

**Por quê:** o ponto e vírgula separava uma oração de um fragmento. O par de travessões partia a frase bem no número que o leitor precisa guardar; com "o equivalente a" entre vírgulas, ela se lê de uma vez.

### S3. Introdução, 2º parágrafo (DPVAT)

> **Antes:** Isso ocorre justamente no período em que o DPVAT foi extinto (2021): 45% da sua arrecadação eram destinados ao custeio do atendimento dessas vítimas, e o SUS deixou de receber cerca de R$ 580 milhões por ano.

> **Depois:** Essa conta recai sobre o SUS justamente no período em que o DPVAT foi extinto, em 2021. Até então, 45% da arrecadação do seguro eram destinados ao custeio do atendimento dessas vítimas; com a extinção, o SUS deixou de receber cerca de R$ 580 milhões por ano.

**Por quê:** o "Isso" não deixava claro a que se referia (à hipótese? ao custo?). Os dois-pontos amarravam três informações numa frase só; "Até então" e "com a extinção" põem a sequência no tempo.

### S4. Introdução, objetivos

> **Antes:** (na modalidade "plataformizada") [...] Por isso, só cruzamos as datas de chegada com as internações...

> **Depois:** (na modalidade “plataformizada”) [...] Na prática, isso significa que só cruzamos as datas de chegada com as internações...

**Por quê:** "Por isso" não decorria da frase anterior, que é uma lista de objetivos. As aspas retas viravam aspas de fechamento dos dois lados no PDF; no `.tex` agora estão como ` ``plataformizada'' `.

### S5. Introdução, contribuição

> **Antes:** Ao medir a carga e o custo público desse risco, este trabalho fornece a base de que uma política pública precisa.

> **Depois:** Ao medir a carga e o custo público desse risco, este trabalho oferece parte da base empírica de que uma política pública precisa.

**Por quê:** "a base" promete mais do que uma prévia sem estimação causal entrega. A versão nova tem o tom mais contido do seu texto de referência.

### S6. 2.1 Dados, nota sobre as fontes

> **Antes:** Nenhum microdado é versionado; o repositório contém o código que os reconstrói (`Makefile`). A única exceção são transcrições de números publicados (Prosus, com citação por célula) e o arquivo de tratamento congelado.

> **Depois:** Os microdados não ficam no repositório, que guarda apenas o código para reconstruí-los (`Makefile`); as únicas exceções são as transcrições de números publicados pela Prosus, com a citação de cada célula, e o arquivo de tratamento congelado.

**Por quê:** "a única exceção são" com dois itens; "versionado" é jargão de git para o leitor da disciplina.

### S7. 2.2, abertura

> **Antes:** A exploração do SIH revelou três armadilhas que, sem tratamento, invalidariam o desfecho. Cada uma virou regra em código, com teste automatizado:

> **Depois:** A exploração do SIH revelou três problemas que, se não fossem tratados, comprometeriam a medida do desfecho. Cada um deles foi incorporado ao código como uma regra, com teste automatizado:

**Por quê:** "armadilhas" e "virou regra" são metáfora e registro oral; o resto da seção, que você reescreveu, é literal.

### S8. 2.2, itens 1 e 2

> **Antes:** ...o diagnóstico principal registra a lesão — uma fratura, por exemplo, com código do capítulo XIX da CID-10 (letras S e T) —, enquanto a causa externa [...]. Para identificar os casos, percorremos os campos em ordem — primeiro `DIAG_SECUN`, depois `DIAGSEC1` a `DIAGSEC9` e, por último, `DIAG_PRINC` — e ficamos com o primeiro código que corresponde à definição de caso.
>
> ...informa se o acidente foi de trânsito — isto é, em via pública — e quem estava no veículo. [...] O erro pesa porque a V29 sozinha concentra 67% das internações de motociclistas.

> **Depois:** ...o diagnóstico principal registra a lesão (uma fratura, por exemplo, com código do capítulo XIX da CID-10, de letras S e T), enquanto a causa externa [...]. Para identificar os casos, percorremos os campos nesta ordem: primeiro `DIAG_SECUN`, depois `DIAGSEC1` a `DIAGSEC9` e, por último, `DIAG_PRINC`. Vale o primeiro código que corresponde à definição de caso.
>
> ...informa se o acidente foi de trânsito (isto é, em via pública) e quem estava no veículo. [...] Esse erro é relevante porque só a categoria V29 concentra 67% das internações de motociclistas.

**Por quê:** três pares de travessão em dois parágrafos. Exemplo e definição cabem em parênteses; a sequência de campos pede dois-pontos e uma frase própria.

### S9. 2.2, ligação entre as bases

> **Antes:** os 39 restantes — grafias diferentes, nomes cortados e municípios que mudaram de nome — foram resolvidos por uma tabela revisada manualmente.

> **Depois:** os 39 restantes (grafias diferentes, nomes cortados e municípios que mudaram de nome) foram resolvidos por uma tabela revisada manualmente.

**Por quê:** mesmo motivo do S8.

### S10. Título da 2.3

`\subsection{2.3 \textbf{Datando...}}` → `\subsection{2.3 Datando...}`. O título já sai em negrito; o `\textbf` a mais era o único caso entre as seções.

### S11. 2.3, 1º parágrafo

> **Antes:** **O evento é a chegada do entregador remunerado por corrida, não a do aplicativo.** O iFood operou como *marketplace* de 2011 a 2017 (o restaurante entregava) e só passou a ter frota própria em 2018. Notícias locais datam a chegada do aplicativo, não da frota; uma tentativa de datar pela lista de cidades arquivada na Wayback Machine mostrou que a página do iFood era do lado do consumidor, o que não serve para esta análise.

> **Depois:** O evento que interessa a esta análise é a chegada do entregador remunerado por corrida, e não a do aplicativo. Entre 2011 e 2017, o iFood funcionou como *marketplace*: o pedido era feito pelo aplicativo, mas a entrega ficava a cargo do restaurante. A frota própria de entregadores só surgiu em 2018. Por isso, as notícias locais, que costumam registrar quando o aplicativo chegou a uma cidade, não servem para datar a chegada dos entregadores. A lista de cidades do iFood arquivada na Wayback Machine tem o mesmo problema, pois a página era voltada ao consumidor e não indicava onde havia frota própria.

**Por quê:** a frase-tese em negrito e o "não X" repetido três vezes ("não a do aplicativo", "não da frota", "não serve") dão o tom de slide. "Do lado do consumidor" era expressão de bastidor; a versão nova explica o que isso quer dizer. **Confira** se a leitura está certa: entendi que a página arquivada listava onde o cliente podia pedir, e não onde havia frota.

### S12. 2.3, 2º parágrafo

> **Antes:** ...com endereço na residência — o mesmo município de residência que o SIH registra. O sinal aparece com clareza nos números. Nos 1.710 municípios estudados, as aberturas [...] passaram de 19,4 mil em 2017 para 40,2 mil em 2018 e 50,4 mil em 2019: mais que dobraram justamente no ano em que o iFood montou sua frota própria...

> **Depois:** ...com o endereço da própria residência, que é também o município de residência registrado pelo SIH. Nos 1.710 municípios estudados, as aberturas [...] passaram de 19,4 mil em 2017 para 40,2 mil em 2018 e 50,4 mil em 2019. Ou seja, mais que dobraram no mesmo ano em que o iFood montou sua frota própria...

**Por quê:** "O sinal aparece com clareza nos números" anuncia o que a frase seguinte já mostra. O travessão e os dois-pontos davam ar de frase de efeito a informações que são apenas sequenciais.

### S13. 2.3, Calibração dos hiperparâmetros

> **Antes:** *k* e *N* foram escolhidos por busca em grade, *k* ∈ {1,5; 2; 3} × *N* ∈ {3; 5; 8}, avaliada **apenas** contra (a) um placebo pré-plataforma — a taxa de quebras detectadas em jan–jun/2016, quando nenhuma plataforma tinha frota própria — e (b) 65 datas de entrada de Rappi e Uber Eats com confiança C extraídas da Wayback Machine, além da lista de 453 cidades com frota do iFood. Nenhuma métrica usou internações. *k* = 3 deixava 63% das entradas conhecidas sem quebra ou com quebra tardia; *k* = 1,5 disparava mais no placebo. A configuração escolhida, *k* = 2, *N* = 5, tem 7,7% de atraso nas 65 entradas e detecta quebra até dez/2023 em 85% das 453 cidades da lista de frota do iFood.

> **Depois:** Os valores de *k* e *N* foram escolhidos por busca em grade (*k* ∈ {1,5; 2; 3} × *N* ∈ {3; 5; 8}), avaliada apenas contra dois critérios: (a) um placebo anterior às plataformas, isto é, a taxa de quebras detectadas entre janeiro e junho de 2016, quando nenhuma plataforma tinha frota própria; e (b) 65 datas de entrada de Rappi e Uber Eats extraídas da Wayback Machine com confiança C (intervalo de até seis meses entre capturas), além da lista de 453 cidades com frota do iFood. Nenhuma métrica usou internações. Com *k* = 3, 63% das entradas conhecidas ficavam sem quebra ou com quebra tardia; com *k* = 1,5, a regra disparava com mais frequência no placebo. A configuração escolhida (*k* = 2, *N* = 5) atrasa 7,7% das 65 entradas e detecta quebra até dezembro de 2023 em 85% das 453 cidades da lista de frota do iFood.

**Por quê:** a frase não deve começar com símbolo ("*k* e *N* foram", "*k* = 3 deixava"). "Confiança C" não estava definida no artigo; a definição vem do D-038 do log ("confiança C até 6 meses"). Os critérios agora seguem o seu formato de enumeração, com (a) e (b) separados por ponto e vírgula.

### S14. 2.3, Congelamento

> **Antes:** foi congelado com no repositório do projeto com SHA-256 `128999bd…7654a2` antes de qualquer cruzamento com o SIH; o script desta versão verifica o hash antes de rodar.

> **Depois:** foi congelado no repositório do projeto, com o hash SHA-256 `128999bd…7654a2`, antes de qualquer cruzamento com o SIH; o script desta versão confere esse hash antes de rodar.

**Por quê:** "congelado com no" sobrou de uma edição anterior.

### S15. 2.4, Desenho

> **Antes:** Diferenças em diferenças com adoção escalonada, unidade município × mês, estimador de Callaway & Sant'Anna (2021) como principal — o estimador de efeitos fixos bidirecionais (TWFE) é inconsistente com efeitos heterogêneos no tempo de adoção (Goodman-Bacon, 2021) — e Sun & Abraham (2021) como robustez.

> **Depois:** Trata-se de um desenho de diferenças em diferenças com adoção escalonada, tendo o município × mês como unidade. O estimador principal é o de Callaway & Sant'Anna (2021), e o de Sun & Abraham (2021) entra como robustez. O estimador tradicional de efeitos fixos bidirecionais (TWFE) não foi adotado porque é inconsistente quando o efeito varia conforme o momento de adoção (Goodman-Bacon, 2021).

**Por quê:** era uma ficha sem verbo, com a justificativa do TWFE enfiada entre travessões no meio da lista. "Trata-se de" é a sua abertura típica.

### S16. 2.4, Estimando principal, grupo de comparação, erros-padrão e inferência

> **Antes:** **Estimando principal (H1):** média simples dos ATT(*e*) para *e* ∈ [0, +24] meses na janela balanceada *e* ∈ [−12, +24], sem covariáveis, também em % da média pré-tratamento dos tratados. **Grupo de comparação:** *not-yet-treated* (municípios ainda não tratados), entre `datado` e `sem_quebra` — comparar com nunca tratados compararia urbanização, não plataforma. **Erros-padrão:** agrupados nas 510 regiões imediatas do IBGE, porque entregador e paciente circulam na região; cluster em município aparece ao lado, na tabela principal. **Inferência:** bilateral a 5%; H1 é sustentada se o estimando for positivo e o IC 95% excluir zero.

> **Depois:** **Estimando principal (H1).** É a média simples dos efeitos ATT(*e*) para *e* ∈ [0, +24] meses, na janela balanceada *e* ∈ [−12, +24], sem covariáveis; o resultado também é apresentado em porcentagem da média pré-tratamento dos tratados. O grupo de comparação é formado pelos municípios ainda não tratados (*not-yet-treated*), tanto `datado` quanto `sem_quebra`. A comparação com municípios nunca tratados foi descartada porque, na prática, compararia graus de urbanização, e não a presença das plataformas. Os erros-padrão são agrupados nas 510 regiões imediatas do IBGE, já que entregadores e pacientes circulam pela região; a versão agrupada por município aparece ao lado, na tabela principal. A inferência é bilateral, a 5%: H1 é sustentada se o estimando for positivo e o IC 95% excluir o zero.

**Por quê:** quatro rótulos em negrito num só parágrafo, todos seguidos de fragmentos. Em prosa, cada decisão vem com o seu motivo ("foi descartada porque", "já que").

### S17. 2.4, Hipóteses secundárias

> **Antes:** H2 — gradiente do efeito na intensidade (tercis de aberturas de MEI por mil habitantes nos 12 meses após a quebra); H3 — concentração em homens de 18–39 anos, o perfil do trabalho de entrega (50,4% do desfecho), contra o complemento; H5 — o mesmo estimando aplicado às **mortes** [...]. **H4**, descritiva e fora do desenho causal, é o subregistro do nexo ocupacional...

> **Depois:** A H2 testa se o efeito cresce com a intensidade da chegada, medida pelos tercis de aberturas de MEI por mil habitantes nos 12 meses após a quebra. A H3 testa se o efeito se concentra em homens de 18 a 39 anos, o perfil típico do trabalho de entrega (50,4% do desfecho), em comparação com os demais. A H5 aplica o mesmo estimando às mortes de motociclistas em trânsito registradas no SIM [...]. Já a H4 é descritiva e fica fora do desenho causal: trata do subregistro do nexo ocupacional...

**Por quê:** cada hipótese ganha um verbo ("testa se", "aplica"). "Contra o complemento" vira "em comparação com os demais". O "Já a H4" explica por que ela aparece por último.

### S18. 2.4, Testes de falha

> **Antes:** **Testes de falha declarados antes:** (1) placebo em ocupantes de automóvel indistinguível do efeito em motociclistas → tendência geral de trânsito; (2) pré-tendências não paralelas → sem leitura causal; (3) **denominador endógeno** — o mesmo estimador com a frota de motos como desfecho; se o efeito percentual...

> **Depois:** **Testes de falha declarados de antemão.** (1) Se o efeito no placebo (ocupantes de automóvel) for indistinguível do efeito em motociclistas, o resultado será lido como tendência geral do trânsito. (2) Se as tendências anteriores ao tratamento não forem paralelas, não haverá leitura causal. (3) Para verificar se o denominador é endógeno, o mesmo estimador é aplicado à frota de motos como desfecho; se o efeito percentual...

**Por quê:** setas são notação de caderno. Cada teste vira uma frase "se..., então...", que é o que ele de fato é.

### S19. 2.4, Pré-registro

> **Antes:** ...foram depositados no OSF Registries (modelo *OSF Preregistration*) (doi: ...), apontando para a tag `pre-registro-v1` do repositório. Todo desvio posterior vai para o log como análise exploratória declarada.

> **Depois:** ...foram depositados no OSF Registries, no modelo *OSF Preregistration* (doi: ...), com referência à tag `pre-registro-v1` do repositório. Qualquer desvio posterior será registrado no log e apresentado como análise exploratória.

**Por quê:** dois parênteses colados e o "vai para o log", que é oral.

### S20. Título e abertura da 2.6

> **Antes:** Dois modelos avaliam o tratamento construído antes da estimação causal. Nenhum usa internações; ambos leem só o arquivo congelado...

> **Depois:** Antes da estimação causal, o tratamento construído foi avaliado por dois modelos. Nenhum deles usa internações: ambos trabalham apenas com o arquivo congelado...

**Por quê:** "antes da estimação causal" ficava ambíguo (o tratamento foi construído antes, ou avaliado antes?). Modelo não "lê". O título da 2.6 também tinha uma chave sem fechar; veja a seção 4.

### S21. 2.6(a), os dois experimentos

> **Antes:** Dois experimentos: [...] *Falso positivo:* séries sem quebra, [...] contando quebras na janela do placebo (jan–jun/2016). O nulo é Poisson puro e, depois, gama-Poisson com choques [...] que representam aceleração local que não é plataforma. [...] *Poder:* séries de 2015-01 a 2025-12 [...]. Acerto é a quebra datada entre 5 meses antes (a regra data o primeiro mês da janela com abertura) e 12 meses depois do salto; quebra antes disso é espúria e esconde a verdadeira, porque a regra fica com a primeira.

> **Depois:** Foram feitos dois experimentos: [...] *Falso positivo:* foram geradas séries sem quebra, [...] e contadas as quebras detectadas na janela do placebo (janeiro a junho de 2016). A hipótese nula é, primeiro, um processo de Poisson puro e, depois, um gama-Poisson com choques [...] que representam acelerações locais sem relação com as plataformas. [...] *Poder:* foram geradas séries de 2015-01 a 2025-12 [...]. Considera-se acerto a quebra datada entre 5 meses antes do salto (porque a regra data o primeiro mês da janela com abertura) e 12 meses depois. Uma quebra anterior a esse intervalo é espúria e esconde a verdadeira, já que a regra só registra a primeira.

**Por quê:** fragmentos sem verbo ("Dois experimentos:", "séries sem quebra, ..."); "aceleração local que não é plataforma" e "a regra fica com a primeira" são fala de bastidor.

### S22. 3.1 Carga e custo público

> **Antes:** Em 2016–2023 o SUS registrou **965.714 internações de motociclistas**; 145.761 só em 2023. [...] Como validação externa, a tabulação da Abramet sobre o mesmo SIH dá R$ 221,5 milhões (+3,9%) e R$ 1.561 por AIH (+0,9%); a diferença está na contagem, e a hipótese é safra do dado (reapresentações posteriores). Em 2025, a preços de dez/2025, o SUS pagou **R$ 288 milhões**.
>
> O valor pago é piso: a tabela SUS remunera abaixo do custo, e o componente hospitalar por ferido grave nos parâmetros do Ipea (TD 2565) é duas ordens de grandeza maior que o valor médio da AIH. Por isso o custo social (Ipea) é reportado à parte, como ordem de grandeza, e nunca somado ao valor pago.

> **Depois:** Entre 2016 e 2023, o SUS registrou 965.714 internações de motociclistas, sendo 145.761 só em 2023. [...] Como validação externa, a tabulação da Abramet sobre o mesmo SIH chega a R$ 221,5 milhões e R$ 1.561 por AIH; os nossos valores são, portanto, 3,9% e 0,9% maiores. A diferença está no número de internações contadas, e a hipótese é que ela venha da data de extração dos dados, já que o SIH incorpora AIHs reapresentadas depois da competência original. Em 2025, a preços de dezembro de 2025, o SUS pagou R$ 288 milhões.
>
> Esse valor deve ser lido como um piso. A tabela SUS remunera abaixo do custo, e o componente hospitalar por ferido grave nos parâmetros do Ipea (CARVALHO, 2020) é duas ordens de grandeza maior que o valor médio da AIH. Por isso, o custo social calculado com esses parâmetros é tratado à parte, apenas como ordem de grandeza, e nunca é somado ao valor pago.

**Por quê:** "+3,9%" ao lado do número da Abramet dava a entender que a Abramet é que estava acima; o certo é o contrário (230,1 / 221,5 = 1,039). "Safra do dado" é jargão. Tirei os negritos dos números, que o seu estilo não usa, e passei "TD 2565" para a chamada da referência que já está na lista.

### S23. 3.2 Invisibilidade ocupacional

> **Antes:** Das 965.714 internações de 2016–2023, **62** têm o campo `CAR_INT` preenchido [...] ou de trajeto (45): **uma em 15.576** (Figura 4). Em 2023 foram 10. O grupo placebo (ocupantes de automóvel) teve zero.
>
> A Previdência repete a cegueira. [...] mas a exploração mostrou que se trata de **quebra de série**, não de mudança de risco: a partir de nov/2023 a concessão por análise documental (Atestmed) passa a dominar [...]. Esse canal responde por 65% dos benefícios de motociclistas em 2024–2025; anos dos dois lados da quebra não se comparam pelo total.

> **Depois:** Das 965.714 internações de 2016 a 2023, apenas 62 têm o campo `CAR_INT` preenchido [...] ou de trajeto (45), o equivalente a uma em cada 15.576 (Figura 4). Em 2023, foram 10. No grupo placebo, de ocupantes de automóvel, não houve nenhuma.
>
> O mesmo padrão aparece nos registros da Previdência. [...] mas a exploração dos dados mostrou que o salto se deve a uma quebra de série, e não a uma mudança no risco. A partir de novembro de 2023, a maior parte dos benefícios passou a ser concedida por análise documental (Atestmed) [...]. Como esse canal responde por 65% dos benefícios de motociclistas em 2024–2025, os totais de antes e depois da mudança não são comparáveis.

**Por quê:** "A Previdência repete a cegueira" é a frase mais "de efeito" do artigo. Os dois-pontos explicativos viraram frases com "Como...", e os negritos saíram.

### S24. 3.3, validação da PNAD

> **Antes:** O pipeline reproduz, com erro de arredondamento, todos os números do informativo do IBGE para 2024 (...), o que valida o recorte novo de motociclistas, que o IBGE não publica.

> **Depois:** Para validar o recorte, o mesmo código foi aplicado ao conjunto dos trabalhadores plataformizados e reproduziu, com diferenças apenas de arredondamento, todos os números do informativo do IBGE para 2024 (...). Isso dá segurança ao recorte de motociclistas, que o IBGE não publica.

**Por quê:** a frase pressupunha que o leitor sabe o que é "o pipeline" e por que reproduzir os números do IBGE valida um recorte que o IBGE não publica. Agora a lógica está explícita.

### S25. 3.3, iFood e SUS

> **Antes:** O resultado operacional do iFood cruza o zero em FY2024 [...]. Com ~1,7 bilhão de pedidos no ano, menos de R$ 0,20 por pedido cobriria essa conta. Esse número dimensiona uma política, mas não a justifica: a fração das internações atribuível à plataforma é exatamente o que a estimação causal vai medir.

> **Depois:** O resultado operacional do iFood passa a ser positivo em FY2024 [...]. Com cerca de 1,7 bilhão de pedidos no ano, menos de R$ 0,20 por pedido cobriria essa conta. Esse número dá a ordem de grandeza de uma eventual política, mas não basta para justificá-la. Para isso, é preciso saber que parte das internações se deve às plataformas, e é essa fração que a estimação causal pretende medir.

**Por quê:** "dimensiona, mas não justifica: ... é exatamente o que" é aforismo; a versão nova diz a mesma coisa em duas frases simples. "~" é notação.

### S26. 3.4, onde a regra vale

> **Antes:** A taxa de falso positivo do placebo define onde a regra vale. [...] acima, com muitas aberturas, qualquer aceleração local passa no teste (≈ 25%). Por isso os 319 municípios de 100 mil+ — todos com iFood já em 2019 — formam uma **coorte precoce** fora da estimação principal, e a variação temporal vem dos 640 municípios `datado` de 20–100 mil.

> **Depois:** A taxa de falso positivo no placebo indica em quais municípios a regra pode ser usada. [...] acima desse porte, com muitas aberturas por mês, qualquer aceleração local passa no teste (cerca de 25%). Por isso, os 319 municípios com 100 mil habitantes ou mais, todos com iFood já em 2019, formam uma *coorte precoce* e ficam fora da estimação principal. A variação no tempo vem, portanto, dos 640 municípios de 20 a 100 mil habitantes que receberam data.

**Por quê:** "100 mil+", "≈" e `datado` em fonte de código são notação de planilha. O termo novo "coorte precoce" foi para itálico, que é o uso normal para introduzir um termo.

### S27. 3.4, Figuras 1 e 2

> **Antes:** As quebras se espalham por todo o período (Figura 1), com pico em 2018–2021 — coerente com o *rollout* da frota própria do iFood [...]. A Figura 2 mostra a adoção escalonada: ao fim de 2025, 46% dos 1.391 municípios de 20–100 mil estão tratados, o que preserva um grupo *not-yet-treated* ao longo de toda a janela.

> **Depois:** As quebras se distribuem por todo o período (Figura 1), com pico entre 2018 e 2021, o que é coerente com a expansão da frota própria do iFood [...]. A Figura 2 mostra a adoção escalonada: ao fim de 2025, 46% dos 1.391 municípios de 20 a 100 mil habitantes estavam tratados, de modo que há municípios ainda não tratados para servir de comparação ao longo de toda a janela.

**Por quê:** "rollout" tem equivalente em português, e "preserva um grupo *not-yet-treated*" diz em inglês técnico o que cabe numa oração simples.

### S28. 3.4, Janela de estimação

> **Antes:** Com a frota municipal começando em jul/2016 e o SIH terminando em dez/2025, a janela balanceada [−12, +24] admite coortes de 2017-07 a 2023-12: **478 dos 640** municípios `datado`. Ficam de fora 50 com quebra anterior e 112 com quebra posterior, que voltam nas versões não balanceada e de contagem.

> **Depois:** Como a série de frota municipal começa em julho de 2016 e o SIH vai até dezembro de 2025, a janela balanceada [−12, +24] só admite coortes de 2017-07 a 2023-12, o que inclui 478 dos 640 municípios com data. Ficam de fora 50 municípios com quebra anterior a esse intervalo e 112 com quebra posterior; eles voltam a ser usados nas versões não balanceada e de contagem.

**Por quê:** causa explícita ("Como...") no lugar de gerúndios encadeados; "50 com quebra anterior" pedia o substantivo.

### S29. Título e 1º parágrafo da 3.5

Título: "A regra simulada: calibrada onde é usada, conservadora e incapaz de datar cidades grandes" → **"Simulando a regra: falsos positivos e capacidade de detecção"**, no mesmo formato de gerúndio que você deu à 2.3 e à 2.6.

> **Antes:** Abaixo de 100 mil habitantes, o falso positivo observado é exatamente o que ruído de contagem com superdispersão moderada produz (Tabela 5 e Figura 5, à esquerda): as quebras espúrias ali são acaso. Acima de 100 mil, o placebo observado é o dobro do que mesmo uma superdispersão forte gera — há acelerações locais reais nas aberturas antes de qualquer plataforma, que a regra não distingue da chegada do entregador. A simulação confirma, por um caminho independente, o corte de 100 mil que o desenho já adotava: a regra não serve para datar cidades grandes, e a coorte precoce não é escolha arbitrária.

> **Depois:** Abaixo de 100 mil habitantes, o falso positivo observado é compatível com o que o simples ruído de contagem, com superdispersão moderada, produziria (Tabela 5 e Figura 5, à esquerda). Ou seja, as quebras espúrias nesses municípios são obra do acaso. Acima de 100 mil, o falso positivo observado fica entre 1,5 e 2 vezes o que mesmo uma superdispersão forte gera, o que indica acelerações reais nas aberturas antes de qualquer plataforma, que a regra não consegue distinguir da chegada dos entregadores. A simulação confirma, por um caminho independente, o corte de 100 mil habitantes que o desenho já adotava: a regra não serve para datar cidades grandes, e a separação da coorte precoce tem base empírica.

**Por quê:** "exatamente" exagera (0,7 observado contra 0,5 a 0,6 simulados) e "o dobro" só vale para a faixa de 100 a 250 mil; veja a seção 4. "Não é escolha arbitrária" responde a uma objeção que ninguém fez.

### S30. 3.5, 2º parágrafo

> **Antes:** A regra é **conservadora** [...]. Como exige ao menos 5 aberturas em 6 meses, num município de 20–50 mil — mediana de zero abertura por mês em 2015–2016 — só saltos de 10 vezes ou mais são datados com frequência. Quando data, data bem: o atraso mediano é de 0 a 2 meses [...]. A consequência direta é que parte dos 751 `sem_quebra` recebeu plataforma, mas com poucos entregadores formalizados para a regra ver. Isso atenua o efeito estimado e dá peso empírico à robustez pré-registrada que exclui os `sem_quebra` do grupo de comparação.

> **Depois:** A regra é conservadora [...]. Como ela exige ao menos 5 aberturas em 6 meses, num município de 20 a 50 mil habitantes, onde a mediana em 2015–2016 era de zero abertura por mês, só saltos de 10 vezes ou mais são datados com frequência. Quando a regra encontra uma data, porém, ela tende a estar certa: o atraso mediano é de 0 a 2 meses [...]. Isso implica que parte dos 751 municípios sem data provavelmente recebeu plataforma, mas com poucos entregadores formalizados para que a regra detectasse a chegada. Esse problema tende a reduzir o efeito estimado e reforça a importância da análise de robustez, prevista no pré-registro, que exclui os municípios sem data do grupo de comparação.

**Por quê:** "Quando data, data bem" é frase de efeito. "A regra ver" personifica a regra. "Provavelmente" deixa o texto alinhado com a conclusão, que já dizia "parte dos municípios sem data provavelmente já recebeu entregadores". "Municípios sem data" é o termo que você usou nas limitações.

### S31. Título e 1º parágrafo da 3.6

Título: "Quem recebe data: o desbalanço regional não é porte nem formalização prévia" → **"Quais municípios recebem data"**.

> **Antes:** A população sozinha discrimina razoavelmente (AUC 0,76); acrescentar a região leva a AUC a 0,90, e a propensão pré-plataforma acrescenta quase nada (0,91). Controlando porte e propensão prévia a formalizar entregadores, um município nordestino tem chance **17 vezes menor** de receber data que um do Sudeste de mesmo porte, e um do Norte, **34 vezes menor** (Figura 6). A propensão prévia é relevante (quase o dobro da chance por unidade de log) mas absorve pouco do efeito regional...

> **Depois:** Só a população já separa razoavelmente os municípios com e sem data (AUC de 0,76). Com a região, a AUC sobe para 0,90; a propensão anterior às plataformas acrescenta quase nada (0,91). Mesmo controlando o porte e a propensão prévia a formalizar entregadores, um município do Nordeste tem chance 17 vezes menor de receber data do que um município do Sudeste de mesmo porte, e um do Norte, 34 vezes menor (Figura 6). **Numa cidade de 30 mil habitantes com a formalização mediana anterior às plataformas (meia abertura por ano em 2015–2016), por exemplo, o modelo M3 prevê 64% de probabilidade de receber data no Sudeste, contra 9% no Nordeste e 5% no Norte.** A propensão prévia tem efeito relevante (cada unidade de log quase dobra a chance), mas explica pouco da diferença regional...

**Por quê:** o título antigo era uma conclusão inteira. A frase em negrito acima é nova: o resumo cita 9%, 5% e 64%, mas esses números não apareciam no corpo do texto (veja a seção 4).

### S32. 3.6, 2º parágrafo

> **Antes:** Duas leituras são compatíveis com isso, e o dado do CNPJ não separa uma da outra: [...] ou chegaram, mas a formalização dos entregadores *depois* da chegada é regionalmente diferente — o que a simulação da seção 3.5 diz que a regra não veria. Em qualquer das duas, o grupo de comparação *not-yet-treated* mistura regiões com trajetórias distintas.

> **Depois:** Esse resultado é compatível com as duas explicações apresentadas na Seção 3.4, e os dados do CNPJ não permitem separar uma da outra: [...] ou chegaram, mas lá os entregadores se formalizam de outra maneira *depois* da chegada, o que, segundo a simulação da Seção 3.5, a regra não conseguiria detectar. Em qualquer dos casos, o grupo de comparação de municípios ainda não tratados mistura regiões com trajetórias diferentes.

**Por quê:** o parágrafo repetia as duas explicações da 3.4 como se fossem novas; agora remete a elas. "Seção" com maiúscula, como no resto do texto.

### S33. Discussão, dois primeiros parágrafos

> **Antes:** **O que já se sabe.** A carga é grande (perto de 150 mil internações por ano), crescente e invisível: o sistema de informação em saúde vê o trabalho em uma internação a cada 15.576, e a Previdência, em uma a duas por mil. [...] Esses fatos não dependem de identificação causal e sustentam, por si, a política mais barata da lista: tornar obrigatório o registro do nexo "trabalho por plataforma" na AIH e no SINAN.
>
> **O que ainda não se sabe — e por que esta versão não responde.** Quanto do crescimento das internações é *causado* pela chegada do entregador por corrida. Essa fração é o que converte "o SUS paga por acidentes de moto" em "o SUS paga por acidentes que a remuneração por corrida causou". Optamos por não estimá-la antes do depósito do plano no OSF: o número de escolhas defensáveis (...) é grande o bastante para que qualquer resultado obtido antes do registro fosse suspeito de busca por especificação.

> **Depois:** Os resultados descritivos já permitem algumas conclusões. O número de internações é alto (perto de 150 mil por ano) e crescente, e quase nenhuma delas é registrada como ligada ao trabalho: o SIH registra o nexo ocupacional em uma internação a cada 15.576, e a Previdência, em 1 a 1,3 a cada mil. [...] Essas constatações não dependem de identificação causal e bastam, por si, para justificar a medida mais simples e barata: tornar obrigatório o registro do nexo "trabalho por plataforma" na AIH e no Sistema de Informação de Agravos de Notificação (SINAN).
>
> O que esta versão ainda não responde é quanto do crescimento das internações foi *causado* pela chegada do entregador remunerado por corrida. É essa fração que permitiria passar da constatação de que o SUS paga por acidentes de moto para a afirmação de que o SUS paga por acidentes causados pela remuneração por corrida. Optamos por não estimá-la antes de depositar o plano no OSF porque o número de escolhas defensáveis na análise (...) é grande o bastante para que qualquer resultado obtido antes do registro levantasse a suspeita de busca pela especificação mais favorável.

**Por quê:** os rótulos de pergunta e resposta e a resposta em fragmento ("Quanto do crescimento...") são o padrão mais reconhecível de texto gerado. "A política mais barata da lista" se referia a uma lista que não existe. O sistema "vê", e o SINAN aparecia sem definição. "Nível de cluster" virou "nível de agrupamento dos erros".

### S34. Discussão, rótulos "Limitações" e "Implicações"

> **Antes:** **Limitações já conhecidas.** Três razões [...] tenda a ser menor que o real — um piso, e não uma estimativa exagerada. [...] **Implicações.** Regular o risco de acidente não depende...

> **Depois:** Quanto às limitações, três razões [...] tenda a ser menor que o real, ou seja, a estimativa deve ser lida como um piso, e não como um exagero. [...] Do ponto de vista das políticas públicas, regular o risco de acidente não depende...

**Por quê:** sem os dois primeiros rótulos (S33), estes dois ficariam sozinhos. Os parágrafos são seus e não mudaram além da primeira frase. Se preferir a Discussão com rótulos, o melhor caminho é manter os quatro com nomes neutros ("Resultados descritivos.", "O que falta estimar.", "Limitações.", "Implicações.").

### S35. Declaração de uso de IA

> **Antes:** (campo `Co-Authored-By` do Git, convenção que registra a assistência -- principalmente no que tange aspectos de organização do trabalho -- e não confere autoria) O autor revisou...

> **Depois:** (campo `Co-Authored-By` do Git, convenção que registra a assistência, principalmente no que tange a aspectos de organização do trabalho, e não confere autoria). O autor revisou...

**Por quê:** faltava o ponto depois do parêntese, "tanger" pede "a", e o `--` sai como meia-risca no PDF. A declaração continua correta para esta revisão: ela já cobre "redação, revisão e formatação desta versão do artigo".

## 4. Correções que não são de estilo

1. **Erro de compilação na 2.6.** Na edição do Overleaf, o `\label` foi para dentro do `\subsection{...}` e a chave que fechava o `\hypertarget` sumiu. O pdflatex acusa `Paragraph ended before \hypertarget was complete` na linha 292. Está corrigido, e o `.tex` novo compila sem erros (`artigo-latex.pdf` foi recompilado com ele).
2. **"O dobro" (3.5).** Acima de 100 mil, o falso positivo observado é 2,0 vezes o simulado com superdispersão forte na faixa de 100 a 250 mil (24,1 contra 12,0), mas 1,5 vez na de 250 mil+ (25,9 contra 16,8). Troquei por "entre 1,5 e 2 vezes".
3. **"Uma a duas por mil" (Discussão).** A 3.2 diz 1 a 1,3 benefícios com nexo acidentário por mil internações. Igualei.
4. **9%, 5% e 64% do resumo.** Esses números não estavam no corpo do texto e não saem de nenhum script do repositório, mas a declaração de IA afirma que "os números do texto foram transcritos das saídas dos scripts do repositório". Refiz a conta com o mesmo modelo M3 de `modelos_artigo.py` (statsmodels, sem penalização), para uma cidade de 30 mil habitantes com a formalização mediana de 2015–2016 (0,5 abertura por ano): Sudeste 64,3%, Nordeste 9,4%, Norte 5,0%. Os números conferem, e acrescentei a frase à 3.6. **Falta** pôr esse cálculo no `modelos_artigo.py`, para que ele saia de um script como os demais; não fiz isso neste PR.
5. **Pequenos erros:** "congelado com no repositório" (S14); espaço dentro de `\emph{ Conclusão:}` (S1); aspas retas em "plataformizada" (S4); ponto final na declaração de IA (S35); `\textbf` dentro do título da 2.3 (S10).
6. **Citação.** "Ipea (TD 2565)" virou "(CARVALHO, 2020)", que é como a referência está na lista.
7. **SINAN** aparecia sem definição; agora está por extenso na primeira menção.

Não mexi, mas vale olhar:

- O resumo dá R$ 1,8 bilhão de resultado do iFood (ano civil de 2025, interpolado), e a introdução, R$ 2,0 bilhões (ano fiscal encerrado em março de 2026). Os dois estão certos, mas o leitor pode tropeçar. Uma saída é acrescentar na introdução "(R$ 1,8 bilhão no ano civil de 2025)".
- Na 2.5, "antes da busca começar": a norma pede "antes de a busca começar". Deixei como está, porque é uso corrente.
- O `artigo.md` e o `artigo.docx` estão desatualizados em relação ao `.tex` desde as edições no Overleaf. Não mexi neles.

## 5. Como usar

- **Para aceitar tudo:** faça o merge do PR e, no Overleaf, puxe as mudanças do GitHub (Menu → GitHub → *Pull GitHub changes into Overleaf*).
- **Para recusar um item:** depois do merge, cole no Overleaf o texto "Antes" do item.
- **Se você editar no Overleaf antes do merge**, o PR pode entrar em conflito com o `main`. É só avisar que eu resolvo.
