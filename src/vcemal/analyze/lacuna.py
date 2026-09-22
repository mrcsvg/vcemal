"""A lacuna SIH x INSS: quanto do que o SUS interna a Previdencia reconhece.

Perna P3(b) do argumento (`docs/pre-projeto.md`). Para cada UF e ano, poe lado
a lado o numerador de saude (internacoes de motociclista no SIH) e o numerador
previdenciario (beneficios concedidos com CID V20-V29), separando os que
tiveram nexo com o trabalho **reconhecido** (especie acidentaria) dos que nao
tiveram (previdenciaria).

O que a razao mede e **invisibilidade**, nao risco (D-002, D-030): beneficio
exige contribuicao e mais de 15 dias de afastamento, e a especie acidentaria
exige empregador. Um entregador informal nao aparece em nenhum dos dois -- e
esse e o ponto. Por isso a taxa sai *por mil internacoes*, e nao como
"cobertura": ninguem esta afirmando que cada AIH deveria virar beneficio.
"""

from __future__ import annotations

import pandas as pd

#: Colunas que o painel do SIH precisa ter.
SOMAS_SIH = ["internacoes", "internacoes_transito", "nexo_ocupacional", "obitos"]

COLUNAS = [
    "meses_sih",
    "meses_inss",
    "internacoes",
    "internacoes_transito",
    "obitos",
    "sih_nexo_ocupacional",
    "beneficios",
    "acidentarios",
    "previdenciarios",
    "beneficios_por_mil_internacoes",
    "acidentarios_por_mil_internacoes",
    "sih_nexo_por_mil_internacoes",
    "pct_acidentario",
]


def _sih(painel: pd.DataFrame, grupo: str, *chaves: str) -> pd.DataFrame:
    faltando = [c for c in (*chaves, "mes", "grupo", *SOMAS_SIH) if c not in painel.columns]
    if faltando:
        raise KeyError(f"painel sem as colunas {faltando}")
    base = painel[painel["grupo"] == grupo]
    saida = base.groupby(list(chaves))[SOMAS_SIH].sum()
    saida["meses_sih"] = _meses_observados(base, chaves)
    return saida.rename(columns={"nexo_ocupacional": "sih_nexo_ocupacional"})


def _meses_observados(df: pd.DataFrame, chaves: tuple[str, ...]) -> pd.Series:
    """Quantas competencias distintas cada chave cobre."""
    return df.drop_duplicates([*chaves, "ano", "mes"]).groupby(list(chaves)).size()


def _inss(agregado: pd.DataFrame, grupo: str, *chaves: str) -> pd.DataFrame:
    faltando = [
        c for c in (*chaves, "mes", "grupo", "classe", "beneficios") if c not in agregado.columns
    ]
    if faltando:
        raise KeyError(f"agregado do INSS sem as colunas {faltando}")
    base = agregado[agregado["grupo"] == grupo]
    largo = (
        base.pivot_table(
            index=list(chaves), columns="classe", values="beneficios", aggfunc="sum", fill_value=0
        )
        .reindex(columns=["acidentario", "previdenciario"], fill_value=0)
        .rename(columns={"acidentario": "acidentarios", "previdenciario": "previdenciarios"})
    )
    largo.columns.name = None
    largo["beneficios"] = largo["acidentarios"] + largo["previdenciarios"]
    # meses cobertos pelo INSS: independe do grupo, porque um mes sem beneficio
    # de motociclista ainda e um mes observado.
    meses = _meses_observados(agregado, chaves)
    largo = largo.reindex(largo.index.union(meses.index), fill_value=0)
    largo["meses_inss"] = meses.reindex(largo.index).fillna(0).astype(int)
    return largo


def por(
    painel: pd.DataFrame, agregado_inss: pd.DataFrame, *chaves: str, grupo: str = "motociclista"
) -> pd.DataFrame:
    """SIH e INSS lado a lado, agregados pelas `chaves` (`"uf", "ano"` ou so `"ano"`).

    Juncao externa: UF-ano que so existe de um lado aparece com zero do outro e
    com `meses_*` dizendo quantos meses cada fonte cobriu. **Comparar so onde os
    dois cobrem os 12 meses** -- a tabela nao esconde a assimetria.
    """
    if "ano" not in chaves:
        raise ValueError("as chaves precisam incluir 'ano'")
    sih = _sih(painel, grupo, *chaves)
    inss = _inss(agregado_inss, grupo, *chaves)
    t = sih.join(inss, how="outer")
    contagens = [
        "meses_sih",
        "meses_inss",
        *SOMAS_SIH[:2],
        "obitos",
        "sih_nexo_ocupacional",
        "beneficios",
        "acidentarios",
        "previdenciarios",
    ]
    t[contagens] = t[contagens].fillna(0).astype(int)

    internacoes = t["internacoes"].where(t["internacoes"] > 0)
    beneficios = t["beneficios"].where(t["beneficios"] > 0)
    t["beneficios_por_mil_internacoes"] = 1000 * t["beneficios"] / internacoes
    t["acidentarios_por_mil_internacoes"] = 1000 * t["acidentarios"] / internacoes
    t["sih_nexo_por_mil_internacoes"] = 1000 * t["sih_nexo_ocupacional"] / internacoes
    t["pct_acidentario"] = 100 * t["acidentarios"] / beneficios
    return t[COLUNAS]


def por_uf_ano(painel: pd.DataFrame, agregado_inss: pd.DataFrame, **kw) -> pd.DataFrame:
    return por(painel, agregado_inss, "uf", "ano", **kw)


def por_ano(painel: pd.DataFrame, agregado_inss: pd.DataFrame, **kw) -> pd.DataFrame:
    return por(painel, agregado_inss, "ano", **kw)
