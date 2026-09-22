"""
Ponte entre o municipio por nome (Senatran) e o codigo IBGE (SIH, IBGE).

O SIH identifica municipio por codigo IBGE de 6 digitos (`MUNIC_RES`); o IBGE
publica o codigo de 7, sendo o setimo o digito verificador; a frota do Senatran
vem so com UF e **nome em caixa alta sem acento**. Casar os tres exige
normalizar o nome, e o nome nao e chave estavel.

Em dezembro/2023, a normalizacao exata casa 5533 de 5572 linhas (99,3%). As 39
restantes nao sao ruido aleatorio -- sao tres coisas distintas:

1. **Grafia divergente** do mesmo municipio: LAGEDO/LAJEDO, TERESINHA/TEREZINHA,
   PARATI/PARATY, GOUVEA/GOUVEIA. Inclui um typo com zero no lugar da letra O
   (`BARAO D0 MONTE ALTO`) e truncamento em 30 caracteres
   (`VILA BELA DA SANTISSIMA TRINDA`).
2. **Municipio renomeado**, com o Senatran carregando o nome antigo. Estes sao
   os perigosos: Santarem (PB) virou Joca Claudino, Fortaleza do Tabocao (TO)
   virou Tabocao, Boa Saude (RN) e o novo nome de Januario Cicco.
3. **Nao e municipio**: `MUNICIPIO NAO INFORMADO`.

**Por que a tabela e fixa e nao um fuzzy match em tempo de execucao.** Rodamos
`difflib` uma vez sobre as 39 sobras, sob revisao, e ele errou cinco -- casou
Santarem (PB) com Santo Andre, Fortaleza do Tabocao com Porto Alegre do
Tocantins, Sao Valerio da Natividade com Chapada da Natividade. Todos os cinco
sao renomeacao, onde o nome novo nao se parece com o velho. Num denominador,
esse erro nao aparece: a frota de um municipio entra na conta de outro e a taxa
sai errada sem nenhum sinal. Por isso o par revisado vira constante, os
municipios que sobrarem sao **reportados, nunca descartados em silencio**, e a
lista e revisavel em diff.
"""

from __future__ import annotations

import re
import unicodedata

#: Linhas da frota que nao sao municipio. Contadas e reportadas, nunca somadas.
#: Aparece em mais de uma UF ao longo da serie, entao a regra e pelo nome.
NAO_E_MUNICIPIO: frozenset[str] = frozenset({"MUNICIPIO NAO INFORMADO"})

#: (UF, nome normalizado no Senatran) -> codigo IBGE de 7 digitos.
#: Revisado a mao contra a lista de municipios do IBGE. Ver docstring do modulo.
APELIDOS: dict[tuple[str, str], int] = {
    # --- Renomeacao: o nome novo nao se parece com o velho ---
    ("PB", "SANTAREM"): 2513653,  # hoje Joca Claudino
    ("PB", "SAO DOMINGOS DE POMBAL"): 2513968,  # hoje Sao Domingos
    ("RN", "BOA SAUDE"): 2405306,  # IBGE ainda registra Januario Cicco
    ("TO", "FORTALEZA DO TABOCAO"): 1708254,  # hoje Tabocao
    ("TO", "SAO VALERIO DA NATIVIDADE"): 1720499,  # hoje Sao Valerio
    # --- Grafia divergente ---
    ("BA", "LAGEDO DO TABOCAL"): 2919058,
    ("MG", "BRASOPOLIS"): 3108909,  # Brazopolis, com z
    ("MT", "POXOREO"): 5107008,  # Poxoreu
    ("RJ", "ARMACAO DE BUZIOS"): 3300233,  # Armacao dos Buzios
    ("RO", "NOVA DO MAMORE"): 1100338,  # Nova Mamore
    ("SP", "EMBU"): 3515004,  # hoje Embu das Artes
    ("BA", "SANTA TERESINHA"): 2928505,
    ("GO", "BOM JESUS"): 5203500,  # Bom Jesus de Goias
    ("MG", "AMPARO DA SERRA"): 3102506,
    ("MG", "BARAO D0 MONTE ALTO"): 3105509,  # zero no lugar da letra O
    ("MG", "GOUVEA"): 3127602,
    ("MG", "QUELUZITA"): 3153806,
    ("MT", "SANTO ANTONIO DO LEVERGER"): 5107800,
    ("MT", "VILA BELA DA SANTISSIMA TRINDA"): 5105507,  # truncado em 30 caracteres
    ("PA", "ELDORADO DOS CARAJAS"): 1502954,
    ("PA", "SANTA ISABEL DO PARA"): 1506500,
    ("PE", "BELEM DE SAO FRANCISCO"): 2601607,
    ("PE", "IGUARACI"): 2606903,
    ("PE", "LAGOA DO ITAENGA"): 2608503,
    ("PI", "SAO FRANCISCO DE ASSIS DO PIAU"): 2209658,  # truncado em 30 caracteres
    ("PR", "BELA VISTA DO CAROBA"): 4102752,
    ("PR", "MUNHOZ DE MELLO"): 4116307,
    ("PR", "PINHAL DO SAO BENTO"): 4119251,
    ("PR", "SANTA CRUZ DO MONTE CASTELO"): 4123303,
    ("RJ", "PARATI"): 3303807,
    ("RJ", "TRAJANO DE MORAIS"): 3305901,
    ("RN", "ARES"): 2401206,  # Arez
    ("RN", "LAGOA DANTA"): 2406205,  # Lagoa d'Anta
    ("RR", "SAO LUIZ"): 1400605,
    ("RS", "SANTANA DO LIVRAMENTO"): 4317103,  # Sant'Ana do Livramento
    ("SC", "BALNEARIO DE PICARRAS"): 4212809,
    ("SC", "LAGEADO GRANDE"): 4209458,
    ("SC", "PRESIDENTE CASTELO BRANCO"): 4213906,
    ("SC", "SAO LOURENCO D OESTE"): 4216909,
    ("SC", "SAO MIGUEL D OESTE"): 4217204,
    ("SE", "AMPARO DE SAO FRANCISCO"): 2800100,
    ("TO", "COUTO DE MAGALHAES"): 1706001,
}


def normalizar(nome: str) -> str:
    """Caixa alta, sem acento, sem pontuacao, espaco simples.

    `Sant'Ana do Livramento` e `SANT ANA DO LIVRAMENTO` colapsam no mesmo texto.
    """
    sem_acento = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]+", " ", sem_acento.upper()).strip()


def para_6_digitos(codigo_ibge: int | str) -> str:
    """Codigo IBGE de 7 digitos -> os 6 que o SIH usa (sem o verificador)."""
    codigo = str(codigo_ibge).strip()
    if len(codigo) == 7:
        return codigo[:6]
    if len(codigo) == 6:
        return codigo
    raise ValueError(f"codigo IBGE nao tem 6 nem 7 digitos: {codigo!r}")


def construir_indice(municipios: list[dict]) -> dict[tuple[str, str], int]:
    """(UF, nome normalizado) -> codigo de 7 digitos, a partir da lista do IBGE.

    `municipios` e a resposta de `vcemal.extract.ibge.listar_municipios`.
    """
    return {(m["uf"], normalizar(m["nome"])): int(m["id"]) for m in municipios}


def resolver(uf: str, nome: str, indice: dict[tuple[str, str], int]) -> int | None:
    """Codigo IBGE de 7 digitos, ou None se o par nao for reconhecido.

    Tenta o nome normalizado e, so entao, a tabela revisada de apelidos.
    """
    limpo = normalizar(nome)
    if limpo in NAO_E_MUNICIPIO:
        return None
    chave = (str(uf).strip().upper(), limpo)
    return indice.get(chave) or APELIDOS.get(chave)
