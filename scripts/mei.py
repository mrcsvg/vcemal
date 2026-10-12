#!/usr/bin/env python3
"""
Mes de chegada do entregador por aplicativo, pelas aberturas de MEI de entrega (D-040).

    make mei                 # baixa a publicacao mais recente do CNPJ (~6 GB) e monta
    make mei ARGS=--offline  # remonta do que ja esta em data/raw/cnpj e data/interim/cnpj

Baixa os Estabelecimentos, o Simples e a tabela de municipios dos dados abertos
do CNPJ, fica so com o CNAE 5320-2/02, conta aberturas por municipio e mes e
aplica a regra de quebra congelada em `vcemal.mei`. Escreve em `output/tabelas/`:

* `tratamento_mei_municipio.csv` -- uma linha por municipio do universo:
  `grupo` (datado, sem_quebra, coorte_precoce) e `mes_tratamento`;
* `aberturas_mei_municipio_mes.csv` -- a serie que a regra le;
* `mei_quebra_por_faixa_ano.csv` -- quantas quebras por faixa de populacao e ano.

E imprime as tres validacoes sem SIH: placebo de 2016 por faixa, concordancia
com o Wayback (se `cronologia_wayback.csv` existir) e a serie nacional.

Nao le o SIH, o painel nem nenhuma tabela de internacao (secao 12 do protocolo).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal import mei
from vcemal import municipios as mun
from vcemal.extract import cnpj, ibge
from vcemal.paths import FONTES, INTERIM, RAW_CNPJ, TABELAS, garantir

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mei")

UNIVERSO = FONTES / "cronologia" / "universo.csv"
#: Primeiro mes da serie: 24 meses de base antes do placebo de 2016-01.
SERIE_INICIO = "2014-01"


def preparar(mes: str, raw: Path, interim: Path, offline: bool) -> None:
    """Zips da Receita -> parquets filtrados, um por parte. Idempotente."""
    garantir(interim)
    for n in cnpj.PARTES:
        alvo = interim / f"entrega_{n}.parquet"
        if alvo.exists():
            continue
        arquivo = raw / f"Estabelecimentos{n}.zip"
        if not offline:
            cnpj.baixar(mes, arquivo.name, raw)
        elif not arquivo.exists():
            raise FileNotFoundError(f"sem {arquivo}; rode sem --offline")
        tabela = cnpj.filtrar_estabelecimentos(arquivo, mei.CNAE_ENTREGA)
        tabela.to_parquet(alvo.with_suffix(".tmp"))
        alvo.with_suffix(".tmp").rename(alvo)
        log.info("parte %d: %d estabelecimentos de entrega", n, len(tabela))
    if not offline:
        for nome in ("Municipios.zip", "Simples.zip"):
            cnpj.baixar(mes, nome, raw)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Quebra nas aberturas de MEI de entrega (D-040)")
    p.add_argument("--mes", help="publicacao do CNPJ, AAAA-MM (padrao: a mais recente)")
    p.add_argument("--offline", action="store_true", help="sem rede: so o que ja foi baixado")
    p.add_argument("--universo", type=Path, default=UNIVERSO)
    p.add_argument("--wayback", type=Path, default=TABELAS / "cronologia_wayback.csv")
    p.add_argument("--saida", type=Path, default=TABELAS)
    args = p.parse_args(argv)

    if args.mes:
        mes = args.mes
    elif args.offline:
        baixados = sorted(d.name for d in RAW_CNPJ.glob("????-??") if d.is_dir())
        if not baixados:
            log.error("nada em %s; rode sem --offline", RAW_CNPJ)
            return 1
        mes = baixados[-1]
    else:
        mes = cnpj.ultimo_mes()
    raw, interim = RAW_CNPJ / mes, INTERIM / "cnpj" / mes
    log.info("publicacao do CNPJ: %s", mes)
    preparar(mes, raw, interim, args.offline)

    estab = pd.concat(
        [pd.read_parquet(interim / f"entrega_{n}.parquet") for n in cnpj.PARTES],
        ignore_index=True,
    )
    caminho_ponte = interim / "ponte_municipio.parquet"
    if caminho_ponte.exists():
        ponte = pd.read_parquet(caminho_ponte)
    elif args.offline:
        log.error("sem %s; a ponte usa a API do IBGE, rode sem --offline", caminho_ponte)
        return 1
    else:
        nomes = cnpj.ler_municipios(raw / "Municipios.zip")
        indice = mun.construir_indice(ibge.listar_municipios())
        ponte, falta = mei.ponte_municipios(estab, nomes, indice)
        ponte.to_parquet(caminho_ponte)
        log.info("ponte: %d pares casados; sem par: %s", len(ponte), falta.values.tolist())

    caminho_simples = interim / "simples_entrega.parquet"
    if not caminho_simples.exists() and (raw / "Simples.zip").exists():
        cnpj.filtrar_simples(raw / "Simples.zip", set(estab["cnpj_basico"])).to_parquet(
            caminho_simples
        )

    universo = pd.read_csv(args.universo)
    # O mes da publicacao esta cortado no meio (a Receita fecha a base em dias
    # variaveis): a serie para no mes anterior.
    fim_serie = str(pd.Period(mes, freq="M") - 1)
    aberturas = mei.aberturas_mensais(estab, ponte, SERIE_INICIO, fim_serie)
    contagens = mei.matriz(aberturas, universo["municipio_ibge"].tolist(), SERIE_INICIO, fim_serie)
    tabela = mei.tratamento(universo, contagens, SERIE_INICIO)

    garantir(args.saida)
    tabela.to_csv(args.saida / "tratamento_mei_municipio.csv", index=False)
    aberturas.to_csv(args.saida / "aberturas_mei_municipio_mes.csv", index=False)
    ano = tabela["mes_quebra"].str.slice(0, 4).replace("", "sem quebra")
    por_ano = pd.crosstab(tabela["faixa"], ano).reindex(list(mei.ROTULOS_FAIXA))
    por_ano.to_csv(args.saida / "mei_quebra_por_faixa_ano.csv")

    serie = aberturas[aberturas["municipio_ibge"].isin(universo["municipio_ibge"])]
    serie = serie.assign(ano=serie["mes"].str.slice(0, 4))
    print(f"\n=== Aberturas 5320-2/02 no universo, por ano (serie ate {fim_serie}) ===")
    print(serie.groupby("ano")["aberturas"].sum().to_frame().T.to_string(index=False))
    if caminho_simples.exists():
        simples = pd.read_parquet(caminho_simples)
        mei_nasc = estab.merge(simples, on="cnpj_basico", how="left")
        nasc = mei_nasc["data_opcao_mei"].fillna("").str.slice(0, 6) == mei_nasc[
            "data_inicio"
        ].str.slice(0, 6)
        principal = mei_nasc["cnae_principal"] == mei.CNAE_ENTREGA
        print(f"MEI ja na abertura (CNAE principal): {nasc[principal].mean():.1%}")

    print("\n=== Placebo: quebra em jan-jun/2016, antes de qualquer plataforma ===")
    print(tabela.groupby("faixa")["placebo_2016"].mean().reindex(list(mei.ROTULOS_FAIXA)).round(3))
    print("\n=== Ano da quebra por faixa ===")
    print(por_ano.to_string())
    print("\n=== Grupos de tratamento ===")
    print(tabela["grupo"].value_counts().to_string())
    if args.wayback.exists():
        v = mei.validar_contra_wayback(tabela, pd.read_csv(args.wayback, dtype=str))
        print("\n=== Concordancia com o Wayback (D-039) ===")
        print(
            f"entradas Rappi/Uber Eats com confianca C: {v['entradas_rappi_uber_c']}; "
            f"sem quebra ou quebra > 6 meses depois: {v['atraso']:.1%}\n"
            f"lista de frota do iFood: {v['cidades_lista_ifood']} cidades; "
            f"com quebra ate dez/2023: {v['cobertura_ifood']:.1%}"
        )
    else:
        log.warning("sem %s: rode `make wayback` para a concordancia", args.wayback)
    return 0


if __name__ == "__main__":
    sys.exit(main())
