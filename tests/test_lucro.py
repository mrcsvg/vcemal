"""Serie de receita e resultado do iFood (Prosus). Tudo offline."""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal import lucro as lucro_mod
from vcemal.analyze import custo, lucro
from vcemal.extract import bcb
from vcemal.paths import FONTE_IFOOD_PROSUS

# --- calendario -------------------------------------------------------------


def test_ano_fiscal_vai_de_abril_a_marco():
    meses = lucro_mod.meses_do_ano_fiscal(2025)
    assert meses[0] == "2024-04"
    assert meses[-1] == "2025-03"
    assert len(meses) == 12


def test_ano_civil_pesa_um_quarto_do_fy_e_tres_quartos_do_seguinte():
    civil = lucro_mod.para_ano_civil({2024: 100.0, 2025: 200.0, 2026: 400.0})
    assert civil == {2024: pytest.approx(175.0), 2025: pytest.approx(350.0)}


def test_ano_civil_nao_extrapola_nas_pontas():
    assert lucro_mod.para_ano_civil({2024: 1.0}) == {}
    assert 2026 not in lucro_mod.para_ano_civil({2025: 1.0, 2026: 1.0})


# --- CSV curado --------------------------------------------------------------


def _linha(**kw):
    base = {
        "ano_fiscal": 2025,
        "metrica": "receita",
        "valor": 1334,
        "unidade": "USD_milhoes",
        "documento": "FY2026 KPI datasheet",
        "url": "https://example.org/x.xlsx",
        "acesso": "2026-09-20",
        "nota": "",
    }
    base.update(kw)
    return base


def test_validar_aceita_linha_completa():
    lucro_mod.validar([_linha()])


@pytest.mark.parametrize(
    "linha, erro",
    [
        (_linha(metrica="lucro_liquido"), "desconhecida"),
        (_linha(unidade="BRL_milhoes"), "esperado"),
        (_linha(url=""), "sem url"),
        (_linha(documento=float("nan")), "sem documento"),
    ],
)
def test_validar_recusa_transcricao_incompleta(linha, erro):
    with pytest.raises(ValueError, match=erro):
        lucro_mod.validar([linha])


def test_validar_recusa_metrica_repetida_no_mesmo_ano():
    with pytest.raises(ValueError, match="repetida"):
        lucro_mod.validar([_linha(), _linha(valor=1)])


def test_o_csv_versionado_passa_na_validacao():
    linhas = pd.read_csv(FONTE_IFOOD_PROSUS, dtype={"nota": str}).to_dict("records")
    lucro_mod.validar(linhas)
    fiscal = lucro.serie_fiscal(linhas)
    assert list(fiscal.index) == list(range(2019, 2027))
    # a emenda entre trading profit e EBIT ajustado tem dois anos de sobreposicao
    assert fiscal.loc[2023, "trading_profit"] == -65 and fiscal.loc[2023, "aebit"] == -83
    assert fiscal.loc[2024, "trading_profit"] == fiscal.loc[2024, "aebit"] == 96
    assert fiscal["receita"].is_monotonic_increasing is False  # FY24 cai: nova regra de receita
    assert fiscal["receita_comparavel"].dropna().is_monotonic_increasing


# --- BCB ---------------------------------------------------------------------


def test_linhas_cambio_le_a_data_do_sgs():
    bruto = [{"data": "01/04/2018", "valor": "3.4075"}, {"data": "01/05/2018", "valor": "-"}]
    assert bcb.linhas_cambio(bruto) == [{"periodo": "2018-04", "cambio": 3.4075}]


# --- conversao ---------------------------------------------------------------


@pytest.fixture
def cambio():
    """R$ 4 por dolar em todo FY2025, R$ 5 em todo FY2026."""
    linhas = [{"periodo": m, "cambio": 4.0} for m in lucro_mod.meses_do_ano_fiscal(2025)]
    linhas += [{"periodo": m, "cambio": 5.0} for m in lucro_mod.meses_do_ano_fiscal(2026)]
    return lucro.indice_cambio(linhas)


@pytest.fixture
def ipca():
    """Indice 100 em todo FY2025, 110 em todo FY2026 e 120 em dezembro/2025 (base)."""
    linhas = [
        {"periodo": m.replace("-", ""), "indice": 100.0}
        for m in lucro_mod.meses_do_ano_fiscal(2025)
    ]
    linhas += [
        {"periodo": m.replace("-", ""), "indice": 120.0 if m == "2025-12" else 110.0}
        for m in lucro_mod.meses_do_ano_fiscal(2026)
    ]
    return custo.indice_ipca(linhas)


@pytest.fixture
def linhas():
    return [
        _linha(ano_fiscal=2025, metrica="receita", valor=1000),
        _linha(ano_fiscal=2025, metrica="aebit", valor=100),
        _linha(ano_fiscal=2025, metrica="pedidos", valor=500, unidade="milhoes"),
        _linha(ano_fiscal=2025, metrica="entregadores_brasil", valor=400_000, unidade="pessoas"),
        _linha(ano_fiscal=2026, metrica="receita", valor=2000),
        _linha(ano_fiscal=2026, metrica="aebit", valor=300),
        _linha(ano_fiscal=2026, metrica="pedidos", valor=1000, unidade="milhoes"),
        _linha(ano_fiscal=2026, metrica="entregadores_brasil", valor=600_000, unidade="pessoas"),
    ]


def test_receita_passa_pelo_cambio_medio_e_pelo_ipca_medio_do_ano_fiscal(linhas, cambio, ipca):
    t = lucro.por_ano_fiscal(linhas, cambio, ipca, base="2025-12")
    assert t.loc[2025, "cambio_medio"] == pytest.approx(4.0)
    assert t.loc[2025, "receita_brl_nominal_milhoes"] == pytest.approx(4000.0)
    # base 120 sobre media 100 -> x1,2
    assert t.loc[2025, "receita_brl_real_milhoes"] == pytest.approx(4800.0)
    # FY2026: media do indice = (11 x 110 + 120) / 12
    media_26 = (11 * 110 + 120) / 12
    assert t.loc[2026, "receita_brl_real_milhoes"] == pytest.approx(2000 * 5.0 * 120 / media_26)
    assert t.loc[2025, "receita_por_pedido_brl_real"] == pytest.approx(4800.0 / 500)
    assert t.loc[2025, "entregadores_brasil"] == 400_000
    assert (t["base_precos"] == "2025-12").all()
    assert list(t.columns) == lucro.COLUNAS_FISCAL


def test_ano_fiscal_sem_cambio_ou_ipca_e_erro_nao_nan(linhas, cambio, ipca):
    with pytest.raises(KeyError, match="FY2026"):
        lucro.por_ano_fiscal(
            linhas, cambio[cambio.index < pd.Period("2026-01", freq="M")], ipca, "2025-12"
        )
    with pytest.raises(KeyError, match="base"):
        lucro.por_ano_fiscal(linhas, cambio, ipca, "2027-01")


def test_ano_civil_interpola_fluxos_e_deixa_estoques_de_fora(linhas, cambio, ipca):
    fiscal = lucro.por_ano_fiscal(linhas, cambio, ipca, base="2025-12")
    civil = lucro.por_ano_civil(fiscal)
    assert list(civil.index) == [2025]
    esperado = (
        0.25 * fiscal.loc[2025, "receita_brl_real_milhoes"]
        + 0.75 * fiscal.loc[2026, "receita_brl_real_milhoes"]
    )
    assert civil.loc[2025, "receita_brl_real_milhoes"] == pytest.approx(esperado)
    assert civil.loc[2025, "pedidos_milhoes"] == pytest.approx(0.25 * 500 + 0.75 * 1000)
    assert "entregadores_brasil" not in civil.columns
    assert civil.loc[2025, "metodo"] == lucro.METODO_CIVIL
    assert civil.loc[2025, "base_precos"] == "2025-12"


def test_metrica_ausente_no_csv_vira_coluna_vazia_e_nao_erro(cambio, ipca):
    so_receita = [_linha(ano_fiscal=2025), _linha(ano_fiscal=2026, valor=2000)]
    t = lucro.por_ano_fiscal(so_receita, cambio, ipca, "2025-12")
    assert t["aebit_brl_real_milhoes"].isna().all()
    assert lucro.por_ano_civil(t)["aebit_brl_real_milhoes"].isna().all()
