#!/usr/bin/env python3
"""
Mudanca de codificacao coincidente (plano, secao 7; D-059): series nacionais.

    make codificacao     # baixa os RD completos de novo, so para contar -- horas

1. Fracao de AIH com codigo V (V01-V99) em algum campo secundario, sobre o total
   de AIH, por UF do arquivo x competencia. Retoma de `data/interim/`.
2. Composicao de `campo_causa` entre as AIH da definicao de caso, das AIH ja
   classificadas em `data/raw/sih/` (sem rede).

Escreve `output/tabelas/codificacao_brasil_mes.csv`, `codificacao_uf_mes.csv`,
`codificacao_campo_causa.csv`, `codificacao_resumo.csv` e
`output/figuras/codificacao.png`.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

from vcemal.extract.sih import baixar_ano, caminho_do_cache
from vcemal.paths import FIGURAS, INTERIM, RAW_SIH, TABELAS, garantir

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("codificacao")
for _ruidoso in ("httpx", "httpcore", "urllib3"):
    logging.getLogger(_ruidoso).setLevel(logging.WARNING)

UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]  # fmt: skip
SECUNDARIOS = ["DIAG_SECUN", *[f"DIAGSEC{i}" for i in range(1, 10)]]
CONTAGENS = INTERIM / "codificacao_uf_mes.csv"


def e_transporte(s: pd.Series) -> pd.Series:
    """Codigo do grupo V01-V99 do capitulo XX."""
    return s.astype("string").str.strip().str.upper().str.match(r"V\d\d").fillna(False)


def contar(rd: pd.DataFrame) -> dict[str, int]:
    """Total de AIH, com V em algum secundario e com V no principal."""
    sec = [c for c in SECUNDARIOS if c in rd.columns]
    v_sec = pd.concat([e_transporte(rd[c]) for c in sec], axis=1).any(axis=1)
    v_princ = e_transporte(rd["DIAG_PRINC"]) if "DIAG_PRINC" in rd else pd.Series(False)
    return {
        "aih": len(rd),
        "aih_v_secundario": int(v_sec.sum()),
        "aih_v_principal": int(v_princ.sum()),
        "campos_secundarios": len(sec),
    }


def serie_rd(ufs: list[str], anos: range) -> pd.DataFrame:
    feito = pd.read_csv(CONTAGENS) if CONTAGENS.exists() else pd.DataFrame()
    ja = set(zip(feito["uf"], feito["ano"], strict=True)) if len(feito) else set()
    cache = caminho_do_cache()
    for uf in ufs:
        for ano in anos:
            if (uf, ano) in ja:
                continue
            antes = set(cache.rglob("RD*.parquet")) if cache.exists() else set()
            caminhos = baixar_ano(uf, ano)
            linhas = []
            for mes, caminho in sorted(caminhos.items()):
                cols = ["DIAG_PRINC", *SECUNDARIOS]
                rd = pd.read_parquet(caminho)
                rd = rd[[c for c in cols if c in rd.columns]]
                linhas.append({"uf": uf, "ano": ano, "mes": mes} | contar(rd))
                # So apaga o que este script trouxe ao cache; o FTP fica (D-036).
                p = Path(caminho)
                if p.is_relative_to(cache) and p not in antes:
                    p.unlink(missing_ok=True)
            if not linhas:
                log.warning("%s %d: nenhum RD", uf, ano)
                continue
            parte = pd.DataFrame(linhas)
            parte.to_csv(CONTAGENS, mode="a", header=not CONTAGENS.exists(), index=False)
            log.info("%s %d: %d meses, %d AIH", uf, ano, len(parte), parte["aih"].sum())
    return pd.read_csv(CONTAGENS)


_PARTE = re.compile(r"ano=(\d{4})/mes=(\d{2})")


def campo_causa() -> pd.DataFrame:
    linhas = []
    for p in sorted(RAW_SIH.glob("uf=*/ano=*/mes=*/parte.parquet")):
        ano, mes = map(int, _PARTE.search(p.as_posix()).groups())
        c = pd.read_parquet(p, columns=["campo_causa"])["campo_causa"].value_counts()
        linhas += [{"ano": ano, "mes": mes, "campo_causa": k, "aih": int(v)} for k, v in c.items()]
    t = pd.DataFrame(linhas).groupby(["ano", "mes", "campo_causa"], as_index=False)["aih"].sum()
    t["pct"] = 100 * t["aih"] / t.groupby(["ano", "mes"])["aih"].transform("sum")
    return t


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Mudanca de codificacao (D-059)")
    p.add_argument("--ufs", nargs="+", default=UFS)
    p.add_argument("--inicio", type=int, default=2015)
    p.add_argument("--fim", type=int, default=2025)
    args = p.parse_args(argv)
    garantir(INTERIM, TABELAS, FIGURAS)

    uf_mes = serie_rd(args.ufs, range(args.inicio, args.fim + 1))
    uf_mes.to_csv(TABELAS / "codificacao_uf_mes.csv", index=False)
    br = uf_mes.groupby(["ano", "mes"], as_index=False)[
        ["aih", "aih_v_secundario", "aih_v_principal"]
    ].sum()
    br["pct_v_secundario"] = 100 * br["aih_v_secundario"] / br["aih"]
    br["pct_v_principal"] = 100 * br["aih_v_principal"] / br["aih"]
    br["competencias"] = uf_mes.groupby(["ano", "mes"]).size().to_numpy()
    br.to_csv(TABELAS / "codificacao_brasil_mes.csv", index=False)

    cc = campo_causa()
    cc.to_csv(TABELAS / "codificacao_campo_causa.csv", index=False)

    # Leitura fixada no D-059.
    a = br.groupby("ano")[["aih", "aih_v_secundario"]].sum()
    pct_ano = 100 * a["aih_v_secundario"] / a["aih"]
    salto = br["pct_v_secundario"].diff().abs()
    i = salto.idxmax()
    resumo = pd.DataFrame([{
        "pct_v_secundario_2017": pct_ano.get(2017, float("nan")),
        "pct_v_secundario_2018": pct_ano.get(2018, float("nan")),
        "variacao_2018_2017_pp": pct_ano.get(2018, float("nan")) - pct_ano.get(2017, float("nan")),
        "maior_salto_mensal_pp": salto.max(),
        "maior_salto_em": f"{br.loc[i, 'ano']}-{br.loc[i, 'mes']:02d}",
        "salto_mensal_mediano_pp": salto.median(),
        "competencias_com_27_ufs": int((br["competencias"] == 27).sum()),
    }])  # fmt: skip
    resumo.to_csv(TABELAS / "codificacao_resumo.csv", index=False)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = pd.to_datetime(dict(year=br["ano"], month=br["mes"], day=1))
    piv = cc.pivot_table(index=["ano", "mes"], columns="campo_causa", values="pct").fillna(0)
    xc = pd.to_datetime(
        dict(year=piv.index.get_level_values(0), month=piv.index.get_level_values(1), day=1)
    )  # noqa: E501
    fig, axs = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    axs[0].plot(x, br["pct_v_secundario"], label="V em campo secundario")
    axs[0].plot(x, br["pct_v_principal"], label="V em DIAG_PRINC")
    axs[0].set_ylabel("% das AIH")
    axs[0].legend(frameon=False, fontsize=8)
    axs[0].set_title(
        "Mudanca de codificacao (D-059): series nacionais do RD", loc="left", fontsize=9
    )
    for col in piv.columns:
        axs[1].plot(xc, piv[col], label=col)
    axs[1].set_ylabel("% das AIH da definicao de caso")
    axs[1].legend(frameon=False, fontsize=7, ncol=4)
    for ax in axs:
        ax.axvspan(pd.Timestamp("2017-07-01"), pd.Timestamp("2018-12-31"), color="grey", alpha=0.15)
    fig.tight_layout()
    fig.savefig(FIGURAS / "codificacao.png", dpi=200)

    print(resumo.T.to_string(header=False))
    print("\nFracao anual com V em campo secundario (%):")
    print(pct_ano.round(3).to_string())
    print("\nComposicao de campo_causa por ano (%):")
    anual = cc.groupby(["ano", "campo_causa"])["aih"].sum().unstack(fill_value=0)
    print((100 * anual.div(anual.sum(axis=1), axis=0)).round(1).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
