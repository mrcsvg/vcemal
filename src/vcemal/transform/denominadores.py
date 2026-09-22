"""
Denominadores do painel: frota de moto (Senatran) e populacao (IBGE).

A frota e o denominador da taxa de internacao de motociclista (D-003). A
populacao entra como controle e como denominador dos grupos que nao tem frota
-- ciclista nao registra em RENAVAM (D-003, excecao).

Nada aqui inventa linha. Municipio que nao casa e **reportado**, nunca
descartado em silencio: um denominador que some deixa a taxa sair `NaN`, o que
se ve; um denominador que casa errado deixa a taxa sair plausivel e errada, o
que nao se ve.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from vcemal import frota as frota_mod
from vcemal import municipios as mun

log = logging.getLogger("vcemal.transform.denominadores")

#: Quantos municipios sem par toleramos antes de considerar o arquivo suspeito.
#: Em dezembro/2023 o casamento exato + apelidos cobre 5571 de 5572 linhas; a
#: unica sobra legitima e `MUNICIPIO NAO INFORMADO`.
LIMITE_SEM_PAR = 20


def _linha_do_cabecalho(caminho: Path, limite: int = 12) -> int:
    """Indice da linha que traz UF e MUNICIPIO. Varia entre os anos da serie."""
    topo = pd.read_excel(caminho, sheet_name=0, header=None, nrows=limite)
    for i, linha in topo.iterrows():
        celulas = {str(v).strip().upper() for v in linha.tolist()}
        if "UF" in celulas and any(c.startswith("MUNIC") for c in celulas):
            return int(i)
    raise ValueError(f"nao achei o cabecalho (UF, MUNICIPIO) em {caminho}")


def ler_frota(caminho: Path) -> pd.DataFrame:
    """Le uma planilha "Frota por Municipio e Tipo" e devolve as linhas de dado."""
    cabecalho = _linha_do_cabecalho(caminho)
    df = pd.read_excel(caminho, sheet_name=0, header=cabecalho)
    df.columns = [str(c).strip().upper() for c in df.columns]

    coluna_municipio = next(c for c in df.columns if c.startswith("MUNIC"))
    df = df.rename(columns={coluna_municipio: "MUNICIPIO"})

    # O cabecalho vem repetido na linha seguinte em parte da serie; e as linhas
    # de rodape (totais, notas) nao tem UF de duas letras.
    df = df[df["UF"].astype(str).str.strip().str.len() == 2].copy()
    df = df[df["MUNICIPIO"].astype(str).str.upper() != "MUNICIPIO"]

    faltando = frota_mod.conferir_colunas(list(df.columns))
    if faltando:
        raise ValueError(f"{caminho.name}: sem as colunas de tipo {faltando}")

    for coluna in (*frota_mod.TIPOS_MOTO, frota_mod.COLUNA_TOTAL):
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0).astype("int64")

    df["UF"] = df["UF"].astype(str).str.strip().str.upper()
    return df


def agregar_frota(
    df: pd.DataFrame, indice: dict[tuple[str, str], int], ano: int, mes: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Soma os tipos de V20-V29 e resolve o municipio para codigo IBGE.

    Devolve `(frota, sem_par)`. `sem_par` sao as linhas cujo municipio nao foi
    reconhecido -- devem ser olhadas, nao ignoradas.
    """
    df = df.copy()
    df[frota_mod.COLUNA_FROTA_MOTO] = df[list(frota_mod.TIPOS_MOTO)].sum(axis=1)
    df["municipio_ibge"] = [
        mun.resolver(uf, nome, indice) for uf, nome in zip(df["UF"], df["MUNICIPIO"], strict=True)
    ]

    sem_par = df[df["municipio_ibge"].isna()][["UF", "MUNICIPIO", frota_mod.COLUNA_FROTA_MOTO]]
    if len(sem_par) > LIMITE_SEM_PAR:
        log.error(
            "%04d-%02d: %d municipios sem par no IBGE (limite %d) -- layout mudou?",
            ano,
            mes,
            len(sem_par),
            LIMITE_SEM_PAR,
        )
    elif len(sem_par):
        log.warning(
            "%04d-%02d: %d municipios sem par: %s",
            ano,
            mes,
            len(sem_par),
            ", ".join(f"{r.UF}/{r.MUNICIPIO}" for r in sem_par.itertuples()),
        )

    frota = df[df["municipio_ibge"].notna()].copy()
    # A coluna vira float64 enquanto houver municipio sem par; sem o cast o
    # codigo chega como "1200013.0".
    frota["municipio_ibge"] = frota["municipio_ibge"].astype("int64")
    frota["municipio_res"] = frota["municipio_ibge"].map(mun.para_6_digitos)
    frota = frota.assign(ano=ano, mes=mes)
    colunas = ["municipio_res", "ano", "mes", frota_mod.COLUNA_FROTA_MOTO, *frota_mod.TIPOS_MOTO]
    if frota_mod.COLUNA_TOTAL in frota.columns:
        colunas.append(frota_mod.COLUNA_TOTAL)
    frota = frota[colunas].rename(columns={frota_mod.COLUNA_TOTAL: "frota_total"})
    frota.columns = [c.lower().replace("-", "_") for c in frota.columns]
    return frota.reset_index(drop=True), sem_par.reset_index(drop=True)


def populacao_para_painel(linhas: list[dict]) -> pd.DataFrame:
    """Linhas de `vcemal.extract.ibge.populacao` -> `municipio_res`, `ano`, `populacao`."""
    if not linhas:
        return pd.DataFrame(columns=["municipio_res", "ano", "populacao"])
    df = pd.DataFrame(linhas)
    df["municipio_res"] = df["municipio_ibge"].map(mun.para_6_digitos)
    return df[["municipio_res", "ano", "populacao"]]


def juntar(painel: pd.DataFrame, frota: pd.DataFrame, populacao: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta frota (municipio x mes) e populacao (municipio x ano) ao painel.

    Join a esquerda: o painel manda. Municipio-mes sem frota fica com `NA`, e a
    taxa sai `NaN` -- de proposito.
    """
    saida = painel.copy()
    saida["municipio_res"] = saida["municipio_res"].astype("string")

    if not frota.empty:
        f = frota.copy()
        f["municipio_res"] = f["municipio_res"].astype("string")
        saida = saida.merge(
            f[["municipio_res", "ano", "mes", frota_mod.COLUNA_FROTA_MOTO]],
            on=["municipio_res", "ano", "mes"],
            how="left",
        )
    else:
        saida[frota_mod.COLUNA_FROTA_MOTO] = pd.NA

    if not populacao.empty:
        p = populacao.copy()
        p["municipio_res"] = p["municipio_res"].astype("string")
        saida = saida.merge(p, on=["municipio_res", "ano"], how="left")
    else:
        saida["populacao"] = pd.NA

    return saida


#: Numerador do desfecho principal declarado no pre-registro (D-023). NAO e
#: `internacoes`, que inclui as AIH de nao-transito, nem `internacoes_condutor`,
#: que e 9,4% do desfecho e condiciona em pratica de codificacao.
NUMERADOR_DESFECHO = "internacoes_transito"


def taxas(painel: pd.DataFrame, por: int = 100_000, numerador: str = "internacoes") -> pd.DataFrame:
    """Taxa de internacao por `por` motos e por `por` habitantes.

    `numerador` default e `internacoes` por compatibilidade, mas **a estimacao
    usa `NUMERADOR_DESFECHO`** (`internacoes_transito`): o desfecho declarado e
    acidente de transito, nao toda AIH do grupo. Passar a coluna errada aqui
    produz taxa plausivel e errada, entao o nome e explicito.

    Denominador zero vira `NaN`, nunca infinito: municipio sem frota registrada
    nao tem taxa definida, e um infinito viaja silencioso ate a regressao.
    """
    saida = painel.copy()
    if numerador not in saida.columns:
        raise KeyError(f"painel sem a coluna de numerador {numerador!r}")
    moto = pd.to_numeric(saida.get(frota_mod.COLUNA_FROTA_MOTO), errors="coerce")
    pop = pd.to_numeric(saida.get("populacao"), errors="coerce")
    internacoes = pd.to_numeric(saida[numerador], errors="coerce")

    saida["taxa_por_frota"] = por * internacoes / moto.where(moto > 0)
    saida["taxa_por_populacao"] = por * internacoes / pop.where(pop > 0)
    return saida
