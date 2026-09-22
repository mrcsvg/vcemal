#!/usr/bin/env python3
"""
Cronologia de entrada das plataformas (F3): modelo, validacao, concordancia e consolidacao.

Subcomandos:

    cronologia.py modelo                      escreve as planilhas-modelo em docs/fontes/cronologia/
    cronologia.py universo                    municipios com 20 mil habitantes ou mais (Censo 2022)
                                              -> universo.csv (unico subcomando com rede: IBGE)
    cronologia.py planilha --codificador A    planilha em branco do codificador, uma linha por
                                              municipio x plataforma, em ordem sorteada fixa
    cronologia.py validar A.csv               regras de `vcemal.cronologia.validar`
    cronologia.py comparar A.csv B.csv        kappa, concordancia de data e lista de discordancias
    cronologia.py consolidar A.csv B.csv [--desempates D.csv] [--saida DIR]
                                              aplica as regras de desempate; escreve
                                              cronologia_entrada.csv, tratamento_municipio.csv e
                                              pendentes.csv
    cronologia.py prosus CONSOLIDADA.csv      municipios com iFood por ano fiscal contra as
                                              cidades que a Prosus publica (D-032)

`make cronologia` roda `consolidar` sobre as planilhas dos dois codificadores,
se existirem. As regras estao em `src/vcemal/cronologia.py` e o protocolo em
`docs/protocolo-cronologia-entrada.md`. Nada aqui toca o SIH: a cronologia so
cruza com o desfecho depois do pre-registro (D-006).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from vcemal import cronologia as cro
from vcemal.extract import ibge
from vcemal.paths import FONTE_IFOOD_PROSUS, FONTES, TABELAS, garantir

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cronologia")

PASTA = FONTES / "cronologia"
CODIFICADOR_A = PASTA / "codificador_a.csv"
CODIFICADOR_B = PASTA / "codificador_b.csv"
DESEMPATES = PASTA / "desempates.csv"
UNIVERSO = PASTA / "universo.csv"
#: Semente do sorteio da ordem de codificacao: a mesma para os dois codificadores,
#: para os blocos coincidirem e a concordancia ser calculada por bloco.
SEMENTE = 20260920

EXEMPLOS = [
    {
        "municipio_ibge": "3106200",
        "uf": "MG",
        "municipio": "Belo Horizonte",
        "plataforma": "99food",
        "evento": "entrada",
        "data_min": "2019-11",
        "data_max": "2019-11",
        "tipo_evidencia": 1,
        "confianca": "A",
        "fonte": "Release da 99 sobre a estreia do 99Food",
        "url": "https://exemplo.invalido/release",
        "data_acesso": "2026-09-20",
        "trecho": "a 99 lanca hoje em Belo Horizonte o 99Food, com entregadores parceiros",
        "buscas": "",
        "observacao": "exemplo: apagar antes de codificar",
        "codificador": "A",
    },
    {
        "municipio_ibge": "4106902",
        "uf": "PR",
        "municipio": "Curitiba",
        "plataforma": "ifood",
        "evento": "entrada",
        "data_min": "2018-06",
        "data_max": "2018-11",
        "tipo_evidencia": 3,
        "confianca": "C",
        "fonte": "Wayback: cadastro de entregadores lista Curitiba em nov/2018, nao em jun/2018",
        "url": "https://web.archive.org/web/2018*/exemplo",
        "data_acesso": "2026-09-20",
        "trecho": "",
        "buscas": "",
        "observacao": "exemplo: apagar antes de codificar",
        "codificador": "A",
    },
    {
        "municipio_ibge": "2927408",
        "uf": "BA",
        "municipio": "Salvador",
        "plataforma": "keeta",
        "evento": "entrada",
        "data_min": "",
        "data_max": "",
        "tipo_evidencia": 0,
        "confianca": "N",
        "fonte": "",
        "url": "",
        "data_acesso": "2026-09-20",
        "trecho": "",
        "buscas": '"Keeta" Salvador; "Keeta" "entregadores" Salvador; keeta.com/br cidades',
        "observacao": "exemplo: apagar antes de codificar",
        "codificador": "A",
    },
]

EXEMPLO_DESEMPATE = [
    {
        "municipio_ibge": "4106902",
        "plataforma": "ifood",
        "evento": "entrada",
        "escolha": "propria",
        "data_min": "2018-09",
        "data_max": "2018-09",
        "confianca": "B",
        "justificativa": "exemplo: terceiro codificador achou materia de 12/09/2018",
        "adjudicador": "C",
    }
]


def _ler(caminho: Path) -> list[dict]:
    df = pd.read_csv(caminho, dtype=str, keep_default_na=False)
    return df.to_dict("records")


def cmd_modelo(args) -> int:
    garantir(args.saida)
    pd.DataFrame(EXEMPLOS, columns=list(cro.COLUNAS)).to_csv(args.saida / "modelo.csv", index=False)
    pd.DataFrame(EXEMPLO_DESEMPATE, columns=list(cro.COLUNAS_DESEMPATE)).to_csv(
        args.saida / "desempates_modelo.csv", index=False
    )
    log.info("modelos em %s", args.saida)
    return 0


def cmd_universo(args) -> int:
    nomes = {m["id"]: m for m in ibge.listar_municipios()}
    pop = ibge.populacao_censo_2022()
    linhas = [
        {
            "municipio_ibge": f"{r['municipio_ibge']:07d}",
            "uf": nomes[r["municipio_ibge"]]["uf"],
            "municipio": nomes[r["municipio_ibge"]]["nome"],
            "populacao_2022": r["populacao"],
        }
        for r in pop
        if r["municipio_ibge"] in nomes and r["populacao"] >= args.minimo
    ]
    garantir(args.saida.parent)
    pd.DataFrame(linhas).sort_values("municipio_ibge").to_csv(args.saida, index=False)
    log.info(
        "universo: %d municipios com %d+ habitantes -> %s", len(linhas), args.minimo, args.saida
    )
    return 0


def cmd_planilha(args) -> int:
    if not args.universo.exists():
        log.error("sem %s -- rode `scripts/cronologia.py universo` antes", args.universo)
        return 1
    uni = pd.read_csv(args.universo, dtype=str)
    uni = uni.sample(frac=1, random_state=SEMENTE).reset_index(drop=True)
    plataformas = args.plataformas or list(cro.PLATAFORMAS)
    linhas = [
        {
            **{c: "" for c in cro.COLUNAS},
            "municipio_ibge": m["municipio_ibge"],
            "uf": m["uf"],
            "municipio": m["municipio"],
            "plataforma": plat,
            "evento": "entrada",
            "codificador": args.codificador,
        }
        for _, m in uni.iterrows()
        for plat in plataformas
    ]
    destino = args.saida or PASTA / f"codificador_{args.codificador.lower()}.csv"
    if destino.exists() and not args.sobrescrever:
        log.error("%s ja existe; use --sobrescrever se for mesmo recomecar", destino)
        return 1
    pd.DataFrame(linhas, columns=list(cro.COLUNAS)).to_csv(destino, index=False)
    log.info(
        "%d linhas (%d municipios x %d plataformas) em ordem sorteada -> %s",
        len(linhas),
        len(uni),
        len(plataformas),
        destino,
    )
    return 0


def cmd_validar(args) -> int:
    linhas = _ler(args.arquivo)
    cro.validar(linhas)
    n_enc = sum(1 for r in linhas if r["confianca"] != "N")
    log.info("%s: %d linhas validas, %d eventos encontrados", args.arquivo, len(linhas), n_enc)
    return 0


def _imprimir_comparacao(res: dict) -> None:
    k = res["kappa_existencia"]
    p = res["pct_data_concordante"]
    print("\n=== Concordancia entre codificadores ===")
    print(f"pares municipio x plataforma : {res['n_pares']}")
    print(f"kappa (encontrou / nao)      : {k:.3f}" if k is not None else "kappa: n/a")
    print(
        f"datas concordantes (+-{cro.TOLERANCIA_MESES} mes) : "
        + (f"{p:.1%} de {res['n_datas']}" if p is not None else "n/a")
    )
    print(f"discordancias                : {len(res['discordancias'])}")
    for d in res["discordancias"][:30]:
        print("  ", d)


def cmd_comparar(args) -> int:
    a, b = _ler(args.a), _ler(args.b)
    cro.validar(a)
    cro.validar(b)
    res = cro.comparar(a, b)
    _imprimir_comparacao(res)
    return 0


def cmd_consolidar(args) -> int:
    a, b = _ler(args.a), _ler(args.b)
    cro.validar(a)
    cro.validar(b)
    _imprimir_comparacao(cro.comparar(a, b))
    desempates = _ler(args.desempates) if args.desempates and args.desempates.exists() else []
    consolidada, pendentes = cro.consolidar(a, b, desempates)
    trat = cro.tratamento(consolidada)
    garantir(args.saida)
    pd.DataFrame(consolidada).to_csv(args.saida / "cronologia_entrada.csv", index=False)
    pd.DataFrame(trat).to_csv(args.saida / "tratamento_municipio.csv", index=False)
    pd.DataFrame(
        [
            {
                "municipio_ibge": p["chave"][0],
                "plataforma": p["chave"][1],
                "evento": p["chave"][2],
                "motivo": p["motivo"],
                "a": f"{p['a']['data_min']}..{p['a']['data_max']} ({p['a']['confianca']})"
                if p["a"]
                else "",
                "b": f"{p['b']['data_min']}..{p['b']['data_max']} ({p['b']['confianca']})"
                if p["b"]
                else "",
            }
            for p in pendentes
        ],
        columns=["municipio_ibge", "plataforma", "evento", "motivo", "a", "b"],
    ).to_csv(args.saida / "pendentes.csv", index=False)
    regras = pd.Series([r["regra"] for r in consolidada]).value_counts()
    print("\n=== Regras aplicadas ===")
    print(regras.to_string())
    print(f"\npendentes de adjudicacao: {len(pendentes)} -> {args.saida / 'pendentes.csv'}")
    tratados = sum(1 for t in trat if t["tratado"])
    print(f"municipios no universo: {len(trat)}; tratados: {tratados}")
    if pendentes:
        print("A cronologia NAO esta fechada: preencha desempates.csv e rode de novo.")
    return 0


def cmd_prosus(args) -> int:
    """Municipios com entrada do iFood ate marco de cada ano fiscal, contra a Prosus."""
    cons = _ler(args.consolidada)
    prosus = pd.read_csv(args.fonte)
    cidades = prosus[prosus["metrica"] == "cidades_brasil"].set_index("ano_fiscal")["valor"]
    entradas = [
        r
        for r in cons
        if r["plataforma"] == "ifood" and r["evento"] == "entrada" and r["confianca"] != "N"
    ]
    print("\n=== iFood: municipios codificados x cidades publicadas pela Prosus (fim de marco) ===")
    print("ano_fiscal  codificados  prosus")
    for fy, n in cidades.items():
        corte = cro.mes_indice(f"{int(fy)}-03")
        cod = sum(1 for r in entradas if cro.mes_indice(r["data_max"]) <= corte)
        print(f"{int(fy)}        {cod:5d}       {int(n):5d}")
    print("codificados > prosus e sinal de erro; muito abaixo e cobertura incompleta do universo.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Cronologia de entrada das plataformas (F3)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("modelo")
    s.add_argument("--saida", type=Path, default=PASTA)
    s.set_defaults(func=cmd_modelo)

    s = sub.add_parser("universo")
    s.add_argument("--minimo", type=int, default=cro.POPULACAO_MINIMA_UNIVERSO)
    s.add_argument("--saida", type=Path, default=UNIVERSO)
    s.set_defaults(func=cmd_universo)

    s = sub.add_parser("planilha")
    s.add_argument("--codificador", required=True, help="identificador curto: A, B, C")
    s.add_argument("--universo", type=Path, default=UNIVERSO)
    s.add_argument("--plataformas", nargs="*", choices=list(cro.PLATAFORMAS))
    s.add_argument("--saida", type=Path, default=None)
    s.add_argument("--sobrescrever", action="store_true")
    s.set_defaults(func=cmd_planilha)

    s = sub.add_parser("validar")
    s.add_argument("arquivo", type=Path)
    s.set_defaults(func=cmd_validar)

    s = sub.add_parser("comparar")
    s.add_argument("a", type=Path)
    s.add_argument("b", type=Path)
    s.set_defaults(func=cmd_comparar)

    s = sub.add_parser("consolidar")
    s.add_argument("a", type=Path, nargs="?", default=CODIFICADOR_A)
    s.add_argument("b", type=Path, nargs="?", default=CODIFICADOR_B)
    s.add_argument("--desempates", type=Path, default=DESEMPATES)
    s.add_argument("--saida", type=Path, default=TABELAS)
    s.set_defaults(func=cmd_consolidar)

    s = sub.add_parser("prosus")
    s.add_argument("consolidada", type=Path)
    s.add_argument("--fonte", type=Path, default=FONTE_IFOOD_PROSUS)
    s.set_defaults(func=cmd_prosus)

    args = p.parse_args(argv)
    if args.cmd == "consolidar" and not (args.a.exists() and args.b.exists()):
        log.error(
            "faltam as planilhas dos codificadores (%s, %s). Leia "
            "docs/protocolo-cronologia-entrada.md e comece por `scripts/cronologia.py modelo`.",
            args.a,
            args.b,
        )
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
