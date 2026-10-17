"""Filtro, classificacao e agregacao das declaracoes de obito do SIM.

Sem rede: recebe DataFrame, devolve DataFrame. A operacionalizacao inteira esta
no D-053 (H5a, H5b e o lado SIM de H4), fixada antes do primeiro download.
"""

from __future__ import annotations

import logging

import pandas as pd

from vcemal import cid as cid_mod

log = logging.getLogger("vcemal.transform.sim")

#: Colunas da DO que o projeto guarda. O resto do arquivo nao sai do download.
COLS: list[str] = [
    "CAUSABAS",
    "CODMUNRES",
    "CODMUNOCOR",
    "DTOBITO",
    "LOCOCOR",
    "ACIDTRAB",
    "CIRCOBITO",
    "SEXO",
    "IDADE",
]

#: `LOCOCOR` fora de estabelecimento de saude: 3 domicilio, 4 via publica,
#: 5 outros, 6 aldeia indigena. 1 (hospital), 2 (outro estabelecimento), 9 e
#: branco ficam de fora -- ignorado nao conta como fora (D-044).
LOCOCOR_FORA_SAUDE: frozenset[str] = frozenset({"3", "4", "5", "6"})

#: `ACIDTRAB` preenchido: 1 sim, 2 nao. 9 (ignorado) e branco nao contam (D-053).
ACIDTRAB_PREENCHIDO: frozenset[str] = frozenset({"1", "2"})

#: `IDADE` da DO: primeiro digito e a unidade (4 = anos), os dois seguintes o valor.
IDADE_18_39: frozenset[str] = frozenset(f"4{n:02d}" for n in range(18, 40))


def filtrar(df: pd.DataFrame) -> pd.DataFrame:
    """So as DO cuja causa basica cai num dos grupos de `vcemal.cid`, colunas de `COLS`."""
    faltam = [c for c in COLS if c not in df.columns]
    if faltam:
        log.warning("colunas ausentes na DO, seguem vazias: %s", faltam)
    out = df.reindex(columns=COLS).astype("string").fillna("")
    for c in COLS:
        out[c] = out[c].str.strip()
    out["CAUSABAS"] = out["CAUSABAS"].str.upper()
    grupo = out["CAUSABAS"].map(cid_mod.grupo_de)
    return out[grupo.notna()].reset_index(drop=True)


def classificar(df: pd.DataFrame) -> pd.DataFrame:
    """Marca grupo, transito, mes do obito e os recortes de H5b e H4."""
    out = df.copy()
    out["grupo"] = out["CAUSABAS"].map(cid_mod.grupo_de)
    out["transito"] = out["CAUSABAS"].map(cid_mod.em_transito).astype(bool)
    data = pd.to_datetime(out["DTOBITO"], format="%d%m%Y", errors="coerce")
    out["ano"] = data.dt.year.astype("Int64")
    out["mes"] = data.dt.month.astype("Int64")
    out["fora_saude"] = out["LOCOCOR"].isin(LOCOCOR_FORA_SAUDE)
    out["homem_18_39"] = (out["SEXO"] == "1") & out["IDADE"].isin(IDADE_18_39)
    out["acidtrab_preenchido"] = out["ACIDTRAB"].isin(ACIDTRAB_PREENCHIDO)
    out["acidtrab_sim"] = out["ACIDTRAB"] == "1"
    out["municipio_ignorado"] = out["CODMUNRES"].str.fullmatch(r"\d{2}0000") | ~out[
        "CODMUNRES"
    ].str.fullmatch(r"\d{6}")
    return out


def casos_h5(df: pd.DataFrame) -> pd.DataFrame:
    """Obitos de motociclista em transito -- o universo de H5 e do lado SIM de H4."""
    return df[(df["grupo"] == "motociclista") & df["transito"]]


def agregar(df: pd.DataFrame) -> pd.DataFrame:
    """Municipio de residencia x ano x mes: H5a e H5b. So municipio conhecido e data valida."""
    m = casos_h5(df)
    m = m[~m["municipio_ignorado"] & m["mes"].notna()]
    painel = (
        m.groupby(["CODMUNRES", "ano", "mes"], as_index=False)
        .agg(
            obitos_moto_transito=("transito", "size"),
            obitos_moto_transito_fora_saude=("fora_saude", "sum"),
        )
        .rename(columns={"CODMUNRES": "municipio_res"})
    )
    painel["obitos_moto_transito_fora_saude"] = painel["obitos_moto_transito_fora_saude"].astype(
        "int64"
    )
    return painel


def h4_uf_ano(df: pd.DataFrame, uf: str) -> pd.DataFrame:
    """Lado SIM de H4 numa UF: homens de 18 a 39, total, ACIDTRAB preenchido e = 1."""
    m = casos_h5(df)
    m = m[m["homem_18_39"] & m["ano"].notna()]
    out = m.groupby("ano", as_index=False).agg(
        obitos_homem_18_39=("homem_18_39", "size"),
        acidtrab_preenchido=("acidtrab_preenchido", "sum"),
        acidtrab_sim=("acidtrab_sim", "sum"),
    )
    out.insert(0, "uf", uf)
    return out
