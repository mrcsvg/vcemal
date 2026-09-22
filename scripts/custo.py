#!/usr/bin/env python3
"""
Custo pago pelo SUS e custo social das internacoes, a precos constantes.

Roda sobre o painel ja montado e baixa so o IPCA (HTTPS, API do IBGE):

    make painel   # antes
    make custo    # este script

Escreve `custo_por_ano.csv` e `custo_por_uf_ano.csv` em `output/tabelas/` e
imprime o recorte de motociclista por ano.

E a perna "nos pagamos" do argumento (docs/pre-projeto.md, P3): o valor pago
pelo SUS deflacionado e piso; o custo social pelos parametros do Ipea e ordem
de grandeza; a perda de producao e a parte que recai sobre a familia. Os tres
saem lado a lado, na mesma base de precos, e nao se somam (D-029).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal import custo as custo_mod
from vcemal.analyze import custo
from vcemal.extract import ibge
from vcemal.paths import INTERIM, PAINEL_MUNICIPIO_MES, TABELAS, garantir

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("custo")

CACHE_IPCA = INTERIM / "ipca_1737.csv"


def carregar_ipca(cache: Path, offline: bool) -> list[dict]:
    """Baixa a serie e guarda em CSV; com `offline`, le so o cache."""
    if offline:
        if not cache.exists():
            raise FileNotFoundError(f"sem cache do IPCA em {cache}; rode sem --offline")
        return pd.read_csv(cache, dtype={"periodo": str}).to_dict("records")
    linhas = ibge.ipca()
    garantir(cache.parent)
    pd.DataFrame(linhas).to_csv(cache, index=False)
    return linhas


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Custo pago e custo social a precos constantes")
    p.add_argument("--painel", type=Path, default=PAINEL_MUNICIPIO_MES)
    p.add_argument("--saida", type=Path, default=TABELAS)
    p.add_argument("--cache-ipca", type=Path, default=CACHE_IPCA)
    p.add_argument("--offline", action="store_true", help="usa o IPCA do cache, sem rede")
    p.add_argument(
        "--base",
        default=None,
        help="competencia dos precos, AAAA-MM (padrao: dezembro do ultimo ano do painel)",
    )
    args = p.parse_args(argv)

    if not args.painel.exists():
        log.error("painel nao encontrado em %s -- rode `make painel` antes", args.painel)
        return 1

    painel = pd.read_parquet(args.painel)
    ipca = custo.indice_ipca(carregar_ipca(args.cache_ipca, args.offline))
    base = args.base or f"{int(painel['ano'].max())}-12"
    if pd.Period(base, freq="M") not in ipca.index:
        ultimo = str(ipca.index[-1])
        log.warning("IPCA ainda nao tem %s; usando o ultimo mes publicado, %s", base, ultimo)
        base = ultimo
    log.info("painel: %d linhas; precos de %s", len(painel), base)
    log.info("parametros: %s", custo_mod.TD2565.fonte)

    garantir(args.saida)
    recortes = {
        "custo_por_ano": custo.por_ano(painel, ipca, base),
        "custo_por_uf_ano": custo.por_uf_ano(painel, ipca, base),
    }
    for nome, tabela in recortes.items():
        destino = args.saida / f"{nome}.csv"
        tabela.round(2).to_csv(destino)
        log.info("%s: %d linhas -> %s", nome, len(tabela), destino)

    moto = recortes["custo_por_ano"].xs("motociclista", level="grupo", drop_level=True)
    if moto.empty:
        return 0
    print(f"\n=== Motociclista (V20-V29), R$ de {base}, em milhoes ===")
    print("val_tot_real       = pago pelo SUS (piso)")
    print("custo_social_real  = Ipea TD 2565 (ordem de grandeza)")
    print("perda_producao_real= parte que recai sobre a familia\n")
    em_milhoes = moto[["val_tot_real", "custo_social_real", "perda_producao_real"]] / 1e6
    print(
        pd.concat([moto[["internacoes", "obitos", "val_por_internacao_real"]], em_milhoes], axis=1)
        .round(1)
        .to_string()
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
