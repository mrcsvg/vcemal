"""Serie de receita e resultado do iFood, como a Prosus publica.

Perna P1 do argumento (`docs/pre-projeto.md`): "eles lucram". Nao e dado de
pesquisa -- e a demonstracao publicada pela parte interessada, transcrita de
`docs/fontes/ifood_prosus.csv` com documento, URL e data de acesso em cada
celula. Este modulo carrega as regras que o CSV precisa obedecer e a
aritmetica do calendario. Sem pandas, sem rede.

**Ano fiscal.** A Prosus fecha em 31 de marco: FY2025 vai de abril/2024 a
marco/2025. Nada aqui bate com o ano civil do SIH sem conversao declarada --
ver `para_ano_civil`.

**Resultado nao e lucro liquido.** O iFood e companhia fechada e nao publica
demonstracao propria. O que existe e o resultado operacional do segmento como
a controladora reporta: *trading profit* ate FY2024, *EBIT ajustado* de FY2023
em diante (os dois anos de sobreposicao ficam na tabela para mostrar a
emenda). Ver D-032.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Mes em que o ano fiscal da Prosus termina.
MES_FIM_ANO_FISCAL = 3


@dataclass(frozen=True)
class Metrica:
    nome: str
    unidade: str
    descricao: str
    fluxo: bool  # True = soma ao longo do ano (receita); False = estoque no fim do ano


#: Metricas aceitas no CSV. Qualquer outra e erro de transcricao.
METRICAS: dict[str, Metrica] = {
    m.nome: m
    for m in (
        Metrica("receita", "USD_milhoes", "Receita do grupo iFood consolidada pela Prosus", True),
        Metrica(
            "receita_comparavel",
            "USD_milhoes",
            "Receita pro-forma na regra de reconhecimento e composicao mais recentes",
            True,
        ),
        Metrica("trading_profit", "USD_milhoes", "Resultado operacional (trading profit)", True),
        Metrica("aebit", "USD_milhoes", "EBIT ajustado", True),
        Metrica("aebitda", "USD_milhoes", "EBITDA ajustado", True),
        Metrica("gmv", "USD_milhoes", "Valor bruto transacionado (GMV)", True),
        Metrica("pedidos", "milhoes", "Pedidos no ano fiscal", True),
        Metrica(
            "entregadores_brasil", "pessoas", "Entregadores ativos no Brasil (fim do ano)", False
        ),
        Metrica(
            "estabelecimentos_brasil", "unidades", "Estabelecimentos no Brasil (fim do ano)", False
        ),
        Metrica("cidades_brasil", "unidades", "Cidades atendidas no Brasil (fim do ano)", False),
    )
}

#: Metricas em dolar, que passam pelo cambio.
EM_DOLAR = tuple(m.nome for m in METRICAS.values() if m.unidade == "USD_milhoes")

#: Fluxos que fazem sentido interpolar para o ano civil.
FLUXOS = tuple(m.nome for m in METRICAS.values() if m.fluxo)

COLUNAS_CSV = ("ano_fiscal", "metrica", "valor", "unidade", "documento", "url", "acesso", "nota")


def meses_do_ano_fiscal(ano_fiscal: int) -> list[str]:
    """Competencias `AAAA-MM` do ano fiscal: abril do ano anterior a marco do ano."""
    inicio = ano_fiscal - 1
    return [f"{inicio}-{m:02d}" for m in range(MES_FIM_ANO_FISCAL + 1, 13)] + [
        f"{ano_fiscal}-{m:02d}" for m in range(1, MES_FIM_ANO_FISCAL + 1)
    ]


#: Peso de cada ano fiscal no ano civil `t`: janeiro a marco de `t` estao em
#: FY(t); abril a dezembro estao em FY(t+1).
PESO_MESMO_ANO = MES_FIM_ANO_FISCAL / 12
PESO_ANO_SEGUINTE = 1 - PESO_MESMO_ANO


def para_ano_civil(por_ano_fiscal: dict[int, float]) -> dict[int, float]:
    """Fluxo anual fiscal -> ano civil, por interpolacao declarada.

    `civil[t] = 0,25 x FY(t) + 0,75 x FY(t+1)`. Assume fluxo uniforme dentro
    do ano fiscal -- e uma aproximacao, e por isso a tabela de saida carrega o
    metodo na coluna. So devolve os anos civis em que os dois anos fiscais
    existem; nao extrapola nas pontas.
    """
    anos = sorted(por_ano_fiscal)
    saida = {}
    for fy in anos:
        seguinte = fy + 1
        if seguinte in por_ano_fiscal:
            saida[fy] = (
                PESO_MESMO_ANO * por_ano_fiscal[fy] + PESO_ANO_SEGUINTE * por_ano_fiscal[seguinte]
            )
    return saida


def validar(linhas: list[dict]) -> None:
    """Regras que o CSV curado precisa obedecer. Erro cedo, com a linha apontada."""
    if not linhas:
        raise ValueError("serie vazia")
    vistos: set[tuple[int, str]] = set()
    for i, r in enumerate(linhas, start=2):  # linha 1 e o cabecalho
        faltando = [c for c in COLUNAS_CSV if c not in r]
        if faltando:
            raise ValueError(f"linha {i}: sem as colunas {faltando}")
        nome = r["metrica"]
        if nome not in METRICAS:
            raise ValueError(f"linha {i}: metrica desconhecida {nome!r}")
        if r["unidade"] != METRICAS[nome].unidade:
            raise ValueError(
                f"linha {i}: {nome} em {r['unidade']!r}, esperado {METRICAS[nome].unidade!r}"
            )
        chave = (int(r["ano_fiscal"]), nome)
        if chave in vistos:
            raise ValueError(f"linha {i}: {nome} repetida para FY{chave[0]}")
        vistos.add(chave)
        for campo in ("documento", "url", "acesso"):
            if not str(r.get(campo) or "").strip() or str(r[campo]) == "nan":
                raise ValueError(f"linha {i}: {nome} FY{chave[0]} sem {campo}")
        float(r["valor"])
