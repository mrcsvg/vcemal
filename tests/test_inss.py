"""Regras do INSS sem pandas: especie, classe, CID e UF em todos os formatos da serie."""

from __future__ import annotations

import pytest

from vcemal import inss


@pytest.mark.parametrize(
    ("valor", "codigo"),
    [
        ("31", 31),
        (91, 91),
        ("Auxílio Doenca Previdenciário", 31),
        ("Auxílio Doenca Previdenciário                ", 31),  # como vem no CSV, com espacos
        ("Auxilio doenca previdenciario", 31),  # sem acento, caixa diferente
        ("Auxílio Doenca por Acidente do Trabalho", 91),
        ("Aposent. Invalidez Acidente Trabalho", 92),
        ("Aposentadoria por Idade", 41),
        ("", None),
        (None, None),
        ("Especie que nao existe", None),
    ],
)
def test_especie_de(valor, codigo):
    assert inss.especie_de(valor) == codigo


@pytest.mark.parametrize(
    ("especie", "classe"),
    [
        (91, "acidentario"),
        (92, "acidentario"),
        (93, "acidentario"),
        (94, "acidentario"),
        (31, "previdenciario"),
        (32, "previdenciario"),
        (36, "previdenciario"),
        (21, "previdenciario"),
        (41, None),  # aposentadoria por idade nao e evento de incapacidade
        (80, None),
        (None, None),
    ],
)
def test_classe_de(especie, classe):
    assert inss.classe_de(especie) == classe


def test_acidentaria_e_previdenciaria_nao_se_cruzam():
    assert not (inss.ACIDENTARIAS & inss.PREVIDENCIARIAS)
    assert (inss.ACIDENTARIAS | inss.PREVIDENCIARIAS).issubset(inss.ESPECIES)


@pytest.mark.parametrize(
    ("valor", "cid"),
    [
        ("V29.8 Motociclista Outr Acid Transp Espec", "V298"),  # ZIP 2021-2023
        ("V28   Motociclista Traum Acid Transp s/Colis", "V28"),  # sem 4o digito
        ("V298", "V298"),  # XLSX 2023+
        ("V29", "V29"),
        ("S525", "S525"),  # CSV 2019, coluna de codigo
        ("S52.5 Frat da Extremidade Distal do Radio", "S525"),
        ("v234", "V234"),
        ("Zerados", None),
        ("Em Branco", None),
        ("000000", None),  # CSV 2020-2021
        ("{ñ class}", None),
        ("013  Tuberculose Meninges", None),  # CID-9 residual
        ("", None),
        (None, None),
    ],
)
def test_normalizar_cid(valor, cid):
    assert inss.normalizar_cid(valor) == cid


@pytest.mark.parametrize(
    ("valor", "uf"),
    [
        ("02009-AL-Belo Monte", "AL"),
        ("13041-PB-Campina Grande", "PB"),
        ("20100-SC-Mafra", "SC"),
        (" 02003-AL-Arapiraca   ", "AL"),
        ("Belo Monte", None),
        ("", None),
        (None, None),
    ],
)
def test_uf_de_municipio(valor, uf):
    assert inss.uf_de_municipio(valor) == uf


@pytest.mark.parametrize(
    ("valor", "uf"),
    [("São Paulo", "SP"), ("Sao Paulo", "SP"), ("Alagoas            ", "AL"), ("SP", "SP")],
)
def test_uf_de_nome(valor, uf):
    assert inss.uf_de_nome(valor) == uf


def test_todas_as_27_ufs():
    assert len(inss.UF_SIGLA) == 27
    assert len(set(inss.UF_SIGLA.values())) == 27


@pytest.mark.parametrize(
    ("despacho", "canal"),
    [
        ("Concessao com Analise Documental", "documental"),
        ("Revisao com Analise Documental", "documental"),
        ("Concessão com Análise Documental", "documental"),
        ("Conc. Base Artigo 27 Inciso Ii do Rbps", "art27_ii"),
        ("Concessao Decorrente de Acao Judicial", "judicial"),
        ("Concessao Normal", "normal"),
        ("Conc. Decorrente Revisao Administrativa", "outro"),
        ("Concessao", "outro"),
        ("64", "outro"),
        ("", "outro"),
        (None, "outro"),
    ],
)
def test_canal_de(despacho, canal):
    assert inss.canal_de(despacho) == canal
    assert canal in inss.CANAIS
