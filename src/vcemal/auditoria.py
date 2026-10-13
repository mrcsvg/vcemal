"""Auditoria do tratamento do MEI por busca independente (D-041).

A quebra nas aberturas de MEI de entrega data o tratamento do V2 (D-040), mas so
foi validada onde o Wayback chega: Rappi e Uber Eats, quase todas acima de 100 mil
habitantes. Abaixo disso -- onde ficam os 640 municipios `datado` -- o unico teste
e procurar a chegada da plataforma pelo protocolo de codificacao, sem saber a data
da quebra, e comparar depois.

**O sorteio.** Em cada estrato de ano da quebra, `POR_CELULA` municipios `datado`
de cada faixa de populacao; `POR_CELULA` iscas `sem_quebra` de cada faixa; e as 27
capitais, todas, por obrigacao. Tudo misturado numa ordem so. Os estratos de ano
separam os tres lugares onde a regra pode errar de jeitos diferentes:

* `2017` -- quebra antes da frota propria do iFood (2018-01). Pelo placebo de 2016,
  uma parte relevante deste ano e falso positivo;
* `2018-2020` -- o rollout que a regra foi feita para ver;
* `2021-2025` -- quebras tardias, onde a entrega de comercio eletronico pode
  contaminar o CNAE 5320-2/02 (D-040).

A faixa de populacao entra no sorteio porque as duas faixas erram diferente (o
placebo dispara em 0,7% dos municipios de 20-50 mil e em 3,8% dos de 50-100 mil):
sem ela, o acaso decide qual faixa a auditoria ve. O veredito continua por estrato
de ano; a faixa e reportada ao lado.

As iscas existem para o codificador nao poder inferir que "todo municipio da lista
tem plataforma": sem elas, a lista inteira e de tratados, e isso empurra a busca a
achar alguma coisa. Metade de cada faixa, para o porte nao denunciar a isca.

**As capitais testam outra coisa.** Sao todas `coorte_precoce` (100 mil ou mais), e
para elas a quebra nao data nada. O que se testa e a premissa da coorte precoce:
frota propria operando ate `LIMITE_PRECOCE`.

**O veredito, declarado antes da codificacao.** Um municipio `datado` concorda
quando a quebra cai no intervalo codificado alargado `TOLERANCIA` meses para cada
lado; uma capital concorda quando o intervalo codificado, alargado igual, comeca
ate `LIMITE_PRECOCE`. Nao achado (`N`) nao conta contra nem a favor. Um estrato
passa com pelo menos `LIMIAR` dos achados concordando e e inconclusivo com menos de
`MINIMO_ACHADOS` achados. O que cada veredito faz com a analise esta na secao 4 do
plano de analise.
"""

from __future__ import annotations

import math

import pandas as pd

#: Sorteio da auditoria: diferente da semente da ordem de codificacao (20260920).
SEMENTE = 20261011

#: Estratos de ano da quebra, inclusive nas pontas.
ESTRATOS: dict[str, tuple[str, str]] = {
    "2017": ("2017", "2017"),
    "2018-2020": ("2018", "2020"),
    "2021-2025": ("2021", "2025"),
}
#: Faixas de populacao em que a quebra data o tratamento (`vcemal.mei.ROTULOS_FAIXA`).
FAIXAS = ("20-50 mil", "50-100 mil")
ISCA = "isca"
CAPITAL = "capital"
#: Municipios por estrato de ano x faixa, e iscas por faixa.
POR_CELULA = 6

#: As 27 capitais, codigo IBGE. Entram todas, fora do sorteio.
CAPITAIS = (
    1100205,  # Porto Velho
    1200401,  # Rio Branco
    1302603,  # Manaus
    1400100,  # Boa Vista
    1501402,  # Belem
    1600303,  # Macapa
    1721000,  # Palmas
    2111300,  # Sao Luis
    2211001,  # Teresina
    2304400,  # Fortaleza
    2408102,  # Natal
    2507507,  # Joao Pessoa
    2611606,  # Recife
    2704302,  # Maceio
    2800308,  # Aracaju
    2927408,  # Salvador
    3106200,  # Belo Horizonte
    3205309,  # Vitoria
    3304557,  # Rio de Janeiro
    3550308,  # Sao Paulo
    4106902,  # Curitiba
    4205407,  # Florianopolis
    4314902,  # Porto Alegre
    5002704,  # Campo Grande
    5103403,  # Cuiaba
    5208707,  # Goiania
    5300108,  # Brasilia
)
#: A coorte precoce e "tratada ate 2018" (D-040).
LIMITE_PRECOCE = "2018-12"

#: Meses de folga de cada lado do intervalo codificado.
TOLERANCIA = 6
#: Fracao minima de achados concordantes para o estrato passar.
LIMIAR = 2 / 3
#: Abaixo disto o estrato nao tem achados bastantes para veredito.
MINIMO_ACHADOS = 6
#: Linha do resumo com os tres estratos `datado` juntos -- descritiva, sem veredito (D-045).
AGREGADO = "datado"

COLUNAS_CHAVE = ("ordem", "municipio_ibge", "uf", "municipio", "faixa", "estrato")


def _mes(aaaa_mm: str) -> int:
    ano, mes = aaaa_mm.split("-")
    return int(ano) * 12 + int(mes) - 1


def _sortear(elegiveis: pd.DataFrame, n: int, rotulo: str) -> pd.DataFrame:
    if len(elegiveis) < n:
        raise ValueError(f"{rotulo}: {len(elegiveis)} municipios elegiveis, menos que {n}")
    return elegiveis.sample(n, random_state=SEMENTE)


def sortear(tratamento_mei: pd.DataFrame) -> pd.DataFrame:
    """`tratamento_mei_municipio.csv` -> a chave da auditoria, em ordem de trabalho.

    Deterministico: ordena por codigo IBGE antes de sortear, entao a amostra
    depende so do conteudo do arquivo congelado e da semente.
    """
    trat = tratamento_mei.sort_values("municipio_ibge").reset_index(drop=True)
    ano = trat["mes_quebra"].fillna("").astype(str).str.slice(0, 4)
    partes = []
    for nome, (ini, fim) in ESTRATOS.items():
        for faixa in FAIXAS:
            elegiveis = trat[
                (trat["grupo"] == "datado") & (trat["faixa"] == faixa) & ano.between(ini, fim)
            ]
            partes.append(
                _sortear(elegiveis, POR_CELULA, f"estrato {nome}, {faixa}").assign(estrato=nome)
            )
    for faixa in FAIXAS:
        elegiveis = trat[(trat["grupo"] == "sem_quebra") & (trat["faixa"] == faixa)]
        partes.append(_sortear(elegiveis, POR_CELULA, f"iscas, {faixa}").assign(estrato=ISCA))
    capitais = trat[trat["municipio_ibge"].astype(int).isin(CAPITAIS)]
    if len(capitais) != len(CAPITAIS):
        raise ValueError(f"so {len(capitais)} das {len(CAPITAIS)} capitais no tratamento")
    partes.append(capitais.assign(estrato=CAPITAL))
    chave = pd.concat(partes).sample(frac=1, random_state=SEMENTE).reset_index(drop=True)
    chave["ordem"] = range(1, len(chave) + 1)
    return chave[list(COLUNAS_CHAVE)]


def lista_cega(chave: pd.DataFrame) -> pd.DataFrame:
    """O que o codificador recebe: so o municipio, na ordem de trabalho."""
    return chave.sort_values("ordem")[["municipio_ibge", "uf", "municipio"]]


def concorda(mes_quebra: str, mes_tratamento: str, incerteza_meses: int) -> bool:
    """A quebra cai em `[data_min - TOLERANCIA, data_max + TOLERANCIA]`?"""
    fim = _mes(mes_tratamento)
    ini = fim - int(incerteza_meses)
    return ini - TOLERANCIA <= _mes(mes_quebra) <= fim + TOLERANCIA


def concorda_precoce(mes_tratamento: str, incerteza_meses: int) -> bool:
    """O intervalo codificado, alargado, comeca ate `LIMITE_PRECOCE`?"""
    ini = _mes(mes_tratamento) - int(incerteza_meses)
    return ini - TOLERANCIA <= _mes(LIMITE_PRECOCE)


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Intervalo de Wilson para a proporcao `k / n`; `(nan, nan)` com `n = 0`."""
    if n == 0:
        return math.nan, math.nan
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    meia = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centro - meia), min(1.0, centro + meia)


def _veredito(estrato: str, achados: int, concordantes: int) -> str:
    if estrato == ISCA:
        return ""
    if achados < MINIMO_ACHADOS:
        return "inconclusivo"
    return "passa" if concordantes >= LIMIAR * achados else "falha"


def _concorda(r) -> bool | None:
    if not r.achado or r.estrato == ISCA:
        return None
    if r.estrato == CAPITAL:
        return concorda_precoce(r.mes_tratamento, r.incerteza_meses)
    return concorda(r.mes_quebra, r.mes_tratamento, r.incerteza_meses)


def _resumir(por_mun: pd.DataFrame, chaves: list[tuple[str, str]], com_veredito: bool):
    linhas = []
    for estrato, faixa in chaves:
        membros = list(ESTRATOS) if estrato == AGREGADO else [estrato]
        grupo = por_mun[por_mun["estrato"].isin(membros)]
        if faixa:
            grupo = grupo[grupo["faixa"] == faixa]
        achados = int(grupo["achado"].sum())
        concordantes = int((grupo["concorda"] == True).sum())  # noqa: E712 -- coluna com None
        # Nao achar nao conta contra (D-045): a coincidencia e sobre os achados.
        julgado = estrato != ISCA and achados > 0
        inf, sup = wilson(concordantes, achados) if julgado else (math.nan, math.nan)
        linha = {
            "estrato": estrato,
            **({"faixa": faixa} if faixa else {}),
            "auditados": len(grupo),
            "achados": achados,
            "concordantes": concordantes,
            "taxa_achado": achados / len(grupo) if len(grupo) else math.nan,
            "taxa_coincidencia": concordantes / achados if julgado else math.nan,
            "ic95_inf": inf,
            "ic95_sup": sup,
        }
        if com_veredito:
            linha["veredito"] = (
                "" if estrato == AGREGADO else _veredito(estrato, achados, concordantes)
            )
        linhas.append(linha)
    return pd.DataFrame(linhas)


def avaliar(
    chave: pd.DataFrame, tratamento_mei: pd.DataFrame, codificado: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compara a quebra com a cronologia codificada da amostra.

    `codificado` e o `tratamento_municipio.csv` que `cronologia.py consolidar`
    escreve sobre as planilhas da auditoria. Devolve uma linha por municipio
    auditado, o resumo por estrato com o veredito e o mesmo resumo aberto por
    faixa, so descritivo. Cada linha traz a taxa de achado, a taxa de coincidencia
    (concordantes sobre achados) e o intervalo de Wilson dela; a linha `AGREGADO`
    junta os tres estratos `datado`, sem veredito (D-045).
    """
    cod = codificado.assign(municipio_ibge=codificado["municipio_ibge"].astype(int))
    faltam = set(chave["municipio_ibge"].astype(int)) - set(cod["municipio_ibge"])
    if faltam:
        raise ValueError(f"municipios da amostra sem codificacao: {sorted(faltam)}")
    mei = tratamento_mei[["municipio_ibge", "mes_quebra"]].assign(
        municipio_ibge=tratamento_mei["municipio_ibge"].astype(int)
    )
    por_mun = (
        chave.assign(municipio_ibge=chave["municipio_ibge"].astype(int))
        .merge(mei, on="municipio_ibge", how="left")
        .merge(
            cod[["municipio_ibge", "tratado", "mes_tratamento", "incerteza_meses"]],
            on="municipio_ibge",
            how="left",
        )
    )
    por_mun["achado"] = por_mun["tratado"].astype(str).str.lower() == "true"
    por_mun["concorda"] = [_concorda(r) for r in por_mun.itertuples()]

    estratos = [*ESTRATOS, AGREGADO, CAPITAL, ISCA]
    resumo = _resumir(por_mun, [(e, "") for e in estratos], com_veredito=True)
    por_faixa = _resumir(
        por_mun, [(e, f) for e in [*ESTRATOS, ISCA] for f in FAIXAS], com_veredito=False
    )
    return por_mun, resumo, por_faixa
