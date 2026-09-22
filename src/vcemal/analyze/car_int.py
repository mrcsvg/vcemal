"""Preenchimento do `CAR_INT` e taxa de nexo ocupacional.

Isto e resultado do V1, nao checagem de qualidade de dado: o quanto o SIH deixa
de marcar nexo ocupacional numa populacao cujo perfil e mecanismo de lesao sao
conhecidos e o que o paper documenta (D-008, H4).

Duas taxas, que nao se confundem:

* **preenchimento** = `car_int_preenchido / internacoes` -- quanto do campo
  chega com um codigo de dominio valido.
* **nexo** = `nexo_ocupacional / car_int_preenchido` -- entre as que tem codigo,
  quantas sao 03 ou 04.

O denominador da segunda e o preenchimento, nunca o total de internacoes.
Dividir nexo por internacoes mistura duas coisas -- o campo estar vazio e o
campo dizer "nao foi trabalho" -- e faz a subnotificacao parecer menor do que e.
"""

from __future__ import annotations

import pandas as pd

#: Contagens que vem do painel e que todo recorte soma.
SOMAS = ["internacoes", "car_int_preenchido", "nexo_ocupacional"]

#: Colunas que qualquer recorte devolve, nesta ordem.
COLUNAS = ["internacoes", "car_int_preenchido", "pct_preenchido", "nexo_ocupacional", "pct_nexo"]


def _taxas(g: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as duas taxas, com NaN (nao zero) onde o denominador e zero."""
    internacoes = g["internacoes"]
    preenchido = g["car_int_preenchido"]
    return g.assign(
        pct_preenchido=100 * preenchido / internacoes.where(internacoes > 0),
        pct_nexo=100 * g["nexo_ocupacional"] / preenchido.where(preenchido > 0),
    )[COLUNAS]


def por(painel: pd.DataFrame, *chaves: str) -> pd.DataFrame:
    """Preenchimento e nexo agregados pelas `chaves` dadas.

    `painel` e a saida de `vcemal.transform.sih.agregar` (ou o parquet do painel).
    """
    faltando = [c for c in (*chaves, *SOMAS) if c not in painel.columns]
    if faltando:
        raise KeyError(f"painel sem as colunas {faltando}")

    return _taxas(painel.groupby(list(chaves), dropna=False)[SOMAS].sum())


def por_ano(painel: pd.DataFrame) -> pd.DataFrame:
    """Recorte principal: ano x grupo de vitima."""
    return por(painel, "ano", "grupo")


def por_uf_ano(painel: pd.DataFrame) -> pd.DataFrame:
    """Recorte de heterogeneidade: UF x ano, so motociclista.

    Preenchimento desigual entre UFs e ao longo do tempo e confundidor direto
    num painel de efeitos fixos -- precisa ser visto antes de qualquer estimacao.
    """
    moto = painel[painel["grupo"] == "motociclista"]
    return por(moto, "uf", "ano")


def por_municipio(painel: pd.DataFrame, minimo: int = 30) -> pd.DataFrame:
    """Motociclista por municipio, so onde ha volume que sustente a taxa.

    `minimo` e o piso de internacoes no periodo inteiro; abaixo dele a taxa e
    ruido e nao entra na tabela.
    """
    moto = painel[painel["grupo"] == "motociclista"]
    tabela = por(moto, "municipio_res")
    return tabela[tabela["internacoes"] >= minimo].sort_values("pct_nexo", ascending=False)
