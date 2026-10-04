"""iFood e SUS no mesmo eixo: o que a plataforma ganha e o que o SUS paga. Sem rede.

Junta P1 (`lucro_ifood_por_ano.csv`, ano civil) e P3(a) (`custo_por_ano.csv`)
numa tabela so, em R$ milhoes da mesma base de precos. E a tabela que a figura
de contraste desenha e a que o leitor consulta no lugar dela.

**Nao e atribuicao.** O valor pago pelo SUS e o de todas as internacoes de
motociclista, entregador ou nao; a parte atribuivel a plataforma e o V2. As
duas series estao lado a lado porque estao na mesma unidade, nao porque uma
cause a outra.

**O resultado do iFood muda de metrica.** A Prosus reportava *trading profit*
e passou a reportar *aEBIT* (D-032). A serie usa o aEBIT onde existe e o
trading profit antes dele, e `metrica_resultado` diz qual e qual -- a emenda
tem que aparecer, nao ser alisada.
"""

from __future__ import annotations

import pandas as pd

COLUNAS = [
    "receita_ifood",
    "resultado_ifood",
    "metrica_resultado",
    "sus_pagou",
    "custo_social",
    "base_precos",
]


def lado_a_lado(
    lucro_civil: pd.DataFrame, custo_por_ano: pd.DataFrame, grupo: str = "motociclista"
) -> pd.DataFrame:
    """Ano civil x (receita e resultado do iFood, pago pelo SUS, custo social), em R$ mi.

    `lucro_civil` e a saida de `analyze.lucro.por_ano_civil` (ou o CSV dela),
    ja em milhoes; `custo_por_ano` e a de `analyze.custo.por_ano`, em reais.
    Bases de preco diferentes sao erro: a comparacao so vale na mesma moeda.
    """
    lucro = lucro_civil.set_index("ano") if "ano" in lucro_civil.columns else lucro_civil
    custo = custo_por_ano[custo_por_ano["grupo"] == grupo].set_index("ano")

    bases = set(lucro["base_precos"].dropna().astype(str)) | set(
        custo["base_precos"].dropna().astype(str)
    )
    if len(bases) != 1:
        raise ValueError(f"lucro e custo em bases de preco diferentes: {sorted(bases)}")

    aebit = lucro["aebit_brl_real_milhoes"]
    trading = lucro["trading_profit_brl_real_milhoes"]
    metrica = pd.Series(pd.NA, index=lucro.index, dtype=object)
    metrica = metrica.mask(trading.notna(), "trading_profit").mask(aebit.notna(), "aebit")

    saida = pd.DataFrame(
        {
            "receita_ifood": lucro["receita_brl_real_milhoes"],
            "resultado_ifood": aebit.fillna(trading),
            "metrica_resultado": metrica,
            "sus_pagou": custo["val_tot_real"] / 1e6,
            "custo_social": custo["custo_social_real"] / 1e6,
        }
    )
    saida = saida.dropna(how="all", subset=["receita_ifood", "resultado_ifood", "sus_pagou"])
    saida["base_precos"] = bases.pop()
    saida.index = saida.index.astype(int)
    saida.index.name = "ano"
    return saida.sort_index()[COLUNAS]
