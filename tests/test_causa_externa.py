"""Onde o filtro de caso procura V20-V29.

A norma do SIH poe a lesao (capitulo XIX) no diagnostico principal e a causa
externa (capitulo XX) no secundario. Procurar no principal devolve painel
vazio: zero AIH por ano de 2016 a 2023, contra 107-145 mil no campo certo.
Ver D-017.
"""

from __future__ import annotations

import pandas as pd

from vcemal import cid
from vcemal.transform.sih import (
    CAMPOS_CAUSA_EXTERNA,
    classificar,
    localizar_causa_externa,
    normalizar,
)


def _classificado(df: pd.DataFrame) -> pd.DataFrame:
    return classificar(normalizar(df))


def test_precedencia_termina_no_principal():
    """O principal entra por ultimo -- e permitido pela norma, mas e excecao."""
    assert CAMPOS_CAUSA_EXTERNA[0] == "DIAG_SECUN"
    assert CAMPOS_CAUSA_EXTERNA[-1] == "DIAG_PRINC"
    assert "DIAGSEC1" in CAMPOS_CAUSA_EXTERNA


def test_acha_causa_no_secundario(amostra_realista):
    out = _classificado(amostra_realista).set_index("N_AIH")
    assert out.loc["1", "causa_externa"] == "V234"
    assert out.loc["1", "campo_causa"] == "DIAGSEC1"
    assert out.loc["1", "grupo"] == "motociclista"


def test_lesao_no_principal_nao_descarta_a_aih(amostra_realista):
    """S720 no principal nao pode fazer a AIH sumir: a causa esta adiante."""
    out = _classificado(amostra_realista)
    assert "1" in set(out["N_AIH"]), "AIH com lesao no principal e causa no DIAGSEC1"


def test_acha_no_diag_secun_classico(amostra_realista):
    out = _classificado(amostra_realista).set_index("N_AIH")
    assert out.loc["2", "causa_externa"] == "V299"
    assert out.loc["2", "campo_causa"] == "DIAG_SECUN"


def test_varre_ate_diagsec2(amostra_realista):
    """Para no primeiro que CASA, nao no primeiro preenchido (S060 nao conta)."""
    out = _classificado(amostra_realista).set_index("N_AIH")
    assert out.loc["3", "causa_externa"] == "V134"
    assert out.loc["3", "campo_causa"] == "DIAGSEC2"
    assert out.loc["3", "grupo"] == "ciclista"


def test_principal_ainda_vale_quando_traz_o_v(amostra_realista):
    out = _classificado(amostra_realista).set_index("N_AIH")
    assert out.loc["4", "causa_externa"] == "V435"
    assert out.loc["4", "campo_causa"] == "DIAG_PRINC"


def test_sem_causa_externa_sai_do_escopo(amostra_realista):
    out = _classificado(amostra_realista)
    assert "5" not in set(out["N_AIH"])
    assert len(out) == 4


def test_localizar_ignora_campo_ausente():
    """Competencia antiga sem DIAGSEC1-9 nao pode quebrar a varredura."""
    df = pd.DataFrame({"DIAG_PRINC": ["V234"], "DIAG_SECUN": ["S720"]})
    codigo, origem = localizar_causa_externa(df)
    assert codigo.iloc[0] == "V234"
    assert origem.iloc[0] == "DIAG_PRINC"


def test_primeiro_que_casa_vence_o_primeiro_preenchido():
    df = pd.DataFrame({"DIAG_SECUN": ["S720"], "DIAGSEC1": ["T141"], "DIAG_PRINC": ["V293"]})
    codigo, origem = localizar_causa_externa(df)
    assert codigo.iloc[0] == "V293"
    assert origem.iloc[0] == "DIAG_PRINC"


def test_nenhum_campo_de_causa_presente():
    df = pd.DataFrame({"VAL_TOT": [1.0]})
    codigo, origem = localizar_causa_externa(df)
    assert codigo.isna().all()
    assert origem.isna().all()


def test_precedencia_entre_dois_codigos_validos():
    """Havendo dois V, vence o de maior precedencia -- regra fixa e testada."""
    df = pd.DataFrame({"DIAG_SECUN": ["V234"], "DIAGSEC1": ["V435"]})
    codigo, _ = localizar_causa_externa(df)
    assert codigo.iloc[0] == "V234"


def test_modulo_cid_expoe_a_mesma_regra():
    assert cid.primeira_causa_externa(["S720", "T141", "V234"]) == "V234"
    assert cid.primeira_causa_externa(["S720", "T141"]) is None
