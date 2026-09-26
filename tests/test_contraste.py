"""iFood e SUS lado a lado: mesma moeda, emenda de metrica visivel, sem atribuicao."""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal.analyze import contraste


@pytest.fixture
def lucro():
    return pd.DataFrame(
        {
            "ano": [2021, 2022, 2023, 2024],
            "receita_brl_real_milhoes": [6000.0, 7000.0, 7500.0, 8000.0],
            "trading_profit_brl_real_milhoes": [-900.0, -500.0, 300.0, None],
            "aebit_brl_real_milhoes": [None, None, 250.0, 1100.0],
            "base_precos": "2025-12",
        }
    )


@pytest.fixture
def custo():
    linhas = []
    for ano, pago in [(2020, 240e6), (2021, 250e6), (2022, 240e6), (2023, 255e6), (2024, 285e6)]:
        linhas.append(dict(ano=ano, grupo="motociclista", val_tot_real=pago,
                           custo_social_real=30e9, base_precos="2025-12"))  # fmt: skip
        linhas.append(dict(ano=ano, grupo="ciclista", val_tot_real=1e6,
                           custo_social_real=1e9, base_precos="2025-12"))  # fmt: skip
    return pd.DataFrame(linhas)


def test_sus_vem_em_milhoes_e_so_do_grupo_pedido(lucro, custo):
    t = contraste.lado_a_lado(lucro, custo)
    assert t.loc[2024, "sus_pagou"] == pytest.approx(285.0)
    assert t.loc[2024, "custo_social"] == pytest.approx(30_000.0)


def test_resultado_usa_aebit_onde_existe_e_diz_qual_metrica(lucro, custo):
    t = contraste.lado_a_lado(lucro, custo)
    assert t.loc[2022, "resultado_ifood"] == -500.0
    assert t.loc[2023, "resultado_ifood"] == 250.0, "aEBIT tem precedencia no ano da emenda"
    assert pd.isna(t.loc[2020, "metrica_resultado"])
    assert t.loc[2021:, "metrica_resultado"].tolist() == [
        "trading_profit",
        "trading_profit",
        "aebit",
        "aebit",
    ]


def test_ano_so_de_um_lado_aparece_com_o_outro_vazio(lucro, custo):
    t = contraste.lado_a_lado(lucro, custo)
    assert list(t.index) == [2020, 2021, 2022, 2023, 2024]
    assert pd.isna(t.loc[2020, "resultado_ifood"])
    assert t.loc[2020, "sus_pagou"] == pytest.approx(240.0)


def test_bases_de_preco_diferentes_sao_erro(lucro, custo):
    custo["base_precos"] = "2024-12"
    with pytest.raises(ValueError, match="bases de preco"):
        contraste.lado_a_lado(lucro, custo)
