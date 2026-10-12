"""Wayback (F3, tipo 3): indice, cache, leitura das listas e intervalo de entrada.

Nenhum teste toca a rede: o HTML e sintetico, e o download e dublado. O layout
real da pagina do iFood nao foi visto daqui (o Wayback recusa o ambiente de
nuvem), entao os testes cobrem os formatos plausiveis -- lista por estado,
`<select>`, UF no proprio item, cidades separadas por virgula -- e o que
importa mais: o que nao pode casar.
"""

from __future__ import annotations

import io
import json
import urllib.error

import pandas as pd
import pytest

from vcemal import cronologia as cro
from vcemal.extract import wayback as ew
from vcemal.transform import wayback as tw

UNIVERSO = [
    {"municipio_ibge": "4106902", "uf": "PR", "municipio": "Curitiba"},
    {"municipio_ibge": "4113700", "uf": "PR", "municipio": "Londrina"},
    {"municipio_ibge": "4115200", "uf": "PR", "municipio": "Maringá"},
    {"municipio_ibge": "4104808", "uf": "PR", "municipio": "Cascavel"},
    {"municipio_ibge": "2303501", "uf": "CE", "municipio": "Cascavel"},
    {"municipio_ibge": "1721000", "uf": "TO", "municipio": "Palmas"},
    {"municipio_ibge": "4117602", "uf": "PR", "municipio": "Palmas"},
    {"municipio_ibge": "3550308", "uf": "SP", "municipio": "São Paulo"},
    {"municipio_ibge": "3205002", "uf": "ES", "municipio": "Serra"},
    {"municipio_ibge": "2408102", "uf": "RN", "municipio": "Natal"},
]
INDICE = tw.construir_indice(UNIVERSO)
POR_CODIGO = {int(m["municipio_ibge"]): m for m in UNIVERSO}


@pytest.fixture(autouse=True)
def _lista_pequena(monkeypatch):
    """O minimo real (20 cidades) nao cabe num teste legivel."""
    monkeypatch.setattr(tw, "MINIMO_CIDADES", 2)


# --- indice do Wayback ---------------------------------------------------------


def test_e_a_pagina_aceita_variantes_e_recusa_pagina_vizinha():
    pagina = "entregador.ifood.com.br/cidades-atendidas"
    assert ew.e_a_pagina("https://entregador.ifood.com.br/cidades-atendidas/", pagina)
    assert ew.e_a_pagina("http://www.entregador.ifood.com.br/cidades-atendidas?utm=x", pagina)
    assert ew.e_a_pagina("http://entregador.ifood.com.br:80/cidades-atendidas", pagina)
    assert not ew.e_a_pagina("https://entregador.ifood.com.br/cidades-atendidas-sp", pagina)


def test_ler_cdx_filtra_status_e_pagina_e_ordena():
    linhas = [
        ["timestamp", "original", "statuscode", "digest"],
        ["20200101000000", "https://entregador.ifood.com.br/cidades-atendidas", "200", "B"],
        ["20190922023250", "https://entregador.ifood.com.br/cidades-atendidas/", "200", "A"],
        ["20190923000000", "https://entregador.ifood.com.br/cidades-atendidas", "301", "R"],
        ["20190924000000", "https://entregador.ifood.com.br/cidades-atendidas-x", "200", "X"],
    ]
    snaps = ew.ler_cdx(linhas, "entregador.ifood.com.br/cidades-atendidas")
    assert [s.digest for s in snaps] == ["A", "B"]
    assert snaps[0].mes == "2019-09"
    assert snaps[0].url.startswith("https://web.archive.org/web/20190922023250/")


def test_ler_cdx_vazio():
    assert ew.ler_cdx([], "x") == []


def test_listar_guarda_o_indice_e_le_offline(tmp_path, monkeypatch):
    resposta = [
        ["timestamp", "original", "statuscode", "digest"],
        ["20190922023250", "https://entregador.ifood.com.br/cidades-atendidas", "200", "A"],
    ]
    chamadas = []

    def falso(url, timeout):
        chamadas.append(url)
        return json.dumps(resposta).encode()

    monkeypatch.setattr(ew, "baixar", falso)
    pagina = "entregador.ifood.com.br/cidades-atendidas"
    assert len(ew.listar(pagina, cache=tmp_path)) == 1
    assert "matchType=prefix" in chamadas[0]
    assert len(ew.listar(pagina, cache=tmp_path, offline=True)) == 1
    assert len(chamadas) == 1, "offline nao vai a rede"


def test_raiz_do_dominio_e_consultada_exata_e_nao_por_prefixo(monkeypatch):
    """Por prefixo, `rappi.com.br/` traria o site inteiro: cada restaurante."""
    resposta = [
        ["timestamp", "original", "statuscode", "digest"],
        ["20190615000000", "https://www.rappi.com.br/", "200", "A"],
        ["20190616000000", "https://www.rappi.com.br/restaurantes", "200", "R"],
    ]
    chamadas = []

    def falso(url, timeout):
        chamadas.append(url)
        return json.dumps(resposta).encode()

    monkeypatch.setattr(ew, "baixar", falso)
    snaps = ew.listar("rappi.com.br/")
    assert "matchType=exact" in chamadas[0]
    assert [s.digest for s in snaps] == ["A"]


def test_offline_sem_indice_guardado_e_erro(tmp_path):
    with pytest.raises(FileNotFoundError):
        ew.listar("x", cache=tmp_path, offline=True)


def _snap(ts, digest):
    return ew.Snapshot(ts, "https://entregador.ifood.com.br/cidades-atendidas", digest)


def test_baixa_um_por_digest_e_reusa_o_cache(tmp_path, monkeypatch):
    baixados = []

    def falso(url, timeout):
        baixados.append(url)
        return b"<li>Curitiba</li>"

    monkeypatch.setattr(ew, "baixar", falso)
    snaps = [_snap("20190101000000", "A"), _snap("20190201000000", "A"), _snap("20190301", "B")]
    arquivos = ew.baixar_snapshots(snaps, tmp_path, pausa=0, dormir=lambda s: None)
    assert set(arquivos) == {"A", "B"}
    assert len(baixados) == 2, "conteudo repetido nao se baixa de novo"
    assert "20190101000000id_/" in baixados[0], "pede o HTML original, sem a barra do Wayback"
    ew.baixar_snapshots(snaps, tmp_path, pausa=0, dormir=lambda s: None)
    assert len(baixados) == 2, "o que esta em disco nao volta a rede"
    assert not list(tmp_path.glob("*.parcial"))


def _erro(code):
    return urllib.error.HTTPError("u", code, "x", {}, io.BytesIO())


def test_insiste_em_429_e_desiste_no_resto(monkeypatch):
    respostas = iter([_erro(429), _erro(503), b"ok"])

    def falso(url, timeout):
        r = next(respostas)
        if isinstance(r, Exception):
            raise r
        return r

    esperas = []
    monkeypatch.setattr(ew, "baixar", falso)
    assert ew._baixar_com_paciencia("u", dormir=esperas.append) == b"ok"
    assert esperas == list(ew.ESPERAS[:2])

    monkeypatch.setattr(ew, "baixar", lambda url, timeout: (_ for _ in ()).throw(_erro(404)))
    with pytest.raises(urllib.error.HTTPError):
        ew._baixar_com_paciencia("u", dormir=lambda s: None)


def test_429_sem_fim_sobe_em_vez_de_virar_snapshot_vazio(monkeypatch):
    monkeypatch.setattr(ew, "baixar", lambda url, timeout: (_ for _ in ()).throw(_erro(429)))
    with pytest.raises(urllib.error.HTTPError):
        ew._baixar_com_paciencia("u", dormir=lambda s: None)


# --- leitura da lista ------------------------------------------------------------


def test_lista_agrupada_por_estado():
    html = """
    <h2>Paraná</h2><ul><li>Curitiba</li><li>Londrina</li><li>Cascavel</li><li>Palmas</li></ul>
    <h2>Ceará</h2><ul><li>Cascavel</li></ul>
    """
    leitura = tw.ler(html, INDICE)
    assert set(leitura.municipios) == {4106902, 4113700, 4104808, 4117602, 2303501}
    assert leitura.ambiguos == []


def test_uf_no_proprio_item_em_varios_formatos():
    html = """<select><option>Palmas - TO</option><option>Cascavel/CE</option>
    <option>Maringá (PR)</option><option>Londrina, PR</option></select>"""
    leitura = tw.ler(html, INDICE)
    assert set(leitura.municipios) == {1721000, 2303501, 4115200, 4113700}


def test_homonimo_sem_uf_nao_casa_com_ninguem():
    leitura = tw.ler("<li>Curitiba</li><li>Palmas</li><li>Cascavel</li>", INDICE)
    assert set(leitura.municipios) == {4106902}
    assert leitura.ambiguos == ["Palmas", "Cascavel"]


def test_titulo_de_estado_nao_recusa_nome_unico():
    """Um "SP" solto na pagina nao pode apagar Curitiba por estar "em SP"."""
    leitura = tw.ler("<p>SP</p><li>Curitiba</li><li>Londrina</li>", INDICE)
    assert {4106902, 4113700} <= set(leitura.municipios)


def test_uf_explicita_que_nao_bate_e_homonimo_pequeno():
    leitura = tw.ler("<li>Curitiba - SC</li><li>Londrina</li>", INDICE)
    assert 4106902 not in leitura.municipios
    assert "Curitiba - SC" in leitura.sem_par


def test_casa_o_item_inteiro_nunca_substring():
    html = """<li>Serra Talhada</li><li>Natal: horário especial de feriado</li>
    <li>Curitiba</li><li>Londrina</li>"""
    leitura = tw.ler(html, INDICE)
    assert 3205002 not in leitura.municipios, "Serra nao casa em Serra Talhada"
    assert 2408102 not in leitura.municipios, "Natal nao casa em aviso de feriado"


def test_cidades_separadas_por_virgula_e_texto_de_script_ignorado():
    html = """<script>var c = "Natal";</script><style>.Serra{}</style>
    <p>Curitiba, Londrina, Maringá</p>"""
    leitura = tw.ler(html, INDICE)
    assert set(leitura.municipios) == {4106902, 4113700, 4115200}


def test_apostrofo_sem_espaco_e_grafia_alternativa_casam():
    """A lista de 2019 escreve "Santa Barbara Doeste", "Dias Davila", "Açu" e "Santa Isabel"."""
    universo = UNIVERSO + [
        {"municipio_ibge": "3545803", "uf": "SP", "municipio": "Santa Bárbara d'Oeste"},
        {"municipio_ibge": "2910057", "uf": "BA", "municipio": "Dias d'Ávila"},
        {"municipio_ibge": "2400208", "uf": "RN", "municipio": "Assú"},
        {"municipio_ibge": "1506500", "uf": "PA", "municipio": "Santa Izabel do Pará"},
    ]
    html = """<li>Santa Barbara Doeste</li><li>Santa Bárbara d'Oeste</li>
    <li>Dias Davila</li><li>Açu</li><li>Santa Isabel do Pará</li>"""
    leitura = tw.ler(html, tw.construir_indice(universo))
    assert set(leitura.municipios) == {3545803, 2910057, 2400208, 1506500}
    assert leitura.sem_par == []


def test_lista_de_termos_do_entregador_uf_antes_de_cada_cidade():
    """Formato da lista do iFood de 2023 em diante: sigla, cidade, sigla, cidade."""
    universo = UNIVERSO + [
        {"municipio_ibge": "2900702", "uf": "BA", "municipio": "Alagoinhas"},
        {"municipio_ibge": "4317103", "uf": "RS", "municipio": "Sant'Ana do Livramento"},
    ]
    html = """<p>PR</p><p>CASCAVEL</p><p>CE</p><p>CASCAVEL</p><p>BA</p><p>ALAGOINHAS_BA</p>
    <p>RS</p><p>SANTANA DO LIVRAMENTO</p><p>RJ</p><p>RIO – BARRA</p>"""
    leitura = tw.ler(html, tw.construir_indice(universo))
    assert set(leitura.municipios) == {4104808, 2303501, 2900702, 4317103}
    assert leitura.ambiguos == []
    assert leitura.sem_par == ["RIO – BARRA"]


def test_sao_paulo_e_titulo_e_capital_ao_mesmo_tempo():
    leitura = tw.ler("<h3>São Paulo</h3><li>Curitiba</li>", INDICE)
    assert 3550308 in leitura.municipios


def test_snapshot_sem_lista_nao_e_legivel():
    assert not tw.ler("<div id='app'></div><p>Carregando...</p>", INDICE).legivel


# --- intervalo -------------------------------------------------------------------


def _tl(*snaps):
    return [
        (ts, f"https://web.archive.org/web/{ts}/entregador.ifood.com.br/cidades-atendidas", cods)
        for ts, cods in snaps
    ]


CWB, LDA, MGA = 4106902, 4113700, 4115200


def test_intervalo_entre_o_ultimo_sem_e_o_primeiro_com():
    tl = _tl(
        ("20190922000000", {CWB: "Curitiba"}),
        ("20191201000000", {CWB: "Curitiba"}),
        ("20200301000000", {CWB: "Curitiba", LDA: "Londrina"}),
    )
    linhas = {int(r["municipio_ibge"]): r for r in tw.intervalos("ifood", tl, POR_CODIGO, "x")}
    lda = linhas[LDA]
    assert (lda["data_min"], lda["data_max"], lda["confianca"]) == ("2019-12", "2020-03", "C")
    assert lda["url"].startswith("https://web.archive.org/web/20200301000000/")
    assert lda["trecho"] == "Londrina"
    assert "20191201 e 20200301" in lda["fonte"]


def test_presente_no_primeiro_snapshot_e_censura_a_esquerda():
    tl = _tl(("20190922000000", {CWB: "Curitiba"}), ("20200101000000", {CWB: "Curitiba"}))
    (cwb,) = tw.intervalos("ifood", tl, POR_CODIGO, "x")
    assert (cwb["data_min"], cwb["data_max"], cwb["confianca"]) == ("2018-01", "2019-09", "D")
    assert "primeiro snapshot legivel" in cwb["observacao"]


def test_intervalo_largo_e_d():
    tl = _tl(("20190101000000", {CWB: "C"}), ("20200201000000", {CWB: "C", MGA: "Maringá"}))
    mga = next(
        r for r in tw.intervalos("ifood", tl, POR_CODIGO, "x") if r["municipio_ibge"] == "4115200"
    )
    assert mga["confianca"] == "D"


def test_sumico_posterior_vai_para_observacao_e_nao_vira_saida():
    tl = _tl(
        ("20190101000000", {CWB: "C"}),
        ("20190301000000", {CWB: "C", LDA: "L"}),
        ("20190501000000", {CWB: "C"}),
        ("20190701000000", {CWB: "C", LDA: "L"}),
    )
    linhas = tw.intervalos("ifood", tl, POR_CODIGO, "x")
    lda = next(r for r in linhas if r["municipio_ibge"] == str(LDA))
    assert lda["data_max"] == "2019-03", "vale a primeira aparicao"
    assert "ausente em 1 snapshot" in lda["observacao"]
    assert all(r["evento"] == "entrada" for r in linhas)


def test_snapshot_depois_da_saida_nacional_nao_data_entrada():
    """Uber Eats saiu em 2022-03: a pagina seguiu no ar, mas nao e entrada."""
    tl = _tl(
        ("20220101000000", {CWB: "Curitiba"}),
        ("20230601000000", {CWB: "Curitiba", LDA: "Londrina"}),
    )
    linhas = tw.intervalos("uber_eats", tl, POR_CODIGO, "x")
    assert [r["municipio_ibge"] for r in linhas] == [str(CWB)]


def test_salto_de_cidades_novas_fica_d_com_aviso(monkeypatch):
    """Lista que passa de polos a regioes metropolitanas nao e rollout de dois meses."""
    monkeypatch.setattr(tw, "SALTO_MINIMO", 2)
    tl = _tl(
        ("20201101000000", {CWB: "Curitiba"}),
        ("20210101000000", {CWB: "Curitiba", LDA: "Londrina", MGA: "Maringá"}),
    )
    linhas = {int(r["municipio_ibge"]): r for r in tw.intervalos("ifood", tl, POR_CODIGO, "x")}
    assert linhas[LDA]["data_max"] == "2021-01"
    assert linhas[LDA]["confianca"] == "D", "intervalo curto, mas num salto"
    assert "salto de 2 cidades" in linhas[LDA]["observacao"]


def test_linhas_passam_na_validacao_da_planilha():
    tl = _tl(
        ("20190922000000", {CWB: "Curitiba"}),
        ("20200301000000", {CWB: "Curitiba", LDA: "Londrina"}),
    )
    linhas = tw.intervalos("ifood", tl, POR_CODIGO, "2026-10-04")
    cro.validar(linhas)
    assert {r["codificador"] for r in linhas} == {"W"}
    assert {r["tipo_evidencia"] for r in linhas} == {3}


def test_sem_snapshot_legivel_nao_ha_linha():
    assert tw.intervalos("ifood", [], POR_CODIGO, "x") == []


# --- ponta a ponta, do cache a tabela --------------------------------------------


def test_subcomando_offline_do_cache_a_tabela(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "cronologia_script", Path(__file__).parents[1] / "scripts" / "cronologia.py"
    )
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)

    universo = tmp_path / "universo.csv"
    pd.DataFrame(UNIVERSO).to_csv(universo, index=False)
    monkeypatch.setattr(ew, "PAGINAS", {"ifood": ew.PAGINAS["ifood"]})
    pagina = ew.PAGINAS["ifood"][0]
    cache = tmp_path / "cache" / "ifood" / ew._caminho(pagina).replace("/", "_")
    cache.mkdir(parents=True)
    original = f"https://{pagina}"
    indice = [
        ["timestamp", "original", "statuscode", "digest"],
        ["20190922000000", original, "200", "A"],
        ["20191201000000", original, "200", "A"],
        ["20200115000000", original, "200", "V"],  # pagina carregada por JavaScript
        ["20200301000000", original, "200", "B"],
    ]
    (cache / "cdx.json").write_text(json.dumps(indice))
    (cache / "A.html").write_text("<li>Curitiba</li><li>Maringá</li>")
    (cache / "V.html").write_text("<div id='app'></div>")
    (cache / "B.html").write_text(
        "<li>Curitiba</li><li>Maringá</li><li>Londrina</li><li>Palmas</li>"
    )

    saida = tmp_path / "saida"
    rc = script.main(
        [
            "wayback",
            "--offline",
            "--universo",
            str(universo),
            "--cache",
            str(tmp_path / "cache"),
            "--saida",
            str(saida),
        ]
    )
    assert rc == 0
    tab = pd.read_csv(saida / "cronologia_wayback.csv", dtype=str).set_index("municipio_ibge")
    assert tab.loc[str(LDA), "data_min"] == "2019-12", (
        "o snapshot sem lista nao conta como ausencia"
    )
    assert tab.loc[str(LDA), "data_max"] == "2020-03"
    snaps = pd.read_csv(saida / "wayback_snapshots.csv")
    assert snaps["legivel"].tolist() == [True, True, False, True]
    nao = pd.read_csv(saida / "wayback_nao_casados.csv")
    assert ("ambiguo", "Palmas") in set(zip(nao["tipo"], nao["item"], strict=True))


def test_snapshot_anterior_a_frota_propria_e_ignorado():
    """iFood antes de 2018 e marketplace (D-020): a lista de 2017 nao data nada."""
    tl = _tl(("20171101000000", {CWB: "Curitiba"}), ("20180601000000", {CWB: "Curitiba"}))
    (cwb,) = tw.intervalos("ifood", tl, POR_CODIGO, "x")
    assert (cwb["data_min"], cwb["data_max"]) == ("2018-01", "2018-06")
    cro.validar([cwb])
