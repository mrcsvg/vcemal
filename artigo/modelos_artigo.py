"""Dois modelos sobre o tratamento congelado, sem tocar no desfecho (D-006, D-046).

1. Monte Carlo da regra de quebra (`vcemal.mei.detectar_quebra`, o código que
   gerou o tratamento): falso positivo sob nulo de Poisson e sob superdispersão,
   e poder para detectar um salto de r vezes na taxa de aberturas, por faixa.
   As séries simuladas partem da taxa de aberturas de 2015–2016 de cada
   município (`aberturas_base_mes` do arquivo congelado).
2. Modelo de seleção: regressão logística de P(datado) entre os 1.391
   municípios de 20–100 mil, com população, região e a propensão a abrir MEI
   de entrega antes de qualquer plataforma. Validação cruzada estratificada
   5×10 para a AUC.

Lê só `docs/fontes/cronologia/tratamento_mei_municipio.csv`. Uso:
python artigo/modelos_artigo.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score

from vcemal.mei import detectar_quebra, meses

RAIZ = Path(__file__).resolve().parents[1]
TRAT = RAIZ / "docs/fontes/cronologia/tratamento_mei_municipio.csv"
FIG = RAIZ / "artigo/figuras"
TAB = RAIZ / "artigo/tabelas"
HASH = "128999bd21de00854c717e181657f5d1832ce78222ec9ef6dd99a3bd8a7654a2"
SEMENTE = 20261013
REGIAO = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
FAIXAS = ["20-50 mil", "50-100 mil", "100-250 mil", "250 mil+"]
PISO = 0.5 / 24  # o mesmo piso de meia abertura em 24 meses da regra
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight"})


def carregar() -> pd.DataFrame:
    assert hashlib.sha256(TRAT.read_bytes()).hexdigest() == HASH, "tratamento difere do congelado"
    t = pd.read_csv(TRAT, dtype={"municipio_ibge": str})
    t["regiao"] = t["municipio_ibge"].str[0].map(REGIAO)
    t["lam"] = np.maximum(t["aberturas_base_mes"], PISO)
    return t


def simular(lam: np.ndarray, n_meses: int, rng, salto: float = 1.0, mes_salto: int | None = None,
            dispersao: float = 0.0) -> np.ndarray:
    """Contagens municipio x mes ~ Poisson(lam), com salto multiplicativo opcional.

    `dispersao` > 0 é a variância relativa de um choque gama mensal (gama-Poisson),
    para representar aceleração local que não é plataforma.
    """
    taxa = np.repeat(lam[:, None], n_meses, axis=1)
    if mes_salto is not None:
        taxa[:, mes_salto:] *= salto
    if dispersao > 0:
        taxa = taxa * rng.gamma(1 / dispersao, dispersao, size=taxa.shape)
    return rng.poisson(taxa)


def monte_carlo(t: pd.DataFrame, rng, reps: int = 200) -> tuple[pd.DataFrame, pd.DataFrame]:
    # (a) Falso positivo na janela do placebo (2016-01 a 2016-06), série desde 2014-01
    n = len(meses("2014-01", "2016-12"))
    linhas = []
    for disp in [0.0, 0.25, 0.5, 1.0]:
        disparos = np.zeros(len(t))
        for _ in range(reps):
            c = simular(t["lam"].to_numpy(), n, rng, dispersao=disp)
            disparos += detectar_quebra(c, "2014-01", inicio="2016-01", fim="2016-06") >= 0
        fp = pd.Series(disparos / reps).groupby(t["faixa"]).mean() * 100
        for f in FAIXAS:
            linhas.append({"dispersao": disp, "faixa": f, "falso_positivo_pct": round(fp[f], 2)})
    obs = t.groupby("faixa")["placebo_2016"].mean() * 100
    for f in FAIXAS:
        linhas.append({"dispersao": "observado", "faixa": f, "falso_positivo_pct": round(obs[f], 2)})
    fp = pd.DataFrame(linhas)

    # (b) Poder: salto de r vezes em 2019-01, série 2015-01 a 2025-12, sem dispersão
    idx = meses("2015-01", "2025-12")
    m0 = idx.index("2019-01")
    pequenos = t[t["faixa"].isin(["20-50 mil", "50-100 mil"])].reset_index(drop=True)
    lam = pequenos["lam"].to_numpy()
    linhas = []
    for r in [2, 3, 5, 10, 20]:
        acerto = np.zeros(len(pequenos))
        precoce = np.zeros(len(pequenos))
        atrasos = []
        for _ in range(reps // 4):
            c = simular(lam, len(idx), rng, salto=r, mes_salto=m0)
            q = detectar_quebra(c, "2015-01")
            # A quebra é o primeiro mês da janela com abertura: pode cair até 5 meses
            # antes do salto sem ser erro. Antes disso é quebra espúria que esconde a verdadeira.
            ok = (q >= m0 - 5) & (q <= m0 + 12)
            acerto += ok
            precoce += (q >= 0) & (q < m0 - 5)
            atrasos.extend((q[ok] - m0).tolist())
        for f in ["20-50 mil", "50-100 mil"]:
            sel = (pequenos["faixa"] == f).to_numpy()
            linhas.append({"salto": r, "faixa": f,
                           "poder_pct": round(100 * acerto[sel].mean() / (reps // 4), 1),
                           "quebra_antes_do_salto_pct": round(100 * precoce[sel].mean() / (reps // 4), 1)})
        linhas.append({"salto": r, "faixa": "atraso mediano (meses)", "poder_pct": float(np.median(atrasos)) if atrasos else np.nan,
                       "quebra_antes_do_salto_pct": np.nan})
    return fp, pd.DataFrame(linhas)


def selecao(t: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = t[t["grupo"].isin(["datado", "sem_quebra"])].copy()
    d["y"] = (d["grupo"] == "datado").astype(int)
    d["log_pop"] = np.log(d["populacao_2022"] / 1000)
    d["log_base"] = np.log(d["lam"] * 12)  # aberturas por ano em 2015-2016, com piso
    d["regiao"] = pd.Categorical(d["regiao"], ["Sudeste", "Sul", "Centro-Oeste", "Nordeste", "Norte"])
    formulas = {
        "M1 população": "y ~ log_pop",
        "M2 + região": "y ~ log_pop + C(regiao)",
        "M3 + propensão pré-plataforma": "y ~ log_pop + C(regiao) + log_base",
    }
    coefs, ajuste = [], []
    X_all = pd.get_dummies(d[["log_pop", "regiao", "log_base"]], columns=["regiao"], drop_first=True, dtype=float)
    colunas = {"M1 população": ["log_pop"],
               "M2 + região": ["log_pop"] + [c for c in X_all if c.startswith("regiao_")],
               "M3 + propensão pré-plataforma": list(X_all.columns)}
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=SEMENTE)
    for nome, f in formulas.items():
        m = smf.logit(f, d).fit(disp=0, cov_type="cluster", cov_kwds={"groups": d["uf"].astype("category").cat.codes})
        ci = m.conf_int()
        for v in m.params.index.drop("Intercept"):
            coefs.append({"modelo": nome, "variavel": v, "odds_ratio": np.exp(m.params[v]),
                          "ic95_inf": np.exp(ci.loc[v, 0]), "ic95_sup": np.exp(ci.loc[v, 1]), "p": m.pvalues[v]})
        auc = cross_val_score(LogisticRegression(max_iter=1000), X_all[colunas[nome]], d["y"], cv=cv, scoring="roc_auc")
        ajuste.append({"modelo": nome, "auc_cv_media": auc.mean(), "auc_cv_dp": auc.std(),
                       "pseudo_r2": m.prsquared, "aic": m.aic, "n": int(m.nobs)})
    return pd.DataFrame(coefs).round(4), pd.DataFrame(ajuste).round(3)


def figuras(fp: pd.DataFrame, poder: pd.DataFrame, coefs: pd.DataFrame) -> None:
    # Figura 5: falso positivo simulado x observado, e poder por salto
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.9))
    x = np.arange(len(FAIXAS))
    estilos = [(0.0, "Poisson puro", "#BBBBBB"), (0.5, "superdispersão 0,5", "#8DA0CB"),
               (1.0, "superdispersão 1,0", "#4C72B0"), ("observado", "placebo observado", "#C44E52")]
    for k, (disp, rot, cor) in enumerate(estilos):
        v = fp[fp["dispersao"].astype(str) == str(disp)].set_index("faixa").loc[FAIXAS, "falso_positivo_pct"]
        axs[0].bar(x + (k - 1.5) * 0.2, v, 0.2, label=rot, color=cor)
    axs[0].set_xticks(x, FAIXAS, fontsize=7)
    axs[0].set_ylabel("% com quebra em jan–jun/2016")
    axs[0].set_title("Falso positivo: simulado × observado", loc="left", fontsize=9)
    axs[0].legend(frameon=False, fontsize=6.5)
    p = poder[poder["faixa"].isin(["20-50 mil", "50-100 mil"])]
    for f, cor in [("20-50 mil", "#4C72B0"), ("50-100 mil", "#DD8452")]:
        s = p[p["faixa"] == f]
        axs[1].plot(s["salto"], s["poder_pct"], marker="o", color=cor, label=f)
    axs[1].set_xscale("log")
    axs[1].set_xticks([2, 3, 5, 10, 20], ["2×", "3×", "5×", "10×", "20×"])
    axs[1].minorticks_off()
    axs[1].set_ylim(0, 100)
    axs[1].set_ylabel("% datado de −5 a +12 meses")
    axs[1].set_title("Poder: salto de r vezes na taxa", loc="left", fontsize=9)
    axs[1].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "fig5_simulacao_regra.png")
    plt.close(fig)

    # Figura 6: razões de chance de região, M2 contra M3
    fig, ax = plt.subplots(figsize=(6.3, 2.6))
    regioes = ["Sul", "Centro-Oeste", "Nordeste", "Norte"]
    for k, (mod, cor) in enumerate([("M2 + região", "#8DA0CB"), ("M3 + propensão pré-plataforma", "#4C72B0")]):
        s = coefs[coefs["modelo"] == mod].set_index("variavel")
        for i, r in enumerate(regioes):
            v = s.loc[f"C(regiao)[T.{r}]"]
            y = i + (k - 0.5) * 0.3
            ax.plot([v["ic95_inf"], v["ic95_sup"]], [y, y], color=cor)
            ax.plot(v["odds_ratio"], y, "o", color=cor, label=mod if i == 0 else None)
    ax.axvline(1, color="black", lw=0.6)
    ax.set_xscale("log")
    ax.set_yticks(range(len(regioes)), regioes)
    ax.set_xlabel("Razão de chances de ter quebra (ref.: Sudeste), IC 95%")
    ax.set_title("Quem recebe data: região, antes e depois da propensão pré-plataforma", loc="left", fontsize=9)
    ax.legend(frameon=False, fontsize=7, loc="upper right")
    fig.savefig(FIG / "fig6_selecao.png")
    plt.close(fig)


def main() -> None:
    rng = np.random.default_rng(SEMENTE)
    t = carregar()
    fp, poder = monte_carlo(t, rng)
    coefs, ajuste = selecao(t)
    fp.to_csv(TAB / "t8_falso_positivo_simulado.csv", index=False)
    poder.to_csv(TAB / "t9_poder_regra.csv", index=False)
    coefs.to_csv(TAB / "t10_selecao_odds_ratios.csv", index=False)
    ajuste.to_csv(TAB / "t11_selecao_ajuste.csv", index=False)
    figuras(fp, poder, coefs)
    pd.set_option("display.width", 160)
    print(fp.pivot(index="faixa", columns="dispersao", values="falso_positivo_pct").loc[FAIXAS])
    print(poder.pivot(index="salto", columns="faixa", values="poder_pct"))
    print(poder.pivot(index="salto", columns="faixa", values="quebra_antes_do_salto_pct"))
    print(coefs.to_string())
    print(ajuste.to_string())


if __name__ == "__main__":
    main()
