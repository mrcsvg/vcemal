#!/usr/bin/env python3
"""
Figura de contraste: resultado operacional do iFood e valor pago pelo SUS.

Sem rede. Le as duas tabelas ja geradas e as poe no mesmo eixo:

    make custo lucro   # antes
    make contraste     # este script

Escreve `contraste_ifood_sus.csv` em `output/tabelas/` (a tabela que a figura
desenha, e a leitura de quem nao le grafico) e `contraste_ifood_sus.png` e
`.svg` em `output/figuras/`.

Um eixo so: as duas series estao em R$ milhoes da mesma base de precos. A
receita fica na tabela e fora da figura -- na escala dela, as outras duas
viram linhas retas perto do zero. A montagem esta em
`vcemal.analyze.contraste`; aqui e so I/O e desenho.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from vcemal.analyze import contraste  # noqa: E402
from vcemal.paths import FIGURAS, TABELAS, garantir  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("contraste")

# Paleta de referencia (validada: duas series, modo claro) e tinta do grafico.
AZUL = "#2a78d6"
LARANJA = "#eb6834"
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
MUDA = "#898781"
GRADE = "#e1e0d9"
BASE = "#c3c2b7"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

TITULO = "Resultado operacional do iFood e valor pago pelo SUS\ncom internações de motociclistas"
NOTA = (
    "O valor do SUS é o de todas as internações de motociclista (CID V20–V29), "
    "entregador ou não; a parte atribuível às plataformas não está\nestimada aqui. "
    "É piso: só o que o SUS pagou pela AIH. Resultado do iFood como a Prosus "
    "reporta, convertido pelo câmbio médio e deflacionado pelo IPCA.\n"
    "Fontes: SIH/SUS (DATASUS); Prosus, relatórios anuais e semestrais; "
    "BCB (SGS 3698); IBGE (SIDRA 1737)."
)


def milhar(x: float, _=None) -> str:
    """1234.5 -> '1.235' (separador de milhar brasileiro)."""
    return f"{x:,.0f}".replace(",", ".")


def desenhar(t: pd.DataFrame, destino: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
            "font.size": 10,
            "axes.edgecolor": BASE,
            "axes.labelcolor": TINTA_2,
            "xtick.color": MUDA,
            "ytick.color": MUDA,
        }
    )
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=200)
    fig.patch.set_facecolor(SUPERFICIE)
    ax.set_facecolor(SUPERFICIE)

    anel = dict(markersize=8, markeredgewidth=2, markeredgecolor=SUPERFICIE)
    linha = dict(linewidth=2, solid_capstyle="round", solid_joinstyle="round")

    sus = t["sus_pagou"].dropna()
    rotulo_sus = "SUS: pago por internações de motociclista"
    ax.plot(sus.index, sus.values, color=LARANJA, marker="o", label=rotulo_sus, **linha, **anel)

    # Um trecho por metrica: ligar trading profit a aEBIT alisaria a emenda.
    ifood = t.dropna(subset=["resultado_ifood"])
    trechos = ifood.groupby("metrica_resultado", sort=False)["resultado_ifood"]
    for i, (_, trecho) in enumerate(trechos):
        rotulo = "iFood: resultado operacional" if i == 0 else None
        ax.plot(trecho.index, trecho.values, color=AZUL, marker="o", label=rotulo, **linha, **anel)

    ax.axhline(0, color=BASE, linewidth=1, zorder=1)
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(BASE)
    ax.tick_params(length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(milhar))
    anos = list(t.index)
    ax.set_xticks(anos, [str(a) for a in anos])
    ax.set_xlim(anos[0] - 0.3, anos[-1] + 1.6)

    # Rotulos diretos so na ponta, em tinta de texto (nunca na cor da serie).
    fim = anos[-1]
    for coluna in ("resultado_ifood", "sus_pagou"):
        valor = t.loc[fim, coluna]
        ax.annotate(
            f"R$ {milhar(valor)} mi",
            (fim, valor),
            xytext=(10, 0),
            textcoords="offset points",
            va="center",
            color=TINTA,
            fontweight="bold",
        )

    # A emenda de metrica, dita onde acontece.
    metricas = t["metrica_resultado"].dropna()
    antes = metricas[metricas == "trading_profit"].index.max()
    depois = metricas[metricas == "aebit"].index.min()
    if pd.notna(antes) and pd.notna(depois):
        meio = (antes + depois) / 2
        ax.axvline(meio, color=GRADE, linewidth=1, zorder=0)
        topo = ax.get_ylim()[1]
        emenda = dict(va="top", color=MUDA, fontsize=8.5)
        ax.text(meio - 0.08, topo, "trading profit", ha="right", **emenda)
        ax.text(meio + 0.08, topo, "aEBIT", ha="left", **emenda)

    ano_base, mes_base = t["base_precos"].iloc[0].split("-")
    subtitulo = f"R$ milhões de {MESES[int(mes_base) - 1]}/{ano_base}, ano civil"
    fig.suptitle(TITULO, x=0.06, y=0.97, ha="left", fontsize=13, fontweight="bold", color=TINTA)
    fig.text(0.06, 0.855, subtitulo, ha="left", color=TINTA_2, fontsize=10)
    fig.legend(
        loc="upper left",
        bbox_to_anchor=(0.052, 0.835),
        ncol=2,
        frameon=False,
        labelcolor=TINTA_2,
        fontsize=9,
        handlelength=1.6,
        columnspacing=2.0,
    )
    fig.text(0.06, 0.015, NOTA, ha="left", va="bottom", color=MUDA, fontsize=7.2, linespacing=1.5)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.75, bottom=0.2)

    for sufixo in ("png", "svg"):
        caminho = destino.with_suffix(f".{sufixo}")
        fig.savefig(caminho, facecolor=SUPERFICIE)
        log.info("figura -> %s", caminho)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Figura de contraste iFood x SUS")
    p.add_argument("--tabelas", type=Path, default=TABELAS)
    p.add_argument("--figuras", type=Path, default=FIGURAS)
    p.add_argument("--inicio", type=int, default=2020, help="primeiro ano da figura")
    args = p.parse_args(argv)

    entradas = ("lucro_ifood_por_ano.csv", "custo_por_ano.csv")
    faltando = [n for n in entradas if not (args.tabelas / n).exists()]
    if faltando:
        log.error("faltam %s -- rode `make custo lucro` antes", ", ".join(faltando))
        return 1

    t = contraste.lado_a_lado(
        pd.read_csv(args.tabelas / "lucro_ifood_por_ano.csv"),
        pd.read_csv(args.tabelas / "custo_por_ano.csv"),
    )
    garantir(args.tabelas, args.figuras)
    t.to_csv(args.tabelas / "contraste_ifood_sus.csv")
    log.info("tabela -> %s", args.tabelas / "contraste_ifood_sus.csv")

    janela = t.loc[args.inicio :]
    desenhar(janela, args.figuras / "contraste_ifood_sus")
    print(janela.round(1).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
