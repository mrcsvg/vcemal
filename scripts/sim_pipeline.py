#!/usr/bin/env python3
"""
Pipeline SIM -> painel municipio x mes de obitos de motociclistas (H5) e o lado
SIM de H4. Operacionalizacao no D-053; precisa de rede para `ftp.datasus.gov.br`.

    make sim                         # 27 UFs, 2015 a 2025
    python scripts/sim_pipeline.py --ufs AC --inicio 2015 --fim 2015   # conferencia

Saida:
    data/raw/sim/uf=<UF>/ano=<AAAA>/parte.parquet   DO na definicao de caso
    data/raw/sim/manifesto.csv                      versao de cada arquivo (D-053)
    data/painel/sim_municipio_mes.parquet           H5a e H5b por municipio x mes
    output/tabelas/h4_sim_uf_ano.csv                lado SIM de H4

Nao le o tratamento nem o painel de estimacao: o cruzamento e a estimacao de H5.
UF-ano ja em disco e no manifesto nao volta a rede; `--refazer` ignora isso.
"""

from __future__ import annotations

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import date

import pandas as pd

from vcemal.extract import sim as ext
from vcemal.paths import INTERIM, PAINEL, PAINEL_SIM_MUNICIPIO_MES, RAW_SIM, TABELAS, garantir
from vcemal.transform import sim as tr

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sim")
for _ruidoso in ("httpx", "httpcore", "urllib3"):
    logging.getLogger(_ruidoso).setLevel(logging.WARNING)

UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]  # fmt: skip
MANIFESTO = RAW_SIM / "manifesto.csv"
H4 = TABELAS / "h4_sim_uf_ano.csv"


def caminho_parte(uf: str, ano: int):
    return RAW_SIM / f"uf={uf}" / f"ano={ano}" / "parte.parquet"


def ler_manifesto() -> pd.DataFrame:
    if MANIFESTO.exists():
        return pd.read_csv(MANIFESTO, dtype={"uf": str})
    return pd.DataFrame()


def extrair(uf: str, ano: int) -> dict | None:
    """Baixa, filtra e grava uma UF-ano. Devolve a linha do manifesto, ou None."""
    pasta = INTERIM / "sim_download" / f"{uf}{ano}"
    baixado = ext.baixar(uf, ano, pasta)
    if baixado is None:
        log.warning("%s %d: DO nao publicada, nem no definitivo nem no preliminar", uf, ano)
        return None
    bruto = pd.read_parquet(baixado.caminho)
    casos = tr.filtrar(bruto)
    destino = caminho_parte(uf, ano)
    destino.parent.mkdir(parents=True, exist_ok=True)
    casos.to_parquet(destino, index=False)
    baixado.caminho.unlink(missing_ok=True)
    linha = asdict(baixado) | {
        "uf": uf,
        "ano": ano,
        "declaracoes": len(bruto),
        "na_definicao_de_caso": len(casos),
        "extraido_em": date.today().isoformat(),
    }
    linha.pop("caminho")
    log.info(
        "%s %d: %d DO, %d na definicao de caso (%s, FTP %s)",
        uf,
        ano,
        len(bruto),
        len(casos),
        "preliminar" if baixado.preliminar else "definitivo",
        baixado.modificado_ftp,
    )
    return linha


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pipeline SIM (D-053)")
    p.add_argument("--ufs", nargs="+", default=UFS)
    p.add_argument("--inicio", type=int, default=2015)
    p.add_argument("--fim", type=int, default=2025)
    p.add_argument("--paralelo", type=int, default=4)
    p.add_argument("--refazer", action="store_true")
    args = p.parse_args(argv)
    garantir(RAW_SIM, PAINEL, TABELAS)

    manifesto = ler_manifesto()
    feitos = set(zip(manifesto["uf"], manifesto["ano"], strict=True)) if len(manifesto) else set()
    pares = [(uf, ano) for uf in args.ufs for ano in range(args.inicio, args.fim + 1)]
    pendentes = [
        (uf, ano)
        for uf, ano in pares
        if args.refazer or (uf, ano) not in feitos or not caminho_parte(uf, ano).exists()
    ]
    log.info("%d UF-ano pedidos, %d a baixar", len(pares), len(pendentes))

    novas: list[dict] = []
    falhas: list[str] = []
    with ThreadPoolExecutor(max_workers=args.paralelo) as pool:
        futuros = {pool.submit(extrair, uf, ano): (uf, ano) for uf, ano in pendentes}
        for f in as_completed(futuros):
            uf, ano = futuros[f]
            try:
                linha = f.result()
            except Exception as e:  # noqa: BLE001
                log.error("falhou %s %d: %r", uf, ano, e)
                falhas.append(f"{uf} {ano}")
                continue
            if linha is not None:
                novas.append(linha)

    if novas:
        refeitos = {(n["uf"], n["ano"]) for n in novas}
        if len(manifesto):
            manifesto = manifesto[
                [
                    (u, a) not in refeitos
                    for u, a in zip(manifesto["uf"], manifesto["ano"], strict=True)
                ]
            ]
        manifesto = pd.concat([manifesto, pd.DataFrame(novas)], ignore_index=True)
        manifesto = manifesto.sort_values(["uf", "ano"]).reset_index(drop=True)
        manifesto.to_csv(MANIFESTO, index=False)

    disponiveis = [(uf, ano) for uf, ano in pares if caminho_parte(uf, ano).exists()]
    if not disponiveis:
        log.error("nada em disco")
        return 1
    preliminar = dict(
        zip(
            zip(manifesto["uf"], manifesto["ano"], strict=True),
            manifesto["preliminar"],
            strict=True,
        )
    )

    paineis, h4 = [], []
    ignorado = data_invalida = 0
    for uf, ano in disponiveis:
        c = tr.classificar(pd.read_parquet(caminho_parte(uf, ano)))
        casos = tr.casos_h5(c)
        ignorado += int(casos["municipio_ignorado"].sum())
        data_invalida += int(casos["mes"].isna().sum())
        parte = tr.agregar(c)
        parte["preliminar"] = bool(preliminar.get((uf, ano), False))
        paineis.append(parte)
        h4.append(tr.h4_uf_ano(c, uf))

    painel = pd.concat(paineis, ignore_index=True)
    # Obito registrado no arquivo de um ano com data de outro -- raro, mas soma.
    painel = painel.groupby(["municipio_res", "ano", "mes"], as_index=False).agg(
        obitos_moto_transito=("obitos_moto_transito", "sum"),
        obitos_moto_transito_fora_saude=("obitos_moto_transito_fora_saude", "sum"),
        preliminar=("preliminar", "max"),
    )
    painel.to_parquet(PAINEL_SIM_MUNICIPIO_MES, index=False)
    tabela_h4 = pd.concat(h4, ignore_index=True).groupby(["uf", "ano"], as_index=False).sum()
    tabela_h4.to_csv(H4, index=False)

    log.info(
        "painel: %d linhas, %d municipios, %d obitos de motociclista em transito "
        "(%d fora de estabelecimento de saude)",
        len(painel),
        painel["municipio_res"].nunique(),
        painel["obitos_moto_transito"].sum(),
        painel["obitos_moto_transito_fora_saude"].sum(),
    )
    log.info(
        "fora do painel: %d com municipio ignorado, %d com data invalida", ignorado, data_invalida
    )
    print("\n=== Obitos de motociclista em transito por ano (SIM, residencia) ===")
    print(
        painel.groupby("ano")[["obitos_moto_transito", "obitos_moto_transito_fora_saude"]]
        .sum()
        .to_string()
    )
    if falhas:
        log.warning("%d UF-ano falharam: %s", len(falhas), ", ".join(sorted(falhas)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
