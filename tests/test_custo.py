"""Custo pago e custo social a precos constantes. Tudo offline."""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal import custo as custo_mod
from vcemal.analyze import custo
from vcemal.extract import ibge


def test_transcricao_bate_com_o_total_impresso_no_ipea():
    """Se um componente foi digitado errado, a soma nao fecha com a tabela."""
    assert custo_mod.TD2565.ferido_grave.total == pytest.approx(
        custo_mod.TOTAL_IMPRESSO_FERIDO_GRAVE, abs=0.01
    )


def test_perda_de_producao_e_a_maior_componente_do_morto():
    m = custo_mod.TD2565.morto
    assert m.perda_producao / m.total > 0.99


def test_custo_social_nao_conta_o_morto_duas_vezes():
    p = custo_mod.TD2565
    c = custo_mod.custo_social(internacoes=10, obitos=1, p=p)
    assert c["total"] == pytest.approx(9 * p.ferido_grave.total + 1 * p.morto.total)


def test_obitos_maior_que_internacoes_falha_alto():
    with pytest.raises(ValueError, match="obitos"):
        custo_mod.custo_social(internacoes=1, obitos=2)


# --- IPCA ------------------------------------------------------------------


@pytest.fixture
def ipca():
    """Indice que dobra entre dez/2014 e dez/2023 e sobe 10% ate dez/2024."""
    linhas = [
        {"periodo": "201412", "indice": 100.0},
        {"periodo": "202301", "indice": 190.0},
        {"periodo": "202312", "indice": 200.0},
        {"periodo": "202412", "indice": 220.0},
    ]
    return custo.indice_ipca(linhas)


def test_linhas_ipca_pula_o_cabecalho_do_sidra():
    bruto = [
        {"V": "Valor", "D3C": "Mês (Código)"},
        {"V": "6508.4000000000000", "D3C": "202301"},
        {"V": "...", "D3C": "202302"},
    ]
    assert ibge.linhas_ipca(bruto) == [{"periodo": "202301", "indice": 6508.4}]


def test_fator_leva_a_reais_da_base(ipca):
    f = custo.fator(ipca, "2023-12")
    assert f[pd.Period("2023-01", freq="M")] == pytest.approx(200 / 190)
    assert f[pd.Period("2023-12", freq="M")] == pytest.approx(1.0)


def test_base_fora_da_serie_falha_alto(ipca):
    with pytest.raises(KeyError, match="base"):
        custo.fator(ipca, "2030-01")


@pytest.fixture
def painel():
    return pd.DataFrame(
        {
            "uf": ["PR", "PR", "PR"],
            "ano": [2023, 2023, 2023],
            "mes": [1, 12, 12],
            "municipio_res": ["410690", "410690", "410690"],
            "grupo": ["motociclista", "motociclista", "ciclista"],
            "internacoes": [10, 10, 5],
            "obitos": [1, 0, 0],
            "dias_perm_total": [50, 40, 10],
            "val_tot": [1900.0, 2000.0, 500.0],
        }
    )


def test_deflaciona_linha_a_linha_pela_competencia(painel, ipca):
    real = custo.deflacionar(painel, ipca, "2023-12")
    assert real["val_tot_real"].iloc[0] == pytest.approx(2000.0), "jan/2023 -> dez/2023"
    assert real["val_tot_real"].iloc[1] == pytest.approx(2000.0), "ja esta na base"


def test_competencia_sem_ipca_e_erro_nao_nan(painel, ipca):
    fora = painel.assign(ano=2027)
    with pytest.raises(KeyError, match="2027-01"):
        custo.deflacionar(fora, ipca, "2023-12")


def test_por_ano_poe_pago_e_social_na_mesma_base(painel, ipca):
    t = custo.por_ano(painel, ipca, "2024-12")
    moto = t.loc[(2023, "motociclista")]
    assert moto["internacoes"] == 20
    assert moto["obitos"] == 1
    assert moto["val_tot_nominal"] == pytest.approx(3900.0)
    # jan: 1900 * 220/190 = 2200; dez: 2000 * 220/200 = 2200
    assert moto["val_tot_real"] == pytest.approx(4400.0)
    assert moto["val_por_internacao_real"] == pytest.approx(220.0)
    p = custo_mod.TD2565
    esperado = 2.2 * (19 * p.ferido_grave.total + 1 * p.morto.total)  # dez/2014 -> dez/2024
    assert moto["custo_social_real"] == pytest.approx(esperado)
    assert moto["base_precos"] == "2024-12"


def test_custo_social_e_muito_maior_que_o_pago(painel, ipca):
    """O ponto do P3: o que o SUS paga e uma fracao do que a sociedade perde."""
    t = custo.por_ano(painel, ipca, "2023-12")
    moto = t.loc[(2023, "motociclista")]
    assert moto["custo_social_real"] > 10 * moto["val_tot_real"]
    assert moto["perda_producao_real"] < moto["custo_social_real"]


def test_recorte_por_uf_ano_so_motociclista(painel, ipca):
    t = custo.por_uf_ano(painel, ipca, "2023-12")
    assert list(t.index.names) == ["uf", "ano"]
    assert t["internacoes"].sum() == 20


def test_painel_sem_val_tot_falha_alto(painel, ipca):
    with pytest.raises(KeyError, match="val_tot"):
        custo.deflacionar(painel.drop(columns="val_tot"), ipca, "2023-12")
