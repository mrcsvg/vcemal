"""Exploração do tratamento congelado e da série do iFood para a versão prévia do artigo.

Lê só arquivos versionados em docs/fontes/ (nenhum microdado, nenhum cruzamento
com o SIH — D-006). Escreve figuras em artigo/figuras/ e tabelas em artigo/tabelas/.
Uso: python artigo/analise_artigo.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
TRAT = RAIZ / "docs/fontes/cronologia/tratamento_mei_municipio.csv"
IFOOD = RAIZ / "docs/fontes/ifood_prosus.csv"
FIG = RAIZ / "artigo/figuras"
TAB = RAIZ / "artigo/tabelas"
HASH_PRE_REGISTRO = "128999bd21de00854c717e181657f5d1832ce78222ec9ef6dd99a3bd8a7654a2"

REGIAO = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight"})
COR = {"20-50 mil": "#4C72B0", "50-100 mil": "#DD8452"}


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)

    h = hashlib.sha256(TRAT.read_bytes()).hexdigest()
    assert h == HASH_PRE_REGISTRO, f"tratamento difere do congelado: {h}"
    print(f"SHA-256 confere com o pré-registro: {h}")

    t = pd.read_csv(TRAT, dtype={"municipio_ibge": str})
    t["regiao"] = t["municipio_ibge"].str[0].map(REGIAO)
    t["faixa_pop"] = pd.cut(t["populacao_2022"], [0, 50_000, 100_000, 250_000, 1e9],
                            labels=["20-50 mil", "50-100 mil", "100-250 mil", "250 mil+"], right=False)

    # Tabela 1: grupos por faixa populacional
    t1 = pd.crosstab(t["faixa_pop"], t["grupo"], margins=True, margins_name="Total")
    t1.to_csv(TAB / "t1_grupos_por_faixa.csv")
    print("\nTabela 1 — grupos por faixa\n", t1)

    # Tabela 2: placebo de 2016 por faixa
    t2 = t.groupby("faixa_pop", observed=True).agg(municipios=("municipio_ibge", "size"),
                                                   placebo_dispara=("placebo_2016", "sum"))
    t2["pct_placebo"] = (100 * t2["placebo_dispara"] / t2["municipios"]).round(1)
    t2.to_csv(TAB / "t2_placebo_2016_por_faixa.csv")
    print("\nTabela 2 — placebo 2016\n", t2)

    d = t[t["grupo"] == "datado"].copy()
    d["mes"] = pd.PeriodIndex(d["mes_tratamento"], freq="M")
    d["ano"] = d["mes"].dt.year

    # Tabela 3: coortes por ano e faixa + estrato de auditoria
    t3 = pd.crosstab(d["ano"], d["faixa"], margins=True, margins_name="Total")
    t3.to_csv(TAB / "t3_coortes_por_ano_faixa.csv")
    print("\nTabela 3 — coortes por ano\n", t3)

    # Janela balanceada e ∈ [−12, +24]: coortes 2017-07 a 2023-12
    ini, fim = pd.Period("2017-07", "M"), pd.Period("2023-12", "M")
    d["janela"] = "na janela balanceada"
    d.loc[d["mes"] < ini, "janela"] = "antes de 2017-07"
    d.loc[d["mes"] > fim, "janela"] = "depois de 2023-12"
    t4 = d["janela"].value_counts()
    t4.to_csv(TAB / "t4_janela_balanceada.csv")
    print("\nTabela 4 — janela balanceada\n", t4)

    # Tabela 5: grupos por região
    t5 = pd.crosstab(t["regiao"], t["grupo"], margins=True, margins_name="Total")
    t5.to_csv(TAB / "t5_grupos_por_regiao.csv")
    print("\nTabela 5 — grupos por região\n", t5)

    # Figura 1: coortes de tratamento por ano, por faixa
    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    piv = pd.crosstab(d["ano"], d["faixa"]).reindex(range(2017, 2026), fill_value=0)
    base = None
    for f in ["20-50 mil", "50-100 mil"]:
        ax.bar(piv.index, piv[f], bottom=base, color=COR[f], label=f"{f} habitantes", width=0.75)
        base = piv[f] if base is None else base + piv[f]
    for x, y in zip(piv.index, piv.sum(axis=1)):
        ax.text(x, y + 2, str(y), ha="center", fontsize=8)
    ax.axvspan(2016.5, 2017.5, color="grey", alpha=0.12)
    ax.axvspan(2020.5, 2025.5, color="grey", alpha=0.06)
    ax.set_xticks(piv.index)
    ax.set_ylabel("Municípios (quebra no ano)")
    ax.set_title("Mês de tratamento dos 640 municípios 'datado', por ano da quebra", loc="left", fontsize=9)
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(FIG / "fig1_coortes.png")
    plt.close(fig)

    # Figura 2: proporção acumulada tratada (entre datado + sem_quebra) por mês
    elegiveis = (t["grupo"].isin(["datado", "sem_quebra"])).sum()
    serie = d["mes"].value_counts().sort_index()
    idx = pd.period_range("2017-01", "2025-12", freq="M")
    acum = serie.reindex(idx, fill_value=0).cumsum() / elegiveis * 100
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    ax.plot(idx.to_timestamp(), acum.values, color="#4C72B0")
    ax.axvspan(pd.Timestamp("2017-07"), pd.Timestamp("2023-12"), color="#55A868", alpha=0.10,
               label="coortes da janela balanceada [−12, +24]")
    ax.set_ylabel("% tratados (acumulado)")
    ax.set_title(f"Adoção escalonada: % dos {elegiveis} municípios de 20–100 mil já tratados", loc="left", fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.savefig(FIG / "fig2_adocao_acumulada.png")
    plt.close(fig)
    pd.DataFrame({"mes": idx.astype(str), "pct_tratados": acum.values.round(2)}).to_csv(
        TAB / "t6_adocao_acumulada.csv", index=False)

    # Figura 3: iFood — pedidos, entregadores e resultado operacional (Prosus)
    f = pd.read_csv(IFOOD)
    w = f.pivot_table(index="ano_fiscal", columns="metrica", values="valor", aggfunc="first")
    w["resultado_operacional"] = w["aebit"].fillna(w["trading_profit"])
    w[["pedidos", "entregadores_brasil", "cidades_brasil", "receita", "resultado_operacional"]].to_csv(
        TAB / "t7_ifood_prosus_nominal_usd.csv")
    # Série em R$ constantes de dez/2025 transcrita do D-032 (make lucro)
    real = pd.DataFrame({
        "ano_fiscal": [2020, 2021, 2022, 2023, 2024, 2025, 2026],
        "resultado_operacional_rs_mi": [-1431, -316, -1209, -385, 521, 1358, 1955],
        "pedidos_mi": [276, 553, 733, 832, 981, 1261, 1877],
        "entregadores_mil": [170, 209, 232, 217, 314, 443, 621],
    })
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.8))
    cores = ["#C44E52" if v < 0 else "#55A868" for v in real["resultado_operacional_rs_mi"]]
    axs[0].bar(real["ano_fiscal"], real["resultado_operacional_rs_mi"] / 1000, color=cores)
    axs[0].axhline(0, color="black", lw=0.6)
    axs[0].set_title("Resultado operacional (R$ bi, dez/2025)", loc="left", fontsize=9)
    axs[0].set_xlabel("Ano fiscal (abr–mar)")
    axs[1].plot(real["ano_fiscal"], real["entregadores_mil"], marker="o", color="#4C72B0", label="entregadores ativos (mil)")
    ax2 = axs[1].twinx()
    ax2.plot(real["ano_fiscal"], real["pedidos_mi"], marker="s", color="#DD8452", label="pedidos (milhões)")
    ax2.spines["top"].set_visible(False)
    axs[1].set_title("Entregadores (azul, mil) e pedidos (laranja, mi)", loc="left", fontsize=9)
    axs[1].set_xlabel("Ano fiscal (abr–mar)")
    fig.tight_layout()
    fig.savefig(FIG / "fig3_ifood.png")
    plt.close(fig)

    # Figura 4: a cegueira do registro — números documentados (D-019, D-030)
    fig, ax = plt.subplots(figsize=(6.3, 2.4))
    rot = ["Internações de motociclista\nno SIH (2016–2023)",
           "Com nexo ocupacional\nregistrado (CAR_INT 03/04)"]
    val = [965_714, 62]
    ax.barh(rot, val, color=["#4C72B0", "#C44E52"])
    ax.set_xscale("log")
    for i, v in enumerate(val):
        ax.text(v * 1.2, i, f"{v:,}".replace(",", "."), va="center", fontsize=8)
    ax.set_xlim(10, 5e6)
    ax.set_title("Uma internação em 15.576 registra o trabalho como causa (escala log)", loc="left", fontsize=9)
    fig.savefig(FIG / "fig4_nexo.png")
    plt.close(fig)
    print("\nFiguras e tabelas escritas em artigo/")


if __name__ == "__main__":
    main()
