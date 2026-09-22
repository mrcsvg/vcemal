"""Adapter do espelho da Base dos Dados. Tudo offline -- nao toca a rede.

Cada teste aqui corresponde a uma divergencia medida entre o espelho e o
arquivo RD. Todas produziriam zero em silencio se nao fossem tratadas.
"""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal import cid
from vcemal.extract import bigquery as bq


def test_car_int_ganha_zero_a_esquerda():
    """`3` -> `03`: sem isso o nexo ocupacional sai zero."""
    df = bq.adaptar(pd.DataFrame({"CAR_INT": ["1", "2", "3", "4", "5", "6"]}))
    assert list(df["CAR_INT"]) == ["01", "02", "03", "04", "05", "06"]
    assert df["CAR_INT"].isin(cid.CAR_INT_OCUPACIONAL).sum() == 2


def test_car_int_adaptado_casa_com_o_dominio_do_rd():
    df = bq.adaptar(pd.DataFrame({"CAR_INT": ["3", "4", "2"]}))
    assert [cid.car_int_preenchido(v) for v in df["CAR_INT"]] == [True, True, True]


def test_sexo_decodificado_volta_ao_dominio():
    """`Masculino` -> `1`: sem isso a contagem de homens sai zero."""
    df = bq.adaptar(pd.DataFrame({"SEXO": ["Masculino", "Feminino", "Masculino"]}))
    assert list(df["SEXO"]) == ["1", "3", "1"]
    assert (df["SEXO"] == "1").sum() == 2


def test_sexo_desconhecido_vira_na_e_nao_chute():
    df = bq.adaptar(pd.DataFrame({"SEXO": ["Ignorado", None]}))
    assert df["SEXO"].isna().all()


def test_data_volta_para_aaaammdd():
    df = bq.adaptar(pd.DataFrame({"DT_INTER": pd.to_datetime(["2023-06-05", "2023-12-31"])}))
    assert list(df["DT_INTER"]) == ["20230605", "20231231"]


def test_consulta_faz_coalesce_do_cid_partido():
    """O codigo de 3 caracteres vive em _categoria, o de 4 em _subcategoria."""
    sql = bq.montar_consulta(2023)
    assert "COALESCE(cid_principal_subcategoria, cid_principal_categoria) AS DIAG_PRINC" in sql
    assert (
        "COALESCE(cid_diagnostico_secundario_1_subcategoria, "
        "cid_diagnostico_secundario_1_categoria) AS DIAGSEC1" in sql
    )


def test_consulta_traz_todos_os_diagsec():
    sql = bq.montar_consulta(2023)
    for i in range(1, 10):
        assert f"AS DIAGSEC{i}" in sql


def test_consulta_filtra_na_origem():
    """Sem filtro viriam ~13 milhoes de AIH por ano, das quais ~150 mil interessam."""
    sql = bq.montar_consulta(2023)
    assert "BETWEEN 'V20' AND 'V29'" in sql
    assert "BETWEEN 'V10' AND 'V19'" in sql
    assert "BETWEEN 'V40' AND 'V49'" in sql


def test_consulta_nao_filtra_por_sigla_uf():
    """`sigla_uf` e INTEGER e esta inteiramente nula -- filtrar ali zera tudo."""
    assert "sigla_uf" not in bq.montar_consulta(2023)


def test_filtro_de_mes_entra_quando_pedido():
    assert "mes IN (6)" in bq.montar_consulta(2023, meses=[6])
    assert "mes IN (1,2,3)" in bq.montar_consulta(2023, meses=[1, 2, 3])
    assert "mes IN" not in bq.montar_consulta(2023)


def test_faixas_espelham_os_grupos_do_cid():
    """Se um grupo entrar em vcemal.cid e nao aqui, a consulta deixa de traze-lo."""
    inicios = {ini for ini, _ in bq.FAIXAS_CID}
    for categorias in cid.GRUPOS_CID.values():
        assert categorias[0] in inicios


@pytest.mark.parametrize("coluna", ["N_AIH", "MUNIC_RES", "DIAG_PRINC", "DIAGSEC1", "CAR_INT"])
def test_mapa_cobre_as_colunas_que_o_transform_exige(coluna):
    from vcemal.transform.sih import COLS

    destinos = {*bq.MAPA_COLUNAS.values(), *bq.MAPA_CID.values(), "CAR_INT", "SEXO"}
    assert coluna in destinos
    assert coluna in COLS


def test_adaptar_nao_quebra_sem_as_colunas():
    df = bq.adaptar(pd.DataFrame({"VAL_TOT": [1.0]}))
    assert list(df.columns) == ["VAL_TOT"]
