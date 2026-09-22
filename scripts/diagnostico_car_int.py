#!/usr/bin/env python3
"""
Preenchimento do `CAR_INT` por ano, UF e municipio.

Roda sobre o painel ja montado -- nao baixa nada:

    make painel        # antes
    make diagnostico   # este script

Escreve CSV em `output/tabelas/` e imprime o recorte por ano.

Por que isto e uma tabela do paper e nao um log de qualidade de dado: o
`CAR_INT` e o unico campo do SIH que marca nexo ocupacional, e o quanto ele
deixa de marcar numa populacao de motociclistas em idade produtiva e a medida
direta da cegueira do sistema de informacao (D-008, H4).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal.analyze import car_int
from vcemal.paths import PAINEL_MUNICIPIO_MES, TABELAS, garantir

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("diagnostico")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Preenchimento do CAR_INT no painel")
    p.add_argument("--painel", type=Path, default=PAINEL_MUNICIPIO_MES)
    p.add_argument("--saida", type=Path, default=TABELAS)
    p.add_argument(
        "--minimo-municipio",
        type=int,
        default=30,
        help="piso de internacoes de motociclista para o municipio entrar na tabela",
    )
    args = p.parse_args(argv)

    if not args.painel.exists():
        log.error("painel nao encontrado em %s -- rode `make painel` antes", args.painel)
        return 1

    painel = pd.read_parquet(args.painel)
    log.info("painel: %d linhas, %d municipios", len(painel), painel["municipio_res"].nunique())

    garantir(args.saida)
    recortes = {
        "car_int_por_ano": car_int.por_ano(painel),
        "car_int_por_uf_ano": car_int.por_uf_ano(painel),
        "car_int_por_municipio": car_int.por_municipio(painel, minimo=args.minimo_municipio),
    }
    for nome, tabela in recortes.items():
        destino = args.saida / f"{nome}.csv"
        tabela.round(4).to_csv(destino)
        log.info("%s: %d linhas -> %s", nome, len(tabela), destino)

    print("\n=== Preenchimento do CAR_INT por ano e grupo ===")
    print("pct_preenchido = codigo valido / internacoes")
    print("pct_nexo       = CAR_INT 03 ou 04 / codigo valido  (NAO sobre internacoes)\n")
    print(recortes["car_int_por_ano"].round(2).to_string())

    moto = recortes["car_int_por_ano"].xs("motociclista", level="grupo", drop_level=False)
    if not moto.empty:
        print(
            f"\nMotociclista, serie inteira: {int(moto['internacoes'].sum())} internacoes, "
            f"{int(moto['nexo_ocupacional'].sum())} com nexo ocupacional declarado."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
