"""Definicao de caso, sem pandas no meio. Um teste por digito que importa."""

from __future__ import annotations

import pytest

from vcemal import cid


@pytest.mark.parametrize(
    ("codigo", "grupo"),
    [
        ("V100", "ciclista"),
        ("V194", "ciclista"),
        ("V200", "motociclista"),
        ("V234", "motociclista"),
        ("V299", "motociclista"),
        ("V400", "auto_placebo"),
        ("V499", "auto_placebo"),
    ],
)
def test_grupo_por_categoria(codigo, grupo):
    assert cid.grupo_de(codigo) == grupo


@pytest.mark.parametrize("codigo", ["S720", "V300", "V500", "W010", "", "X"])
def test_fora_do_escopo(codigo):
    assert cid.grupo_de(codigo) is None
    assert not cid.em_transito(codigo)
    assert not cid.condutor_em_transito(codigo)


def test_categorias_terminais_sao_as_tres_ultimas_dezenas():
    assert sorted(cid.CATEGORIAS_TERMINAIS) == ["V19", "V29", "V49"]
    for categoria in cid.CATEGORIAS_TERMINAIS:
        assert cid.e_terminal(categoria)
    assert not cid.e_terminal("V28")


@pytest.mark.parametrize(
    ("codigo", "transito"),
    [
        # Estrutura padrao: .0 .1 .2 nao-transito, .3 embarque, .4 .5 .9 transito
        ("V230", False),
        ("V231", False),
        ("V232", False),
        ("V233", True),
        ("V234", True),
        ("V235", True),
        ("V239", True),
        # Estrutura terminal: .3 e nao-transito EXPLICITO, .6 e transito
        ("V293", False),
        ("V294", True),
        ("V295", True),
        ("V296", True),
        ("V298", False),
        ("V299", True),
        # Mesma regra vale para ciclista e auto
        ("V193", False),
        ("V196", True),
        ("V493", False),
        ("V496", True),
    ],
)
def test_em_transito_respeita_a_estrutura_da_categoria(codigo, transito):
    assert cid.em_transito(codigo) is transito


def test_terminal_e_padrao_divergem_no_tres_e_no_seis():
    """O motivo de o modulo existir: uma regra unica erraria estes quatro."""
    assert cid.em_transito("V233") and not cid.em_transito("V293")
    assert cid.em_transito("V296") and not cid.em_transito("V236")


@pytest.mark.parametrize("codigo", ["V234", "V294", "V134", "V434"])
def test_condutor_em_transito_e_sempre_o_quatro(codigo):
    assert cid.condutor_em_transito(codigo)


@pytest.mark.parametrize("codigo", ["V230", "V235", "V239", "V296", "V233"])
def test_nao_condutor_em_transito(codigo):
    assert not cid.condutor_em_transito(codigo)


def test_codigo_aceita_minusculo():
    assert cid.grupo_de("v234") == "motociclista"
    assert cid.condutor_em_transito("v234")


@pytest.mark.parametrize("codigo", ["01", "02", "03", "04", "05", "06"])
def test_car_int_valido(codigo):
    assert cid.car_int_preenchido(codigo)


@pytest.mark.parametrize("codigo", ["", " ", "00", "0", "99", "9", None, "07", "xx"])
def test_car_int_nao_preenchido(codigo):
    assert not cid.car_int_preenchido(codigo)


def test_nexo_ocupacional_e_so_03_e_04():
    assert sorted(cid.CAR_INT_OCUPACIONAL) == ["03", "04"]
    for codigo in cid.CAR_INT_OCUPACIONAL:
        assert cid.car_int_preenchido(codigo)


@pytest.mark.parametrize("codigo", ["V23", "V29", "V19", "V49"])
def test_categoria_sem_quarto_digito_entra_no_grupo_mas_nao_no_transito(codigo):
    """AIH com CID de 3 caracteres existe no SIH e nao pode virar transito."""
    assert cid.grupo_de(codigo) is not None
    assert not cid.em_transito(codigo)
    assert not cid.condutor_em_transito(codigo)


def test_digitos_transito_escolhe_a_tabela_pela_categoria():
    assert cid.digitos_transito("V23") == cid.TRANSITO_PADRAO
    assert cid.digitos_transito("V29") == cid.TRANSITO_TERMINAL
    assert "6" in cid.digitos_transito("V29")
    assert "6" not in cid.digitos_transito("V23")
