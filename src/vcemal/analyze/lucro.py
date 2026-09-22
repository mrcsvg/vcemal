"""Receita e resultado do iFood em reais constantes, no eixo da serie de custo.

Tres passos, cada um declarado na tabela de saida:

1. **Cambio.** Dolar -> real pela media mensal do BCB (SGS 3698) sobre os doze
   meses do ano fiscal. Coluna `cambio_medio`.
2. **Deflator.** Real corrente -> real de `base_precos` pelo IPCA numero-indice
   (o mesmo de `vcemal.analyze.custo`), com o indice medio dos doze meses do
   ano fiscal, porque receita e fluxo distribuido no ano.
3. **Calendario.** Ano fiscal (abril-marco) -> ano civil por
   `vcemal.lucro.para_ano_civil`, so para fluxos. Estoques (entregadores,
   estabelecimentos, cidades) ficam na tabela fiscal, com a data que tem.
"""

from __future__ import annotations

import pandas as pd

from vcemal import lucro as lucro_mod

COLUNAS_FISCAL = [
    "inicio",
    "fim",
    "pedidos_milhoes",
    "gmv_usd_milhoes",
    "receita_usd_milhoes",
    "receita_comparavel_usd_milhoes",
    "trading_profit_usd_milhoes",
    "aebit_usd_milhoes",
    "aebitda_usd_milhoes",
    "cambio_medio",
    "receita_brl_nominal_milhoes",
    "receita_brl_real_milhoes",
    "receita_comparavel_brl_real_milhoes",
    "trading_profit_brl_real_milhoes",
    "aebit_brl_real_milhoes",
    "aebitda_brl_real_milhoes",
    "gmv_brl_real_milhoes",
    "receita_por_pedido_brl_real",
    "entregadores_brasil",
    "estabelecimentos_brasil",
    "cidades_brasil",
    "base_precos",
]

COLUNAS_CIVIL = [
    "pedidos_milhoes",
    "receita_usd_milhoes",
    "receita_brl_real_milhoes",
    "receita_comparavel_brl_real_milhoes",
    "trading_profit_brl_real_milhoes",
    "aebit_brl_real_milhoes",
    "aebitda_brl_real_milhoes",
    "gmv_brl_real_milhoes",
    "base_precos",
    "metodo",
]

METODO_CIVIL = "0,25 x AF(t) + 0,75 x AF(t+1), fluxo uniforme no ano fiscal"


def serie_fiscal(linhas: list[dict]) -> pd.DataFrame:
    """CSV curado (formato longo) -> uma linha por ano fiscal, uma coluna por metrica."""
    lucro_mod.validar(linhas)
    df = pd.DataFrame(linhas)
    df["ano_fiscal"] = df["ano_fiscal"].astype(int)
    df["valor"] = pd.to_numeric(df["valor"])
    largo = df.pivot(index="ano_fiscal", columns="metrica", values="valor").sort_index()
    largo.columns.name = None
    for nome in lucro_mod.METRICAS:
        if nome not in largo.columns:
            largo[nome] = float("nan")
    return largo


def media_no_ano_fiscal(mensal: pd.Series, anos_fiscais: list[int]) -> pd.Series:
    """Media de uma serie mensal (indexada por `Period('M')`) nos doze meses de cada FY.

    Mes faltando e erro: acontece quando o ano fiscal vai alem do ultimo mes
    publicado pelo BCB ou pelo IBGE.
    """
    saida = {}
    for fy in anos_fiscais:
        meses = [pd.Period(m, freq="M") for m in lucro_mod.meses_do_ano_fiscal(fy)]
        faltando = [str(m) for m in meses if m not in mensal.index]
        if faltando:
            raise KeyError(f"FY{fy} sem os meses {', '.join(faltando)}")
        saida[fy] = float(mensal.reindex(meses).mean())
    return pd.Series(saida, name=mensal.name)


def indice_cambio(linhas: list[dict]) -> pd.Series:
    """Linhas de `vcemal.extract.bcb.cambio_mensal` -> serie mensal indexada por `Period('M')`."""
    if not linhas:
        raise ValueError("serie de cambio vazia")
    s = pd.Series(
        {pd.Period(str(r["periodo"]), freq="M"): float(r["cambio"]) for r in linhas},
        name="cambio",
    ).sort_index()
    if (s <= 0).any():
        raise ValueError("cambio nao positivo")
    return s


def por_ano_fiscal(
    linhas: list[dict], cambio: pd.Series, ipca: pd.Series, base: str
) -> pd.DataFrame:
    """Tabela por ano fiscal: dolar como publicado, reais correntes e reais de `base`."""
    fiscal = serie_fiscal(linhas)
    anos = list(fiscal.index)
    cambio_fy = media_no_ano_fiscal(cambio, anos)
    ipca_fy = media_no_ano_fiscal(ipca, anos)
    alvo = pd.Period(base, freq="M")
    if alvo not in ipca.index:
        raise KeyError(f"IPCA sem a competencia base {base}")
    deflator_fy = ipca[alvo] / ipca_fy

    t = pd.DataFrame(index=fiscal.index)
    t["inicio"] = [lucro_mod.meses_do_ano_fiscal(fy)[0] for fy in anos]
    t["fim"] = [lucro_mod.meses_do_ano_fiscal(fy)[-1] for fy in anos]
    t["pedidos_milhoes"] = fiscal["pedidos"]
    for nome in lucro_mod.EM_DOLAR:
        t[f"{nome}_usd_milhoes"] = fiscal[nome]
    t["cambio_medio"] = cambio_fy
    t["receita_brl_nominal_milhoes"] = fiscal["receita"] * cambio_fy
    for nome in lucro_mod.EM_DOLAR:
        t[f"{nome}_brl_real_milhoes"] = fiscal[nome] * cambio_fy * deflator_fy
    t["receita_por_pedido_brl_real"] = t["receita_brl_real_milhoes"] / t["pedidos_milhoes"]
    for nome in ("entregadores_brasil", "estabelecimentos_brasil", "cidades_brasil"):
        t[nome] = fiscal[nome]
    t["base_precos"] = base
    t.index.name = "ano_fiscal"
    return t[COLUNAS_FISCAL]


def por_ano_civil(fiscal: pd.DataFrame) -> pd.DataFrame:
    """Fluxos da tabela fiscal levados ao ano civil. Estoques ficam de fora."""
    saida = {}
    for col in COLUNAS_CIVIL:
        if col in ("base_precos", "metodo"):
            continue
        serie = fiscal[col].dropna()
        saida[col] = pd.Series(lucro_mod.para_ano_civil(serie.to_dict()), dtype=float)
    t = pd.DataFrame(saida)
    t.index.name = "ano"
    t = t.sort_index()
    t["base_precos"] = fiscal["base_precos"].iloc[0]
    t["metodo"] = METODO_CIVIL
    return t[COLUNAS_CIVIL]
