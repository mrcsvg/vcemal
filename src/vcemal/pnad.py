"""Regras do modulo de plataformas da PNAD Continua -- sem pandas, sem rede.

Perna P2 do argumento (`docs/pre-projeto.md`): "o trabalho e precario". O
modulo suplementar "Trabalho por meio de plataformas digitais" rodou no 4o
trimestre de 2022 e no 3o de 2024 e 2025 (D-031). Aqui moram as definicoes que
o IBGE usa e que o projeto reproduz ao pe da letra, para que a tabela do
projeto bata com o informativo oficial antes de dizer qualquer coisa nova.
"""

from __future__ import annotations

#: Rodadas em que o modulo foi a campo: (ano, trimestre).
RODADAS: tuple[tuple[int, int], ...] = ((2022, 4), (2024, 3), (2025, 3))

#: Variaveis lidas do microdado. Nomes como no dicionario do IBGE.
VARIAVEIS: tuple[str, ...] = (
    "Ano",
    "Trimestre",
    "UF",
    "V1023",  # tipo de area: 1 capital, 2 resto da RM, 3 resto da RIDE, 4 resto da UF
    "V1028",  # peso com pos-estratificacao
    "V2007",  # sexo: 1 homem, 2 mulher
    "V2009",  # idade
    "VD4002",  # 1 ocupado
    "VD4009",  # posicao na ocupacao, trabalho principal
    "V4019",  # negocio tinha CNPJ (conta-propria e empregador): 1 sim, 2 nao
    "VD4012",  # contribui para previdencia em qualquer trabalho: 1 sim
    "V4039",  # horas habituais por semana, trabalho principal
    "VD4016",  # rendimento habitual, trabalho principal (R$ correntes)
    "V4010",  # codigo da ocupacao (COD, 4 digitos)
    "SD14001",  # derivada do IBGE: plataformizado em aplicativo de servicos no trabalho principal
    "S140093",  # prestou servico por aplicativo de entrega de comida, produtos etc.: 1 sim
)

#: `SD14001`, e nao o bruto `S14009`: a derivada do IBGE e mais estrita (em
#: 2024, 2.743 contra 2.950 na amostra) e e a que o informativo publica.
#: Com `S14009` o total sai 1,79 milhao; com `SD14001`, os 1,65 milhao oficiais.

#: Condutor de motocicleta (COD 8321). E a ocupacao do desfecho V20-V29.
COD_MOTOCICLISTA = "8321"

#: Ocupacoes "compativeis com a funcao de entregador" na definicao do IBGE
#: (informativo 2024, nota 21): condutores de veiculos automotores (moto,
#: automovel, caminhao), condutores de veiculos a pedal e mensageiros/
#: entregadores. Entregador = uma destas ocupacoes **e** aplicativo de entrega.
OCUPACOES_ENTREGADOR: frozenset[str] = frozenset({"8321", "8322", "8332", "9331", "9621"})

#: VD4009 de empregado no setor publico e militar. O universo do informativo
#: exclui os dois: as estatisticas sao "do setor privado".
SETOR_PUBLICO: frozenset[int] = frozenset({5, 6, 7})

#: Semanas por mes na conversao de rendimento mensal em rendimento-hora.
#: 52,14 / 12. Reproduz o rendimento-hora publicado pelo IBGE (R$ 10,8 para
#: motociclistas plataformizados em 2024 = 2.119 / (45,2 x 4,345)).
SEMANAS_POR_MES = 4.345

REGIAO: dict[str, str] = {
    "1": "Norte",
    "2": "Nordeste",
    "3": "Sudeste",
    "4": "Sul",
    "5": "Centro-Oeste",
}


def _int(valor: object) -> int | None:
    texto = str(valor).strip() if valor is not None else ""
    return int(texto) if texto.isdigit() else None


def informal(vd4009: object, v4019: object) -> bool | None:
    """Definicao de informalidade do IBGE, sobre o trabalho principal.

    Informal: empregado sem carteira (privado, domestico ou publico),
    empregador sem CNPJ, conta-propria sem CNPJ, trabalhador familiar auxiliar.
    None quando nao ocupado.
    """
    posicao = _int(vd4009)
    if posicao is None:
        return None
    if posicao in (2, 4, 6, 10):
        return True
    if posicao in (8, 9):
        return _int(v4019) == 2
    return False


def setor_privado(vd4009: object) -> bool | None:
    posicao = _int(vd4009)
    if posicao is None:
        return None
    return posicao not in SETOR_PUBLICO


def regiao_de(uf: object) -> str | None:
    """Grande regiao pelo primeiro digito do codigo da UF."""
    texto = str(uf).strip()
    return REGIAO.get(texto[:1]) if texto else None


def trimestre_do_deflator(trimestre: int) -> str:
    """`3` -> `"07-08-09"`, como a coluna `trim` do arquivo de deflator do IBGE."""
    meses = range(3 * trimestre - 2, 3 * trimestre + 1)
    return "-".join(f"{m:02d}" for m in meses)
