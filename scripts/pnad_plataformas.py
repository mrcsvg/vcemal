#!/usr/bin/env python3
"""
As quatro estatisticas da precariedade, do modulo de plataformas da PNAD Continua.

Baixa o microdado das rodadas do modulo (4T2022, 3T2024, 3T2025) pelo FTP do
IBGE -- HTTPS, ~230 MB por rodada, 2 a 3,5 GB descompactado -- e escreve:

    output/tabelas/pnad_plataformas.csv         Brasil e grandes regioes
    output/tabelas/pnad_plataformas_uf.csv      por UF

Uma linha por rodada x recorte x grupo: pessoas (ponderado), informalidade,
contribuicao previdenciaria, horas semanais, rendimento medio e por hora,
nominal e real. Os grupos incluem motociclistas plataformizados e nao
plataformizados -- a ponte com o desfecho V20-V29 do SIH (D-031).

O rendimento real usa o deflator do IBGE da rodada mais recente pedida, para
que as rodadas fiquem na mesma base.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal import pnad as pnad_mod
from vcemal.extract import pnad as extract_pnad
from vcemal.paths import INTERIM, TABELAS, garantir
from vcemal.transform import pnad as transform_pnad

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pnad")


def rodada(ano: int, trimestre: int) -> tuple[int, int]:
    return ano, trimestre


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Modulo de plataformas da PNAD Continua")
    p.add_argument(
        "--rodadas",
        nargs="+",
        default=[f"{a}-{t}" for a, t in pnad_mod.RODADAS],
        help="ano-trimestre, ex.: 2024-3 (padrao: todas as rodadas do modulo)",
    )
    p.add_argument("--cache", type=Path, default=INTERIM / "pnad")
    p.add_argument("--saida", type=Path, default=TABELAS)
    args = p.parse_args(argv)

    rodadas = [rodada(*map(int, r.split("-"))) for r in args.rodadas]
    garantir(args.cache, args.saida)

    pessoas_por_rodada = []
    deflator_ref = None
    for ano, trimestre in rodadas:
        txt, dicionario, deflator = extract_pnad.baixar_rodada(ano, trimestre, args.cache)
        lay = extract_pnad.layout(dicionario)
        pessoas = transform_pnad.preparar(transform_pnad.ler(txt, lay))
        pessoas_por_rodada.append(pessoas)
        if deflator_ref is None or (ano, trimestre) >= max(rodadas):
            deflator_ref = extract_pnad.deflator(deflator)
    todas = pd.concat(pessoas_por_rodada, ignore_index=True)
    todas = transform_pnad.deflacionar(todas, deflator_ref)

    brasil = transform_pnad.resumir(todas)
    regioes = transform_pnad.resumir(todas, "regiao")
    ufs = transform_pnad.resumir(todas, "uf")
    nacional = pd.concat([brasil, regioes], ignore_index=True)
    for nome, tabela in {"pnad_plataformas": nacional, "pnad_plataformas_uf": ufs}.items():
        destino = args.saida / f"{nome}.csv"
        tabela.round(2).to_csv(destino, index=False)
        log.info("%s: %d linhas -> %s", nome, len(tabela), destino)

    print("\n=== Brasil, setor privado, trabalho principal; R$ do trimestre do deflator ===")
    print(
        brasil.assign(pessoas_mil=(brasil["pessoas"] / 1000).round(0))[
            [
                "ano",
                "grupo",
                "pessoas_mil",
                "pct_informal",
                "pct_contribuinte",
                "horas_media",
                "rend_medio_real",
                "rend_hora_real",
            ]
        ]
        .round(1)
        .to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
