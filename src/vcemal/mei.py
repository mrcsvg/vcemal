"""Chegada de entregador por aplicativo pelas aberturas de MEI de entrega rapida (D-040).

O tratamento do V2 e a chegada de entregador remunerado por corrida. Datar isso
por busca municipio a municipio nao escala (D-039: o Wayback nao data o iFood,
e a busca na web devolve o presente). O Cadastro Nacional da Pessoa Juridica
data por construcao: o entregador de aplicativo que se formaliza abre um MEI
com CNAE 5320-2/02 ("servicos de entrega rapida"), e o cadastro guarda o mes
de inicio de atividade e o municipio do endereco -- que, no MEI, e a casa do
entregador, o mesmo municipio de residencia que o SIH registra.

**O que se mede e o que nao se mede.** A maior parte dos entregadores nao e MEI
(D-031: mais de 84% de informalidade entre motociclistas). Nao se usa o nivel,
usa-se a **quebra**: o mes em que as aberturas do municipio passam a dobrar a
propria linha de base. O motoboy MEI de restaurante existe desde antes das
plataformas; o que elas trazem e o salto.

**A regra, congelada antes de qualquer cruzamento com o SIH.** Para cada
municipio e mes `t` de 2017-01 a 2025-06, com `W` = aberturas em `[t, t+5]` e
`lam` = media mensal de `[t-24, t-1]` vezes 6 (piso de meia abertura em 24
meses), `t` dispara se for o primeiro mes com

    W >= MINIMO_JANELA,  W >= FATOR * lam  e  P(Poisson(lam) >= W) < ALFA,

e a quebra e o primeiro mes de `[t, t+5]` com alguma abertura.

Parametros escolhidos numa grade avaliada so contra placebo (2016) e contra o
Wayback, nunca contra internacao: ver D-040.

**Onde a regra vale.** Abaixo de 100 mil habitantes o placebo de 2016 dispara
em menos de 4% dos municipios (0,7% entre 20 e 50 mil); de 100 mil para cima,
em um quarto -- com muitas aberturas, qualquer aceleracao local passa no teste.
Por isso a quebra so data o tratamento abaixo do corte; acima dele o municipio
e coorte precoce, tratado ate 2018, sem data fina.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import poisson

CNAE_ENTREGA = "5320202"

#: Regra de quebra (D-040). Mudar qualquer um destes e mudar o tratamento.
FATOR = 2.0
MINIMO_JANELA = 5
JANELA = 6
BASE = 24
ALFA = 0.01
#: Primeiro mes candidato: o piso nacional de frota propria mais antigo de uma
#: plataforma de comida e 2016-12 (Uber Eats); 2017-01 e o primeiro mes cheio.
INICIO = "2017-01"
#: Ultimo mes candidato: a janela de 6 meses termina em 2025-12, o fim do painel do SIH.
FIM = "2025-06"
#: Placebo: meses candidatos antes de qualquer plataforma, com base de 24 meses completa.
PLACEBO = ("2016-01", "2016-06")

#: Abaixo disto a quebra data o tratamento; de 100 mil para cima e coorte precoce.
CORTE_POPULACAO = 100_000
FAIXAS = (20_000, 50_000, 100_000, 250_000)
ROTULOS_FAIXA = ("20-50 mil", "50-100 mil", "100-250 mil", "250 mil+")


def meses(inicio: str, fim: str) -> list[str]:
    """`AAAA-MM` de `inicio` a `fim`, inclusive."""
    return [str(p) for p in pd.period_range(inicio, fim, freq="M")]


def ponte_municipios(
    pares: pd.DataFrame, nomes_rf: dict[str, str], indice: dict[tuple[str, str], int]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(UF, codigo da Receita) -> codigo IBGE, pelo nome e os apelidos revisados.

    A tabela de municipios da Receita nao traz UF; ela vem do estabelecimento.
    Devolve a ponte e o que nao casou (exterior, grafia sem apelido), para relatorio.
    """
    from vcemal.municipios import resolver

    linhas, falta = [], []
    for uf, rf in pares[["uf", "municipio_rf"]].drop_duplicates().itertuples(index=False):
        codigo = resolver(uf, nomes_rf.get(rf, ""), indice)
        (linhas if codigo else falta).append((uf, rf, codigo or nomes_rf.get(rf, "")))
    ponte = pd.DataFrame(linhas, columns=["uf", "municipio_rf", "municipio_ibge"])
    return ponte, pd.DataFrame(falta, columns=["uf", "municipio_rf", "nome_receita"])


def aberturas_mensais(
    estabelecimentos: pd.DataFrame,
    ponte: pd.DataFrame,
    inicio: str,
    fim: str,
) -> pd.DataFrame:
    """Aberturas de CNAE principal 5320-2/02 por municipio IBGE e mes.

    So matriz: a filial de uma transportadora nao e um entregador a mais.
    Estabelecimento baixado conta -- a data de inicio e o que importa, e o
    cadastro guarda os baixados (D-040). Municipio sem ponte (exterior) sai.
    """
    e = estabelecimentos[
        (estabelecimentos["cnae_principal"] == CNAE_ENTREGA)
        & (estabelecimentos["matriz_filial"] == "1")
    ].copy()
    e["mes"] = e["data_inicio"].str.slice(0, 4) + "-" + e["data_inicio"].str.slice(4, 6)
    e = e[(e["mes"] >= inicio) & (e["mes"] <= fim)]
    e = e.merge(ponte, on=["uf", "municipio_rf"], how="inner")
    return (
        e.groupby(["municipio_ibge", "mes"]).size().rename("aberturas").reset_index()
        if len(e)
        else pd.DataFrame(columns=["municipio_ibge", "mes", "aberturas"])
    )


def matriz(aberturas: pd.DataFrame, municipios: list[int], inicio: str, fim: str) -> np.ndarray:
    """Municipio x mes, com zero onde nao houve abertura."""
    colunas = meses(inicio, fim)
    tabela = aberturas.pivot_table(
        index="municipio_ibge", columns="mes", values="aberturas", aggfunc="sum"
    )
    return tabela.reindex(index=municipios, columns=colunas).fillna(0).to_numpy(float)


def detectar_quebra(
    contagens: np.ndarray,
    primeiro_mes: str,
    inicio: str = INICIO,
    fim: str = FIM,
    fator: float = FATOR,
    minimo: int = MINIMO_JANELA,
    janela: int = JANELA,
    base: int = BASE,
    alfa: float = ALFA,
) -> np.ndarray:
    """Indice (coluna de `contagens`) do mes da quebra por linha, ou -1 se nao houver.

    `contagens` e municipio x mes a partir de `primeiro_mes`. Mes candidato sem
    `base` meses antes ou sem `janela` meses depois e pulado, nunca adivinhado.
    """
    todos = meses(primeiro_mes, "2100-12")
    i0 = max(todos.index(inicio), base)
    i1 = min(todos.index(fim), contagens.shape[1] - janela)
    acumulado = np.concatenate([np.zeros((contagens.shape[0], 1)), contagens.cumsum(axis=1)], 1)
    quebra = np.full(contagens.shape[0], -1)
    for t in range(i0, i1 + 1):
        w = acumulado[:, t + janela] - acumulado[:, t]
        lam = (acumulado[:, t] - acumulado[:, t - base]) / base * janela
        lam = np.maximum(lam, 0.5 * janela / base)
        dispara = (w >= minimo) & (w >= fator * lam) & (poisson.sf(w - 1, lam) < alfa)
        quebra[dispara & (quebra < 0)] = t
    # A janela olha para a frente: o mes que dispara pode vir antes da primeira
    # abertura dela. A quebra e o primeiro mes da janela com abertura -- so
    # atrasa, nunca antecipa, o que a contagem mostra.
    for i in np.flatnonzero(quebra >= 0):
        t = quebra[i]
        quebra[i] = t + int(np.argmax(contagens[i, t : t + janela] > 0))
    return quebra


def faixa(populacao: pd.Series) -> pd.Series:
    return pd.cut(
        populacao, [*FAIXAS, float("inf")], labels=list(ROTULOS_FAIXA), right=False
    ).astype(str)


def tratamento(universo: pd.DataFrame, contagens: np.ndarray, primeiro_mes: str) -> pd.DataFrame:
    """Uma linha por municipio do universo, na ordem de `universo`.

    `grupo`:
    * `datado` -- abaixo do corte, com quebra: `mes_tratamento` e o mes da quebra;
    * `sem_quebra` -- abaixo do corte, sem quebra: **nao** e "nunca tratado",
      pode ter plataforma com poucos entregadores MEI para o teste ver;
    * `coorte_precoce` -- de 100 mil para cima: tratado ate 2018, sem data fina.
    """
    todos = meses(primeiro_mes, "2100-12")
    q = detectar_quebra(contagens, primeiro_mes)
    p = detectar_quebra(contagens, primeiro_mes, inicio=PLACEBO[0], fim=PLACEBO[1])
    i_base = todos.index(INICIO)
    saida = universo[["municipio_ibge", "uf", "municipio", "populacao_2022"]].copy()
    saida["faixa"] = faixa(saida["populacao_2022"]).to_numpy()
    saida["mes_quebra"] = [todos[t] if t >= 0 else "" for t in q]
    saida["aberturas_base_mes"] = contagens[:, i_base - BASE : i_base].mean(axis=1).round(3)
    saida["placebo_2016"] = p >= 0
    grande = saida["populacao_2022"] >= CORTE_POPULACAO
    saida["grupo"] = np.where(grande, "coorte_precoce", np.where(q >= 0, "datado", "sem_quebra"))
    saida["mes_tratamento"] = np.where(saida["grupo"] == "datado", saida["mes_quebra"], "")
    return saida


def validar_contra_wayback(
    tabela: pd.DataFrame, wayback: pd.DataFrame, folga: int = 6
) -> dict[str, float]:
    """Quanto a quebra concorda com o que o Wayback ja data (D-039), sem SIH.

    * `atraso`: entre as entradas de Rappi e Uber Eats com confianca C, fracao
      sem quebra ou com quebra mais de `folga` meses depois do `data_max` -- a
      quebra marca a primeira plataforma, entao pode vir antes, nunca muito depois;
    * `cobertura_ifood`: fracao da lista de frota do iFood com quebra ate dez/2023.
    """
    t = tabela.set_index("municipio_ibge")
    ev = wayback[wayback["plataforma"].isin(["rappi", "uber_eats"]) & (wayback["confianca"] == "C")]
    ev = ev.sort_values("data_max").drop_duplicates("municipio_ibge")
    idx = {m: i for i, m in enumerate(meses("2000-01", "2100-12"))}
    atrasos = []
    for _, r in ev.iterrows():
        q = t.at[int(r["municipio_ibge"]), "mes_quebra"]
        atrasos.append(q == "" or idx[q] > idx[r["data_max"]] + folga)
    lista = wayback.loc[wayback["plataforma"] == "ifood", "municipio_ibge"].astype(int)
    q_ifood = t.loc[t.index.intersection(lista), "mes_quebra"]
    return {
        "entradas_rappi_uber_c": len(atrasos),
        "atraso": float(np.mean(atrasos)) if atrasos else float("nan"),
        "cidades_lista_ifood": len(q_ifood),
        "cobertura_ifood": float(((q_ifood != "") & (q_ifood <= "2023-12")).mean()),
    }
