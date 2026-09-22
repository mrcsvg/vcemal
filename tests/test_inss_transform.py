"""Os quatro layouts da serie do INSS entram, um so painel sai. Tudo offline."""

# ruff: noqa: E501 -- as linhas sao registros reais dos arquivos, e quebrar mudaria o dado

from __future__ import annotations

import pandas as pd
import pytest

from vcemal.transform import inss as tr

CAB_2019 = "Competência concessão;Espécie;CID;CID;Despacho;Dt Nascimento;Sexo.;Clientela;Mun Resid;Vínculo dependentes;Forma Filiação;UF;Qt SM RMI"
CAB_2021 = "Competência concessão;Espécie;CID;CID_1;Despacho;Dt Nascimento;Sexo.;Clientela;Mun Resid;Vínculo dependentes;Forma Filiação;UF;Qt SM RMI"
CAB_2023 = "Competência concessão;Espécie;CID;Despacho;Dt Nascimento;Sexo.;Clientela;Tipo de Cálculo;Mun Resid;Vínculo dependentes;Forma Filiação;UF;Qt SM RMI"


def _csv(tmp_path, nome, cabecalho, linhas, codificacao):
    caminho = tmp_path / nome
    texto = "\r\n".join([cabecalho, *linhas]) + "\r\n"
    caminho.write_bytes(texto.encode(codificacao))
    return caminho


@pytest.fixture
def csv_2019(tmp_path):
    """latin-1, competencia por extenso, CID em duas colunas (codigo, nome)."""
    return _csv(
        tmp_path,
        "concedidos_201901.csv",
        CAB_2019,
        [
            "janeiro/2019;Auxílio Doenca Previdenciário;V234;V23.4 Condutor Acid Trans;Concessao Normal;01/01/1990;Masculino;Urbano;02003-AL-Arapiraca;Não Informado;Autônomo;Alagoas;1,068",
            "janeiro/2019;Auxílio Doenca por Acidente do Trabalho;V299;V29.9 Motociclista Acid Trans Ne;Concessao Normal;01/01/1990;Masculino;Urbano;71035-SP-São Paulo;Não Informado;Empregado;São Paulo;2,500",
            "janeiro/2019;Aposentadoria por Idade;000000;Zerados;Concessao Normal;01/01/1955;Feminino;Rural;02003-AL-Arapiraca;Não Informado;Segurado Especial;Alagoas;1",
        ],
        "latin-1",
    )


@pytest.fixture
def csv_2021(tmp_path):
    """UTF-8 com BOM, `CID_1`, e a coluna UF errada (D-030)."""
    return _csv(
        tmp_path,
        "concedidos_202101.csv",
        CAB_2021,
        [
            "202101;Auxílio Doenca Previdenciário;V299;V29.9 Motociclista Acid Trans Ne;Concessao Normal;01/01/1990;Masculino;Urbano;20100-SC-Mafra;Não Informado;Empregado;Alagoas;1",
            "202101;Auxílio Doenca Previdenciário;V134;V13.4 Ciclista;Concessao Normal;01/01/1990;Masculino;Urbano;13041-PB-Campina Grande;Não Informado;Empregado;Alagoas;1",
        ],
        "utf-8-sig",
    )


@pytest.fixture
def csv_2023(tmp_path):
    """latin-1, CID e nome numa coluna so, com `Tipo de Cálculo` no meio."""
    return _csv(
        tmp_path,
        "concedidos_202301.csv",
        CAB_2023,
        [
            "202301;Auxílio Doenca por Acidente do Trabalho                ;V29.8 Motociclista Outr Acid Transp Espec;Concessao Normal;01/01/1990;Masculino     ;Urbano  ;Rmi Informada;71035-SP-São Paulo                      ;Não Informado;Empregado          ;São Paulo          ;  1,500",
            "202301;Auxílio Doenca Previdenciário                ;V28   Motociclista Traum Acid Transp s/Colis;Concessao Normal;01/01/1990;Masculino     ;Urbano  ;Rmi Informada;71035-SP-São Paulo                      ;Não Informado;Autônomo           ;São Paulo          ;  1,000",
            "202301;Auxílio Doenca Previdenciário                ;V43.5 Ocupante Automovel;Concessao Normal;01/01/1990;Masculino     ;Urbano  ;Rmi Informada;71035-SP-São Paulo                      ;Não Informado;Autônomo           ;São Paulo          ;  1,000",
        ],
        "latin-1",
    )


@pytest.fixture
def xlsx_2025(tmp_path):
    """Linha de titulo, cabecalho duplicado (codigo/nome), especie numerica."""
    cab = [
        "APS", "APS", "Competência concessão", "Espécie", "Espécie", "CID", "CID", "Despacho",
        "Despacho", "Dt Nascimento", "Sexo.", "Clientela", "Mun Resid", "Vínculo dependentes",
        "Forma Filiação", "UF", " Qt SM RMI ", "Ramo Atividade", "Dt DCB", "Dt DDB", "Dt DIB",
        "País de Acordo Internacional", "Classificador PA",
    ]  # fmt: skip
    linhas = [
        ["CONCEDIDOS FEVEREIRO DE 2025"] + [None] * 22,
        cab,
        [
            "2001390",
            "02001390-Aps X",
            "202502",
            "31",
            "Auxílio Doenca Previdenciário",
            "V299",
            "V29.9 Motociclista Acid Trans Ne",
            "64",
            "Concessao",
            "1990-01-01",
            "Masculino",
            "Urbano",
            "71035-SP-São Paulo",
            "Não Informado",
            "Autônomo",
            "São Paulo",
            "1",
            "Comerciario",
            None,
            None,
            None,
            "{ñ class}",
            "Sem",
        ],  # fmt: skip
        [
            "2001390",
            "02001390-Aps X",
            "202502",
            "91",
            "Auxílio Doenca por Acidente do Trabalho",
            "V29",
            "V29   Motociclista Traum Outr Acid",
            "64",
            "Concessao",
            "1990-01-01",
            "Masculino",
            "Urbano",
            "31000-MG-Belo Horizonte",
            "Não Informado",
            "Empregado",
            "Minas Gerais",
            "3",
            "Comerciario",
            None,
            None,
            None,
            "{ñ class}",
            "Sem",
        ],  # fmt: skip
        [
            "2001390",
            "02001390-Aps X",
            "202502",
            "41",
            "Aposentadoria por Idade",
            "V299",
            "V29.9 Motociclista Acid Trans Ne",
            "64",
            "Concessao",
            "1950-01-01",
            "Masculino",
            "Urbano",
            "71035-SP-São Paulo",
            "Não Informado",
            "Empregado",
            "São Paulo",
            "1",
            "Comerciario",
            None,
            None,
            None,
            "{ñ class}",
            "Sem",
        ],  # fmt: skip
    ]
    caminho = tmp_path / "concedidos_202502.xlsx"
    pd.DataFrame(linhas).to_excel(caminho, index=False, header=False)
    return caminho


def test_2019_cid_em_duas_colunas_e_competencia_por_extenso(csv_2019):
    n = tr.normalizar(tr.ler(csv_2019), 2019, 1)
    assert n["cid"].tolist() == ["V234", "V299", None]
    assert n["grupo"].tolist() == ["motociclista", "motociclista", None]
    assert n["especie"].tolist() == [31, 91, 41]
    assert n["classe"].tolist() == ["previdenciario", "acidentario", None]
    assert n["qt_sm_rmi"].tolist() == pytest.approx([1.068, 2.5, 1.0])
    assert n["uf"].tolist() == ["AL", "SP", "AL"]


def test_2021_uf_vem_do_municipio_e_nao_da_coluna_uf(csv_2021):
    """A coluna UF diz Alagoas nas duas linhas; o municipio diz SC e PB."""
    n = tr.normalizar(tr.ler(csv_2021), 2021, 1)
    assert n["uf"].tolist() == ["SC", "PB"]
    assert n["grupo"].tolist() == ["motociclista", "ciclista"]


def test_2023_cid_com_nome_na_mesma_coluna_e_espacos(csv_2023):
    n = tr.normalizar(tr.ler(csv_2023), 2023, 1)
    assert n["cid"].tolist() == ["V298", "V28", "V435"]
    assert n["grupo"].tolist() == ["motociclista", "motociclista", "auto_placebo"]
    assert n["classe"].tolist() == ["acidentario", "previdenciario", "previdenciario"]
    assert n["forma_filiacao"].tolist() == ["Empregado", "Autônomo", "Autônomo"]
    assert n["qt_sm_rmi"].tolist() == pytest.approx([1.5, 1.0, 1.0])


def test_2025_xlsx_titulo_cabecalho_duplicado_e_especie_numerica(xlsx_2025):
    n = tr.normalizar(tr.ler(xlsx_2025), 2025, 2)
    assert n["especie"].tolist() == [31, 91, 41]
    assert n["cid"].tolist() == ["V299", "V29", "V299"]
    assert n["uf"].tolist() == ["SP", "MG", "SP"]
    assert n["qt_sm_rmi"].tolist() == pytest.approx([1.0, 3.0, 1.0])


def test_competencia_do_arquivo_diferente_do_indice_e_erro(csv_2023):
    with pytest.raises(ValueError, match="competencia"):
        tr.normalizar(tr.ler(csv_2023), 2023, 2)


def test_agregar_so_conta_incapacidade_nos_grupos_do_projeto(xlsx_2025):
    """Aposentadoria por idade com CID V29 e ruido, nao evento: fica de fora."""
    a = tr.agregar(tr.normalizar(tr.ler(xlsx_2025), 2025, 2))
    assert a["beneficios"].sum() == 2
    assert set(a["classe"]) == {"previdenciario", "acidentario"}
    sp = a[(a["uf"] == "SP") & (a["classe"] == "previdenciario")].iloc[0]
    assert sp["beneficios"] == 1 and sp["sm_rmi_total"] == pytest.approx(1.0)
    assert list(a.columns) == ["uf", "ano", "mes", "grupo", "classe", *tr.SOMAS]


def test_csv_que_nao_decodifica_falha_alto(tmp_path):
    caminho = tmp_path / "x.csv"
    caminho.write_bytes(b"\xff\xfe" + "Competência concessão;Espécie".encode("utf-16"))
    with pytest.raises(ValueError, match="sem as colunas"):
        tr.normalizar(tr.ler(caminho), 2020, 1)


def test_xlsx_sem_cabecalho_falha_alto(tmp_path):
    caminho = tmp_path / "sem.xlsx"
    pd.DataFrame([["a", "b"], ["c", "d"]]).to_excel(caminho, index=False, header=False)
    with pytest.raises(ValueError, match="cabecalho"):
        tr.ler(caminho)
