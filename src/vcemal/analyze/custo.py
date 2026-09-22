"""Custo publico e custo social das internacoes, a precos constantes.

Perna P3 do argumento (`docs/pre-projeto.md`): "nos pagamos". Tres numeros
que precisam aparecer lado a lado, e nao se substituem:

* `val_tot_real` -- o que o SUS **pagou**, deflacionado. Piso.
* `custo_social_real` -- o que a sociedade **perdeu**, pelos parametros do
  Ipea (`vcemal.custo`). Ordem de grandeza.
* `perda_producao_real` -- a parte do custo social que recai sobre a familia
  do acidentado, nao sobre o SUS. E a maior componente (D-029).

Deflator: IPCA numero-indice (IBGE, tabela 1737, variavel 2266). Tudo sai em
reais da competencia `base`, que a tabela carrega na coluna `base_precos` para
ninguem somar reais de datas diferentes sem ver.
"""

from __future__ import annotations

import pandas as pd

from vcemal import custo as custo_mod

#: Contagens do painel que todo recorte soma.
SOMAS = ["internacoes", "obitos", "dias_perm_total", "val_tot"]

COLUNAS = [
    "internacoes",
    "obitos",
    "dias_perm_total",
    "val_tot_nominal",
    "val_tot_real",
    "val_por_internacao_real",
    "custo_social_real",
    "hospitalar_ipea_real",
    "perda_producao_real",
    "base_precos",
]


def indice_ipca(linhas: list[dict]) -> pd.Series:
    """Linhas de `vcemal.extract.ibge.ipca` -> serie mensal indexada por `Period('M')`."""
    if not linhas:
        raise ValueError("serie do IPCA vazia")
    s = pd.Series(
        {pd.Period(str(r["periodo"]), freq="M"): float(r["indice"]) for r in linhas}
    ).sort_index()
    if (s <= 0).any():
        raise ValueError("IPCA com indice nao positivo")
    return s


def fator(ipca: pd.Series, base: str) -> pd.Series:
    """Fator que leva cada competencia a reais de `base`: `ipca[base] / ipca[t]`."""
    alvo = pd.Period(base, freq="M")
    if alvo not in ipca.index:
        raise KeyError(f"IPCA sem a competencia base {base}")
    return ipca[alvo] / ipca


def deflacionar(painel: pd.DataFrame, ipca: pd.Series, base: str) -> pd.DataFrame:
    """Acrescenta `val_tot_real` linha a linha, pela competencia `(ano, mes)`.

    Competencia do painel sem IPCA e erro, nao NaN silencioso: acontece quando
    o painel vai alem do ultimo mes publicado pelo IBGE.
    """
    faltando = [c for c in (*SOMAS, "ano", "mes") if c not in painel.columns]
    if faltando:
        raise KeyError(f"painel sem as colunas {faltando}")

    saida = painel.copy()
    competencia = pd.PeriodIndex(
        pd.to_datetime(dict(year=saida["ano"], month=saida["mes"], day=1)), freq="M"
    )
    sem_ipca = sorted({str(p) for p in competencia.unique() if p not in ipca.index})
    if sem_ipca:
        raise KeyError(f"IPCA sem as competencias do painel: {', '.join(sem_ipca)}")

    f = fator(ipca, base)
    saida["val_tot_real"] = pd.to_numeric(saida["val_tot"], errors="coerce").fillna(0.0) * (
        f.reindex(competencia).to_numpy()
    )
    return saida


def por(
    painel: pd.DataFrame,
    ipca: pd.Series,
    base: str,
    *chaves: str,
    parametros: custo_mod.ParametrosCusto = custo_mod.TD2565,
) -> pd.DataFrame:
    """Custo pago e custo social agregados pelas `chaves`, em reais de `base`."""
    faltando = [c for c in chaves if c not in painel.columns]
    if faltando:
        raise KeyError(f"painel sem as colunas {faltando}")

    real = deflacionar(painel, ipca, base)
    g = real.groupby(list(chaves), dropna=False)[[*SOMAS, "val_tot_real"]].sum()
    g = g.rename(columns={"val_tot": "val_tot_nominal"})

    # Parametros do Ipea estao em R$ da base deles; um fator so os leva a `base`.
    inflacao = float(fator(ipca, base)[pd.Period(parametros.base_precos, freq="M")])
    sobreviventes = g["internacoes"] - g["obitos"]
    if (sobreviventes < 0).any():
        raise ValueError("obitos maior que internacoes em algum recorte")
    fg, mo = parametros.ferido_grave, parametros.morto
    g["custo_social_real"] = inflacao * (sobreviventes * fg.total + g["obitos"] * mo.total)
    g["hospitalar_ipea_real"] = inflacao * (
        sobreviventes * fg.hospitalar + g["obitos"] * mo.hospitalar
    )
    g["perda_producao_real"] = inflacao * (
        sobreviventes * fg.perda_producao + g["obitos"] * mo.perda_producao
    )
    internacoes = g["internacoes"]
    g["val_por_internacao_real"] = g["val_tot_real"] / internacoes.where(internacoes > 0)
    g["base_precos"] = str(pd.Period(base, freq="M"))
    return g[COLUNAS]


def por_ano(painel: pd.DataFrame, ipca: pd.Series, base: str, **kw) -> pd.DataFrame:
    """Recorte principal: ano x grupo de vitima."""
    return por(painel, ipca, base, "ano", "grupo", **kw)


def por_uf_ano(painel: pd.DataFrame, ipca: pd.Series, base: str, **kw) -> pd.DataFrame:
    """UF x ano, so motociclista."""
    moto = painel[painel["grupo"] == "motociclista"]
    return por(moto, ipca, base, "uf", "ano", **kw)
