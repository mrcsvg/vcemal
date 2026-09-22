"""Fixtures compartilhadas. Nenhum teste toca a rede ou o disco de dados."""

from __future__ import annotations

import pandas as pd
import pytest


def _aih(n_aih: str, diag: str, car_int: str = "02", **kw) -> dict:
    """Uma AIH sintetica com os campos que o pipeline le."""
    base = {
        "N_AIH": n_aih,
        "MUNIC_RES": "410690",
        "MUNIC_MOV": "410690",
        "IDADE": 28,
        "COD_IDADE": 4,
        "SEXO": "1",
        "DT_INTER": "20230105",
        "DT_SAIDA": "20230110",
        "DIAS_PERM": 5,
        "UTI_MES_TO": 0,
        "MORTE": 0,
        "CAR_INT": car_int,
        "DIAG_PRINC": diag,
        "DIAG_SECUN": "S720",
        "VAL_TOT": 1200.0,
        "VAL_SH": 800.0,
        "VAL_SP": 400.0,
        "CNES": "1",
        "ESPEC": "3",
        "PROC_REA": "1",
        "RACA_COR": "1",
    }
    base.update(kw)
    return base


@pytest.fixture
def amostra() -> pd.DataFrame:
    """Amostra original do projeto: um caso por grupo, mais um fora do escopo."""
    return pd.DataFrame(
        [
            _aih("1", "V234", "02"),  # motociclista condutor, transito
            _aih("2", "V285", "03", UTI_MES_TO=3, MORTE=1, IDADE=34, VAL_TOT=8400.0),
            _aih("3", "V134", "02", SEXO="3", IDADE=45),  # ciclista condutor
            _aih("4", "V435", "04", MUNIC_RES="355030", MUNIC_MOV="355030", IDADE=19),
            _aih("5", "S720", "02", MUNIC_RES="355030", MUNIC_MOV="355030", IDADE=61),
        ]
    )


@pytest.fixture
def amostra_quarto_digito() -> pd.DataFrame:
    """Cobre as duas estruturas do quarto digito, lado a lado.

    `.3` e `.6` sao os digitos que separam a estrutura padrao da terminal.
    """
    return pd.DataFrame(
        [
            # Estrutura padrao (V20-V28, V10-V18, V40-V48)
            _aih("p0", "V230"),  # condutor, NAO transito
            _aih("p2", "V232"),  # nao especificado, NAO transito
            _aih("p3", "V233"),  # embarque/desembarque -> transito por convencao
            _aih("p4", "V234"),  # condutor, transito
            _aih("p5", "V235"),  # passageiro, transito
            _aih("p9", "V239"),  # nao especificado, transito
            # Estrutura terminal (V19, V29, V49)
            _aih("t3", "V293"),  # qualquer, NAO transito nao especificado
            _aih("t4", "V294"),  # condutor, transito
            _aih("t6", "V296"),  # nao especificado, transito
            _aih("t8", "V298"),  # outros acidentes de transporte especificados
            _aih("t9", "V299"),  # qualquer, transito nao especificado
            _aih("c3", "V193"),  # ciclista terminal, NAO transito
            _aih("a3", "V493"),  # auto terminal, NAO transito
        ]
    )


@pytest.fixture
def amostra_car_int() -> pd.DataFrame:
    """Motociclistas com o CAR_INT em todos os estados que a serie produz."""
    return pd.DataFrame(
        [
            _aih("1", "V234", "02"),  # valido, sem nexo
            _aih("2", "V234", "03"),  # valido, nexo (local de trabalho)
            _aih("3", "V234", "04"),  # valido, nexo (trajeto)
            _aih("4", "V234", ""),  # branco
            _aih("5", "V234", "99"),  # sentinela de ignorado
            _aih("6", "V234", "00"),  # sentinela de ignorado
        ]
    )


@pytest.fixture
def amostra_realista() -> pd.DataFrame:
    """Como o SIH realmente codifica: lesao no principal, causa no secundario.

    A norma do SIH manda o capitulo XIX (S/T) para `DIAG_PRINC` e o capitulo XX
    (V a Y) para o diagnostico secundario. No dado real do SIH o codigo V
    aparece em `DIAGSEC1`. Ver D-017.
    """
    linhas = [
        # lesao no principal, causa de moto em DIAGSEC1 -- o caso dominante
        _aih("1", "S720", car_int="02") | {"DIAG_SECUN": "", "DIAGSEC1": "V234"},
        # causa no DIAG_SECUN classico (layout antigo)
        _aih("2", "S065", car_int="03") | {"DIAG_SECUN": "V299", "DIAGSEC1": ""},
        # ciclista, causa mais adiante na lista
        _aih("3", "S823", car_int="02")
        | {"DIAG_SECUN": "S060", "DIAGSEC1": "", "DIAGSEC2": "V134"},
        # auto placebo, com o V direto no principal (excecao permitida)
        _aih("4", "V435", car_int="04") | {"DIAG_SECUN": "S320", "DIAGSEC1": ""},
        # so lesao, nenhuma causa externa -- sai do escopo
        _aih("5", "S720", car_int="02") | {"DIAG_SECUN": "T141", "DIAGSEC1": ""},
    ]
    df = pd.DataFrame(linhas)
    for i in range(1, 10):
        df[f"DIAGSEC{i}"] = df.get(f"DIAGSEC{i}", "")
    return df
