"""
Definicao de caso: CID-10, capitulo XX (causas externas de morbidade).

Este modulo carrega sozinho a decisao metodologica do projeto. Nada aqui
depende de pandas ou do SIH -- e uma tabela de dominio, e os testes cobrem
cada digito.

O quarto caractere das categorias de transporte NAO tem a mesma leitura em
todas as categorias. Ha duas estruturas:

ESTRUTURA PADRAO -- categorias de colisao/nao-colisao (V10-V18, V20-V28,
V40-V48):

    .0  condutor, acidente NAO de transito
    .1  passageiro, acidente NAO de transito
    .2  nao especificado, acidente NAO de transito
    .3  pessoa ao embarcar ou desembarcar
    .4  condutor, acidente de transito
    .5  passageiro, acidente de transito
    .9  nao especificado, acidente de transito

ESTRUTURA TERMINAL -- categorias "outros e nao especificados" (V19, V29,
V49), que reaproveitam .3, .6 e .8 com outro sentido:

    .0  condutor, colisao com outro veiculo a motor, NAO de transito
    .1  passageiro, colisao com outro veiculo a motor, NAO de transito
    .2  nao especificado, colisao com outro veiculo a motor, NAO de transito
    .3  qualquer ocupante, acidente NAO de transito nao especificado
    .4  condutor, colisao com outro veiculo a motor, de transito
    .5  passageiro, colisao com outro veiculo a motor, de transito
    .6  nao especificado, colisao com outro veiculo a motor, de transito
    .8  qualquer ocupante, outros acidentes de transporte especificados
    .9  qualquer ocupante, acidente de transito nao especificado

A diferenca que importa: **`.3` e acidente de transito na estrutura padrao
(embarque/desembarque, convencao NCHS) e explicitamente NAO-transito na
estrutura terminal**, e `.6` so existe -- e so e transito -- na terminal.
Uma regra unica sobre o quarto digito erra V19.3, V29.3 e V49.3, e no SIH
brasileiro isso nao e detalhe: **V29 sozinha e 67% das internacoes de
motociclista** (646.928 de 965.714 AIH, Brasil 2016-2023). A regra achatada
classificava 60.511 AIH como transito indevidamente -- V29.3 (13.706, nao-
transito explicito) e V29.8 (46.805, "outros acidentes de transporte
especificados") --, 6,3% do desfecho. Ver D-010 em `docs/decisoes.md`.

Referencia da faixa de transito: CDC/NCHS, definicao padrao de lesao de
transito -- `V20-V28[.3-.9]`, `V29-V79[.4-.9]`, `V19[.4-.6]`.

**A causa externa nao mora no diagnostico principal.** Pela norma do SIH/SUS, a
internacao por causa externa leva no diagnostico principal o *tipo de
traumatismo* (capitulo XIX, S e T) e no diagnostico secundario a *origem* da
causa (capitulo XX, V a Y). Procurar V20-V29 em `DIAG_PRINC` devolve painel
vazio -- medido: zero AIH em todo ano de 2016 a 2023, contra 107 mil a 145 mil
por ano no campo certo. Ver D-017 e `primeira_causa_externa`.
"""

from __future__ import annotations

from collections.abc import Iterable

# ---------------------------------------------------------------------------
# Grupos de vitima
# ---------------------------------------------------------------------------
# Papel de cada grupo no desenho: ver docs/decisoes.md D-004 (ciclista e teste
# do mecanismo, nao desfecho paralelo) e D-005 (auto e placebo).

GRUPOS_CID: dict[str, list[str]] = {
    "ciclista": [f"V{n:02d}" for n in range(10, 20)],  # V10-V19
    "motociclista": [f"V{n:02d}" for n in range(20, 30)],  # V20-V29
    "auto_placebo": [f"V{n:02d}" for n in range(40, 50)],  # V40-V49
}

#: Categoria -> grupo, achatado para lookup direto.
CATEGORIA_GRUPO: dict[str, str] = {
    categoria: grupo for grupo, categorias in GRUPOS_CID.items() for categoria in categorias
}

# ---------------------------------------------------------------------------
# Estrutura do quarto digito
# ---------------------------------------------------------------------------

#: Categorias "outros e nao especificados" de cada grupo, que usam a estrutura
#: terminal. Sao sempre a ultima categoria da dezena.
CATEGORIAS_TERMINAIS: frozenset[str] = frozenset({"V19", "V29", "V49"})

#: Quarto digito = condutor em acidente de transito. Vale nas duas estruturas.
CONDUTOR_TRANSITO: frozenset[str] = frozenset({"4"})

#: Quarto digito = condutor, com ou sem transito (`.0` nao-transito, `.4` transito).
CONDUTOR: frozenset[str] = frozenset({"0", "4"})

#: Acidente de transito na estrutura padrao. Inclui `.3` (embarque/desembarque),
#: seguindo a faixa V20-V28[.3-.9] do NCHS.
TRANSITO_PADRAO: frozenset[str] = frozenset({"3", "4", "5", "9"})

#: Acidente de transito na estrutura terminal. `.3` fica de fora -- e
#: nao-transito explicito. `.8` tambem: "outros acidentes de transporte
#: especificados" nao afirma transito.
TRANSITO_TERMINAL: frozenset[str] = frozenset({"4", "5", "6", "9"})

#: `.3` da estrutura padrao: entra em transito por convencao, nao por definicao.
#: Marcado a parte para que a escolha seja auditavel em analise de sensibilidade.
EMBARQUE_DESEMBARQUE: frozenset[str] = frozenset({"3"})


def e_terminal(categoria: str) -> bool:
    """A categoria de 3 caracteres usa a estrutura terminal do quarto digito?"""
    return categoria in CATEGORIAS_TERMINAIS


def digitos_transito(categoria: str) -> frozenset[str]:
    """Quartos digitos que indicam acidente de transito nesta categoria."""
    return TRANSITO_TERMINAL if e_terminal(categoria) else TRANSITO_PADRAO


def grupo_de(cid: str) -> str | None:
    """Grupo de vitima de um CID-10, ou None se fora da definicao de caso."""
    return CATEGORIA_GRUPO.get((cid or "")[:3].upper())


def em_transito(cid: str) -> bool:
    """O CID indica acidente de transito, respeitando a estrutura da categoria."""
    cid = (cid or "").upper()
    categoria, digito = cid[:3], cid[3:4]
    if categoria not in CATEGORIA_GRUPO:
        return False
    return digito in digitos_transito(categoria)


def condutor_em_transito(cid: str) -> bool:
    """O CID indica condutor em acidente de transito (`.4` nas duas estruturas)."""
    cid = (cid or "").upper()
    categoria, digito = cid[:3], cid[3:4]
    if categoria not in CATEGORIA_GRUPO:
        return False
    return digito in CONDUTOR_TRANSITO


# ---------------------------------------------------------------------------
# Caracter da internacao (campo CAR_INT do arquivo RD do SIH)
# ---------------------------------------------------------------------------
# CONFERIR contra a "Estrutura dos arquivos SIHSUS - RD" da competencia mais
# antiga da serie antes de encadear: a tabela de dominio mudou de versao ao
# longo do periodo. Ver D-008 em docs/decisoes.md.

CAR_INT_LABEL: dict[str, str] = {
    "01": "eletivo",
    "02": "urgencia",
    "03": "acid_local_trabalho",
    "04": "acid_trajeto_trabalho",
    "05": "outro_acid_transito",
    "06": "outra_lesao_envenenamento",
}

#: Codigos que marcam nexo ocupacional -- o unico sinal de trabalho no SIH.
CAR_INT_OCUPACIONAL: frozenset[str] = frozenset({"03", "04"})

#: Valores que aparecem no lugar de um codigo valido e NAO contam como
#: preenchimento. `00` e `99` circulam como sentinela de "ignorado" em parte da
#: serie; string vazia sai do strip de campo em branco.
CAR_INT_AUSENTE: frozenset[str] = frozenset({"", "00", "0", "99", "9"})


def car_int_preenchido(valor: str | None) -> bool:
    """O CAR_INT traz um codigo de dominio de fato, nao branco nem sentinela.

    Denominador da taxa de nexo ocupacional. Contar branco como preenchido
    infla o denominador e subestima a subnotificacao -- que e justamente o
    achado do V1 (D-008).
    """
    if valor is None:
        return False
    codigo = str(valor).strip()
    if codigo in CAR_INT_AUSENTE:
        return False
    return codigo in CAR_INT_LABEL


# ---------------------------------------------------------------------------
# Onde procurar a causa externa
# ---------------------------------------------------------------------------


def primeira_causa_externa(codigos: Iterable[str | None]) -> str | None:
    """Primeiro codigo da sequencia que cai na definicao de caso.

    Recebe os diagnosticos de uma AIH **na ordem de precedencia** e devolve o
    primeiro que pertence a um dos grupos de `GRUPOS_CID`. None quando nenhum
    pertence -- a AIH esta fora do escopo.

    Por que "o primeiro que casa" e nao "o primeiro preenchido": o campo de
    precedencia mais alta costuma trazer a lesao (`S720`), nao a causa. Parar
    no primeiro campo nao nulo descartaria a AIH inteira por causa de um S no
    caminho.
    """
    for codigo in codigos:
        if codigo and grupo_de(codigo):
            return codigo
    return None
