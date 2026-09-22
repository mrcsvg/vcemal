"""Normalizacao, classificacao e agregacao das AIH do SIH/SUS.

Sem efeito colateral e sem rede: recebe DataFrame, devolve DataFrame. O
download vive em `vcemal.extract.sih`, a definicao de caso em `vcemal.cid`.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from vcemal import cid as cid_mod

log = logging.getLogger("vcemal.transform.sih")

#: Colunas do arquivo RD que o projeto usa. Competencias antigas nao tem todas;
#: `normalizar` avisa e segue com as que existem.
COLS: list[str] = [
    "N_AIH",
    "MUNIC_RES",
    "MUNIC_MOV",
    "NASC",
    "IDADE",
    "COD_IDADE",
    "SEXO",
    "DT_INTER",
    "DT_SAIDA",
    "DIAS_PERM",
    "UTI_MES_TO",
    "MORTE",
    "CAR_INT",
    "DIAG_PRINC",
    "DIAG_SECUN",
    *[f"DIAGSEC{i}" for i in range(1, 10)],
    "VAL_TOT",
    "VAL_SH",
    "VAL_SP",
    "CNES",
    "ESPEC",
    "PROC_REA",
    "RACA_COR",
]

#: Campos de diagnostico varridos atras da causa externa, **em ordem de
#: precedencia**. A norma do SIH manda a causa externa (capitulo XX) para o
#: diagnostico secundario e deixa a lesao (capitulo XIX) no principal, mas
#: permite o principal em alguns casos -- por isso ele entra por ultimo, e nao
#: fica de fora. Ver D-017.
CAMPOS_CAUSA_EXTERNA: tuple[str, ...] = (
    "DIAG_SECUN",
    *[f"DIAGSEC{i}" for i in range(1, 10)],
    "DIAG_PRINC",
)

_COLS_TEXTO = (
    "MUNIC_RES",
    "MUNIC_MOV",
    "CAR_INT",
    "SEXO",
    "CNES",
    "PROC_REA",
    *CAMPOS_CAUSA_EXTERNA,
)
_COLS_INT = ("DIAS_PERM", "UTI_MES_TO", "IDADE", "MORTE")
_COLS_VALOR = ("VAL_TOT", "VAL_SH", "VAL_SP")
_COLS_DATA = ("DT_INTER", "DT_SAIDA")

#: COD_IDADE 4 = anos, 3 = meses, 2 = dias, 1 = horas.
_COD_IDADE_ANOS = 4


def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes, tipos e a idade em anos completos."""
    df = df.copy()
    df.columns = [c.upper().strip() for c in df.columns]

    faltando = [c for c in COLS if c not in df.columns]
    if faltando:
        log.warning("colunas ausentes nesta competencia: %s", faltando)
    df = df[[c for c in COLS if c in df.columns]]

    for c in _COLS_TEXTO:
        if c in df:
            df[c] = df[c].astype("string").str.strip()

    for c in (*_COLS_INT, *_COLS_VALOR):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    for c in _COLS_DATA:
        if c in df:
            df[c] = pd.to_datetime(df[c], format="%Y%m%d", errors="coerce")

    if "COD_IDADE" in df and "IDADE" in df:
        cod = pd.to_numeric(df["COD_IDADE"], errors="coerce")
        # Menor de um ano vira 0 -- a unidade nao e ano, e a faixa de interesse
        # do projeto (18-39) nao e afetada.
        df["idade_anos"] = df["IDADE"].where(cod == _COD_IDADE_ANOS, 0)
    elif "IDADE" in df:
        df["idade_anos"] = df["IDADE"]
    else:
        df["idade_anos"] = pd.Series(np.nan, index=df.index, dtype="float64")

    return df


def localizar_causa_externa(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Acha o codigo de causa externa de cada AIH e de qual campo ele veio.

    Varre `CAMPOS_CAUSA_EXTERNA` na ordem e fica com o **primeiro codigo que
    cai na definicao de caso** -- nao o primeiro campo preenchido. A diferenca
    importa: o campo de precedencia mais alta costuma trazer a lesao (`S720`),
    e parar nele descartaria a AIH inteira.

    Vetorizado de proposito: isto roda sobre milhoes de AIH por competencia, e
    um `apply` linha a linha aqui domina o tempo do pipeline.
    """
    codigo = pd.Series(pd.NA, index=df.index, dtype="string")
    origem = pd.Series(pd.NA, index=df.index, dtype="string")

    for campo in CAMPOS_CAUSA_EXTERNA:
        if campo not in df.columns:
            continue
        candidato = df[campo].astype("string").str.strip().str.upper()
        casa = candidato.str[:3].map(cid_mod.CATEGORIA_GRUPO).notna()
        preencher = codigo.isna() & casa
        if not preencher.any():
            continue
        codigo = codigo.mask(preencher, candidato)
        origem = origem.mask(preencher, campo)

    return codigo, origem


def classificar(df: pd.DataFrame) -> pd.DataFrame:
    """Marca grupo de vitima, leitura do quarto digito e nexo ocupacional.

    Devolve so as AIH dentro da definicao de caso -- as demais saem aqui.
    """
    df = df.copy()
    causa, origem = localizar_causa_externa(df)
    df["causa_externa"] = causa
    df["campo_causa"] = origem

    cid = causa.fillna("")
    cat3 = cid.str[:3]
    dig4 = cid.str[3:4]

    df["grupo"] = cat3.map(cid_mod.CATEGORIA_GRUPO).astype("object")
    no_escopo = df["grupo"].notna()

    # O quarto digito muda de sentido entre a estrutura padrao e a terminal
    # (V19/V29/V49), por isso a regra nao pode ser uma mascara so. Ver vcemal.cid.
    terminal = cat3.isin(cid_mod.CATEGORIAS_TERMINAIS)
    df["categoria_terminal"] = terminal & no_escopo
    df["em_transito"] = no_escopo & np.where(
        terminal,
        dig4.isin(cid_mod.TRANSITO_TERMINAL),
        dig4.isin(cid_mod.TRANSITO_PADRAO),
    )
    df["condutor_transito"] = no_escopo & dig4.isin(cid_mod.CONDUTOR_TRANSITO)
    # `.3` da estrutura padrao entra em transito por convencao NCHS, nao por
    # definicao. Isolado para a analise de sensibilidade.
    df["embarque_desembarque"] = no_escopo & ~terminal & dig4.isin(cid_mod.EMBARQUE_DESEMBARQUE)

    car_int = df["CAR_INT"] if "CAR_INT" in df else pd.Series(pd.NA, index=df.index, dtype="string")
    df["car_int_label"] = car_int.map(cid_mod.CAR_INT_LABEL).fillna("desconhecido")
    df["car_int_valido"] = car_int.map(cid_mod.car_int_preenchido).fillna(False).astype(bool)
    df["nexo_ocupacional"] = car_int.isin(cid_mod.CAR_INT_OCUPACIONAL).fillna(False)

    uti = df["UTI_MES_TO"] if "UTI_MES_TO" in df else pd.Series(0, index=df.index)
    morte = df["MORTE"] if "MORTE" in df else pd.Series(0, index=df.index)
    df["uti"] = pd.to_numeric(uti, errors="coerce").fillna(0) > 0
    df["obito"] = pd.to_numeric(morte, errors="coerce").fillna(0) == 1

    return df[no_escopo].copy()


def agregar(df: pd.DataFrame, uf: str, ano: int, mes: int) -> pd.DataFrame:
    """Agrega para municipio de residencia x competencia x grupo de vitima."""
    df = df.assign(uf=uf, ano=ano, mes=mes)
    sexo = df["SEXO"] if "SEXO" in df else pd.Series(pd.NA, index=df.index, dtype="string")
    idade = df["idade_anos"]
    homem = (sexo == "1").fillna(False)
    faixa = idade.between(18, 39).fillna(False)
    df = df.assign(
        _homem=homem,
        _faixa_18_39=faixa,
        # H3 (D-023) precisa do CRUZAMENTO, nao das marginais: `homens` e
        # `faixa_18_39` nao permitem reconstruir quantas AIH sao de homem de
        # 18 a 39. Duas versoes, e a diferenca entre elas e deliberada:
        #   `homem_18_39`          -> perfil principal, ~50% do desfecho
        #   `condutor_homem_18_39` -> secundario, ~5%: `.4` e raro porque `.9`
        #      (nao especificado) domina, e quem codifica `.4` em vez de `.9`
        #      varia por hospital e UF -- pratica de codificacao correlacionada
        #      com urbanizacao, que e o que determina a entrada da plataforma.
        _homem_18_39=homem & faixa,
        _perfil_entrega=df["condutor_transito"] & homem & faixa,
    )

    painel = (
        df.groupby(["uf", "ano", "mes", "MUNIC_RES", "grupo"], dropna=False)
        .agg(
            internacoes=("N_AIH", "count"),
            internacoes_condutor=("condutor_transito", "sum"),
            internacoes_transito=("em_transito", "sum"),
            internacoes_embarque=("embarque_desembarque", "sum"),
            homens=("_homem", "sum"),
            idade_media=("idade_anos", "mean"),
            faixa_18_39=("_faixa_18_39", "sum"),
            homem_18_39=("_homem_18_39", "sum"),
            condutor_homem_18_39=("_perfil_entrega", "sum"),
            dias_perm_total=("DIAS_PERM", "sum"),
            internacoes_uti=("uti", "sum"),
            obitos=("obito", "sum"),
            val_tot=("VAL_TOT", "sum"),
            nexo_ocupacional=("nexo_ocupacional", "sum"),
            car_int_preenchido=("car_int_valido", "sum"),
        )
        .reset_index()
    )
    return painel.rename(columns={"MUNIC_RES": "municipio_res"})
