"""H4 (D-057): recorte do lado SIH, juncao com o SIM e fracoes como razao de somas."""

from __future__ import annotations

import pandas as pd
import pytest

from vcemal import h4


def _aih(**cols) -> pd.DataFrame:
    base = {
        "grupo": "motociclista",
        "em_transito": True,
        "SEXO": "1",
        "idade_anos": 25,
        "MUNIC_RES": "410690",
        "car_int_valido": True,
        "nexo_ocupacional": False,
    }
    n = max((len(v) for v in cols.values()), default=1)
    return pd.DataFrame({k: cols.get(k, [v] * n) for k, v in base.items()})


def test_sih_recorta_motociclista_transito_homem_18_39():
    a = _aih(
        grupo=["motociclista", "ciclista", "motociclista", "motociclista", "motociclista",
               "motociclista"],
        em_transito=[True, True, False, True, True, True],
        SEXO=["1", "1", "1", "3", "1", "1"],
        idade_anos=[25, 25, 25, 25, 40, 18],
    )  # fmt: skip
    assert len(h4.sih_casos(a)) == 2


def test_sih_uf_vem_da_residencia():
    a = _aih(
        MUNIC_RES=["410690", "350010", "350010"],
        car_int_valido=[True, True, False],
        nexo_ocupacional=[True, False, False],
    )
    t = h4.sih_uf_ano(a, 2020)
    assert t.to_dict("records") == [
        {"uf": "PR", "ano": 2020, "internacoes_homem_18_39": 1, "car_int_preenchido": 1,
         "nexo_ocupacional": 1},
        {"uf": "SP", "ano": 2020, "internacoes_homem_18_39": 2, "car_int_preenchido": 1,
         "nexo_ocupacional": 0},
    ]  # fmt: skip


def test_brasil_e_razao_de_somas():
    sih = pd.DataFrame({"uf": ["AC", "SP"], "ano": [2020, 2020],
                        "internacoes_homem_18_39": [10, 990], "car_int_preenchido": [10, 90],
                        "nexo_ocupacional": [5, 0]})  # fmt: skip
    sim = pd.DataFrame({"uf": ["SP"], "ano": [2020], "obitos_homem_18_39": [100],
                        "acidtrab_preenchido": [50], "acidtrab_sim": [5]})  # fmt: skip
    t = h4.juntar(sih, sim)
    assert t.loc[t["uf"] == "AC", "obitos_homem_18_39"].item() == 0
    b = h4.brasil_ano(t)
    assert b["sih_pct_preenchido"].item() == pytest.approx(10.0)
    assert b["sih_pct_nexo"].item() == pytest.approx(5.0)  # 5/100, nao media de 50% e 0%
    assert b["sim_pct_nexo"].item() == pytest.approx(10.0)


def test_pnad_referencia_e_fracao_no_brasil():
    pnad = pd.DataFrame({
        "ano": [2024] * 3, "trimestre": [3] * 3, "regiao": ["Brasil", "Brasil", "Sul"],
        "grupo": ["motociclistas", "motociclistas_plataformizados", "motociclistas"],
        "pessoas": [1000.0, 350.0, 99.0],
    })  # fmt: skip
    r = h4.pnad_referencia(pnad)
    assert r["pct_plataformizado_teto"].item() == pytest.approx(35.0)
