#!/usr/bin/env python3
"""
A lacuna SIH x INSS: beneficios concedidos com CID V20-V29 contra internacoes.

Baixa os arquivos mensais de beneficios concedidos (HTTPS, portal de dados
abertos do INSS), agrega por UF x mes x grupo x classe e, se o painel do SIH
existir, escreve a comparacao por UF x ano e por ano:

    python scripts/lacuna_inss.py --inicio 2019-01 --fim 2025-12

Saidas:
    data/painel/inss_uf_mes.parquet
    output/tabelas/lacuna_inss_por_uf_ano.csv
    output/tabelas/lacuna_inss_por_ano.csv

O XLSX de 2023 em diante leva ~1 min por mes para abrir; a serie inteira e
uma hora. O cache em `data/interim/inss/` evita rebaixar.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal.analyze import lacuna
from vcemal.extract import inss as extract_inss
from vcemal.paths import INTERIM, PAINEL, PAINEL_MUNICIPIO_MES, TABELAS, garantir
from vcemal.transform import inss as transform_inss

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lacuna_inss")

DESTINO_INSS = PAINEL / "inss_uf_mes.parquet"


def competencias(inicio: str, fim: str) -> list[tuple[int, int]]:
    return [(p.year, p.month) for p in pd.period_range(inicio, fim, freq="M")]


def coletar(inicio: str, fim: str, cache: Path, offline: bool) -> pd.DataFrame:
    indice = {} if offline else extract_inss.indice()
    partes: list[pd.DataFrame] = []
    for ano, mes in competencias(inicio, fim):
        try:
            caminho = extract_inss.baixar_mes(ano, mes, cache, indice)
            if caminho is None:
                continue
            bruto = transform_inss.ler(caminho)
            normalizado = transform_inss.normalizar(bruto, ano, mes)
            agregado = transform_inss.agregar(normalizado)
        except Exception as e:  # noqa: BLE001
            log.error("falhou %04d-%02d: %s", ano, mes, e)
            continue
        moto = agregado[agregado["grupo"] == "motociclista"]["beneficios"].sum()
        log.info("%04d-%02d: %d linhas, %d beneficios de motociclista", ano, mes, len(bruto), moto)
        partes.append(agregado)
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Lacuna SIH x INSS por UF e ano")
    p.add_argument("--inicio", required=True, help="AAAA-MM (serie mensal comeca em 2018-12)")
    p.add_argument("--fim", required=True, help="AAAA-MM")
    p.add_argument("--painel", type=Path, default=PAINEL_MUNICIPIO_MES)
    p.add_argument("--cache", type=Path, default=INTERIM / "inss")
    p.add_argument("--saida", type=Path, default=TABELAS)
    p.add_argument("--offline", action="store_true", help="so meses ja no cache, sem rede")
    args = p.parse_args(argv)

    garantir(PAINEL, args.cache, args.saida)
    agregado = coletar(args.inicio, args.fim, args.cache, args.offline)
    if agregado.empty:
        log.error("nenhuma competencia do INSS foi obtida")
        return 1
    agregado.to_parquet(DESTINO_INSS, index=False)
    log.info(
        "INSS: %d linhas, %d competencias -> %s",
        len(agregado),
        len(agregado.groupby(["ano", "mes"])),
        DESTINO_INSS,
    )

    moto = agregado[agregado["grupo"] == "motociclista"]
    print("\n=== INSS, beneficios concedidos com CID V20-V29, por ano e classe ===")
    print(
        moto.pivot_table(index="ano", columns="classe", values="beneficios", aggfunc="sum")
        .fillna(0)
        .astype(int)
        .to_string()
    )

    if not args.painel.exists():
        log.warning("painel do SIH nao encontrado em %s; sem tabela de lacuna", args.painel)
        return 0
    painel = pd.read_parquet(args.painel)
    recortes = {
        "lacuna_inss_por_uf_ano": lacuna.por_uf_ano(painel, agregado),
        "lacuna_inss_por_ano": lacuna.por_ano(painel, agregado),
    }
    for nome, tabela in recortes.items():
        destino = args.saida / f"{nome}.csv"
        tabela.round(3).to_csv(destino)
        log.info("%s: %d linhas -> %s", nome, len(tabela), destino)

    print("\n=== Lacuna por ano, motociclista (comparar so onde meses_sih = meses_inss = 12) ===")
    print(recortes["lacuna_inss_por_ano"].round(2).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
