"""Painel de estimacao do V2. Tudo offline, sobre dados de brinquedo."""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal.paths import FONTES
from vcemal.transform import estimacao as est

TRAT = pd.DataFrame(
    {
        "municipio_ibge": [4100103, 4100202, 4100301],
        "uf": ["PR", "PR", "PR"],
        "municipio": ["A", "B", "C"],
        "populacao_2022": [30_000, 60_000, 200_000],
        "faixa": ["20-50 mil", "50-100 mil", "100-250 mil"],
        "mes_quebra": ["2019-03", None, None],
        "aberturas_base_mes": [0.1, 0.0, 2.0],
        "placebo_2016": [False, False, True],
        "grupo": ["datado", "sem_quebra", "coorte_precoce"],
        "mes_tratamento": ["2019-03", None, None],
    }
)
REGIOES = pd.DataFrame(
    {"municipio_ibge": [4100103, 4100202, 4100301], "regiao_imediata": [410001, 410001, 410002]}
)


def _tratamento():
    t = TRAT.copy()
    t["municipio_res"] = t["municipio_ibge"].astype(str).str[:6]
    t["g"] = [est.periodo_de(m) if isinstance(m, str) else 0 for m in t["mes_tratamento"]]
    return t


def _linha(mun, ano, mes, grupo, uf="PR", transito=1, internacoes=1, h=0):
    return {
        "uf": uf,
        "ano": ano,
        "mes": mes,
        "municipio_res": mun,
        "grupo": grupo,
        "internacoes": internacoes,
        "internacoes_transito": transito,
        "homem_18_39": h,
        "condutor_homem_18_39": 0,
    }


def test_periodo_comeca_em_2015_01():
    assert est.periodo_de("2015-01") == 1
    assert est.periodo_de("2016-07") == 19
    assert est.periodo_de("2025-12") == 132


def test_hash_do_tratamento_congelado_confere():
    est.conferir_hash(FONTES / "cronologia" / "tratamento_mei_municipio.csv")


def test_hash_errado_para_tudo(tmp_path):
    f = tmp_path / "t.csv"
    f.write_text("municipio_ibge\n1\n")
    with pytest.raises(ValueError, match="pre-registro"):
        est.conferir_hash(f)


def test_tratamento_congelado_tem_os_grupos_do_plano():
    t = est.ler_tratamento(FONTES / "cronologia" / "tratamento_mei_municipio.csv")
    assert t["grupo"].value_counts().to_dict() == {
        "sem_quebra": 751,
        "datado": 640,
        "coorte_precoce": 319,
    }
    assert (t.loc[t["grupo"] != "datado", "g"] == 0).all()
    janela = t["g"].between(est.periodo_de("2017-07"), est.periodo_de("2023-12"))
    assert janela.sum() == 478  # plano, secao 5


def test_soma_por_cima_da_uf_do_arquivo():
    """Residente internado em outra UF vem em outra linha; nao pode virar duplicata."""
    painel = pd.DataFrame(
        [
            _linha("410010", 2019, 3, "motociclista", uf="PR", transito=2),
            _linha("410010", 2019, 3, "motociclista", uf="SC", transito=1),
        ]
    )
    y = est.desfechos_sih(painel)
    assert len(y) == 1
    assert y["moto_internacoes_transito"].item() == 3


def test_montar_preenche_zero_e_balanceia():
    painel = pd.DataFrame(
        [
            _linha("410010", 2019, 3, "motociclista", transito=2, internacoes=3, h=1),
            _linha("410010", 2019, 3, "auto_placebo", transito=1),
        ]
    )
    den = pd.DataFrame(
        {"municipio_res": ["410010"], "ano": [2019], "mes": [3], "frota_moto": [4000]}
    )
    df = est.montar(painel, den, _tratamento(), REGIOES)

    n_meses = est.periodo_de("2025-12")
    assert len(df) == 3 * n_meses
    assert df.groupby("municipio_ibge").size().eq(n_meses).all()
    assert df["moto_internacoes_transito"].sum() == 2
    assert df["cicl_internacoes_transito"].sum() == 0  # grupo sem caso nao some

    a = df[(df["municipio_ibge"] == 4100103) & (df["periodo"] == est.periodo_de("2019-03"))]
    assert a["taxa_moto_transito"].item() == pytest.approx(100_000 * 2 / 4000)
    assert a["taxa_moto_resto"].item() == pytest.approx(100_000 * 2 / 4000)
    assert a["g"].item() == est.periodo_de("2019-03")
    # sem frota, a taxa e NaN -- nunca zero
    assert df.loc[df["frota_moto"].isna(), "taxa_moto_transito"].isna().all()


def test_montar_recusa_municipio_sem_regiao():
    painel = pd.DataFrame([_linha("410010", 2019, 3, "motociclista")])
    den = pd.DataFrame(columns=["municipio_res", "ano", "mes", "frota_moto"])
    with pytest.raises(ValueError, match="regiao imediata"):
        est.montar(painel, den, _tratamento(), REGIOES.iloc[:2])


def test_intensidade_conta_12_meses_a_partir_da_quebra():
    ab = pd.DataFrame(
        {
            "municipio_ibge": [4100103] * 4,
            "mes": ["2019-02", "2019-03", "2020-02", "2020-03"],
            "aberturas": [100, 3, 3, 100],
        }
    )
    i = est.intensidade(_tratamento(), ab)
    assert i.loc[4100103] == pytest.approx(1000 * 6 / 30_000)
    assert list(i.index) == [4100103]


def test_tercis_so_entre_tratados_da_janela():
    idx = pd.Index(range(7))
    intens = pd.Series([1, 2, 3, 4, 5, 6, 99.0], index=idx)
    g = pd.Series([est.periodo_de("2019-01")] * 6 + [est.periodo_de("2017-01")], index=idx)
    t = est.tercis(intens, g)
    assert t.iloc[:6].tolist() == [1, 1, 2, 2, 3, 3]
    assert pd.isna(t.iloc[6])
