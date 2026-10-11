"""Auditoria do tratamento do MEI por busca independente (D-041).

A quebra nas aberturas de MEI de entrega data o tratamento do V2 (D-040), mas so
foi validada onde o Wayback chega: Rappi e Uber Eats, quase todas acima de 100 mil
habitantes. Abaixo disso -- onde ficam os 640 municipios `datado` -- o unico teste
e procurar a chegada da plataforma pelo protocolo de codificacao, sem saber a data
da quebra, e comparar depois.

**O sorteio.** `POR_ESTRATO` municipios `datado` em cada estrato de ano da quebra e
`ISCAS` municipios `sem_quebra`, misturados numa ordem so. Os estratos separam os
tres lugares onde a regra pode errar de jeitos diferentes:

* `2017` -- quebra antes da frota propria do iFood (2018-01). Pelo placebo de 2016,
  uma parte relevante deste ano e falso positivo;
* `2018-2020` -- o rollout que a regra foi feita para ver;
* `2021-2025` -- quebras tardias, onde a entrega de comercio eletronico pode
  contaminar o CNAE 5320-2/02 (D-040).

As iscas existem para o codificador nao poder inferir que "todo municipio da lista
tem plataforma": sem elas, a lista inteira e de tratados, e isso empurra a busca a
achar alguma coisa.

**O veredito, declarado antes da codificacao.** Um municipio auditado concorda
quando a quebra cai no intervalo codificado alargado `TOLERANCIA` meses para cada
lado. Nao achado (`N`) nao conta contra nem a favor. Um estrato passa com pelo menos
`LIMIAR` dos achados concordando e e inconclusivo com menos de `MINIMO_ACHADOS`
achados. O que cada veredito faz com a analise esta na secao 4 do plano de analise.
"""

from __future__ import annotations

import pandas as pd

#: Sorteio da auditoria: diferente da semente da ordem de codificacao (20260920).
SEMENTE = 20261011

#: Estratos de ano da quebra, inclusive nas pontas.
ESTRATOS: dict[str, tuple[str, str]] = {
    "2017": ("2017", "2017"),
    "2018-2020": ("2018", "2020"),
    "2021-2025": ("2021", "2025"),
}
ISCA = "isca"
POR_ESTRATO = 12
ISCAS = 12

#: Meses de folga de cada lado do intervalo codificado.
TOLERANCIA = 6
#: Fracao minima de achados concordantes para o estrato passar.
LIMIAR = 2 / 3
#: Abaixo disto o estrato nao tem achados bastantes para veredito.
MINIMO_ACHADOS = 6

COLUNAS_CHAVE = ("ordem", "municipio_ibge", "uf", "municipio", "estrato")


def _mes(aaaa_mm: str) -> int:
    ano, mes = aaaa_mm.split("-")
    return int(ano) * 12 + int(mes) - 1


def sortear(tratamento_mei: pd.DataFrame) -> pd.DataFrame:
    """`tratamento_mei_municipio.csv` -> a chave da auditoria, em ordem de trabalho.

    Deterministico: ordena por codigo IBGE antes de sortear, entao a amostra
    depende so do conteudo do arquivo congelado e da semente.
    """
    trat = tratamento_mei.sort_values("municipio_ibge").reset_index(drop=True)
    ano = trat["mes_quebra"].fillna("").astype(str).str.slice(0, 4)
    partes = []
    for nome, (ini, fim) in ESTRATOS.items():
        elegiveis = trat[(trat["grupo"] == "datado") & ano.between(ini, fim)]
        if len(elegiveis) < POR_ESTRATO:
            raise ValueError(
                f"estrato {nome}: {len(elegiveis)} municipios datados, menos que {POR_ESTRATO}"
            )
        partes.append(elegiveis.sample(POR_ESTRATO, random_state=SEMENTE).assign(estrato=nome))
    sem_quebra = trat[trat["grupo"] == "sem_quebra"]
    if len(sem_quebra) < ISCAS:
        raise ValueError(f"so {len(sem_quebra)} municipios sem_quebra para {ISCAS} iscas")
    partes.append(sem_quebra.sample(ISCAS, random_state=SEMENTE).assign(estrato=ISCA))
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


def _veredito(estrato: str, achados: int, concordantes: int) -> str:
    if estrato == ISCA:
        return ""
    if achados < MINIMO_ACHADOS:
        return "inconclusivo"
    return "passa" if concordantes >= LIMIAR * achados else "falha"


def avaliar(
    chave: pd.DataFrame, tratamento_mei: pd.DataFrame, codificado: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compara a quebra com a cronologia codificada da amostra.

    `codificado` e o `tratamento_municipio.csv` que `cronologia.py consolidar`
    escreve sobre as planilhas da auditoria. Devolve uma linha por municipio
    auditado e o resumo por estrato, com o veredito.
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
    tratado = por_mun["tratado"].astype(str).str.lower() == "true"
    por_mun["achado"] = tratado
    por_mun["concorda"] = [
        concorda(r.mes_quebra, r.mes_tratamento, r.incerteza_meses)
        if r.achado and r.estrato != ISCA
        else None
        for r in por_mun.itertuples()
    ]

    resumo = []
    for estrato in [*ESTRATOS, ISCA]:
        grupo = por_mun[por_mun["estrato"] == estrato]
        achados = int(grupo["achado"].sum())
        concordantes = int((grupo["concorda"] == True).sum())  # noqa: E712 -- coluna com None
        resumo.append(
            {
                "estrato": estrato,
                "auditados": len(grupo),
                "achados": achados,
                "concordantes": concordantes,
                "veredito": _veredito(estrato, achados, concordantes),
            }
        )
    return por_mun, pd.DataFrame(resumo)
