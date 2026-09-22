"""Testes da definicao de caso e da agregacao do painel."""

from __future__ import annotations

import pandas as pd

from vcemal.transform.sih import agregar, classificar, normalizar


def _classificado(df: pd.DataFrame) -> pd.DataFrame:
    return classificar(normalizar(df))


def test_descarta_fora_do_escopo(amostra):
    out = _classificado(amostra)
    assert len(out) == 4, "S720 nao e causa externa de transporte, deve sair"


def test_grupos(amostra):
    out = _classificado(amostra).set_index("DIAG_PRINC")
    assert out.loc["V234", "grupo"] == "motociclista"
    assert out.loc["V134", "grupo"] == "ciclista"
    assert out.loc["V435", "grupo"] == "auto_placebo"


def test_quarto_digito_separa_condutor(amostra):
    out = _classificado(amostra).set_index("DIAG_PRINC")
    assert out.loc["V234", "condutor_transito"], ".4 = condutor em transito"
    assert not out.loc["V285", "condutor_transito"], ".5 = passageiro"
    assert out.loc["V285", "em_transito"]


def test_nexo_ocupacional(amostra):
    out = _classificado(amostra)
    assert out["nexo_ocupacional"].sum() == 2, "CAR_INT 03 e 04"


def test_agregacao_nao_perde_aih(amostra):
    out = _classificado(amostra)
    painel = agregar(out, "PR", 2023, 1)
    assert painel["internacoes"].sum() == len(out)


def test_estrutura_terminal_nao_vira_transito(amostra_quarto_digito):
    """V29.3/V19.3/V49.3 sao nao-transito explicito no CID-10."""
    out = _classificado(amostra_quarto_digito).set_index("DIAG_PRINC")
    for codigo in ("V293", "V193", "V493"):
        assert not out.loc[codigo, "em_transito"], f"{codigo} e nao-transito"
    assert out.loc["V296", "em_transito"], "V29.6 e transito, so existe na terminal"
    assert not out.loc["V298", "em_transito"], "V29.8 nao afirma transito"


def test_estrutura_padrao_conta_embarque(amostra_quarto_digito):
    out = _classificado(amostra_quarto_digito).set_index("DIAG_PRINC")
    assert out.loc["V233", "em_transito"]
    assert out.loc["V233", "embarque_desembarque"]
    assert not out.loc["V234", "embarque_desembarque"]
    assert not out.loc["V293", "embarque_desembarque"], "nao se aplica a terminal"


def test_nao_transito_fica_no_painel_mas_fora_do_transito(amostra_quarto_digito):
    """A AIH nao some -- so nao conta como transito. O filtro e do desfecho."""
    out = _classificado(amostra_quarto_digito)
    assert len(out) == len(amostra_quarto_digito)
    # transito: V233 V234 V235 V239 (padrao) + V294 V296 V299 (terminal)
    assert out["em_transito"].sum() == 7
    assert out["condutor_transito"].sum() == 2  # V234 e V294


def test_categoria_terminal_marcada(amostra_quarto_digito):
    out = _classificado(amostra_quarto_digito).set_index("DIAG_PRINC")
    assert out.loc["V293", "categoria_terminal"]
    assert not out.loc["V233", "categoria_terminal"]


def test_classificar_sobrevive_a_coluna_ausente(amostra):
    """Competencia antiga sem UTI_MES_TO nao pode derrubar o pipeline."""
    sem_uti = normalizar(amostra).drop(columns=["UTI_MES_TO", "MORTE"])
    out = classificar(sem_uti)
    assert not out["uti"].any()
    assert not out["obito"].any()


def test_agregacao_soma_por_municipio_e_grupo(amostra):
    painel = agregar(_classificado(amostra), "PR", 2023, 1)
    assert set(painel["municipio_res"]) == {"410690", "355030"}
    moto = painel[painel["grupo"] == "motociclista"]
    assert moto["internacoes"].sum() == 2
    assert moto["obitos"].sum() == 1
    assert moto["internacoes_uti"].sum() == 1
    assert moto["val_tot"].sum() == 9600.0


def test_flags_sao_bool_puro(amostra_quarto_digito):
    """Flag como object ou boolean nulavel quebra soma e filtro rio abaixo."""
    out = _classificado(amostra_quarto_digito)
    for coluna in ("em_transito", "condutor_transito", "embarque_desembarque", "uti", "obito"):
        assert out[coluna].dtype == bool, coluna


def test_perfil_demografico_e_cruzamento_nao_marginal(amostra):
    """H3 (D-023) precisa do cruzamento: as marginais nao o reconstroem."""
    painel = agregar(_classificado(amostra), "PR", 2023, 1)
    for coluna in ("homem_18_39", "condutor_homem_18_39"):
        assert coluna in painel.columns
    # V234: homem de 28, condutor -> entra nos dois
    cwb = painel[(painel["municipio_res"] == "410690") & (painel["grupo"] == "motociclista")]
    assert cwb["homem_18_39"].sum() == 2, "V234 (28) e V285 (34), ambos homens na faixa"
    assert cwb["condutor_homem_18_39"].sum() == 1, "so V234 e condutor (.4)"


def test_perfil_condutor_e_subconjunto_do_perfil_amplo(amostra_quarto_digito):
    painel = agregar(_classificado(amostra_quarto_digito), "PR", 2023, 1)
    assert (painel["condutor_homem_18_39"] <= painel["homem_18_39"]).all()
    assert (painel["homem_18_39"] <= painel["internacoes"]).all()


def test_perfil_exclui_fora_da_faixa_etaria(amostra):
    """V134 e mulher de 45, V435 e homem de 19 -- so o segundo entra na faixa."""
    painel = agregar(_classificado(amostra), "PR", 2023, 1)
    ciclista = painel[painel["grupo"] == "ciclista"]
    assert ciclista["homem_18_39"].sum() == 0
    auto = painel[painel["grupo"] == "auto_placebo"]
    assert auto["homem_18_39"].sum() == 1
