"""Auditoria do tratamento do MEI (D-041): sorteio cego e veredito por estrato.

Sem rede e sem SIH: o tratamento do MEI e o da codificacao sao montados a mao.
"""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal import auditoria as aud


def _tratamento_mei(n_por_ano: int = 20, n_sem_quebra: int = 30) -> pd.DataFrame:
    linhas, cod = [], 1100000
    for ano in range(2017, 2026):
        for i in range(n_por_ano):
            cod += 1
            mes = f"{ano}-{i % 12 + 1:02d}"
            linhas.append((cod, "datado", mes, "20-50 mil"))
    for _ in range(n_sem_quebra):
        cod += 1
        linhas.append((cod, "sem_quebra", "", "20-50 mil"))
    for _ in range(10):
        cod += 1
        linhas.append((cod, "coorte_precoce", "", "250 mil+"))
    return pd.DataFrame(
        [
            {
                "municipio_ibge": c,
                "uf": "RO",
                "municipio": f"M{c}",
                "populacao_2022": 30_000,
                "faixa": f,
                "mes_quebra": m,
                "grupo": g,
                "mes_tratamento": m if g == "datado" else "",
            }
            for c, g, m, f in linhas
        ]
    )


# --- sorteio -------------------------------------------------------------------


def test_sorteio_tem_doze_por_estrato_e_doze_iscas():
    chave = aud.sortear(_tratamento_mei())
    assert chave["estrato"].value_counts().to_dict() == {
        "2017": aud.POR_ESTRATO,
        "2018-2020": aud.POR_ESTRATO,
        "2021-2025": aud.POR_ESTRATO,
        "isca": aud.ISCAS,
    }
    assert chave["municipio_ibge"].is_unique


def test_sorteio_respeita_o_estrato_e_nunca_pega_coorte_precoce():
    trat = _tratamento_mei()
    chave = aud.sortear(trat).merge(trat, on="municipio_ibge")
    assert set(chave["grupo"]) == {"datado", "sem_quebra"}
    ano = chave["mes_quebra"].str.slice(0, 4)
    assert (ano[chave["estrato"] == "2017"] == "2017").all()
    assert ano[chave["estrato"] == "2018-2020"].between("2018", "2020").all()
    assert ano[chave["estrato"] == "2021-2025"].between("2021", "2025").all()
    assert (chave.loc[chave["estrato"] == "isca", "grupo"] == "sem_quebra").all()


def test_sorteio_nao_depende_da_ordem_das_linhas():
    trat = _tratamento_mei()
    a = aud.sortear(trat)
    b = aud.sortear(trat.sample(frac=1, random_state=1))
    pd.testing.assert_frame_equal(a, b)


def test_ordem_de_trabalho_mistura_iscas_e_estratos():
    """Iscas e datados intercalados: a posicao na lista nao entrega o grupo."""
    chave = aud.sortear(_tratamento_mei())
    primeiros = chave["estrato"].head(aud.ISCAS)
    assert primeiros.nunique() > 1


def test_lista_cega_nao_carrega_estrato_nem_data():
    cega = aud.lista_cega(aud.sortear(_tratamento_mei()))
    assert list(cega.columns) == ["municipio_ibge", "uf", "municipio"]


def test_estrato_pequeno_demais_recusa_o_sorteio():
    with pytest.raises(ValueError, match="2017"):
        aud.sortear(_tratamento_mei(n_por_ano=5))


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


def _chave_e_mei(estrato: str, quebras: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    cods = list(range(1, len(quebras) + 1))
    chave = pd.DataFrame({"municipio_ibge": cods, "estrato": estrato})
    mei = pd.DataFrame({"municipio_ibge": cods, "mes_quebra": quebras})
    return chave, mei


def test_estrato_passa_com_dois_tercos_concordantes():
    chave, mei = _chave_e_mei("2018-2020", ["2019-01"] * 9)
    cod = _codificado({i: ("2019-02", 0) if i <= 6 else ("2021-01", 0) for i in range(1, 10)})
    _, resumo = aud.avaliar(chave, mei, cod)
    linha = resumo.set_index("estrato").loc["2018-2020"]
    assert (linha["achados"], linha["concordantes"], linha["veredito"]) == (9, 6, "passa")


def test_estrato_falha_abaixo_de_dois_tercos():
    chave, mei = _chave_e_mei("2017", ["2017-04"] * 8)
    cod = _codificado({i: ("2017-05", 0) if i <= 3 else ("2019-01", 2) for i in range(1, 9)})
    _, resumo = aud.avaliar(chave, mei, cod)
    assert resumo.set_index("estrato").loc["2017", "veredito"] == "falha"


def test_poucos_achados_e_inconclusivo_e_nao_achado_nao_conta_contra():
    chave, mei = _chave_e_mei("2021-2025", ["2022-01"] * 12)
    cod = _codificado({i: ("2022-02", 0) if i <= 5 else None for i in range(1, 13)})
    por_mun, resumo = aud.avaliar(chave, mei, cod)
    linha = resumo.set_index("estrato").loc["2021-2025"]
    assert (linha["achados"], linha["veredito"]) == (5, "inconclusivo")
    assert por_mun["concorda"].isna().sum() == 7


def test_isca_so_e_descrita_sem_veredito():
    chave = pd.DataFrame({"municipio_ibge": [1, 2], "estrato": "isca"})
    mei = pd.DataFrame({"municipio_ibge": [1, 2], "mes_quebra": ["", ""]})
    _, resumo = aud.avaliar(chave, mei, _codificado({1: ("2020-01", 0), 2: None}))
    linha = resumo.set_index("estrato").loc["isca"]
    assert (linha["achados"], linha["veredito"]) == (1, "")


def test_municipio_da_amostra_sem_linha_codificada_e_erro():
    chave, mei = _chave_e_mei("2017", ["2017-04"] * 2)
    with pytest.raises(ValueError, match="sem codificacao"):
        aud.avaliar(chave, mei, _codificado({1: None}))
