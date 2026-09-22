"""
SIH/SUS pelo espelho da Base dos Dados no BigQuery.

**Segunda fonte, nao substituta.** O caminho oficial do projeto e o `.dbc` do
FTP do DATASUS (`vcemal.extract.sih`). Este modulo existe porque o FTP nao e
alcancavel de todo ambiente, e porque o Anexo A ja previa a Base dos Dados
"para conferencia": duas fontes com a mesma definicao de caso, e a divergencia
entre elas vira diagnostico. Ver D-018.

Precisa de um projeto GCP so para faturar a consulta -- a tabela e publica e
vive no projeto `basedosdados`. O free tier (1 TB/mes) cobre a serie inteira
deste projeto com folga: a tabela e particionada por `ano`, e selecionar coluna
mantem cada ano na casa de 1 GB.

O ESPELHO NAO E O ARQUIVO RD. Cinco divergencias medidas, todas tratadas no
adapter abaixo -- e cada uma delas produziria erro silencioso se ignorada:

1. `carater_internacao` vem como `1`-`6`, nao `01`-`06`. Sem o zero a esquerda,
   `CAR_INT_OCUPACIONAL` nao casa e o nexo ocupacional sai **zero**.
2. `sexo_paciente` vem decodificado (`Masculino`/`Feminino`), nao `1`/`3`. Sem
   traduzir, a contagem de homens sai **zero** numa populacao 85% masculina.
3. O CID vem partido em duas colunas mutuamente exclusivas: codigo de tres
   caracteres em `_categoria`, de quatro em `_subcategoria`. Ler so uma perde
   metade dos codigos -- e o quarto digito mora justamente na outra.
4. `sigla_uf` e INTEGER e esta **inteiramente nula**, apesar de ser coluna de
   clustering. Nao da para filtrar por UF ali; o recorte sai do prefixo do
   codigo de municipio.
5. `carater_internacao` aparece 100% preenchido, sem um unico nulo. No RD cru
   ha branco. **A taxa de preenchimento desta fonte nao e confiavel** -- o
   numerador do nexo e piso, o denominador nao. Ver D-018.
"""

from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger("vcemal.extract.bigquery")

TABELA = "basedosdados.br_ms_sih.aihs_reduzidas"

#: Coluna do espelho -> coluna do arquivo RD que o `transform` espera.
#: Onde o valor e uma tupla, o CID vem partido e precisa de COALESCE.
MAPA_COLUNAS: dict[str, str] = {
    "id_aih": "N_AIH",
    "id_municipio_paciente": "MUNIC_RES",
    "id_municipio_estabelecimento": "MUNIC_MOV",
    "idade_paciente": "IDADE",
    "unidade_medida_idade_paciente": "COD_IDADE",
    "data_internacao": "DT_INTER",
    "data_saida": "DT_SAIDA",
    "quantidade_dias_permanencia": "DIAS_PERM",
    "quantidade_dias_uti_mes": "UTI_MES_TO",
    "indicador_obito": "MORTE",
    "valor_aih": "VAL_TOT",
    "valor_serivico_hospitalar": "VAL_SH",  # o typo e da fonte
    "valor_servico_profissional": "VAL_SP",
    "id_estabelecimento_cnes": "CNES",
    "especialidade_leito": "ESPEC",
    "procedimento_realizado": "PROC_REA",
    "raca_cor_paciente": "RACA_COR",
}

#: Campos de CID partidos em categoria/subcategoria -> nome no RD.
MAPA_CID: dict[str, str] = {
    "cid_principal": "DIAG_PRINC",
    "cid_secundario": "DIAG_SECUN",
    **{f"cid_diagnostico_secundario_{i}": f"DIAGSEC{i}" for i in range(1, 10)},
}

#: `sexo_paciente` decodificado -> dominio do RD (1 = masculino, 3 = feminino).
MAPA_SEXO: dict[str, str] = {"Masculino": "1", "Feminino": "3"}

#: Faixas do capitulo XX que interessam, para filtrar na origem e nao trazer
#: 13 milhoes de AIH por ano. Espelha `vcemal.cid.GRUPOS_CID`.
FAIXAS_CID: tuple[tuple[str, str], ...] = (("V10", "V19"), ("V20", "V29"), ("V40", "V49"))


def _coalesce_cid(prefixo: str, alias: str) -> str:
    return f"COALESCE({prefixo}_subcategoria, {prefixo}_categoria) AS {alias}"


def montar_consulta(ano: int, meses: list[int] | None = None) -> str:
    """SQL que devolve as AIH da definicao de caso, ja com nomes do RD.

    Filtra na origem: sem isso viriam ~13 milhoes de AIH por ano, das quais
    ~150 mil interessam.
    """
    cids = ",\n    ".join(_coalesce_cid(p, a) for p, a in MAPA_CID.items())
    outras = ",\n    ".join(f"{o} AS {d}" for o, d in MAPA_COLUNAS.items())
    faixas = " OR ".join(
        f"SUBSTR(c.{alias}, 1, 3) BETWEEN '{ini}' AND '{fim}'"
        for alias in MAPA_CID.values()
        for ini, fim in FAIXAS_CID
    )
    filtro_mes = f" AND mes IN ({','.join(str(m) for m in meses)})" if meses else ""
    return f"""
WITH c AS (
  SELECT
    ano, mes,
    {cids},
    carater_internacao AS CAR_INT,
    sexo_paciente AS SEXO,
    {outras}
  FROM `{TABELA}`
  WHERE ano = {ano}{filtro_mes}
)
SELECT * FROM c WHERE {faixas}
"""


def adaptar(df: pd.DataFrame) -> pd.DataFrame:
    """Traduz o espelho para o dominio do arquivo RD.

    Cada linha aqui corresponde a uma divergencia medida entre as duas fontes;
    ver a docstring do modulo. Sem este passo o pipeline roda sem erro e produz
    zeros -- que e o pior modo de falhar.
    """
    df = df.copy()
    df.columns = [c.upper() if c.upper() in _ESPERADAS else c for c in df.columns]

    if "CAR_INT" in df:
        # `2` -> `02`: o dominio do RD tem dois digitos.
        df["CAR_INT"] = df["CAR_INT"].astype("string").str.strip().str.zfill(2)
    if "SEXO" in df:
        df["SEXO"] = df["SEXO"].astype("string").str.strip().map(MAPA_SEXO).astype("string")
    for coluna in ("DT_INTER", "DT_SAIDA"):
        if coluna in df:
            # O transform espera AAAAMMDD; aqui ja vem DATE.
            df[coluna] = pd.to_datetime(df[coluna], errors="coerce").dt.strftime("%Y%m%d")
    return df


_ESPERADAS = {*MAPA_COLUNAS.values(), *MAPA_CID.values(), "CAR_INT", "SEXO"}


def consultar(ano: int, meses: list[int] | None = None, cliente=None) -> pd.DataFrame:
    """Baixa um ano (ou meses dele) ja no dominio do RD.

    `cliente` e um `google.cloud.bigquery.Client`; quando omitido, e construido
    a partir de `GOOGLE_APPLICATION_CREDENTIALS`. Import adiado para que o
    pacote funcione sem a dependencia instalada.
    """
    if cliente is None:
        from google.cloud import bigquery

        cliente = bigquery.Client()

    sql = montar_consulta(ano, meses)
    job = cliente.query(sql)
    df = job.result().to_dataframe()
    log.info(
        "%s: %d AIH na definicao de caso (%.2f GB processados)",
        ano,
        len(df),
        (job.total_bytes_processed or 0) / 1e9,
    )
    return adaptar(df)


def custo_estimado(ano: int, meses: list[int] | None = None, cliente=None) -> float:
    """GB que a consulta processaria, sem executar. Use antes de varrer a serie."""
    from google.cloud import bigquery

    cliente = cliente or bigquery.Client()
    cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    job = cliente.query(montar_consulta(ano, meses), job_config=cfg)
    return (job.total_bytes_processed or 0) / 1e9
