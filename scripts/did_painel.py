#!/usr/bin/env python3
"""
Monta o painel de estimacao do V2 (municipio x mes) para o estimador em R.

    make denominadores   # antes
    make did             # este script e depois scripts/did_estimar.R

Le o painel do SIH, os denominadores, o tratamento congelado (confere o hash,
D-041), as aberturas de MEI (proxy de H2, D-043) e as regioes imediatas do IBGE
(cluster, D-025). Escreve `data/painel/estimacao_municipio_mes.csv` -- CSV e nao
Parquet porque o R do projeto le com `data.table::fread`, sem `arrow`.

So a lista de regioes vai a rede, e uma vez: fica em cache em `data/interim/`.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal.paths import (
    FONTES,
    INTERIM,
    PAINEL,
    PAINEL_MUNICIPIO_MES,
    PAINEL_SIM_MUNICIPIO_MES,
    TABELAS,
)
from vcemal.transform import estimacao

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("did_painel")

TRATAMENTO = FONTES / "cronologia" / "tratamento_mei_municipio.csv"
DENOMINADORES = PAINEL / "denominadores_municipio_mes.parquet"
ABERTURAS = TABELAS / "aberturas_mei_municipio_mes.csv"
CACHE_REGIOES = INTERIM / "municipios_ibge.csv"
DESTINO = PAINEL / "estimacao_municipio_mes.csv"


def regioes(cache: Path) -> pd.DataFrame:
    if not cache.exists():
        from vcemal.extract import ibge

        m = pd.DataFrame(ibge.listar_municipios()).rename(columns={"id": "municipio_ibge"})
        m.to_csv(cache, index=False)
    return pd.read_csv(cache)


def main() -> int:
    p = argparse.ArgumentParser(description="Painel de estimacao do V2")
    p.add_argument("--saida", type=Path, default=DESTINO)
    args = p.parse_args()

    tratamento = estimacao.ler_tratamento(TRATAMENTO)
    log.info("tratamento congelado confere: %s", estimacao.HASH_TRATAMENTO[:12])
    painel = pd.read_parquet(PAINEL_MUNICIPIO_MES)
    den = pd.read_parquet(DENOMINADORES)
    aberturas = pd.read_csv(ABERTURAS)

    # O SIM entra se ja foi extraido (`make sim`, D-053); sem ele, H5 nao roda.
    sim = pd.read_parquet(PAINEL_SIM_MUNICIPIO_MES) if PAINEL_SIM_MUNICIPIO_MES.exists() else None
    if sim is None:
        log.warning("sem painel do SIM em %s: H5 fica de fora", PAINEL_SIM_MUNICIPIO_MES)

    df = estimacao.montar(painel, den, tratamento, regioes(CACHE_REGIOES), aberturas, sim)

    sem_frota = df[(df["periodo"] >= estimacao.periodo_de("2016-07")) & ~(df["frota_moto"] > 0)]
    if len(sem_frota):
        log.warning(
            "%d municipio-meses sem frota de moto a partir de 2016-07 (taxa NaN): %s",
            len(sem_frota),
            sorted(sem_frota["municipio_ibge"].unique())[:10],
        )
    log.info("municipios por grupo:\n%s", estimacao.resumo(df).to_string())
    total = df["moto_internacoes_transito"].sum()
    log.info("internacoes de motociclista em transito no universo: %d", total)
    if sim is not None:
        log.info(
            "obitos de motociclista em transito no universo: %d (%d fora de estab. de saude)",
            df["obitos_moto_transito"].sum(),
            df["obitos_moto_transito_fora_saude"].sum(),
        )

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.saida, index=False)
    log.info("%d linhas -> %s", len(df), args.saida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
