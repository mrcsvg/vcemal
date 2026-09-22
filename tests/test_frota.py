"""Quais tipos do RENAVAM compoem o denominador de V20-V29."""

from __future__ import annotations

from vcemal import cid, frota


def test_denominador_nao_e_so_motocicleta():
    """Motoneta e side-car estao na nota de inclusao do CID-10; ciclomotor e o moped."""
    assert "MOTOCICLETA" in frota.TIPOS_MOTO
    assert "MOTONETA" in frota.TIPOS_MOTO
    assert "CICLOMOTOR" in frota.TIPOS_MOTO
    assert "SIDE-CAR" in frota.TIPOS_MOTO
    assert len(frota.TIPOS_MOTO) == 4


def test_tres_rodas_fica_de_fora():
    """O CID-10 manda triciclo para V30-V39, que nao e o desfecho deste projeto."""
    assert "TRICICLO" not in frota.TIPOS_MOTO
    assert "QUADRICICLO" not in frota.TIPOS_MOTO
    assert set(frota.TIPOS_FORA_DE_V20_V29) == {"TRICICLO", "QUADRICICLO"}


def test_excluido_e_incluido_nao_se_cruzam():
    assert not set(frota.TIPOS_MOTO) & set(frota.TIPOS_FORA_DE_V20_V29)


def test_grupo_do_numerador_existe_no_cid():
    """O denominador so faz sentido contra V20-V29 -- se o grupo sumir, isto quebra."""
    assert cid.grupo_de("V234") == "motociclista"


def test_conferir_colunas_acha_o_que_falta():
    presentes = ["UF", "MUNICIPIO", "TOTAL", "MOTOCICLETA", "MOTONETA"]
    assert frota.conferir_colunas(presentes) == ["CICLOMOTOR", "SIDE-CAR"]


def test_conferir_colunas_ignora_caixa_e_espaco():
    presentes = [" motocicleta ", "Motoneta", "CICLOMOTOR", "side-car"]
    assert frota.conferir_colunas(presentes) == []
