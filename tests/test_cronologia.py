"""Regras da cronologia de entrada (F3). Tudo offline."""

from __future__ import annotations

import pytest

from vcemal import cronologia as cro


def linha(**kw):
    base = {
        "municipio_ibge": "4106902",
        "uf": "PR",
        "municipio": "Curitiba",
        "plataforma": "ifood",
        "evento": "entrada",
        "data_min": "2018-09",
        "data_max": "2018-09",
        "tipo_evidencia": "2",
        "confianca": "B",
        "fonte": "Gazeta do Povo, 12/09/2018",
        "url": "https://exemplo.invalido/materia",
        "data_acesso": "2026-09-20",
        "trecho": "entregadores do iFood comecam a circular",
        "buscas": "",
        "observacao": "",
        "codificador": "A",
    }
    base.update(kw)
    return base


def nao_encontrado(**kw):
    base = {
        "data_min": "",
        "data_max": "",
        "tipo_evidencia": "0",
        "confianca": "N",
        "fonte": "",
        "url": "",
        "buscas": '"iFood" "entregadores" Curitiba',
    }
    base.update(kw)
    return linha(**base)


# --- datas ------------------------------------------------------------------


def test_mes_indice_e_inverso_de_indice_mes():
    assert cro.indice_mes(cro.mes_indice("2018-01")) == "2018-01"
    assert cro.mes_indice("2019-01") - cro.mes_indice("2018-01") == 12


@pytest.mark.parametrize("ruim", ["2018", "2018-13", "18-01", "2018/01", "jan/2018"])
def test_data_fora_do_formato_e_erro(ruim):
    with pytest.raises(ValueError):
        cro.mes_indice(ruim)


# --- validacao ---------------------------------------------------------------


def test_linha_completa_passa():
    cro.validar([linha(), nao_encontrado(plataforma="keeta")])


def test_entrada_antes_da_frota_propria_e_marketplace_e_recusada():
    with pytest.raises(ValueError, match="marketplace"):
        cro.validar([linha(data_min="2016-05", data_max="2016-05")])


@pytest.mark.parametrize(
    "kw, erro",
    [
        ({"plataforma": "aiqfome"}, "plataforma desconhecida"),
        ({"evento": "expansao"}, "evento"),
        ({"confianca": "E"}, "confianca"),
        ({"confianca": "A", "data_max": "2018-10"}, "intervalo"),
        ({"confianca": "C", "data_max": "2019-09"}, "intervalo"),
        ({"data_min": "2018-10"}, "data_min depois"),
        ({"url": ""}, "sem url"),
        ({"municipio_ibge": "410690"}, "7 digitos"),
        ({"codificador": ""}, "sem codificador"),
        ({"tipo_evidencia": "0"}, "tipo_evidencia"),
    ],
)
def test_validar_recusa(kw, erro):
    with pytest.raises(ValueError, match=erro):
        cro.validar([linha(**kw)])


def test_nao_encontrado_exige_buscas_e_nao_admite_data():
    with pytest.raises(ValueError, match="buscas"):
        cro.validar([nao_encontrado(buscas="")])
    with pytest.raises(ValueError, match="nao pode ter data"):
        cro.validar([nao_encontrado(data_min="2018-01", data_max="2018-01")])


def test_confianca_d_admite_intervalo_largo():
    cro.validar([linha(confianca="D", tipo_evidencia="3", data_max="2020-12")])


def test_evento_repetido_na_mesma_data_e_erro_mas_reentrada_nao():
    with pytest.raises(ValueError, match="repetida"):
        cro.validar([linha(), linha()])
    cro.validar(
        [
            linha(plataforma="99food", data_min="2020-02", data_max="2020-02"),
            linha(plataforma="99food", evento="saida", data_min="2023-03", data_max="2023-03"),
            linha(plataforma="99food", data_min="2025-09", data_max="2025-09"),
        ]
    )


# --- concordancia --------------------------------------------------------------


def test_concordam_dentro_de_um_mes_ou_com_intervalos_que_se_cruzam():
    assert cro.concordam(linha(), linha(data_min="2018-10", data_max="2018-10"))
    assert not cro.concordam(linha(), linha(data_min="2018-11", data_max="2018-11"))
    assert cro.concordam(
        linha(confianca="C", data_min="2018-06", data_max="2018-11"),
        linha(data_min="2018-11", data_max="2018-11"),
    )
    assert not cro.concordam(linha(), nao_encontrado())
    assert cro.concordam(nao_encontrado(), nao_encontrado())


def test_kappa():
    assert cro.kappa([]) is None
    assert cro.kappa([(True, True), (False, False)]) == pytest.approx(1.0)
    assert cro.kappa([(True, True), (True, True)]) == pytest.approx(1.0)
    # 50% de acordo ao acaso com marginais iguais -> kappa 0
    assert cro.kappa([(True, True), (True, False), (False, True), (False, False)]) == pytest.approx(
        0.0
    )


def test_comparar_exige_o_mesmo_universo():
    with pytest.raises(ValueError, match="universos"):
        cro.comparar([linha()], [linha(), linha(plataforma="rappi")])


def test_comparar_separa_existencia_de_data():
    a = [
        linha(),
        linha(municipio_ibge="3550308", plataforma="rappi", data_min="2018-01", data_max="2018-01"),
    ]
    b = [
        linha(codificador="B", data_min="2019-03", data_max="2019-03"),
        nao_encontrado(codificador="B", municipio_ibge="3550308", plataforma="rappi"),
    ]
    res = cro.comparar(a, b)
    assert res["n_pares"] == 2
    assert res["n_datas"] == 1
    assert res["pct_data_concordante"] == 0.0
    motivos = sorted(d["motivo"] for d in res["discordancias"])
    assert motivos == ["data", "existencia"]


# --- consolidacao --------------------------------------------------------------


def test_r1_concordantes_fica_o_de_maior_confianca():
    a = [linha(confianca="C", tipo_evidencia="3", data_min="2018-06", data_max="2018-11")]
    b = [linha(codificador="B", data_min="2018-10", data_max="2018-10")]
    cons, pend = cro.consolidar(a, b)
    assert not pend
    assert cons[0]["codificador"] == "B" and cons[0]["regra"] == "R1-concordantes"


def test_r2_evidencia_forte_vence_o_nao_encontrado_e_fraca_vai_para_adjudicacao():
    cons, pend = cro.consolidar([linha()], [nao_encontrado(codificador="B")])
    assert cons[0]["regra"] == "R2-evidencia-forte" and not pend
    fraca = linha(confianca="C", tipo_evidencia="3", data_max="2018-12")
    cons, pend = cro.consolidar([fraca], [nao_encontrado(codificador="B")])
    assert not cons and pend[0]["motivo"] == "existencia com evidencia fraca"


def test_r3_discordantes():
    forte_a = linha()
    forte_b = linha(codificador="B", data_min="2019-06", data_max="2019-06")
    cons, pend = cro.consolidar([forte_a], [forte_b])
    assert not cons and pend[0]["motivo"] == "datas fortes discordantes"
    # confianca diferente decide
    cons, pend = cro.consolidar(
        [forte_a],
        [
            linha(
                codificador="B",
                confianca="C",
                tipo_evidencia="3",
                data_min="2019-06",
                data_max="2019-09",
            )
        ],
    )
    assert cons[0]["regra"] == "R3-maior-confianca" and cons[0]["codificador"] == "A"
    # dois fracos discordantes viram uniao com confianca D
    fa = linha(confianca="C", tipo_evidencia="3", data_min="2018-03", data_max="2018-06")
    fb = linha(
        codificador="B", confianca="C", tipo_evidencia="3", data_min="2018-10", data_max="2019-01"
    )
    cons, pend = cro.consolidar([fa], [fb])
    assert cons[0]["regra"] == "R3-uniao-dos-intervalos"
    assert (cons[0]["data_min"], cons[0]["data_max"], cons[0]["confianca"]) == (
        "2018-03",
        "2019-01",
        "D",
    )


def test_adjudicacao_vence_qualquer_regra_e_nunca_e_media():
    a, b = [linha()], [linha(codificador="B", data_min="2019-06", data_max="2019-06")]
    d = [
        {
            "municipio_ibge": "4106902",
            "plataforma": "ifood",
            "evento": "entrada",
            "escolha": "propria",
            "data_min": "2018-11",
            "data_max": "2018-11",
            "confianca": "B",
            "justificativa": "materia de 20/11/2018",
            "adjudicador": "C",
        }
    ]
    cons, pend = cro.consolidar(a, b, d)
    assert not pend and cons[0]["data_min"] == "2018-11" and cons[0]["regra"].startswith("R0")
    d[0]["escolha"] = "nenhum"
    cons, pend = cro.consolidar(a, b, d)
    assert cons == [] and pend == []


# --- tratamento ------------------------------------------------------------------


def test_tratamento_usa_o_data_max_da_entrada_mais_antiga_e_carrega_a_incerteza():
    cons = [
        {
            **linha(confianca="C", tipo_evidencia="3", data_min="2018-06", data_max="2018-09"),
            "regra": "x",
        },
        {**linha(plataforma="rappi", data_min="2018-08", data_max="2018-08"), "regra": "x"},
        {**nao_encontrado(municipio_ibge="2927408", municipio="Salvador", uf="BA"), "regra": "x"},
    ]
    t = {r["municipio_ibge"]: r for r in cro.tratamento(cons)}
    cur = t["4106902"]
    assert cur["tratado"] and cur["mes_tratamento"] == "2018-08"  # rappi e certa antes do ifood
    assert cur["incerteza_meses"] == 0 and cur["plataformas"] == "ifood|rappi"
    assert cur["mes_saida_total"] is None
    assert not t["2927408"]["tratado"]


def test_tratamento_reverso_so_quando_todas_as_plataformas_sairam():
    base = [
        {**linha(plataforma="uber_eats", data_min="2017-05", data_max="2017-05"), "regra": "x"},
        {
            **linha(plataforma="uber_eats", evento="saida", data_min="2022-03", data_max="2022-03"),
            "regra": "x",
        },
    ]
    assert cro.tratamento(base)[0]["mes_saida_total"] == "2022-03"
    com_ifood = base + [{**linha(), "regra": "x"}]
    assert cro.tratamento(com_ifood)[0]["mes_saida_total"] is None
