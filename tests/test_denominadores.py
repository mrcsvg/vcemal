"""Frota e populacao como denominador do painel. Tudo offline."""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal import municipios as mun
from vcemal.transform import denominadores as den

INDICE = {
    ("PR", "CURITIBA"): 4106902,
    ("SP", "SAO PAULO"): 3550308,
    ("BA", "SALVADOR"): 2927408,
}

#: Layout do arquivo real: titulo, total geral, cabecalho repetido, dados, rodape.
_CABECALHO = [
    "UF",
    "MUNICIPIO",
    "TOTAL",
    "AUTOMOVEL",
    "CICLOMOTOR",
    "MOTOCICLETA",
    "MOTONETA",
    "SIDE-CAR",
    "TRICICLO",
    "QUADRICICLO",
]


def _planilha(tmp_path, linhas, sufixo=".xlsx"):
    grade = [
        ["Frota de veiculos, por"] + [None] * 9,
        [119227657] + [None] * 9,
        _CABECALHO,
        _CABECALHO,  # o cabecalho vem repetido em parte da serie
        *linhas,
        ["Fonte: Senatran"] + [None] * 9,  # rodape sem UF de duas letras
    ]
    caminho = tmp_path / f"frota{sufixo}"
    pd.DataFrame(grade).to_excel(caminho, index=False, header=False)
    return caminho


@pytest.fixture
def arquivo(tmp_path):
    return _planilha(
        tmp_path,
        [
            #                 TOTAL  AUTO  CICLO  MOTOCI  MOTON  SIDE  TRI  QUAD
            ["PR", "CURITIBA", 1737730, 800000, 1448, 170754, 31820, 36, 381, 30],
            ["SP", "SAO PAULO", 9460584, 5000000, 6068, 1231804, 239469, 95, 1715, 57],
            ["BA", "SALVADOR", 1036885, 500000, 1681, 173239, 19924, 17, 561, 3],
            ["SP", "MUNICIPIO NAO INFORMADO", 2, 1, 0, 1, 0, 0, 0, 0],
        ],
    )


def test_ler_frota_acha_cabecalho_deslocado(arquivo):
    df = den.ler_frota(arquivo)
    assert len(df) == 4, "tira titulo, cabecalho repetido e rodape"
    assert set(df["UF"]) == {"PR", "SP", "BA"}


def test_ler_frota_acha_o_dado_fora_da_primeira_aba(tmp_path, arquivo):
    """2016: a primeira aba e um glossario; o dado vem na segunda."""
    dado = pd.read_excel(arquivo, header=None)
    caminho = tmp_path / "frota_2016.xlsx"
    with pd.ExcelWriter(caminho) as xl:
        pd.DataFrame([[None, "Automovel", "veiculo automotor"]]).to_excel(
            xl, sheet_name="Glossario", index=False, header=False
        )
        dado.to_excel(xl, sheet_name="JUL_2016", index=False, header=False)
    df = den.ler_frota(caminho)
    assert len(df) == 4
    assert set(df["UF"]) == {"PR", "SP", "BA"}


def test_ler_frota_falha_alto_se_faltar_tipo(tmp_path):
    grade = [["UF", "MUNICIPIO", "TOTAL", "MOTOCICLETA"], ["PR", "CURITIBA", 10, 5]]
    caminho = tmp_path / "incompleto.xlsx"
    pd.DataFrame(grade).to_excel(caminho, index=False, header=False)
    with pytest.raises(ValueError, match="sem as colunas de tipo"):
        den.ler_frota(caminho)


def test_ler_frota_sem_cabecalho_reconhecivel(tmp_path):
    caminho = tmp_path / "estranho.xlsx"
    pd.DataFrame([["a", "b"], ["c", "d"]]).to_excel(caminho, index=False, header=False)
    with pytest.raises(ValueError, match="nao achei o cabecalho"):
        den.ler_frota(caminho)


def test_frota_moto_soma_os_quatro_tipos(arquivo):
    frota, _ = den.agregar_frota(den.ler_frota(arquivo), INDICE, 2023, 12)
    cwb = frota.set_index("municipio_res").loc["410690"]
    assert cwb["frota_moto"] == 170754 + 31820 + 1448 + 36


def test_frota_moto_ignora_triciclo_e_quadriciclo(arquivo):
    """Tres rodas e V30-V39, fora do numerador -- nao pode entrar no denominador."""
    frota, _ = den.agregar_frota(den.ler_frota(arquivo), INDICE, 2023, 12)
    cwb = frota.set_index("municipio_res").loc["410690"]
    assert cwb["frota_moto"] < cwb["frota_total"]
    assert 381 not in frota["frota_moto"].tolist()


def test_so_motocicleta_subestimaria(arquivo):
    """A diferenca nao e decorativa: em Curitiba da ~19%."""
    frota, _ = den.agregar_frota(den.ler_frota(arquivo), INDICE, 2023, 12)
    cwb = frota.set_index("municipio_res").loc["410690"]
    assert cwb["frota_moto"] / cwb["motocicleta"] > 1.15


def test_municipio_nao_informado_e_reportado_nao_somado(arquivo):
    frota, sem_par = den.agregar_frota(den.ler_frota(arquivo), INDICE, 2023, 12)
    assert len(frota) == 3
    assert len(sem_par) == 1
    assert sem_par.iloc[0]["MUNICIPIO"] == "MUNICIPIO NAO INFORMADO"


def test_codigo_sai_com_6_digitos(arquivo):
    frota, _ = den.agregar_frota(den.ler_frota(arquivo), INDICE, 2023, 12)
    assert all(len(c) == 6 for c in frota["municipio_res"])


@pytest.fixture
def painel():
    return pd.DataFrame(
        {
            "uf": ["PR", "PR", "SP"],
            "ano": [2023, 2023, 2023],
            "mes": [12, 12, 12],
            "municipio_res": ["410690", "410690", "355030"],
            "grupo": ["motociclista", "ciclista", "motociclista"],
            "internacoes": [204, 50, 1477],
        }
    )


@pytest.fixture
def frota_pronta(arquivo):
    return den.agregar_frota(den.ler_frota(arquivo), INDICE, 2023, 12)[0]


@pytest.fixture
def populacao_pronta():
    return den.populacao_para_painel(
        [
            {"municipio_ibge": 4106902, "ano": 2023, "populacao": 1963726},
            {"municipio_ibge": 3550308, "ano": 2023, "populacao": 12396372},
        ]
    )


def test_juntar_preserva_o_painel(painel, frota_pronta, populacao_pronta):
    saida = den.juntar(painel, frota_pronta, populacao_pronta)
    assert len(saida) == len(painel)
    assert saida["frota_moto"].notna().all()


def test_taxa_por_frota(painel, frota_pronta, populacao_pronta):
    saida = den.taxas(den.juntar(painel, frota_pronta, populacao_pronta))
    moto = saida[(saida["municipio_res"] == "410690") & (saida["grupo"] == "motociclista")]
    esperado = 100_000 * 204 / (170754 + 31820 + 1448 + 36)
    assert moto["taxa_por_frota"].iloc[0] == pytest.approx(esperado)


def test_municipio_sem_frota_fica_nan_e_nao_zero(frota_pronta, populacao_pronta):
    """Taxa indefinida precisa sair NaN: zero viraria 'municipio sem risco'."""
    painel = pd.DataFrame(
        {
            "uf": ["MG"],
            "ano": [2023],
            "mes": [12],
            "municipio_res": ["310620"],
            "grupo": ["motociclista"],
            "internacoes": [10],
        }
    )
    saida = den.taxas(den.juntar(painel, frota_pronta, populacao_pronta))
    assert pd.isna(saida["frota_moto"].iloc[0])
    assert pd.isna(saida["taxa_por_frota"].iloc[0])


def test_denominador_zero_nao_vira_infinito(painel, populacao_pronta):
    frota = pd.DataFrame(
        {"municipio_res": ["410690"], "ano": [2023], "mes": [12], "frota_moto": [0]}
    )
    saida = den.taxas(den.juntar(painel, frota, populacao_pronta))
    assert pd.isna(saida["taxa_por_frota"].iloc[0])


def test_populacao_para_painel_vazia():
    vazia = den.populacao_para_painel([])
    assert list(vazia.columns) == ["municipio_res", "ano", "populacao"]
    assert vazia.empty


def test_juntar_sem_frota_nem_populacao(painel):
    saida = den.taxas(den.juntar(painel, pd.DataFrame(), pd.DataFrame()))
    assert saida["taxa_por_frota"].isna().all()
    assert saida["taxa_por_populacao"].isna().all()


def test_para_6_digitos_usado_na_populacao(populacao_pronta):
    assert set(populacao_pronta["municipio_res"]) == {"410690", "355030"}
    assert mun.para_6_digitos(4106902) == "410690"


def test_numerador_do_desfecho_e_transito_nao_internacoes():
    """D-023: o desfecho e acidente de transito, nao toda AIH do grupo."""
    assert den.NUMERADOR_DESFECHO == "internacoes_transito"


def test_taxa_aceita_numerador_explicito(painel, frota_pronta, populacao_pronta):
    base = den.juntar(
        painel.assign(internacoes_transito=painel["internacoes"] // 2),
        frota_pronta,
        populacao_pronta,
    )
    ampla = den.taxas(base)
    estrita = den.taxas(base, numerador=den.NUMERADOR_DESFECHO)
    assert (estrita["taxa_por_frota"] < ampla["taxa_por_frota"]).all()


def test_numerador_inexistente_falha_alto(painel, frota_pronta, populacao_pronta):
    base = den.juntar(painel, frota_pronta, populacao_pronta)
    with pytest.raises(KeyError, match="numerador"):
        den.taxas(base, numerador="coluna_que_nao_existe")


def test_linhas_populacao_le_o_agregado_do_censo():
    from vcemal.extract import ibge

    bruto = [
        {
            "resultados": [
                {
                    "series": [
                        {"localidade": {"id": "4106902"}, "serie": {"2022": "1773733"}},
                        {"localidade": {"id": "1234567"}, "serie": {"2022": "..."}},
                    ]
                }
            ]
        }
    ]
    assert ibge.linhas_populacao(bruto) == [
        {"municipio_ibge": 4106902, "ano": 2022, "populacao": 1773733}
    ]
