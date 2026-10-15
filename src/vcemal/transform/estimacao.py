"""Painel de estimacao do V2: municipio x mes, com tratamento, desfechos e cluster.

E o insumo unico do estimador (`scripts/did_estimar.R`). Tudo que o plano de
analise (`docs/pre-registro/plano-de-analise.md`) fixa sobre a amostra mora
aqui; o R so estima.

Tres coisas que o painel do SIH nao entrega prontas:

* **Zero e linha que falta.** O painel do SIH so tem linha onde houve
  internacao. Municipio-mes sem internacao e zero, nao ausencia -- sem o
  preenchimento, o estimador compara so meses com acidente.
* **A UF do painel e a do arquivo, nao a da residencia.** Residente internado em
  outra UF aparece em outra linha com o mesmo `municipio_res`; soma-se por cima.
* **O tratamento e o arquivo congelado.** O hash e conferido antes de ler; se
  nao bater, nada roda (D-041).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from vcemal import municipios as mun

#: SHA-256 de `docs/fontes/cronologia/tratamento_mei_municipio.csv`, o mesmo do
#: plano de analise (secao 4). Mudar o arquivo e mudar o tratamento.
HASH_TRATAMENTO = "128999bd21de00854c717e181657f5d1832ce78222ec9ef6dd99a3bd8a7654a2"

#: Primeiro mes do painel. `periodo` = 1 em 2015-01.
INICIO = pd.Period("2015-01", freq="M")
FIM = pd.Period("2025-12", freq="M")

#: Janela de evento do estimando principal (plano, secao 5).
E_MIN, E_MAX = -12, 24

#: Contagens do painel do SIH que viram desfecho, por grupo de vitima.
CONTAGENS = ["internacoes", "internacoes_transito", "homem_18_39", "condutor_homem_18_39"]
GRUPOS_VITIMA = {"motociclista": "moto", "ciclista": "cicl", "auto_placebo": "auto"}

#: Grupos do tratamento que entram na estimacao principal (plano, secao 4).
GRUPOS_ESTIMACAO = ("datado", "sem_quebra")


def conferir_hash(caminho: Path, esperado: str = HASH_TRATAMENTO) -> None:
    """Para tudo se o arquivo do tratamento nao for o congelado."""
    obtido = hashlib.sha256(Path(caminho).read_bytes()).hexdigest()
    if obtido != esperado:
        raise ValueError(
            f"{caminho}: SHA-256 {obtido} nao e o do pre-registro ({esperado}). "
            "O tratamento congelado nao muda depois do deposito (D-041)."
        )


def periodo(ano: int | pd.Series, mes: int | pd.Series) -> int | pd.Series:
    """Indice mensal: 2015-01 -> 1."""
    return (ano - INICIO.year) * 12 + mes


def periodo_de(aaaa_mm: str) -> int:
    p = pd.Period(aaaa_mm, freq="M")
    return periodo(p.year, p.month)


def ler_tratamento(caminho: Path) -> pd.DataFrame:
    """Arquivo congelado -> uma linha por municipio, com `g` (0 = sem quebra)."""
    conferir_hash(caminho)
    t = pd.read_csv(caminho, dtype={"municipio_ibge": "int64"})
    t["municipio_res"] = t["municipio_ibge"].map(mun.para_6_digitos)
    t["g"] = [periodo_de(m) if isinstance(m, str) else 0 for m in t["mes_tratamento"]]
    t["g"] = t["g"].astype("int64")
    return t


def desfechos_sih(painel: pd.DataFrame) -> pd.DataFrame:
    """Painel do SIH -> municipio x ano x mes, uma coluna por grupo de vitima e contagem.

    Soma por cima da UF do arquivo. Colunas: `moto_internacoes`,
    `moto_internacoes_transito`, `moto_homem_18_39`, ..., `auto_internacoes_transito`.
    """
    p = painel[painel["grupo"].isin(GRUPOS_VITIMA)].copy()
    for c in CONTAGENS:
        p[c] = pd.to_numeric(p[c], errors="coerce").fillna(0).astype("int64")
    soma = p.groupby(["municipio_res", "ano", "mes", "grupo"], as_index=False)[CONTAGENS].sum()
    largo = soma.pivot_table(
        index=["municipio_res", "ano", "mes"], columns="grupo", values=CONTAGENS, fill_value=0
    )
    largo.columns = [f"{GRUPOS_VITIMA[g]}_{c}" for c, g in largo.columns]
    # Grupo sem nenhum caso no recorte nao pode sumir das colunas.
    todas = [f"{v}_{c}" for c in CONTAGENS for v in GRUPOS_VITIMA.values()]
    largo = largo.reindex(columns=todas, fill_value=0).astype("int64").reset_index()
    largo["municipio_res"] = largo["municipio_res"].astype(str)
    return largo


def intensidade(tratamento: pd.DataFrame, aberturas: pd.DataFrame) -> pd.Series:
    """Proxy de H2 (D-043): aberturas de MEI 5320-2/02 por mil habitantes nos 12
    meses a partir da quebra, Censo 2022. Indexada por `municipio_ibge`; so `datado`.
    """
    dat = tratamento[tratamento["grupo"] == "datado"][
        ["municipio_ibge", "mes_tratamento", "populacao_2022"]
    ]
    ab = aberturas.copy()
    ab["p"] = ab["mes"].map(periodo_de)
    m = ab.merge(dat, on="municipio_ibge")
    m["g"] = m["mes_tratamento"].map(periodo_de)
    m = m[(m["p"] >= m["g"]) & (m["p"] <= m["g"] + 11)]
    soma = m.groupby("municipio_ibge")["aberturas"].sum()
    soma = soma.reindex(dat["municipio_ibge"], fill_value=0)
    pop = dat.set_index("municipio_ibge")["populacao_2022"]
    return (1000 * soma / pop).rename("intensidade_mei")


def tercis(intens: pd.Series, g: pd.Series) -> pd.Series:
    """Tercis de intensidade entre os tratados da janela balanceada (D-043).

    `g` e o periodo de tratamento, indexado como `intens`. Fora da janela: NA.
    """
    dentro = g.between(periodo_de("2017-07"), periodo_de("2023-12"))
    x = intens[dentro & (g > 0)]
    rotulo = pd.qcut(x.rank(method="first"), 3, labels=[1, 2, 3]).astype("Int64")
    return rotulo.reindex(intens.index)


def montar(
    painel: pd.DataFrame,
    denominadores: pd.DataFrame,
    tratamento: pd.DataFrame,
    regioes: pd.DataFrame,
    aberturas: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Painel balanceado municipio x mes, 2015-01 a 2025-12, para todo o universo.

    O recorte da estimacao (grupo, janela, coortes) e do estimador: aqui ficam os
    1.710 municipios do universo com `grupo_trat`, para que a robustez que usa a
    `coorte_precoce` saia do mesmo arquivo.

    `regioes`: `municipio_ibge`, `regiao_imediata`. `denominadores`:
    `municipio_res`, `ano`, `mes`, `frota_moto` (populacao nao entra: o desfecho e
    por frota, e a populacao anual tem buraco em 2022-2023, D-015).
    """
    t = tratamento.rename(columns={"grupo": "grupo_trat"})
    base = t[
        ["municipio_ibge", "municipio_res", "uf", "faixa", "populacao_2022", "grupo_trat", "g"]
    ].merge(regioes[["municipio_ibge", "regiao_imediata"]], on="municipio_ibge", how="left")
    if base["regiao_imediata"].isna().any():
        faltam = base.loc[base["regiao_imediata"].isna(), "municipio_ibge"].tolist()
        raise ValueError(f"municipios sem regiao imediata (cluster): {faltam[:10]}")

    meses = pd.period_range(INICIO, FIM, freq="M")
    grade = pd.DataFrame({"ano": meses.year, "mes": meses.month})
    df = base.merge(grade, how="cross")
    df["periodo"] = periodo(df["ano"], df["mes"])

    y = desfechos_sih(painel)
    df = df.merge(y, on=["municipio_res", "ano", "mes"], how="left")
    cols_y = [c for c in y.columns if c not in ("municipio_res", "ano", "mes")]
    df[cols_y] = df[cols_y].fillna(0).astype("int64")

    d = denominadores[["municipio_res", "ano", "mes", "frota_moto"]].copy()
    d["municipio_res"] = d["municipio_res"].astype(str)
    df = df.merge(d, on=["municipio_res", "ano", "mes"], how="left")

    moto = pd.to_numeric(df["frota_moto"], errors="coerce")
    por_moto = 100_000 / moto.where(moto > 0)
    # Desfecho principal de H1 (plano, secao 3): transito, por 100 mil motos.
    df["taxa_moto_transito"] = df["moto_internacoes_transito"] * por_moto
    # H3: perfil contra complemento, sobre `internacoes` como o plano declara.
    df["taxa_moto_h1839"] = df["moto_homem_18_39"] * por_moto
    df["taxa_moto_resto"] = (df["moto_internacoes"] - df["moto_homem_18_39"]) * por_moto
    df["taxa_moto_condutor_h1839"] = df["moto_condutor_homem_18_39"] * por_moto

    if aberturas is not None:
        intens = intensidade(tratamento, aberturas)
        g = tratamento.set_index("municipio_ibge")["g"].reindex(intens.index)
        h2 = pd.DataFrame({"intensidade_mei": intens, "tercil_h2": tercis(intens, g)})
        df = df.merge(h2, left_on="municipio_ibge", right_index=True, how="left")

    df["regiao_imediata"] = df["regiao_imediata"].astype("int64")
    return df.sort_values(["municipio_ibge", "periodo"]).reset_index(drop=True)


def resumo(df: pd.DataFrame) -> pd.DataFrame:
    """Quantos municipios por grupo e quantos `datado` cabem na janela balanceada."""
    um = df.drop_duplicates("municipio_ibge")
    janela = um["g"].between(periodo_de("2017-07"), periodo_de("2023-12"))
    return (
        um.assign(na_janela=np.where(um["grupo_trat"] == "datado", janela, np.nan))
        .groupby("grupo_trat")
        .agg(municipios=("municipio_ibge", "size"), na_janela=("na_janela", "sum"))
    )
