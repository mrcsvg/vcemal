#!/usr/bin/env python3
"""
Monta os denominadores do painel: frota de moto (Senatran) e populacao (IBGE).

Precisa de rede, mas so de HTTPS -- roda em ambiente sem acesso ao FTP do
DATASUS, ao contrario de `sih_pipeline.py`.

    python scripts/denominadores.py --inicio 2016-07 --fim 2025-12

Saida:
    data/painel/denominadores_municipio_mes.parquet

Com `--painel`, junta ao painel do SIH e grava as taxas em
`data/painel/painel_com_taxas.parquet`.

Cobertura: a serie "Frota por Municipio e Tipo" comeca em **julho de 2016**.
Antes disso o Senatran so publica frota por UF, sem abertura municipal (D-015).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal import municipios as mun
from vcemal.extract import ibge, senatran
from vcemal.paths import INTERIM, PAINEL, PAINEL_MUNICIPIO_MES, garantir
from vcemal.transform import denominadores as den

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("denominadores")

DESTINO_PADRAO = PAINEL / "denominadores_municipio_mes.parquet"
DESTINO_TAXAS = PAINEL / "painel_com_taxas.parquet"


def competencias(inicio: str, fim: str) -> list[tuple[int, int]]:
    return [(p.year, p.month) for p in pd.period_range(inicio, fim, freq="M")]


def coletar_frota(inicio: str, fim: str, cache: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Baixa e agrega a frota mes a mes. Devolve `(frota, sem_par)`."""
    indice_ibge = mun.construir_indice(ibge.listar_municipios())
    partes: list[pd.DataFrame] = []
    sobras: list[pd.DataFrame] = []
    indices_ano: dict[int, dict[int, str]] = {}

    for ano, mes in competencias(inicio, fim):
        if ano not in indices_ano:
            indices_ano[ano] = senatran.indice_do_ano(ano)
        try:
            caminho = senatran.baixar_mes(ano, mes, cache, indice=indices_ano[ano])
            if caminho is None:
                continue
            bruto = den.ler_frota(caminho)
            frota, sem_par = den.agregar_frota(bruto, indice_ibge, ano, mes)
        except Exception as e:  # noqa: BLE001
            log.error("falhou frota %04d-%02d: %s", ano, mes, e)
            continue
        partes.append(frota)
        if len(sem_par):
            sobras.append(sem_par.assign(ano=ano, mes=mes))

    frota = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
    sem_par = pd.concat(sobras, ignore_index=True) if sobras else pd.DataFrame()
    return frota, sem_par


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Frota de moto e populacao por municipio")
    p.add_argument("--inicio", required=True, help="AAAA-MM (frota municipal comeca em 2016-07)")
    p.add_argument("--fim", required=True, help="AAAA-MM")
    p.add_argument("--saida", type=Path, default=DESTINO_PADRAO)
    p.add_argument("--cache", type=Path, default=INTERIM / "senatran")
    p.add_argument(
        "--painel",
        type=Path,
        default=None,
        help=f"painel do SIH para juntar e calcular taxas (ex.: {PAINEL_MUNICIPIO_MES})",
    )
    args = p.parse_args(argv)

    garantir(PAINEL, args.cache)

    frota, sem_par = coletar_frota(args.inicio, args.fim, args.cache)
    if frota.empty:
        log.error("nenhuma competencia de frota foi obtida")
        return 1

    anos = sorted({int(a) for a in frota["ano"].unique()})
    linhas_pop, anos_sem_pop = ibge.populacao(anos)
    populacao = den.populacao_para_painel(linhas_pop)

    denominadores = frota.merge(populacao, on=["municipio_res", "ano"], how="left")
    denominadores.to_parquet(args.saida, index=False)
    log.info(
        "denominadores: %d linhas, %d municipios, %d competencias -> %s",
        len(denominadores),
        denominadores["municipio_res"].nunique(),
        len(denominadores.groupby(["ano", "mes"])),
        args.saida,
    )
    if anos_sem_pop:
        log.warning("anos sem estimativa populacional: %s", ", ".join(anos_sem_pop))
    if len(sem_par):
        log.warning("%d linhas de municipio nao reconhecido (ver log acima)", len(sem_par))

    if args.painel:
        if not args.painel.exists():
            log.error("painel nao encontrado em %s -- rode `make painel` antes", args.painel)
            return 1
        painel = pd.read_parquet(args.painel)
        com_taxas = den.taxas(den.juntar(painel, frota, populacao))
        com_taxas.to_parquet(DESTINO_TAXAS, index=False)
        log.info("painel com taxas: %d linhas -> %s", len(com_taxas), DESTINO_TAXAS)

        moto = com_taxas[com_taxas["grupo"] == "motociclista"]
        cobertura = 100 * moto["frota_moto"].notna().mean() if len(moto) else 0.0
        print(f"\nmotociclista: {len(moto)} linhas, {cobertura:.1f}% com frota casada")
        print(moto["taxa_por_frota"].describe().round(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
