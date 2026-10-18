#!/usr/bin/env python3
"""
H4, descritiva: nexo de trabalho registrado no SIH e no SIM, por UF e ano (D-057).

    make painel sim pnad   # antes: AIH em data/raw/sih, h4_sim_uf_ano.csv, pnad_plataformas.csv
    make h4                # este script, sem rede

Escreve `output/tabelas/h4_uf_ano.csv`, `h4_brasil_ano.csv` e `h4_pnad_referencia.csv`.
Sem teste: e descricao, ao lado do preenchimento de cada campo (plano, H4).
"""

from __future__ import annotations

import logging
import re
import sys

import pandas as pd

from vcemal import h4
from vcemal.paths import RAW_SIH, TABELAS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("h4")

COLS = ["grupo", "em_transito", "SEXO", "idade_anos", "MUNIC_RES", "car_int_valido",
        "nexo_ocupacional"]  # fmt: skip
_ANO = re.compile(r"ano=(\d{4})")


def main() -> int:
    partes = sorted(RAW_SIH.glob("uf=*/ano=*/mes=*/parte.parquet"))
    if not partes:
        log.error("sem AIH em %s -- rode make painel", RAW_SIH)
        return 1
    sih = pd.concat(
        [h4.sih_uf_ano(pd.read_parquet(p, columns=COLS), int(_ANO.search(str(p)).group(1)))
         for p in partes],
        ignore_index=True,
    ).groupby(["uf", "ano"], as_index=False).sum()  # fmt: skip
    log.info("SIH: %d competencias lidas", len(partes))

    sim = pd.read_csv(TABELAS / "h4_sim_uf_ano.csv")
    tabela = h4.juntar(sih, sim)
    brasil = h4.brasil_ano(tabela)
    tabela.round(2).to_csv(TABELAS / "h4_uf_ano.csv", index=False)
    brasil.round(2).to_csv(TABELAS / "h4_brasil_ano.csv", index=False)

    pnad_csv = TABELAS / "pnad_plataformas.csv"
    if pnad_csv.exists():
        ref = h4.pnad_referencia(pd.read_csv(pnad_csv))
        ref.round(2).to_csv(TABELAS / "h4_pnad_referencia.csv", index=False)
    else:
        ref = None
        log.warning("sem %s: a referencia da PNAD fica de fora (make pnad)", pnad_csv)

    print("\n=== H4: homens de 18 a 39, motociclista em transito, Brasil ===")
    print(brasil.round(1).to_string(index=False))
    if ref is not None:
        print("\n=== Referencia PNAD: fracao plataformizada entre motociclistas (teto, D-057) ===")
        print(ref.round(1).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
