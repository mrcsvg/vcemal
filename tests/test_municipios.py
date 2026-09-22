"""Ponte nome -> codigo IBGE. Errar aqui corrompe a taxa sem deixar sinal."""

from __future__ import annotations

import pytest

from vcemal import municipios as mun

INDICE = {
    ("PR", "CURITIBA"): 4106902,
    ("SP", "SAO PAULO"): 3550308,
    ("BA", "SALVADOR"): 2927408,
    ("RS", "SANT ANA DO LIVRAMENTO"): 4317103,
    ("MG", "BRAZOPOLIS"): 3108909,
}


@pytest.mark.parametrize(
    ("bruto", "esperado"),
    [
        ("Curitiba", "CURITIBA"),
        ("SÃO PAULO", "SAO PAULO"),
        ("Sant'Ana do Livramento", "SANT ANA DO LIVRAMENTO"),
        ("Embu-Guaçu", "EMBU GUACU"),
        ("  Poxoréu  ", "POXOREU"),
    ],
)
def test_normalizar(bruto, esperado):
    assert mun.normalizar(bruto) == esperado


def test_resolver_nome_exato():
    assert mun.resolver("PR", "CURITIBA", INDICE) == 4106902
    assert mun.resolver("pr", "Curitiba", INDICE) == 4106902


def test_resolver_apostrofo_colapsa():
    assert mun.resolver("RS", "SANTANA DO LIVRAMENTO", INDICE) == 4317103


@pytest.mark.parametrize(
    ("uf", "nome", "codigo"),
    [
        ("PB", "SANTAREM", 2513653),
        ("TO", "FORTALEZA DO TABOCAO", 1708254),
        ("RN", "BOA SAUDE", 2405306),
        ("MG", "BARAO D0 MONTE ALTO", 3105509),
        ("MT", "VILA BELA DA SANTISSIMA TRINDA", 5105507),
        ("SP", "EMBU", 3515004),
        ("MT", "POXOREO", 5107008),
    ],
)
def test_apelidos_revisados(uf, nome, codigo):
    assert mun.resolver(uf, nome, INDICE) == codigo


def test_renomeacao_nao_cai_em_municipio_parecido():
    """O fuzzy casava Santarem/PB com Santo Andre. A tabela nao erra isso."""
    assert mun.resolver("PB", "SANTAREM", INDICE) == 2513653
    assert mun.resolver("TO", "SAO VALERIO DA NATIVIDADE", INDICE) == 1720499


@pytest.mark.parametrize("uf", ["SP", "RJ", "MG"])
def test_municipio_nao_informado_sai_em_qualquer_uf(uf):
    assert mun.resolver(uf, "MUNICIPIO NAO INFORMADO", INDICE) is None


def test_desconhecido_vira_none_e_nao_chute():
    assert mun.resolver("PR", "CIDADE QUE NAO EXISTE", INDICE) is None


@pytest.mark.parametrize(
    ("entrada", "esperado"), [(4106902, "410690"), ("3550308", "355030"), ("410690", "410690")]
)
def test_para_6_digitos(entrada, esperado):
    assert mun.para_6_digitos(entrada) == esperado


@pytest.mark.parametrize("ruim", ["41069", "41069022", "", "abc"])
def test_para_6_digitos_rejeita_tamanho_errado(ruim):
    with pytest.raises(ValueError, match="6 nem 7"):
        mun.para_6_digitos(ruim)


def test_apelidos_nao_colidem_com_o_indice():
    """Apelido que ja casa por nome exato e apelido morto -- e sinal de engano."""
    assert not set(mun.APELIDOS) & set(INDICE)


def test_todo_apelido_tem_codigo_de_7_digitos():
    for chave, codigo in mun.APELIDOS.items():
        assert len(str(codigo)) == 7, chave


def test_construir_indice():
    indice = mun.construir_indice([{"id": 4106902, "nome": "Curitiba", "uf": "PR"}])
    assert indice == {("PR", "CURITIBA"): 4106902}
