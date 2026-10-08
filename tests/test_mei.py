"""MEI de entrega (D-040): leitura do CNPJ, ponte de municipios, regra de quebra e grupos.

Nada toca a rede nem o SIH: o zip da Receita e o servidor WebDAV sao dublados.
"""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from vcemal import mei
from vcemal.extract import cnpj

INICIO_SERIE = "2014-01"
MESES = mei.meses(INICIO_SERIE, "2026-08")


def _serie(base: float, salto_em: str | None = None, depois: float = 0.0) -> np.ndarray:
    """Contagem mensal deterministica: `base` por mes, `depois` a partir de `salto_em`."""
    s = np.full(len(MESES), base)
    if salto_em:
        s[MESES.index(salto_em) :] = depois
    return s


def _quebra(*series) -> list[str]:
    q = mei.detectar_quebra(np.vstack(series), INICIO_SERIE)
    return [MESES[t] if t >= 0 else "" for t in q]


# --- regra de quebra -----------------------------------------------------------


def test_salto_e_detectado_ate_tres_meses_antes_dele():
    """A janela olha para a frente: a quebra pode antecipar o salto em ate metade dela."""
    (q,) = _quebra(_serie(1, "2018-06", 4))
    assert "2018-03" <= q <= "2018-06"


def test_serie_que_so_cresce_devagar_nao_quebra():
    crescendo = np.round(np.linspace(2, 4, len(MESES)))
    assert _quebra(crescendo) == [""]


def test_cidade_pequena_precisa_do_minimo_de_aberturas():
    """Sem nenhuma abertura antes, 4 em seis meses ainda e acaso; 5 ja e quebra."""
    quatro, cinco = np.zeros(len(MESES)), np.zeros(len(MESES))
    i = MESES.index("2020-03")
    quatro[i : i + 4] = 1
    cinco[i : i + 5] = 1
    assert _quebra(quatro, cinco) == ["", "2020-03"]


def test_salto_antes_de_2017_nao_e_tratamento_e_e_placebo():
    serie = _serie(1, "2016-03", 4)
    assert _quebra(serie) == [""], "salto de 2016 nao vira quebra na janela principal"
    p = mei.detectar_quebra(serie[None, :], INICIO_SERIE, inicio="2016-01", fim="2016-06")
    assert p[0] >= 0


def test_vale_so_a_primeira_quebra():
    s = _serie(1, "2018-06", 4)
    s[MESES.index("2022-01") :] = 16
    (q,) = _quebra(s)
    assert q < "2019-01"


def test_fim_alem_da_serie_nao_quebra_e_ancora_na_primeira_abertura():
    """Mes sem janela completa nao e avaliado; o salto no fim cai no mes em que comeca."""
    s = np.zeros(len(MESES))
    s[-3:] = 10  # salto nos tres ultimos meses da serie (2026-06 a 2026-08)
    q = mei.detectar_quebra(s[None, :], INICIO_SERIE, fim="2030-12")
    assert MESES[q[0]] == "2026-06"


# --- grupos de tratamento ------------------------------------------------------------

UNIVERSO = pd.DataFrame(
    {
        "municipio_ibge": [1, 2, 3, 4],
        "uf": ["PR", "PR", "SP", "SP"],
        "municipio": ["Pequena", "Quieta", "Media", "Capital"],
        "populacao_2022": [30_000, 25_000, 80_000, 2_000_000],
    }
)


def test_grupos_por_populacao_e_quebra():
    contagens = np.vstack(
        [
            _serie(0.2, "2019-07", 2),  # pequena, quebra
            np.zeros(len(MESES)),  # pequena, nunca abre nada
            _serie(1, "2018-06", 4),  # media, quebra
            _serie(40, "2017-06", 90),  # capital: coorte precoce mesmo com quebra
        ]
    )
    t = mei.tratamento(UNIVERSO, contagens, INICIO_SERIE).set_index("municipio")
    assert t.loc["Pequena", "grupo"] == "datado"
    assert t.loc["Pequena", "mes_tratamento"] == t.loc["Pequena", "mes_quebra"] != ""
    assert t.loc["Quieta", "grupo"] == "sem_quebra"
    assert t.loc["Quieta", "mes_tratamento"] == ""
    assert t.loc["Media", "grupo"] == "datado"
    assert t.loc["Capital", "grupo"] == "coorte_precoce"
    assert t.loc["Capital", "mes_tratamento"] == "", "acima do corte nao ha data fina"
    assert t.loc["Capital", "faixa"] == "250 mil+"
    assert t.loc["Quieta", "faixa"] == "20-50 mil"


def test_validar_contra_wayback():
    tabela = pd.DataFrame({"municipio_ibge": [1, 2, 3], "mes_quebra": ["2018-05", "", "2020-01"]})
    wayback = pd.DataFrame(
        {
            "municipio_ibge": ["1", "2", "3", "3"],
            "plataforma": ["rappi", "uber_eats", "ifood", "rappi"],
            "confianca": ["C", "C", "D", "C"],
            "data_max": ["2019-08", "2021-01", "2023-12", "2019-03"],
        }
    )
    v = mei.validar_contra_wayback(tabela, wayback)
    # 1: quebra antes da entrada (ok); 2: sem quebra (atraso); 3: quebra 10 meses depois (atraso)
    assert v["entradas_rappi_uber_c"] == 3
    assert v["atraso"] == pytest.approx(2 / 3)
    assert v["cobertura_ifood"] == 1.0


# --- contagem de aberturas ----------------------------------------------------------


def test_aberturas_so_matriz_cnae_principal_no_periodo_e_com_ponte():
    estab = pd.DataFrame(
        {
            "cnpj_basico": ["1", "2", "3", "4", "5", "6"],
            "matriz_filial": ["1", "2", "1", "1", "1", "1"],
            "data_inicio": ["20180310", "20180311", "20180312", "20120101", "20180301", "20180320"],
            "cnae_principal": ["5320202", "5320202", "4930202", "5320202", "5320202", "5320202"],
            "uf": ["PR", "PR", "PR", "PR", "EX", "PR"],
            "municipio_rf": ["7535", "7535", "7535", "7535", "9707", "7535"],
        }
    )
    ponte = pd.DataFrame({"uf": ["PR"], "municipio_rf": ["7535"], "municipio_ibge": [4106902]})
    a = mei.aberturas_mensais(estab, ponte, "2014-01", "2026-08")
    # conta 1 e 6; fica fora a filial (2), outro CNAE (3), antes do periodo (4), exterior (5)
    assert a.to_dict("records") == [{"municipio_ibge": 4106902, "mes": "2018-03", "aberturas": 2}]


def test_ponte_de_municipios_reporta_o_que_nao_casa():
    pares = pd.DataFrame({"uf": ["PR", "EX", "PR"], "municipio_rf": ["7535", "9707", "7535"]})
    nomes = {"7535": "CURITIBA", "9707": "EXTERIOR"}
    indice = {("PR", "CURITIBA"): 4106902}
    ponte, falta = mei.ponte_municipios(pares, nomes, indice)
    assert ponte.to_dict("records") == [
        {"uf": "PR", "municipio_rf": "7535", "municipio_ibge": 4106902}
    ]
    assert falta["nome_receita"].tolist() == ["EXTERIOR"]


# --- leitura do zip da Receita ------------------------------------------------------------


def _zip(tmp_path, nome: str, linhas: list[list[str]]):
    corpo = "\n".join(";".join(f'"{c}"' for c in linha) for linha in linhas) + "\n"
    caminho = tmp_path / nome
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("K3241.K03200Y0.D60912.ESTABELE", corpo.encode("latin-1"))
    return caminho


def _estab(cnpj_basico, principal, secundaria, municipio="7535", nome="LOJA"):
    linha = [""] * 30
    linha[0], linha[3], linha[4], linha[5] = cnpj_basico, "1", nome, "08"
    linha[10], linha[11], linha[12] = "20190415", principal, secundaria
    linha[19], linha[20] = "PR", municipio
    return linha


def test_filtrar_estabelecimentos_principal_ou_secundaria_em_latin1(tmp_path):
    arquivo = _zip(
        tmp_path,
        "Estabelecimentos0.zip",
        [
            _estab("11111111", "5320202", "", nome="ENTREGAS SÃO JOÃO"),
            _estab("22222222", "4930202", "5320202,5611201"),
            _estab("33333333", "5611201", "4930202"),
        ],
    )
    t = cnpj.filtrar_estabelecimentos(arquivo, "5320202")
    assert t["cnpj_basico"].tolist() == ["11111111", "22222222"]
    assert t["cnae_secundaria_tem"].tolist() == [False, True]
    assert t["situacao"].tolist() == ["08", "08"], "baixado fica"


def test_filtrar_simples_e_ler_municipios(tmp_path):
    simples = tmp_path / "Simples.zip"
    with zipfile.ZipFile(simples, "w") as z:
        z.writestr(
            "S",
            '"11111111";"S";"20190101";"00000000";"S";"20190415";"00000000"\n'
            '"99999999";"S";"20190101";"00000000";"N";"00000000";"00000000"\n',
        )
    s = cnpj.filtrar_simples(simples, {"11111111"})
    assert s.to_dict("records") == [
        {
            "cnpj_basico": "11111111",
            "opcao_mei": "S",
            "data_opcao_mei": "20190415",
            "data_exclusao_mei": "00000000",
        }
    ]
    municipios = tmp_path / "Municipios.zip"
    with zipfile.ZipFile(municipios, "w") as z:
        z.writestr("M", '"7535";"CURITIBA"\n"9701";"BRASÍLIA"\n'.encode("latin-1"))
    assert cnpj.ler_municipios(municipios) == {"7535": "CURITIBA", "9701": "BRASÍLIA"}


# --- download com retomada ----------------------------------------------------------------


class _Resposta(io.BytesIO):
    def __init__(self, corpo: bytes, status: int, cair_depois: int | None = None):
        super().__init__(corpo)
        self.status, self._cair = status, cair_depois

    def read(self, n=-1):
        if self._cair is not None and self.tell() >= self._cair:
            raise ConnectionError("conexao caiu")
        return super().read(min(n, 4) if n and n > 0 else n)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_baixar_retoma_de_onde_parou(tmp_path, monkeypatch):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("x.txt", "conteudo " * 50)
    corpo = buffer.getvalue()
    monkeypatch.setattr(cnpj, "listar", lambda caminho="": {"Simples.zip": len(corpo)})
    ranges = []

    def falso(pedido, timeout):
        inicio = int(pedido.headers["Range"].removeprefix("bytes=").rstrip("-"))
        ranges.append(inicio)
        if len(ranges) == 1:
            return _Resposta(corpo, 200, cair_depois=40)  # cai depois de 40 bytes
        return _Resposta(corpo[inicio:], 206)

    monkeypatch.setattr(cnpj.urllib.request, "urlopen", falso)
    final = cnpj.baixar("2026-09", "Simples.zip", tmp_path, dormir=lambda s: None)
    assert final.read_bytes() == corpo
    assert ranges[0] == 0 and ranges[1] == 40, "a segunda tentativa pede o resto"
    assert not (tmp_path / "Simples.zip.part").exists()
    assert cnpj.baixar("2026-09", "Simples.zip", tmp_path) == final, "zip integro nao rebaixa"
