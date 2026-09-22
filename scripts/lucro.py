#!/usr/bin/env python3
"""
Receita e resultado do iFood, como a Prosus publica, em reais constantes.

Le a transcricao curada em `docs/fontes/ifood_prosus.csv` e baixa so o cambio
(BCB, SGS 3698) e o IPCA (IBGE, SIDRA 1737):

    make lucro

Escreve `lucro_ifood_por_ano_fiscal.csv` (abril-marco, como reportado) e
`lucro_ifood_por_ano.csv` (ano civil, interpolado) em `output/tabelas/`, na
mesma `base_precos` que `make custo` usa por padrao -- e o eixo da serie de
custo. Se `custo_por_ano.csv` ja existir, imprime as duas lado a lado.

E a perna "eles lucram" do argumento (docs/pre-projeto.md, P1). Nao e lucro
liquido: e o resultado operacional do segmento como a controladora reporta,
e a moeda de origem e o dolar (D-032).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal import lucro as lucro_mod
from vcemal.analyze import custo, lucro
from vcemal.extract import bcb, ibge
from vcemal.paths import FONTE_IFOOD_PROSUS, INTERIM, TABELAS, garantir

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lucro")

CACHE_IPCA = INTERIM / "ipca_1737.csv"
CACHE_CAMBIO = INTERIM / "cambio_3698.csv"


def carregar(cache: Path, offline: bool, baixar, nome: str) -> list[dict]:
    if offline:
        if not cache.exists():
            raise FileNotFoundError(f"sem cache de {nome} em {cache}; rode sem --offline")
        return pd.read_csv(cache, dtype={"periodo": str}).to_dict("records")
    linhas = baixar()
    garantir(cache.parent)
    pd.DataFrame(linhas).to_csv(cache, index=False)
    return linhas


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Receita e resultado do iFood a precos constantes")
    p.add_argument("--fonte", type=Path, default=FONTE_IFOOD_PROSUS)
    p.add_argument("--saida", type=Path, default=TABELAS)
    p.add_argument("--cache-ipca", type=Path, default=CACHE_IPCA)
    p.add_argument("--cache-cambio", type=Path, default=CACHE_CAMBIO)
    p.add_argument("--offline", action="store_true", help="usa cambio e IPCA do cache, sem rede")
    p.add_argument(
        "--base",
        default=None,
        help="competencia dos precos, AAAA-MM (padrao: dezembro do ultimo ano civil completo)",
    )
    args = p.parse_args(argv)

    linhas = pd.read_csv(args.fonte, dtype={"nota": str}).to_dict("records")
    fiscal_bruto = lucro.serie_fiscal(linhas)
    anos = list(fiscal_bruto.index)
    inicio = lucro_mod.meses_do_ano_fiscal(anos[0])[0]
    fim = lucro_mod.meses_do_ano_fiscal(anos[-1])[-1]
    log.info("fonte: %s -- FY%d a FY%d (%s a %s)", args.fonte, anos[0], anos[-1], inicio, fim)

    ipca = custo.indice_ipca(carregar(args.cache_ipca, args.offline, ibge.ipca, "IPCA"))
    cambio = lucro.indice_cambio(
        carregar(args.cache_cambio, args.offline, lambda: bcb.cambio_mensal(inicio, fim), "cambio")
    )

    base = args.base or f"{anos[-1] - 1}-12"
    if pd.Period(base, freq="M") not in ipca.index:
        ultimo = str(ipca.index[-1])
        log.warning("IPCA ainda nao tem %s; usando o ultimo mes publicado, %s", base, ultimo)
        base = ultimo

    fiscal = lucro.por_ano_fiscal(linhas, cambio, ipca, base)
    civil = lucro.por_ano_civil(fiscal)
    garantir(args.saida)
    for nome, tabela in {
        "lucro_ifood_por_ano_fiscal": fiscal,
        "lucro_ifood_por_ano": civil,
    }.items():
        destino = args.saida / f"{nome}.csv"
        tabela.round(2).to_csv(destino)
        log.info("%s: %d linhas -> %s", nome, len(tabela), destino)

    print(f"\n=== iFood (Prosus), R$ de {base}, em milhoes -- ano fiscal abril-marco ===")
    print("receita: como publicada, convertida pelo cambio medio do ano fiscal")
    print("trading_profit / aebit: resultado operacional; a metrica muda em FY2024-25\n")
    colunas = [
        "cambio_medio",
        "receita_brl_real_milhoes",
        "trading_profit_brl_real_milhoes",
        "aebit_brl_real_milhoes",
        "pedidos_milhoes",
        "receita_por_pedido_brl_real",
        "entregadores_brasil",
    ]
    print(fiscal[colunas].round(1).to_string())

    custo_por_ano = args.saida / "custo_por_ano.csv"
    if custo_por_ano.exists():
        c = pd.read_csv(custo_por_ano)
        moto = c[c["grupo"] == "motociclista"].set_index("ano")
        if str(moto["base_precos"].iloc[0]) != base:
            log.warning(
                "custo_por_ano esta em R$ de %s, nao %s -- rode os dois com o mesmo --base",
                moto["base_precos"].iloc[0],
                base,
            )
        lado = pd.DataFrame(
            {
                "receita_ifood": civil["receita_brl_real_milhoes"],
                "resultado_ifood": civil["aebit_brl_real_milhoes"].fillna(
                    civil["trading_profit_brl_real_milhoes"]
                ),
                "sus_pagou_moto": moto["val_tot_real"] / 1e6,
                "custo_social_moto": moto["custo_social_real"] / 1e6,
            }
        ).dropna(how="all")
        print(f"\n=== Ano civil, R$ de {base}, em milhoes: iFood x internacoes de motociclista ===")
        print(lado.round(1).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
