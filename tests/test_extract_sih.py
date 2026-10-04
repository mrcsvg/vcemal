"""Contrato do extrator do SIH contra o PySUS 2.x. Offline: o PySUS e dublado."""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal.extract import sih


class _Arquivo:
    """Arquivo do catalogo. `group` nulo de proposito: e assim que vem (D-034)."""

    def __init__(self, basename: str):
        self.basename = basename
        self.name = basename
        self.group = None
        self.year = None
        self.month = None
        self.state = None


class _Baixados:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    def to_dataframe(self) -> pd.DataFrame:
        return self._df


class _Catalogo(list):
    """FileBag dublado: guarda quais indices foram pedidos no download."""

    def __init__(self, nomes: list[str], df: pd.DataFrame | None = None):
        super().__init__(_Arquivo(n) for n in nomes)
        self._df = df if df is not None else pd.DataFrame({"DIAG_PRINC": ["V232"]})
        self.indices_baixados: list[int] | None = None

    def download(self, indexes=None):
        self.indices_baixados = indexes
        return _Baixados(self._df)


@pytest.fixture(autouse=True)
def sem_ftp(monkeypatch):
    """Nenhum teste vai ao FTP. Por padrao, o mes tambem nao existe la."""
    pedidos: list[tuple[str, int, int]] = []

    def falso(uf, ano, mes):
        pedidos.append((uf, ano, mes))
        return None

    monkeypatch.setattr(sih, "baixar_da_origem", falso)
    return pedidos


@pytest.fixture
def pysus_dublado(monkeypatch):
    """Substitui a funcao do PySUS. Devolve (registro de chamadas, catalogo mutavel)."""
    registro: list[dict] = []
    estado: dict[str, _Catalogo] = {}

    def falso(uf, ano, mes, **kw):
        registro.append({"uf": uf, "ano": ano, "mes": mes, **kw})
        return estado["catalogo"]

    monkeypatch.setattr(sih, "_sih", lambda: falso)
    return registro, estado


QUATRO_GRUPOS = ["ERAC1508.parquet", "RDAC1508.parquet", "RJAC1508.parquet", "SPAC1508.parquet"]


def test_consulta_o_catalogo_sem_baixar_e_nunca_filtra_por_group(pysus_dublado):
    """Regressao do D-034: `group` vem nulo no catalogo e filtrar por ele perde arquivo."""
    registro, estado = pysus_dublado
    estado["catalogo"] = _Catalogo(QUATRO_GRUPOS)

    sih.baixar_mes("AC", 2015, 8)

    assert len(registro) == 1
    chamada = registro[0]
    assert chamada["download"] is False, "o catalogo tem que ser consultado sem baixar"
    assert "group" not in chamada, "filtrar por group perde competencias (D-034)"


def test_baixa_so_o_arquivo_rd_e_nao_os_outros_tres_grupos(pysus_dublado):
    _, estado = pysus_dublado
    catalogo = _Catalogo(QUATRO_GRUPOS)
    estado["catalogo"] = catalogo

    df = sih.baixar_mes("AC", 2015, 8)

    assert catalogo.indices_baixados == [1], "o RD e o segundo da lista neste catalogo"
    assert len(df) == 1


def test_reconhece_o_rd_por_nome_mesmo_com_group_nulo():
    assert sih.e_arquivo_rd(_Arquivo("RDAC1508.parquet"))
    assert sih.e_arquivo_rd(_Arquivo("rdac1508.parquet"))
    assert not sih.e_arquivo_rd(_Arquivo("ERAC1508.parquet"))
    assert not sih.e_arquivo_rd(_Arquivo("SPAC1508.parquet"))


def test_competencia_nao_publicada_vira_none_e_nao_excecao(pysus_dublado):
    _, estado = pysus_dublado
    estado["catalogo"] = _Catalogo([])

    assert sih.baixar_mes("AC", 2026, 12) is None


def test_competencia_sem_rd_vira_none_mesmo_com_outros_grupos(pysus_dublado):
    _, estado = pysus_dublado
    estado["catalogo"] = _Catalogo(["ERAC1508.parquet", "SPAC1508.parquet"])

    assert sih.baixar_mes("AC", 2015, 8) is None


def test_rd_que_baixa_vazio_vira_none(pysus_dublado):
    _, estado = pysus_dublado
    estado["catalogo"] = _Catalogo(["RDAC1508.parquet"], df=pd.DataFrame())

    assert sih.baixar_mes("AC", 2015, 8) is None


def test_erro_de_rede_sobe_em_vez_de_virar_competencia_vazia(monkeypatch):
    """Falha de rede nao pode se disfarcar de 'mes sem dado' e sumir do painel."""

    def explode(*a, **kw):
        raise ConnectionError("ftp fora do ar")

    monkeypatch.setattr(sih, "_sih", lambda: explode)
    with pytest.raises(ConnectionError):
        sih.baixar_mes("PR", 2023, 1)


def test_caminho_do_bruto_particiona_por_uf_ano_mes():
    caminho = sih.caminho_do_bruto("PR", 2023, 1)
    assert caminho.parts[-4:] == ("uf=PR", "ano=2023", "mes=01", "parte.parquet")


def test_salvar_bruto_grava_no_caminho_que_a_retomada_procura(tmp_path, monkeypatch):
    monkeypatch.setattr(sih, "RAW_SIH", tmp_path)
    df = pd.DataFrame({"N_AIH": ["1"], "DIAG_PRINC": ["V232"]})

    destino = sih.salvar_bruto(df, "PR", 2023, 1)

    assert destino == sih.caminho_do_bruto("PR", 2023, 1)
    assert destino.exists()
    assert pd.read_parquet(destino).equals(df)


def test_meses_inclui_as_duas_pontas():
    assert sih.meses("2023-11", "2024-02") == [(2023, 11), (2023, 12), (2024, 1), (2024, 2)]


# --- download por ano (D-035) ---------------------------------------------


def test_mes_do_arquivo_le_o_mes_do_nome():
    assert sih.mes_do_arquivo("RDDF1509.parquet") == 9
    assert sih.mes_do_arquivo("rdac2301.parquet") == 1
    assert sih.mes_do_arquivo("RDSP1512.parquet") == 12


@pytest.mark.parametrize("ruim", ["ERDF1509.parquet", "RDDF15.parquet", "qualquer.txt", ""])
def test_mes_do_arquivo_recusa_nome_fora_do_padrao(ruim):
    assert sih.mes_do_arquivo(ruim) is None


class _Local:
    def __init__(self, basename: str, path: str):
        self.basename = basename
        self.name = basename
        self.path = path


class _CatalogoAno(_Catalogo):
    def download(self, indexes=None):
        self.indices_baixados = indexes
        return [_Local(self[i].basename, f"/cache/{self[i].basename}") for i in indexes]


def test_baixar_ano_pede_os_doze_meses_numa_consulta_so(pysus_dublado):
    """O ganho do D-035: uma consulta ao catalogo por ano, nao doze."""
    registro, estado = pysus_dublado
    estado["catalogo"] = _CatalogoAno([f"RDDF15{m:02d}.parquet" for m in range(1, 13)])

    caminhos = sih.baixar_ano("DF", 2015)

    assert len(registro) == 1
    assert registro[0]["ano"] == [2015]
    assert registro[0]["mes"] == list(range(1, 13))
    assert registro[0]["download"] is False
    assert sorted(caminhos) == list(range(1, 13))
    assert caminhos[9].name == "RDDF1509.parquet"


def test_baixar_ano_ignora_os_outros_grupos(pysus_dublado):
    _, estado = pysus_dublado
    catalogo = _CatalogoAno(["RDDF1501.parquet", "ERDF1501.parquet", "SPDF1501.parquet"])
    estado["catalogo"] = catalogo

    caminhos = sih.baixar_ano("DF", 2015)

    assert catalogo.indices_baixados == [0]
    assert list(caminhos) == [1]


def test_baixar_ano_sem_rd_devolve_vazio(pysus_dublado):
    _, estado = pysus_dublado
    estado["catalogo"] = _CatalogoAno(["ERDF1501.parquet"])

    assert sih.baixar_ano("DF", 2015) == {}


# --- o que falta no espelho vem do FTP (D-036) -----------------------------


def test_baixar_ano_busca_no_ftp_o_mes_ausente_do_espelho(pysus_dublado, sem_ftp, monkeypatch):
    """Regressao do D-036: DF 2016-04 existe no DATASUS e nao no espelho."""
    _, estado = pysus_dublado
    estado["catalogo"] = _CatalogoAno(
        [f"RDDF16{m:02d}.parquet" for m in range(1, 13) if m != 4] + ["ERDF1604.parquet"]
    )
    recuperado = sih.RAW_SIH_ORIGEM / "RDDF1604.parquet"

    def origem(uf, ano, mes):
        sem_ftp.append((uf, ano, mes))
        return recuperado

    monkeypatch.setattr(sih, "baixar_da_origem", origem)

    caminhos = sih.baixar_ano("DF", 2016)

    assert sem_ftp == [("DF", 2016, 4)], "so o mes que falta vai ao FTP"
    assert sorted(caminhos) == list(range(1, 13))
    assert caminhos[4] == recuperado


def test_baixar_ano_sem_rd_no_espelho_tenta_o_ftp_nos_meses_pedidos(pysus_dublado, sem_ftp):
    _, estado = pysus_dublado
    estado["catalogo"] = _CatalogoAno(["ERDF1601.parquet"])

    assert sih.baixar_ano("DF", 2016, [3, 7]) == {}
    assert sem_ftp == [("DF", 2016, 3), ("DF", 2016, 7)]


def test_baixar_ano_nao_vai_ao_ftp_quando_o_espelho_tem_tudo(pysus_dublado, sem_ftp):
    _, estado = pysus_dublado
    estado["catalogo"] = _CatalogoAno([f"RDDF15{m:02d}.parquet" for m in range(1, 13)])

    sih.baixar_ano("DF", 2015)

    assert sem_ftp == []


def test_nome_rd_segue_o_padrao_do_datasus():
    assert sih.nome_rd("df", 2016, 4) == "RDDF1604.dbc"
    assert sih.nome_rd("SP", 2025, 12, "parquet") == "RDSP2512.parquet"


def test_baixar_da_origem_mes_nao_publicado_vira_none(tmp_path, monkeypatch):
    monkeypatch.undo()  # desfaz o `sem_ftp` para testar a funcao de verdade
    monkeypatch.setattr(sih, "RAW_SIH_ORIGEM", tmp_path)
    monkeypatch.setattr(sih, "_baixar_ftp", lambda nome, destino: False)

    assert sih.baixar_da_origem("DF", 2026, 12) is None


def test_baixar_da_origem_converte_e_apaga_o_dbc(tmp_path, monkeypatch):
    monkeypatch.undo()
    monkeypatch.setattr(sih, "RAW_SIH_ORIGEM", tmp_path)

    def ftp(nome, destino):
        destino.write_bytes(b"dbc")
        return True

    def converter(dbc):
        saida = dbc.with_suffix(".parquet")
        saida.write_bytes(b"pq")
        return saida

    monkeypatch.setattr(sih, "_baixar_ftp", ftp)
    monkeypatch.setattr(sih, "_dbc_para_parquet", converter)

    caminho = sih.baixar_da_origem("DF", 2016, 4)

    assert caminho == tmp_path / "RDDF1604.parquet"
    assert caminho.exists()
    assert not (tmp_path / "RDDF1604.dbc").exists()


def test_baixar_da_origem_nao_volta_a_rede_se_ja_convertido(tmp_path, monkeypatch):
    monkeypatch.undo()
    monkeypatch.setattr(sih, "RAW_SIH_ORIGEM", tmp_path)
    (tmp_path / "RDDF1604.parquet").write_bytes(b"pq")

    def explode(*a):
        raise AssertionError("nao devia ir ao FTP")

    monkeypatch.setattr(sih, "_baixar_ftp", explode)

    assert sih.baixar_da_origem("DF", 2016, 4) == tmp_path / "RDDF1604.parquet"


def test_erro_de_ftp_que_nao_e_550_sobe(tmp_path, monkeypatch):
    """Arquivo inexistente e None; qualquer outra recusa do servidor e erro."""

    class _FTP:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self):
            pass

        def cwd(self, d):
            pass

        def retrbinary(self, cmd, cb):
            raise sih.ftplib.error_perm(self.resposta)

    monkeypatch.setattr(sih.ftplib, "FTP", _FTP)

    _FTP.resposta = "550 No such file"
    assert sih._baixar_ftp("RDDF2612.dbc", tmp_path / "RDDF2612.dbc") is False

    _FTP.resposta = "530 Login incorrect"
    with pytest.raises(sih.ftplib.error_perm):
        sih._baixar_ftp("RDDF1604.dbc", tmp_path / "RDDF1604.dbc")
    assert list(tmp_path.iterdir()) == [], "download parcial nao pode ficar para tras"
