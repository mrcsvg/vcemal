"""SIH e INSS lado a lado: a razao mede invisibilidade, e a cobertura fica explicita."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from vcemal.analyze import lacuna


@pytest.fixture
def painel():
    linhas = []
    for mes in range(1, 13):
        linhas.append(
            dict(uf="SP", ano=2023, mes=mes, municipio_res="355030", grupo="motociclista",
                 internacoes=1000, internacoes_transito=900, nexo_ocupacional=1, obitos=20)
        )  # fmt: skip
        linhas.append(
            dict(uf="SP", ano=2023, mes=mes, municipio_res="355030", grupo="auto_placebo",
                 internacoes=300, internacoes_transito=250, nexo_ocupacional=0, obitos=5)
        )  # fmt: skip
    for mes in range(1, 7):  # RS: so meio ano de SIH
        linhas.append(
            dict(uf="RS", ano=2023, mes=mes, municipio_res="431490", grupo="motociclista",
                 internacoes=100, internacoes_transito=90, nexo_ocupacional=0, obitos=2)
        )  # fmt: skip
    return pd.DataFrame(linhas)


@pytest.fixture
def inss():
    linhas = []
    for mes in range(1, 13):
        linhas.append(dict(uf="SP", ano=2023, mes=mes, grupo="motociclista",
                           classe="previdenciario", beneficios=5, sm_rmi_total=6.0))  # fmt: skip
        linhas.append(dict(uf="SP", ano=2023, mes=mes, grupo="motociclista",
                           classe="acidentario", beneficios=1, sm_rmi_total=1.5))  # fmt: skip
        linhas.append(dict(uf="SP", ano=2023, mes=mes, grupo="ciclista",
                           classe="previdenciario", beneficios=2, sm_rmi_total=2.0))  # fmt: skip
        # RS: os 12 meses observados, mas so 3 com beneficio de motociclista
        if mes <= 3:
            linhas.append(dict(uf="RS", ano=2023, mes=mes, grupo="motociclista",
                               classe="previdenciario", beneficios=2, sm_rmi_total=2))  # fmt: skip
        else:
            linhas.append(dict(uf="RS", ano=2023, mes=mes, grupo="ciclista",
                               classe="previdenciario", beneficios=1, sm_rmi_total=1))  # fmt: skip
    return pd.DataFrame(linhas)


def test_por_uf_ano_poe_as_duas_fontes_lado_a_lado(painel, inss):
    t = lacuna.por_uf_ano(painel, inss)
    sp = t.loc[("SP", 2023)]
    assert sp["internacoes"] == 12_000
    assert sp["sih_nexo_ocupacional"] == 12
    assert sp["beneficios"] == 72 and sp["acidentarios"] == 12 and sp["previdenciarios"] == 60
    assert sp["beneficios_por_mil_internacoes"] == pytest.approx(6.0)
    assert sp["acidentarios_por_mil_internacoes"] == pytest.approx(1.0)
    assert sp["sih_nexo_por_mil_internacoes"] == pytest.approx(1.0)
    assert sp["pct_acidentario"] == pytest.approx(100 * 12 / 72)


def test_cobertura_em_meses_fica_explicita(painel, inss):
    t = lacuna.por_uf_ano(painel, inss)
    assert t.loc[("SP", 2023), "meses_sih"] == 12
    assert t.loc[("SP", 2023), "meses_inss"] == 12
    assert t.loc[("RS", 2023), "meses_sih"] == 6
    assert t.loc[("RS", 2023), "meses_inss"] == 12, "mes sem beneficio de moto ainda e observado"


def test_placebo_e_outro_grupo(painel, inss):
    t = lacuna.por_uf_ano(painel, inss, grupo="auto_placebo")
    sp = t.loc[("SP", 2023)]
    assert sp["internacoes"] == 3600
    assert sp["beneficios"] == 0
    assert np.isnan(sp["pct_acidentario"])


def test_por_ano_soma_as_ufs(painel, inss):
    t = lacuna.por_ano(painel, inss)
    assert t.loc[2023, "internacoes"] == 12_600
    assert t.loc[2023, "beneficios"] == 78


def test_uf_so_de_um_lado_aparece_com_zero_do_outro(painel, inss):
    so_inss = inss[inss["uf"] == "SP"].assign(uf="BA")
    t = lacuna.por_uf_ano(painel, pd.concat([inss, so_inss]))
    ba = t.loc[("BA", 2023)]
    assert ba["internacoes"] == 0 and ba["meses_sih"] == 0
    assert ba["beneficios"] == 72
    assert np.isnan(ba["beneficios_por_mil_internacoes"])


def test_sem_ano_nas_chaves_falha_alto(painel, inss):
    with pytest.raises(ValueError, match="ano"):
        lacuna.por(painel, inss, "uf")


def test_painel_sem_colunas_falha_alto(painel, inss):
    with pytest.raises(KeyError, match="obitos"):
        lacuna.por_ano(painel.drop(columns="obitos"), inss)
