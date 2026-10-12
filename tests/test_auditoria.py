"""Auditoria do tratamento do MEI (D-041): sorteio cego e veredito por estrato.

Sem rede e sem SIH: o tratamento do MEI e o da codificacao sao montados a mao.
"""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal import auditoria as aud


def _tratamento_mei(n_por_celula: int = 10, capitais=aud.CAPITAIS) -> pd.DataFrame:
    linhas, cod = [], 1000000
    for ano in range(2017, 2026):
        for faixa in aud.FAIXAS:
            for i in range(n_por_celula):
                cod += 1
                linhas.append((cod, "datado", f"{ano}-{i % 12 + 1:02d}", faixa))
    for faixa in aud.FAIXAS:
        for _ in range(3 * n_por_celula):
            cod += 1
            linhas.append((cod, "sem_quebra", "", faixa))
    for c in capitais:
        linhas.append((c, "coorte_precoce", "2016-03", "250 mil+"))
    for _ in range(10):
        cod += 1
        linhas.append((cod, "coorte_precoce", "", "100-250 mil"))
    return pd.DataFrame(
        [
            {
                "municipio_ibge": c,
                "uf": "RO",
                "municipio": f"M{c}",
                "faixa": f,
                "mes_quebra": m,
                "grupo": g,
                "mes_tratamento": m if g == "datado" else "",
            }
            for c, g, m, f in linhas
        ]
    )


# --- sorteio -------------------------------------------------------------------


def test_sorteio_tem_seis_por_celula_iscas_por_faixa_e_todas_as_capitais():
    chave = aud.sortear(_tratamento_mei())
    celulas = chave.groupby(["estrato", "faixa"]).size().to_dict()
    for estrato in [*aud.ESTRATOS, aud.ISCA]:
        for faixa in aud.FAIXAS:
            assert celulas[(estrato, faixa)] == aud.POR_CELULA
    assert set(chave.loc[chave["estrato"] == aud.CAPITAL, "municipio_ibge"]) == set(aud.CAPITAIS)
    assert len(chave) == 4 * 2 * aud.POR_CELULA + len(aud.CAPITAIS)
    assert chave["municipio_ibge"].is_unique


def test_sorteio_respeita_estrato_e_nunca_pega_outra_coorte_precoce():
    trat = _tratamento_mei()
    chave = aud.sortear(trat).merge(trat[["municipio_ibge", "grupo", "mes_quebra"]])
    ano = chave["mes_quebra"].str.slice(0, 4)
    assert (ano[chave["estrato"] == "2017"] == "2017").all()
    assert ano[chave["estrato"] == "2018-2020"].between("2018", "2020").all()
    assert ano[chave["estrato"] == "2021-2025"].between("2021", "2025").all()
    assert (chave.loc[chave["estrato"] == aud.ISCA, "grupo"] == "sem_quebra").all()
    precoce = chave[chave["grupo"] == "coorte_precoce"]
    assert set(precoce["municipio_ibge"]) == set(aud.CAPITAIS)


def test_sorteio_nao_depende_da_ordem_das_linhas():
    trat = _tratamento_mei()
    a = aud.sortear(trat)
    b = aud.sortear(trat.sample(frac=1, random_state=1))
    pd.testing.assert_frame_equal(a, b)


def test_ordem_de_trabalho_mistura_os_estratos():
    """Iscas, capitais e datados intercalados: a posicao na lista nao entrega o grupo."""
    chave = aud.sortear(_tratamento_mei())
    assert chave["estrato"].head(12).nunique() > 2


def test_lista_cega_nao_carrega_estrato_faixa_nem_data():
    cega = aud.lista_cega(aud.sortear(_tratamento_mei()))
    assert list(cega.columns) == ["municipio_ibge", "uf", "municipio"]


def test_celula_pequena_demais_recusa_o_sorteio():
    with pytest.raises(ValueError, match="2017, 20-50 mil"):
        aud.sortear(_tratamento_mei(n_por_celula=3))


def test_capital_faltando_recusa_o_sorteio():
    with pytest.raises(ValueError, match="capitais"):
        aud.sortear(_tratamento_mei(capitais=aud.CAPITAIS[:-1]))


# --- veredito -------------------------------------------------------------------


def _codificado(linhas: dict[int, tuple[str, int] | None]) -> pd.DataFrame:
    """{municipio: (mes_tratamento, incerteza_meses) ou None se nao achado}."""
    return pd.DataFrame(
        [
            {
                "municipio_ibge": c,
                "tratado": v is not None,
                "mes_tratamento": v[0] if v else None,
                "incerteza_meses": v[1] if v else None,
            }
            for c, v in linhas.items()
        ]
    )


def test_concordancia_admite_seis_meses_dos_dois_lados_do_intervalo():
    # intervalo codificado 2019-03..2019-06; quebra pode cair em 2018-09..2019-12
    assert aud.concorda("2018-09", "2019-06", 3)
    assert aud.concorda("2019-12", "2019-06", 3)
    assert not aud.concorda("2018-08", "2019-06", 3)
    assert not aud.concorda("2020-01", "2019-06", 3)


def test_capital_concorda_se_o_intervalo_comeca_ate_2018_com_folga():
    assert aud.concorda_precoce("2018-05", 0)
    assert aud.concorda_precoce("2019-06", 0), "seis meses de folga depois de dez/2018"
    assert aud.concorda_precoce("2020-03", 12), "o intervalo comeca em 2019-03"
    assert not aud.concorda_precoce("2019-07", 0)


def _chave_e_mei(estrato: str, quebras: list[str], faixa: str = "20-50 mil"):
    cods = list(range(1, len(quebras) + 1))
    chave = pd.DataFrame({"municipio_ibge": cods, "estrato": estrato, "faixa": faixa})
    mei = pd.DataFrame({"municipio_ibge": cods, "mes_quebra": quebras})
    return chave, mei


def _resumo(chave, mei, cod) -> pd.Series:
    _, resumo, _ = aud.avaliar(chave, mei, cod)
    return resumo.set_index("estrato")


def test_estrato_passa_com_dois_tercos_concordantes():
    chave, mei = _chave_e_mei("2018-2020", ["2019-01"] * 9)
    cod = _codificado({i: ("2019-02", 0) if i <= 6 else ("2021-01", 0) for i in range(1, 10)})
    linha = _resumo(chave, mei, cod).loc["2018-2020"]
    assert (linha["achados"], linha["concordantes"], linha["veredito"]) == (9, 6, "passa")


def test_estrato_falha_abaixo_de_dois_tercos():
    chave, mei = _chave_e_mei("2017", ["2017-04"] * 8)
    cod = _codificado({i: ("2017-05", 0) if i <= 3 else ("2019-01", 2) for i in range(1, 9)})
    assert _resumo(chave, mei, cod).loc["2017", "veredito"] == "falha"


def test_poucos_achados_e_inconclusivo_e_nao_achado_nao_conta_contra():
    chave, mei = _chave_e_mei("2021-2025", ["2022-01"] * 12)
    cod = _codificado({i: ("2022-02", 0) if i <= 5 else None for i in range(1, 13)})
    por_mun, resumo, _ = aud.avaliar(chave, mei, cod)
    linha = resumo.set_index("estrato").loc["2021-2025"]
    assert (linha["achados"], linha["veredito"]) == (5, "inconclusivo")
    assert por_mun["concorda"].isna().sum() == 7


def test_capital_e_julgada_pelo_limite_precoce_e_nao_pela_quebra():
    chave, mei = _chave_e_mei(aud.CAPITAL, ["2016-03"] * 6, faixa="250 mil+")
    cod = _codificado({i: ("2018-06", 0) if i <= 4 else ("2020-01", 0) for i in range(1, 7)})
    linha = _resumo(chave, mei, cod).loc[aud.CAPITAL]
    assert (linha["concordantes"], linha["veredito"]) == (4, "passa")


def test_isca_so_e_descrita_sem_veredito():
    chave, mei = _chave_e_mei(aud.ISCA, ["", ""])
    linha = _resumo(chave, mei, _codificado({1: ("2020-01", 0), 2: None})).loc[aud.ISCA]
    assert (linha["achados"], linha["veredito"]) == (1, "")


def test_resumo_por_faixa_abre_o_estrato_sem_veredito():
    chave, mei = _chave_e_mei("2017", ["2017-04"] * 4)
    chave.loc[2:, "faixa"] = "50-100 mil"
    cod = _codificado({1: ("2017-05", 0), 2: None, 3: ("2017-04", 0), 4: ("2017-06", 0)})
    _, _, por_faixa = aud.avaliar(chave, mei, cod)
    f = por_faixa.set_index(["estrato", "faixa"])
    assert f.loc[("2017", "20-50 mil"), "achados"] == 1
    assert f.loc[("2017", "50-100 mil"), "concordantes"] == 2
    assert "veredito" not in por_faixa.columns


def test_municipio_da_amostra_sem_linha_codificada_e_erro():
    chave, mei = _chave_e_mei("2017", ["2017-04"] * 2)
    with pytest.raises(ValueError, match="sem codificacao"):
        aud.avaliar(chave, mei, _codificado({1: None}))
