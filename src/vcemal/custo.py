"""Parametros de custo social por vitima (Ipea, TD 2565) -- sem pandas e sem rede.

E a camada que converte internacao em custo economico: o que a sociedade perde,
nao o que o SUS pagou. `VAL_TOT` do SIH e o valor **pago** e e piso declarado
(dicionario do painel); este modulo poe ao lado dele a estimativa de custo
social, com perda de producao separada, porque ela recai sobre a familia do
entregador e nao sobre o SUS.

**Fonte:** Carvalho, C. H. R. *Custos dos acidentes de transito no Brasil:
estimativa simplificada com base na atualizacao das pesquisas do Ipea sobre
custos de acidentes nos aglomerados urbanos e rodovias.* Texto para Discussao
2565, Ipea, 2020. Tabela 1A, "componentes de custos associados as pessoas",
em R$ de **dezembro de 2014**.

**Mapeamento declarado (D-029):**

* uma AIH de motociclista = **ferido grave** em acidente *com vitimas*;
* uma AIH com `MORTE = 1` = **morto** em acidente *com fatalidade*.

**Ressalva que o paper precisa carregar:** a Tabela 1A vem da pesquisa de
rodovias federais (Ipea/Denatran/ANTP 2006) atualizada; o Ipea nao publica a
abertura por pessoa para aglomerados urbanos, que e onde a entrega acontece.
Custo por vitima em rodovia tende a ser maior que em area urbana (velocidade,
gravidade), entao a estimativa e para ser lida como **ordem de grandeza**, nao
como valor pontual -- e sempre ao lado do `val_tot` deflacionado, que e o piso.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Componentes:
    """Componentes elementares de custo por pessoa, em R$ da `base_precos` do parametro."""

    pre_hospitalar: float
    hospitalar: float
    pos_hospitalar: float
    perda_producao: float
    remocao: float

    @property
    def total(self) -> float:
        return (
            self.pre_hospitalar
            + self.hospitalar
            + self.pos_hospitalar
            + self.perda_producao
            + self.remocao
        )


@dataclass(frozen=True)
class ParametrosCusto:
    """Um conjunto de parametros, com fonte e data-base explicitas."""

    fonte: str
    #: Competencia dos precos, `AAAA-MM`. Tudo e reexpresso pelo IPCA a partir daqui.
    base_precos: str
    ferido_grave: Componentes
    morto: Componentes


#: Ipea TD 2565, Tabela 1A. Ferido grave na coluna "com vitimas"; morto na
#: coluna "com fatalidade". O total de "mortos" nao esta impresso na tabela --
#: e a soma dos componentes, como nas demais linhas.
TD2565 = ParametrosCusto(
    fonte="Ipea, TD 2565 (Carvalho, 2020), Tabela 1A, R$ dez./2014",
    base_precos="2014-12",
    ferido_grave=Componentes(
        pre_hospitalar=1_111.73,
        hospitalar=72_855.40,
        pos_hospitalar=3_150.21,
        perda_producao=47_797.94,
        remocao=218.64,
    ),
    morto=Componentes(
        pre_hospitalar=86.28,
        hospitalar=143.19,
        pos_hospitalar=0.0,
        perda_producao=432_557.99,
        remocao=499.24,
    ),
)

#: Total impresso na Tabela 1A para ferido grave em acidente com vitimas.
#: Serve de conferencia da transcricao (ver tests).
TOTAL_IMPRESSO_FERIDO_GRAVE = 125_133.91


def custo_social(internacoes: int, obitos: int, p: ParametrosCusto = TD2565) -> dict[str, float]:
    """Custo social de `internacoes` AIH, das quais `obitos` sairam em obito.

    Quem morreu no hospital entra como morto, nao como ferido grave -- os dois
    parametros nao se somam para a mesma pessoa. Valores em R$ da `p.base_precos`;
    deflacionar/inflacionar e trabalho de `vcemal.analyze.custo`.
    """
    if obitos > internacoes:
        raise ValueError(f"obitos ({obitos}) maior que internacoes ({internacoes})")
    sobreviventes = internacoes - obitos
    componentes = ("pre_hospitalar", "hospitalar", "pos_hospitalar", "perda_producao", "remocao")
    saida = {
        c: sobreviventes * getattr(p.ferido_grave, c) + obitos * getattr(p.morto, c)
        for c in componentes
    }
    saida["total"] = sum(saida.values())
    return saida
