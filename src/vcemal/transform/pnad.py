"""Do microdado da PNAD Continua as quatro estatisticas da precariedade. Sem rede.

Reproduz o recorte do informativo do IBGE ("Trabalho por meio de plataformas
digitais 2024") antes de ir alem dele: pessoas de 14 anos ou mais ocupadas na
semana de referencia, **exclusive setor publico e militares**, no trabalho
principal. Se `resumir` nao devolver os numeros publicados para 2024 (D-031),
a leitura esta errada, nao o IBGE.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from vcemal import pnad as pnad_mod

log = logging.getLogger("vcemal.transform.pnad")


def ler(
    txt: Path, layout: dict[str, tuple[int, int]], variaveis=pnad_mod.VARIAVEIS
) -> pd.DataFrame:
    """Le so as `variaveis` do arquivo de largura fixa, como texto.

    Fatia bytes linha a linha: mais rapido que `read_fwf` para um arquivo de
    2 GB do qual se quer vinte colunas, e sem inferencia de tipo no meio.
    """
    faltando = [v for v in variaveis if v not in layout]
    if faltando:
        raise KeyError(f"dicionario sem as variaveis {faltando}")
    fatias = [(layout[v][0] - 1, layout[v][0] - 1 + layout[v][1]) for v in variaveis]
    colunas: list[list[str]] = [[] for _ in variaveis]
    with txt.open("rb") as f:
        for linha in f:
            for i, (a, b) in enumerate(fatias):
                colunas[i].append(linha[a:b].decode("ascii", "replace"))
    df = pd.DataFrame(
        {v: pd.Series(c, dtype="string") for v, c in zip(variaveis, colunas, strict=True)}
    )
    log.info("%s: %d pessoas", txt.name, len(df))
    return df


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.strip().replace("", pd.NA), errors="coerce")


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Tipos e as marcas que `resumir` usa. Uma linha por pessoa, como veio."""
    saida = pd.DataFrame(index=df.index)
    saida["ano"] = _num(df["Ano"]).astype("Int64")
    saida["trimestre"] = _num(df["Trimestre"]).astype("Int64")
    saida["uf"] = df["UF"].str.strip()
    saida["regiao"] = saida["uf"].map(pnad_mod.regiao_de)
    saida["capital"] = _num(df["V1023"]) == 1
    saida["peso"] = _num(df["V1028"])
    saida["homem"] = _num(df["V2007"]) == 1
    saida["idade"] = _num(df["V2009"])
    ocupado = _num(df["VD4002"]) == 1
    privado = df["VD4009"].map(pnad_mod.setor_privado)
    saida["universo"] = ocupado & privado.eq(True)
    saida["informal"] = [
        pnad_mod.informal(a, b) for a, b in zip(df["VD4009"], df["V4019"], strict=True)
    ]
    saida["contribuinte"] = _num(df["VD4012"]) == 1
    saida["horas"] = _num(df["V4039"])
    saida["rend"] = _num(df["VD4016"])
    ocupacao = df["V4010"].str.strip()
    saida["plataformizado"] = _num(df["SD14001"]) == 1
    saida["app_entrega"] = _num(df["S140093"]) == 1
    saida["motociclista"] = ocupacao == pnad_mod.COD_MOTOCICLISTA
    saida["entregador"] = saida["app_entrega"] & ocupacao.isin(pnad_mod.OCUPACOES_ENTREGADOR)
    return saida


def deflacionar(pessoas: pd.DataFrame, deflator: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta `rend_real`: rendimento em reais do trimestre de referencia do deflator.

    O fator e por UF e trimestre (`Habitual`). Pessoa sem fator e erro: e o
    sinal de que o deflator nao e o da rodada.
    """
    saida = pessoas.copy()
    chave = saida[["ano", "trimestre", "uf"]].copy()
    chave["trim"] = chave["trimestre"].map(lambda t: pnad_mod.trimestre_do_deflator(int(t)))
    fator = chave.merge(
        deflator.rename(columns={"Ano": "ano", "UF": "uf"}),
        on=["ano", "trim", "uf"],
        how="left",
    )["Habitual"].to_numpy()
    if np.isnan(fator).any():
        faltam = chave[np.isnan(fator)].drop_duplicates().head(5).to_dict("records")
        raise KeyError(f"deflator sem fator para {faltam}")
    saida["rend_real"] = saida["rend"] * fator
    return saida


#: Grupos que a tabela reporta, na ordem. Cada um e um filtro sobre `preparar`.
#: `app_entrega` e `entregadores` sao subconjuntos de `plataformizado` (SD14001):
#: e assim que o IBGE chega aos 485 mil e 274 mil de 2024. Sem essa condicao o
#: bruto `S140093` inclui gente que a derivada do IBGE nao conta como
#: plataformizada e o total sobe para 622 mil.
GRUPOS: dict[str, str] = {
    "ocupados_privado": "universo",
    "plataformizados": "universo & plataformizado",
    "nao_plataformizados": "universo & ~plataformizado",
    "app_entrega": "universo & plataformizado & app_entrega",
    "entregadores": "universo & plataformizado & entregador",
    "motociclistas": "universo & motociclista",
    "motociclistas_plataformizados": "universo & motociclista & plataformizado",
    "motociclistas_nao_plataformizados": "universo & motociclista & ~plataformizado",
}

COLUNAS = [
    "pessoas",
    "amostra",
    "pct_informal",
    "pct_contribuinte",
    "pct_homens",
    "horas_media",
    "rend_medio",
    "rend_hora",
    "rend_medio_real",
    "rend_hora_real",
]


def _media(valores: pd.Series, peso: pd.Series) -> float:
    ok = valores.notna() & peso.notna()
    if not ok.any():
        return float("nan")
    return float(np.average(valores[ok].astype(float), weights=peso[ok].astype(float)))


def _resumo(g: pd.DataFrame) -> dict[str, float]:
    peso = g["peso"]
    horas = _media(g["horas"], peso)
    rend = _media(g["rend"], peso)
    rend_real = _media(g["rend_real"], peso) if "rend_real" in g else float("nan")
    divisor = horas * pnad_mod.SEMANAS_POR_MES if horas and horas > 0 else float("nan")
    return {
        "pessoas": float(peso.sum()),
        "amostra": int(len(g)),
        "pct_informal": 100 * _media(g["informal"].astype("boolean").astype("Float64"), peso),
        "pct_contribuinte": 100 * _media(g["contribuinte"].astype(float), peso),
        "pct_homens": 100 * _media(g["homem"].astype(float), peso),
        "horas_media": horas,
        "rend_medio": rend,
        "rend_hora": rend / divisor,
        "rend_medio_real": rend_real,
        "rend_hora_real": rend_real / divisor,
    }


def resumir(pessoas: pd.DataFrame, *chaves: str) -> pd.DataFrame:
    """Uma linha por (ano, trimestre, *chaves, grupo), ponderada por `peso`.

    `rend_hora` e `rend_medio / (horas_media x 4,345)`, razao de medias -- e
    assim que o IBGE publica. Sem `chaves`, sai o Brasil.
    """
    linhas = []
    base_chaves = ["ano", "trimestre", *chaves]
    for grupo, expressao in GRUPOS.items():
        sel = pessoas[pessoas.eval(expressao)]
        if sel.empty:
            continue
        for valores, g in sel.groupby(base_chaves, dropna=False):
            valores = valores if isinstance(valores, tuple) else (valores,)
            linhas.append(
                dict(zip(base_chaves, valores, strict=True)) | {"grupo": grupo} | _resumo(g)
            )
    saida = pd.DataFrame(linhas)
    if not chaves:
        saida.insert(2, "regiao", "Brasil")
    return saida[[*base_chaves, *(["regiao"] if not chaves else []), "grupo", *COLUNAS]]
