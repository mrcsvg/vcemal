"""Preenchimento do CAR_INT: o denominador e o achado (D-008, H4)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from vcemal.analyze import car_int
from vcemal.transform.sih import agregar, classificar, normalizar


@pytest.fixture
def painel(amostra_car_int) -> pd.DataFrame:
    return agregar(classificar(normalizar(amostra_car_int)), "PR", 2023, 1)


def test_branco_e_sentinela_nao_contam_como_preenchido(painel):
    assert painel["internacoes"].sum() == 6
    assert painel["car_int_preenchido"].sum() == 3, "'' , '99' e '00' nao sao codigo"
    assert painel["nexo_ocupacional"].sum() == 2


def test_taxa_de_nexo_usa_preenchimento_como_denominador(painel):
    tabela = car_int.por_ano(painel)
    linha = tabela.loc[(2023, "motociclista")]
    assert linha["pct_nexo"] == pytest.approx(200 / 3), "2 de 3 validos, nao 2 de 6"
    assert linha["pct_preenchido"] == pytest.approx(50.0)


def test_denominador_ingenuo_subestimaria_a_subnotificacao(painel):
    """Sobre internacoes daria 33%, sobre preenchimento da 67%. A diferenca e o ponto."""
    tabela = car_int.por_ano(painel)
    ingenuo = 100 * painel["nexo_ocupacional"].sum() / painel["internacoes"].sum()
    assert tabela.loc[(2023, "motociclista"), "pct_nexo"] > ingenuo


def test_denominador_zero_vira_nan_e_nao_infinito():
    painel = pd.DataFrame(
        {
            "ano": [2023],
            "grupo": ["motociclista"],
            "uf": ["PR"],
            "municipio_res": ["410690"],
            "internacoes": [10],
            "car_int_preenchido": [0],
            "nexo_ocupacional": [0],
        }
    )
    tabela = car_int.por_ano(painel)
    assert np.isnan(tabela.loc[(2023, "motociclista"), "pct_nexo"])
    assert tabela.loc[(2023, "motociclista"), "pct_preenchido"] == 0.0


def test_recorte_por_uf_ano_so_tem_motociclista(amostra):
    painel = agregar(classificar(normalizar(amostra)), "PR", 2023, 1)
    tabela = car_int.por_uf_ano(painel)
    assert list(tabela.index.names) == ["uf", "ano"]
    assert tabela["internacoes"].sum() == 2


def test_recorte_por_municipio_respeita_o_piso(painel):
    assert car_int.por_municipio(painel, minimo=1)["internacoes"].sum() == 6
    assert car_int.por_municipio(painel, minimo=100).empty


def test_painel_sem_as_colunas_falha_alto():
    with pytest.raises(KeyError):
        car_int.por_ano(pd.DataFrame({"ano": [2023], "grupo": ["motociclista"]}))
