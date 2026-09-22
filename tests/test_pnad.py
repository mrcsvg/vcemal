"""Modulo de plataformas da PNAD: regras puras, leitura de largura fixa e resumo ponderado."""

# ruff: noqa: E501 -- layout e registros de largura fixa nao quebram

from __future__ import annotations

import pandas as pd
import pytest

from vcemal import pnad
from vcemal.transform import pnad as tr


@pytest.mark.parametrize(
    ("vd4009", "v4019", "esperado"),
    [
        ("01", " ", False),  # privado com carteira
        ("02", " ", True),  # privado sem carteira
        ("04", " ", True),  # domestico sem carteira
        ("06", " ", True),  # publico sem carteira: informal na definicao do IBGE
        ("07", " ", False),  # estatutario
        ("08", "1", False),  # empregador com CNPJ
        ("08", "2", True),  # empregador sem CNPJ
        ("09", "1", False),  # conta-propria com CNPJ
        ("09", "2", True),  # conta-propria sem CNPJ -- o entregador de app
        ("10", " ", True),  # familiar auxiliar
        ("  ", " ", None),  # nao ocupado
    ],
)
def test_informal(vd4009, v4019, esperado):
    assert pnad.informal(vd4009, v4019) is esperado


@pytest.mark.parametrize(
    ("vd4009", "esperado"), [("01", True), ("09", True), ("05", False), ("07", False), ("  ", None)]
)
def test_setor_privado(vd4009, esperado):
    assert pnad.setor_privado(vd4009) is esperado


@pytest.mark.parametrize(
    ("uf", "regiao"),
    [
        ("35", "Sudeste"),
        ("11", "Norte"),
        ("43", "Sul"),
        ("53", "Centro-Oeste"),
        ("29", "Nordeste"),
        ("", None),
    ],
)
def test_regiao(uf, regiao):
    assert pnad.regiao_de(uf) == regiao


@pytest.mark.parametrize(("t", "s"), [(1, "01-02-03"), (3, "07-08-09"), (4, "10-11-12")])
def test_trimestre_do_deflator(t, s):
    assert pnad.trimestre_do_deflator(t) == s


def test_rendimento_hora_reproduz_o_ibge():
    """Motociclistas plataformizados, 2024: R$ 2.119 por mes, 45,2 h/semana -> R$ 10,8/h."""
    assert round(2119 / (45.2 * pnad.SEMANAS_POR_MES), 1) == 10.8


# --- leitura de largura fixa -------------------------------------------------

LAYOUT = {
    "Ano": (1, 4), "Trimestre": (5, 1), "UF": (6, 2), "V1023": (8, 1), "V1028": (9, 8),
    "V2007": (17, 1), "V2009": (18, 3), "VD4002": (21, 1), "VD4009": (22, 2), "V4019": (24, 1),
    "VD4012": (25, 1), "V4039": (26, 3), "VD4016": (29, 8), "V4010": (37, 4), "SD14001": (41, 1),
    "S140093": (42, 1),
}  # fmt: skip


def _linha(
    uf,
    peso,
    sexo,
    ocupado,
    vd4009,
    v4019,
    contrib,
    horas,
    rend,
    ocup,
    s14009,
    s140093,
    ano="2024",
    tri="3",
):
    return f"{ano}{tri}{uf}1{peso:08.2f}{sexo}030{ocupado}{vd4009:>2}{v4019}{contrib}{horas:>3}{rend:>8}{ocup:>4}{s14009}{s140093}"


@pytest.fixture
def txt(tmp_path):
    linhas = [
        # SP: motociclista plataformizado, conta-propria sem CNPJ, nao contribui, 48h, R$ 2000
        _linha("35", 100.0, "1", "1", "09", "2", "2", "048", "00002000", "8321", "1", "1"),
        # SP: motociclista nao plataformizado, empregado com carteira, contribui, 40h, R$ 1600
        _linha("35", 100.0, "1", "1", "01", " ", "1", "040", "00001600", "8321", "2", "2"),
        # RS: entregador de bicicleta plataformizado, 30h, R$ 900, peso maior
        _linha("43", 300.0, "2", "1", "09", "2", "2", "030", "00000900", "9331", "1", "1"),
        # SP: cozinheiro que usa app de entrega (nao e entregador)
        _linha("35", 100.0, "2", "1", "02", " ", "2", "044", "00001800", "5120", "1", "1"),
        # SP: servidor publico -- fora do universo
        _linha("35", 100.0, "1", "1", "07", " ", "1", "040", "00005000", "2410", "2", "2"),
        # SP: desocupado -- fora do universo
        _linha("35", 100.0, "1", "2", "  ", " ", " ", "   ", "        ", "    ", " ", " "),
    ]
    caminho = tmp_path / "PNADC_2024_trimestre3.txt"
    caminho.write_bytes(("\n".join(linhas) + "\n").encode("ascii"))
    return caminho


def test_ler_fatia_as_variaveis_pelo_layout(txt):
    df = tr.ler(txt, LAYOUT)
    assert len(df) == 6
    assert df["V4010"].tolist()[:3] == ["8321", "8321", "9331"]
    assert df["VD4016"].iloc[0] == "00002000"


def test_ler_sem_variavel_no_dicionario_falha_alto(txt):
    with pytest.raises(KeyError, match="V1028"):
        tr.ler(txt, {k: v for k, v in LAYOUT.items() if k != "V1028"})


def test_preparar_marca_universo_e_grupos(txt):
    p = tr.preparar(tr.ler(txt, LAYOUT))
    assert p["universo"].tolist() == [True, True, True, True, False, False]
    assert p["informal"].tolist()[:4] == [True, False, True, True]
    assert p["motociclista"].tolist()[:2] == [True, True]
    assert p["entregador"].tolist()[:4] == [True, False, True, False], (
        "cozinheiro usa app, nao entrega"
    )
    assert p["regiao"].tolist()[:3] == ["Sudeste", "Sudeste", "Sul"]


def test_resumir_pondera_e_reproduz_a_razao_de_medias(txt):
    p = tr.preparar(tr.ler(txt, LAYOUT))
    r = tr.resumir(p).set_index("grupo")
    ent = r.loc["entregadores"]
    assert ent["pessoas"] == pytest.approx(400.0)
    assert ent["amostra"] == 2
    assert ent["pct_informal"] == pytest.approx(100.0)
    assert ent["pct_contribuinte"] == pytest.approx(0.0)
    # media ponderada: (48*100 + 30*300) / 400 = 34.5 h ; (2000*100 + 900*300)/400 = 1175
    assert ent["horas_media"] == pytest.approx(34.5)
    assert ent["rend_medio"] == pytest.approx(1175.0)
    assert ent["rend_hora"] == pytest.approx(1175 / (34.5 * pnad.SEMANAS_POR_MES))
    moto = r.loc["motociclistas"]
    assert moto["pct_contribuinte"] == pytest.approx(50.0)
    assert r.loc["ocupados_privado", "amostra"] == 4, "publico e desocupado ficam fora"
    assert (
        "motociclistas_plataformizados" in r.index
        and r.loc["motociclistas_plataformizados", "amostra"] == 1
    )


def test_resumir_por_regiao(txt):
    p = tr.preparar(tr.ler(txt, LAYOUT))
    r = tr.resumir(p, "regiao")
    sul = r[(r["regiao"] == "Sul") & (r["grupo"] == "entregadores")].iloc[0]
    assert sul["pessoas"] == pytest.approx(300.0) and sul["horas_media"] == pytest.approx(30.0)


def test_deflacionar_por_uf_e_trimestre(txt):
    p = tr.preparar(tr.ler(txt, LAYOUT))
    defl = pd.DataFrame(
        {
            "Ano": [2024, 2024],
            "trim": ["07-08-09", "07-08-09"],
            "UF": ["35", "43"],
            "Habitual": [1.10, 1.05],
        }
    )
    d = tr.deflacionar(p, defl)
    assert d["rend_real"].iloc[0] == pytest.approx(2200.0)
    assert d["rend_real"].iloc[2] == pytest.approx(945.0)


def test_deflacionar_sem_fator_falha_alto(txt):
    p = tr.preparar(tr.ler(txt, LAYOUT))
    defl = pd.DataFrame({"Ano": [2024], "trim": ["07-08-09"], "UF": ["35"], "Habitual": [1.1]})
    with pytest.raises(KeyError, match="deflator"):
        tr.deflacionar(p, defl)
