"""H4, descritiva: fracao com nexo de trabalho registrado no SIH e no SIM (D-044, D-057).

Sem rede. O lado SIM vem pronto de `vcemal.transform.sim.h4_uf_ano`; aqui fica o
lado SIH, sobre as AIH ja classificadas, e a juncao das duas bases.
"""

from __future__ import annotations

import pandas as pd

#: Codigo IBGE da UF (dois primeiros digitos do municipio) -> sigla.
UF_DO_CODIGO: dict[str, str] = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}  # fmt: skip


#: Colunas de contagem da tabela juntada; o resto e fracao derivada delas.
CONTAGENS: list[str] = [
    "internacoes_homem_18_39",
    "car_int_preenchido",
    "nexo_ocupacional",
    "obitos_homem_18_39",
    "acidtrab_preenchido",
    "acidtrab_sim",
]


def sih_casos(aih: pd.DataFrame) -> pd.DataFrame:
    """AIH de motociclista em transito, homem de 18 a 39 -- o universo de H4 no SIH."""
    homem = aih["SEXO"].astype("string").str.strip() == "1"
    faixa = pd.to_numeric(aih["idade_anos"], errors="coerce").between(18, 39)
    sel = (aih["grupo"] == "motociclista") & aih["em_transito"].astype(bool) & homem & faixa
    return aih[sel.fillna(False)]


def sih_uf_ano(aih: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Lado SIH de uma competencia: por UF de residencia, total, CAR_INT valido e nexo."""
    c = sih_casos(aih)
    uf = c["MUNIC_RES"].astype("string").str[:2].map(UF_DO_CODIGO)
    out = (
        c.assign(uf=uf, ano=ano)
        .dropna(subset=["uf"])
        .groupby(["uf", "ano"], as_index=False)
        .agg(
            internacoes_homem_18_39=("grupo", "size"),
            car_int_preenchido=("car_int_valido", "sum"),
            nexo_ocupacional=("nexo_ocupacional", "sum"),
        )
    )
    return out.astype({"car_int_preenchido": "int64", "nexo_ocupacional": "int64"})


def juntar(sih: pd.DataFrame, sim: pd.DataFrame) -> pd.DataFrame:
    """SIH e SIM lado a lado por UF x ano, com preenchimento e fracao com nexo."""
    t = sih.merge(sim, on=["uf", "ano"], how="outer").sort_values(["uf", "ano"])
    t[CONTAGENS] = t[CONTAGENS].fillna(0).astype("int64")
    return com_fracoes(t)


def com_fracoes(t: pd.DataFrame) -> pd.DataFrame:
    """Preenchimento sobre o total; nexo sobre o preenchido (D-008), nos dois campos."""
    t = t.copy()
    t["sih_pct_preenchido"] = 100 * t["car_int_preenchido"] / t["internacoes_homem_18_39"]
    t["sih_pct_nexo"] = 100 * t["nexo_ocupacional"] / t["car_int_preenchido"]
    t["sim_pct_preenchido"] = 100 * t["acidtrab_preenchido"] / t["obitos_homem_18_39"]
    t["sim_pct_nexo"] = 100 * t["acidtrab_sim"] / t["acidtrab_preenchido"]
    return t.reset_index(drop=True)


def brasil_ano(t: pd.DataFrame) -> pd.DataFrame:
    """Soma as UFs e recalcula as fracoes -- razao de somas, nao media de fracoes."""
    soma = t.groupby("ano", as_index=False)[CONTAGENS].sum()
    return com_fracoes(soma)


def pnad_referencia(pnad: pd.DataFrame) -> pd.DataFrame:
    """Fracao plataformizada entre motociclistas ocupados, Brasil, por rodada (teto, D-057)."""
    b = pnad[pnad["regiao"] == "Brasil"].pivot_table(
        index=["ano", "trimestre"], columns="grupo", values="pessoas", aggfunc="first"
    )
    out = pd.DataFrame(
        {
            "motociclistas": b["motociclistas"],
            "motociclistas_plataformizados": b["motociclistas_plataformizados"],
        }
    )
    out["pct_plataformizado_teto"] = (
        100 * out["motociclistas_plataformizados"] / out["motociclistas"]
    )
    return out.reset_index()
