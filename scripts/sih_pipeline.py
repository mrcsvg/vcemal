#!/usr/bin/env python3
"""
Pipeline SIH/SUS -> painel municipio x mes de internacoes de motociclistas.

Entrypoint fino: a logica esta em `vcemal.extract.sih` e `vcemal.transform.sih`,
a definicao de caso em `vcemal.cid`. Rodar LOCAL -- precisa de rede para
`ftp.datasus.gov.br`.

    pip install -e ".[dev]"
    python scripts/sih_pipeline.py --ufs PR SP BA --inicio 2015-01 --fim 2025-12

Saida:
    data/raw/sih/uf=<UF>/ano=<AAAA>/mes=<MM>/parte.parquet   (AIH filtradas)
    data/painel/painel_municipio_mes.parquet                 (agregado)

Rodado contra a base real em set/2026 (D-034). Competencia ja gravada em
`data/raw/sih/` e lida do disco; o PySUS ainda mantem cache proprio em
`~/pysus/`, entao uma interrupcao nao custa o download refeito. Para conferir
antes de uma serie longa, rode com uma UF e um mes.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal.analyze import car_int
from vcemal.extract.sih import baixar_ano, caminho_do_bruto, meses, salvar_bruto
from vcemal.paths import PAINEL, PAINEL_MUNICIPIO_MES, RAW_SIH, garantir
from vcemal.transform.sih import agregar, classificar, normalizar

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sih")

# O PySUS 2.x consulta o catalogo por HTTP a cada competencia. Numa serie
# nacional sao milhares de linhas de `HTTP Request: HEAD ...` cobrindo o log
# que interessa -- o de quantas AIH cada competencia trouxe.
for _ruidoso in ("httpx", "httpcore", "urllib3"):
    logging.getLogger(_ruidoso).setLevel(logging.WARNING)


def por_ano(inicio: str, fim: str) -> dict[int, list[int]]:
    """Competencias agrupadas por ano: `{2015: [1, 2, ...], 2016: [...]}`."""
    agrupado: dict[int, list[int]] = {}
    for ano, mes in meses(inicio, fim):
        agrupado.setdefault(ano, []).append(mes)
    return agrupado


def processar(
    uf: str,
    ano: int,
    mes: int,
    guardar_bruto: bool,
    caminho_local: Path | None,
    refazer: bool = False,
) -> pd.DataFrame | None:
    """Classifica e agrega uma competencia ja baixada. None se nao houver dado.

    Competencia ja gravada e lida do disco, nao reprocessada: a serie nacional
    sao 3.564 competencias, e uma interrupcao no meio nao pode custar o que ja
    foi feito. `--refazer` ignora o que esta em disco.
    """
    caminho = caminho_do_bruto(uf, ano, mes)
    if not refazer and caminho.exists():
        df = pd.read_parquet(caminho)
        log.info("%s %04d-%02d: %d AIH ja em disco", uf, ano, mes, len(df))
        return agregar(df, uf, ano, mes) if not df.empty else None

    if caminho_local is None:
        log.warning("sem arquivo RD para %s %04d-%02d", uf, ano, mes)
        return None

    bruto = pd.read_parquet(caminho_local)
    if bruto.empty:
        return None

    df = classificar(normalizar(bruto))
    log.info("%s %04d-%02d: %d AIH de interesse (de %d)", uf, ano, mes, len(df), len(bruto))
    if df.empty:
        return None
    if guardar_bruto:
        salvar_bruto(df, uf, ano, mes)
    return agregar(df, uf, ano, mes)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--ufs", nargs="+", required=True)
    p.add_argument("--inicio", required=True, help="AAAA-MM")
    p.add_argument("--fim", required=True, help="AAAA-MM")
    p.add_argument(
        "--sem-bruto",
        action="store_true",
        help="nao salvar o nivel individual, so o painel",
    )
    p.add_argument(
        "--refazer",
        action="store_true",
        help="reprocessa competencias ja gravadas em vez de le-las do disco",
    )
    args = p.parse_args(argv)

    garantir(RAW_SIH, PAINEL)

    paineis: list[pd.DataFrame] = []
    falhas: list[str] = []
    for uf in args.ufs:
        for ano, meses_do_ano in por_ano(args.inicio, args.fim).items():
            # So vai a rede se faltar alguma competencia do ano em disco.
            pendentes = [
                m for m in meses_do_ano if args.refazer or not caminho_do_bruto(uf, ano, m).exists()
            ]
            caminhos: dict[int, Path] = {}
            if pendentes:
                try:
                    caminhos = baixar_ano(uf, ano)
                except Exception as e:  # noqa: BLE001
                    log.error("falhou o download de %s %d: %s", uf, ano, e)
                    falhas.extend(f"{uf} {ano:04d}-{m:02d}" for m in pendentes)
                    continue

            for mes in meses_do_ano:
                try:
                    parte = processar(
                        uf,
                        ano,
                        mes,
                        guardar_bruto=not args.sem_bruto,
                        caminho_local=caminhos.get(mes),
                        refazer=args.refazer,
                    )
                except Exception as e:  # noqa: BLE001
                    log.error("falhou %s %04d-%02d: %s", uf, ano, mes, e)
                    falhas.append(f"{uf} {ano:04d}-{mes:02d}")
                    continue
                if parte is not None:
                    paineis.append(parte)

    if not paineis:
        log.error("nada foi processado")
        return 1

    painel = pd.concat(paineis, ignore_index=True)
    painel.to_parquet(PAINEL_MUNICIPIO_MES, index=False)
    log.info(
        "painel salvo em %s: %d linhas, %d municipios",
        PAINEL_MUNICIPIO_MES,
        len(painel),
        painel["municipio_res"].nunique(),
    )
    if falhas:
        log.warning("%d competencias falharam: %s", len(falhas), ", ".join(falhas))

    # Diagnostico que interessa antes de qualquer estimacao (D-008).
    print("\n=== Preenchimento do CAR_INT e nexo ocupacional ===")
    print("pct_nexo tem o preenchimento como denominador, nao o total de internacoes.\n")
    print(car_int.por_ano(painel).round(2).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
