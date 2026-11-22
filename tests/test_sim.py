"""SIM: operacionalizacao do D-053 (transform) e contrato do extrator (offline)."""

from __future__ import annotations

import ftplib

import pandas as pd
import pytest

from vcemal.extract import sim as ext
from vcemal.transform import sim as tr


def _do(**cols) -> pd.DataFrame:
    base = {
        "CAUSABAS": "V234",
        "CODMUNRES": "120040",
        "CODMUNOCOR": "120040",
        "DTOBITO": "07022015",
        "LOCOCOR": "4",
        "ACIDTRAB": "",
        "CIRCOBITO": "1",
        "SEXO": "1",
        "IDADE": "425",
    }
    n = max((len(v) for v in cols.values()), default=1)
    return pd.DataFrame({k: cols.get(k, [v] * n) for k, v in base.items()})


def test_filtrar_guarda_so_a_definicao_de_caso():
    df = _do(CAUSABAS=["V234", "I219", "V134", "V474", "X599"])
    df["OUTRA"] = "x"
    out = tr.filtrar(df)
    assert out["CAUSABAS"].tolist() == ["V234", "V134", "V474"]
    assert list(out.columns) == tr.COLS


def test_transito_segue_a_regra_do_quarto_digito():
    # V29.3 e nao-transito na estrutura terminal; V20.3 e transito na padrao.
    c = tr.classificar(tr.filtrar(_do(CAUSABAS=["V293", "V203", "V299", "V200"])))
    assert c["transito"].tolist() == [False, True, True, False]


def test_fora_de_saude_nao_conta_ignorado_nem_branco():
    lococor = ["1", "2", "3", "4", "5", "6", "9", ""]
    c = tr.classificar(tr.filtrar(_do(LOCOCOR=lococor)))
    assert c["fora_saude"].tolist() == [False, False, True, True, True, True, False, False]


def test_acidtrab_preenchido_e_so_1_ou_2():
    c = tr.classificar(tr.filtrar(_do(ACIDTRAB=["1", "2", "9", ""])))
    assert c["acidtrab_preenchido"].tolist() == [True, True, False, False]
    assert c["acidtrab_sim"].tolist() == [True, False, False, False]


def test_homem_18_39_le_a_unidade_da_idade():
    # 418 e 439 entram; 417, 440, 5xx (100+ anos), 325 (25 meses) e mulher nao.
    idade = ["418", "439", "417", "440", "518", "325", "425"]
    sexo = ["1", "1", "1", "1", "1", "1", "2"]
    c = tr.classificar(tr.filtrar(_do(IDADE=idade, SEXO=sexo)))
    assert c["homem_18_39"].tolist() == [True, True, False, False, False, False, False]


def test_agregar_por_municipio_e_mes_do_obito():
    df = _do(
        CAUSABAS=["V234", "V234", "V299", "V293", "V474", "V234", "V234"],
        CODMUNRES=["120040", "120040", "120040", "120040", "120040", "120000", "120040"],
        DTOBITO=["07022015", "28022015", "01032015", "01032015", "01032015", "01032015", "x"],
        LOCOCOR=["4", "1", "9", "4", "4", "4", "4"],
    )
    painel = tr.agregar(tr.classificar(tr.filtrar(df)))
    # V29.3 (nao-transito), V47 (auto), municipio ignorado e data invalida saem.
    assert painel.to_dict("records") == [
        {
            "municipio_res": "120040",
            "ano": 2015,
            "mes": 2,
            "obitos_moto_transito": 2,
            "obitos_moto_transito_fora_saude": 1,
        },
        {
            "municipio_res": "120040",
            "ano": 2015,
            "mes": 3,
            "obitos_moto_transito": 1,
            "obitos_moto_transito_fora_saude": 0,
        },
    ]


def test_h4_conta_preenchimento_e_nexo():
    df = _do(ACIDTRAB=["1", "2", "9", "1"], IDADE=["425", "425", "425", "450"])
    h4 = tr.h4_uf_ano(tr.classificar(tr.filtrar(df)), "AC")
    assert h4.to_dict("records") == [
        {
            "uf": "AC",
            "ano": 2015,
            "obitos_homem_18_39": 3,
            "acidtrab_preenchido": 2,
            "acidtrab_sim": 1,
        }
    ]


def test_coluna_ausente_segue_vazia():
    df = _do().drop(columns=["ACIDTRAB"])
    out = tr.filtrar(df)
    assert out["ACIDTRAB"].tolist() == [""]


# --- extrator: definitivo, depois preliminar, e so o 550 e "nao existe" -----


class _FTP:
    def __init__(self, existe: dict[str, set[str]], erro: Exception | None = None):
        self.existe, self.erro, self.dir = existe, erro, None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self):
        pass

    def voidcmd(self, cmd):
        pass

    def cwd(self, d):
        self.dir = d

    def size(self, nome):
        if self.erro:
            raise self.erro
        if nome not in self.existe.get(self.dir, set()):
            raise ftplib.error_perm("550 The system cannot find the file specified.")
        return 123

    def sendcmd(self, cmd):
        return "213 20260828163918"

    def retrbinary(self, cmd, escrever):
        escrever(b"dbc")


@pytest.fixture
def ftp(monkeypatch):
    def montar(existe, erro=None):
        monkeypatch.setattr(ext.ftplib, "FTP", lambda *a, **k: _FTP(existe, erro))

    return montar


def test_ano_definitivo_vem_do_definitivo(ftp, tmp_path):
    ftp({ext.FTP_DIR_DEFINITIVO: {"DOAC2024.dbc"}, ext.FTP_DIR_PRELIMINAR: {"DOAC2024.dbc"}})
    assert ext._baixar_ftp("DOAC2024.dbc", tmp_path / "x.dbc") == (
        ext.FTP_DIR_DEFINITIVO,
        123,
        "2026-08-28T16:39:18",
    )


def test_ano_ausente_do_definitivo_vem_do_preliminar(ftp, tmp_path):
    ftp({ext.FTP_DIR_PRELIMINAR: {"DOAC2025.dbc"}})
    diretorio, _, _ = ext._baixar_ftp("DOAC2025.dbc", tmp_path / "x.dbc")
    assert diretorio == ext.FTP_DIR_PRELIMINAR
    assert (tmp_path / "x.dbc").read_bytes() == b"dbc"


def test_ano_nao_publicado_e_none(ftp, tmp_path):
    ftp({})
    assert ext._baixar_ftp("DOAC2027.dbc", tmp_path / "x.dbc") is None
    assert not list(tmp_path.iterdir())


def test_outro_erro_do_servidor_sobe(ftp, tmp_path):
    ftp({}, erro=ftplib.error_perm("530 Login incorrect."))
    with pytest.raises(ftplib.error_perm):
        ext._baixar_ftp("DOAC2024.dbc", tmp_path / "x.dbc")
