"""Localizacao do arquivo mensal do Senatran, cujo nome nao e chave estavel.

Os nomes aqui sao todos reais, colhidos das paginas de 2016 a 2025.
"""

from __future__ import annotations

import pytest

from vcemal.extract import senatran


@pytest.mark.parametrize(
    ("arquivo", "mes"),
    [
        ("frota_munic_modelo_dezembro_2023.xls", 12),
        ("frota_munic_modelo_dezembro_2019.xls", 12),
        ("FrotaporMunicipioetipoDEZEMBRO2025.xlsx", 12),  # sem separador, caixa alta
        ("copy_of_FrotaporMunicpioeTipoSETEMBRO2025.xlsx", 9),  # "Municpio" com typo
        ("frota-por-municipio-e-tipo-agosto-2025.xlsx", 8),
        ("Frota_por_municipio_tipo_Janeiro_2025.xlsx", 1),
        ("copy2_of_Frota_por_municipio_tipo_Maro_2025.xlsx", 3),  # Marco sem cedilha
        ("FrotaporMunicpioeTipoJunho2025.xlsx", 6),
        ("frota_por_municipio_e_tipo-dez_16.xlsx", 12),  # abreviacao, ano de 2 digitos
        ("frota_por_municipio_e_tipo-jul_16.xlsx", 7),
    ],
)
def test_mes_do_arquivo(arquivo, mes):
    assert senatran.mes_do_arquivo(arquivo) == mes


@pytest.mark.parametrize("arquivo", ["frota_munic.xls", "relatorio_2025.xlsx", ""])
def test_mes_indeterminado_vira_none(arquivo):
    assert senatran.mes_do_arquivo(arquivo) is None


def test_abreviacao_so_casa_como_token_inteiro():
    """`mar` solto e mes; dentro de outra palavra, nao."""
    assert senatran.mes_do_arquivo("frota_mar_2020.xls") == 3
    assert senatran.mes_do_arquivo("frota_marcas_2020.xls") is None


def test_ano_confere_descarta_arquivo_de_outro_ano():
    """`Frota_Munic_Modelo_Fevereiro_20241.xls` aparece solto na pagina de 2025."""
    assert not senatran.ano_confere("Frota_Munic_Modelo_Fevereiro_20241.xls", 2025)
    assert senatran.ano_confere("Frota_Munic_Modelo_Fevereiro_20241.xls", 2024)


def test_ano_confere_aceita_nome_sem_ano_de_4_digitos():
    """2016 usa `-dez_16`; a pagina ja e a do ano."""
    assert senatran.ano_confere("frota_por_municipio_e_tipo-dez_16.xlsx", 2016)


def test_todo_mes_tem_grafia_e_abreviacao():
    assert sorted(set(senatran.GRAFIAS_MES.values())) == list(range(1, 13))
    assert sorted(senatran.ABREVIACOES_MES.values()) == list(range(1, 13))
