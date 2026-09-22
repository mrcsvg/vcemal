"""Leitura e agregacao dos beneficios concedidos do INSS. Sem rede.

O arquivo mensal muda de layout quatro vezes na serie, e este modulo e o unico
lugar que sabe disso:

| Periodo           | Formato | Codificacao | CID                        | Especie |
|-------------------|---------|-------------|----------------------------|---------|
| 2019              | CSV `;` | latin-1     | duas colunas `CID;CID`     | nome    |
| 2020 - abr/2021   | CSV `;` | UTF-8 + BOM | `CID;CID_1`                | nome    |
| mai/2021 - mai/2023 | ZIP->CSV `;` | latin-1 | uma coluna `V29.8 Motoc...` | nome  |
| jun/2023 -        | XLSX    | --          | `CID;CID` (codigo, nome)   | codigo e nome |

Alem disso, em 2020-2021 a coluna `UF` **nao corresponde** ao municipio de
residencia (D-030). A UF e lida do campo `Mun Resid`, presente e consistente em
todos os anos, e a coluna `UF` so entra como reserva.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from vcemal import cid as cid_mod
from vcemal import inss as inss_mod

log = logging.getLogger("vcemal.transform.inss")

#: Colunas da saida de `normalizar`, nesta ordem.
COLUNAS = [
    "ano",
    "mes",
    "uf",
    "especie",
    "classe",
    "cid",
    "grupo",
    "forma_filiacao",
    "clientela",
    "qt_sm_rmi",
]

_CODIFICACOES = ("utf-8-sig", "latin-1")


def _desduplicar(colunas: list[object]) -> list[str]:
    """`CID, CID` -> `CID, CID nome`; `Espécie, Espécie` -> `Espécie, Espécie nome`."""
    vistos: dict[str, int] = {}
    saida = []
    for c in colunas:
        nome = str(c).strip()
        vistos[nome] = vistos.get(nome, 0) + 1
        saida.append(nome if vistos[nome] == 1 else f"{nome} nome")
    return saida


def _ler_csv(caminho: Path) -> pd.DataFrame:
    erro: Exception | None = None
    for codificacao in _CODIFICACOES:
        try:
            df = pd.read_csv(caminho, sep=";", dtype=str, encoding=codificacao, engine="python")
        except UnicodeDecodeError as e:  # noqa: PERF203
            erro = e
            continue
        df.columns = _desduplicar(list(df.columns))
        return df
    raise ValueError(f"{caminho.name}: nao decodifica em {_CODIFICACOES}") from erro


def _ler_xlsx(caminho: Path) -> pd.DataFrame:
    """XLSX com linha de titulo antes do cabecalho e nomes de coluna duplicados."""
    bruto = pd.read_excel(caminho, header=None, dtype=str)
    for i in range(min(10, len(bruto))):
        celulas = {inss_mod.texto_simples(v) for v in bruto.iloc[i].tolist()}
        if any(c.startswith("competencia") for c in celulas):
            df = bruto.iloc[i + 1 :].reset_index(drop=True)
            df.columns = _desduplicar(bruto.iloc[i].tolist())
            return df
    raise ValueError(f"{caminho.name}: nao achei a linha de cabecalho (Competência ...)")


#: Sem estas tres, nao ha o que agregar. O resto tem reserva.
ESSENCIAIS = ("Espécie", "CID", "Mun Resid")


def ler(caminho: Path) -> pd.DataFrame:
    """Arquivo mensal, em qualquer dos layouts, como texto bruto com colunas desduplicadas."""
    df = _ler_xlsx(caminho) if caminho.suffix.lower() in (".xlsx", ".xls") else _ler_csv(caminho)
    faltando = [c for c in ESSENCIAIS if _coluna(df, c) is None]
    if faltando:
        raise ValueError(f"{caminho.name}: sem as colunas {faltando} -- layout novo?")
    return df


def _coluna(df: pd.DataFrame, *candidatas: str) -> str | None:
    simples = {inss_mod.texto_simples(c): c for c in df.columns}
    for nome in candidatas:
        if inss_mod.texto_simples(nome) in simples:
            return simples[inss_mod.texto_simples(nome)]
    return None


def _serie(df: pd.DataFrame, nome: str | None) -> pd.Series:
    if nome is None:
        return pd.Series([None] * len(df), index=df.index, dtype=object)
    return df[nome]


def normalizar(df: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
    """Qualquer layout -> `COLUNAS`. `ano` e `mes` vem do indice do portal, nao do arquivo.

    A competencia dentro do arquivo e conferida quando legivel (`202301` ou
    `janeiro/2023`); divergencia e erro, porque significa arquivo trocado.
    """
    col_comp = _coluna(df, "Competência concessão")
    if col_comp is not None:
        _conferir_competencia(df[col_comp], ano, mes)

    especie = _serie(df, _coluna(df, "Espécie")).map(inss_mod.especie_de)
    col_nome = _coluna(df, "Espécie nome")
    if col_nome is not None:
        especie = especie.where(especie.notna(), df[col_nome].map(inss_mod.especie_de))
    sem_especie = df.loc[especie.isna(), _coluna(df, "Espécie")].dropna().unique()
    if len(sem_especie):
        log.warning(
            "%04d-%02d: %d especies sem codigo na tabela: %s",
            ano,
            mes,
            len(sem_especie),
            ", ".join(map(str, sem_especie[:10])),
        )

    cid = _serie(df, _coluna(df, "CID")).map(inss_mod.normalizar_cid)
    for reserva in ("CID nome", "CID_1"):
        col = _coluna(df, reserva)
        if col is not None:
            cid = cid.where(cid.notna(), df[col].map(inss_mod.normalizar_cid))

    uf = _serie(df, _coluna(df, "Mun Resid")).map(inss_mod.uf_de_municipio)
    reserva_uf = _serie(df, _coluna(df, "UF")).map(inss_mod.uf_de_nome)
    uf = uf.where(uf.notna(), reserva_uf)

    rmi = (
        _serie(df, _coluna(df, "Qt SM RMI"))
        .astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    saida = pd.DataFrame(
        {
            "ano": ano,
            "mes": mes,
            "uf": uf,
            "especie": especie.astype("Int64"),
            "classe": especie.map(inss_mod.classe_de),
            "cid": cid,
            "grupo": cid.map(lambda c: cid_mod.grupo_de(c) if c else None),
            "forma_filiacao": _serie(df, _coluna(df, "Forma Filiação")).astype(str).str.strip(),
            "clientela": _serie(df, _coluna(df, "Clientela")).astype(str).str.strip(),
            "qt_sm_rmi": pd.to_numeric(rmi, errors="coerce"),
        }
    )
    return saida[COLUNAS]


def _conferir_competencia(valores: pd.Series, ano: int, mes: int) -> None:
    amostra = str(valores.dropna().iloc[0]).strip() if valores.notna().any() else ""
    lido: tuple[int, int] | None = None
    if amostra.isdigit() and len(amostra) == 6:
        lido = (int(amostra[:4]), int(amostra[4:]))
    elif "/" in amostra:
        nome, _, a = amostra.partition("/")
        from vcemal.extract.senatran import mes_do_arquivo

        m = mes_do_arquivo(nome)
        if m is not None and a.strip().isdigit():
            lido = (int(a), m)
    if lido is not None and lido != (ano, mes):
        raise ValueError(f"arquivo diz competencia {lido}, indice diz {(ano, mes)}")


#: Contagens que `agregar` produz por uf x ano x mes x grupo x classe.
SOMAS = ["beneficios", "sm_rmi_total"]


def agregar(normalizado: pd.DataFrame) -> pd.DataFrame:
    """Beneficios com CID nos grupos do projeto, por UF x mes x grupo x classe.

    So entram linhas com `grupo` (V10-V19, V20-V29, V40-V49) **e** `classe`
    (especie de incapacidade, acidentaria ou previdenciaria). Aposentadoria por
    idade com CID V29 e ruido de preenchimento, nao evento.
    """
    base = normalizado[normalizado["grupo"].notna() & normalizado["classe"].notna()]
    base = base[base["uf"].notna()]
    g = base.groupby(["uf", "ano", "mes", "grupo", "classe"], dropna=False)
    saida = g.agg(beneficios=("cid", "size"), sm_rmi_total=("qt_sm_rmi", "sum")).reset_index()
    saida["ano"] = saida["ano"].astype(int)
    saida["mes"] = saida["mes"].astype(int)
    return saida
