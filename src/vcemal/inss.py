"""Tabelas e regras da base de beneficios concedidos do INSS -- sem pandas, sem rede.

Perna P3(b) do argumento (`docs/pre-projeto.md`): a lacuna entre o que o SUS
interna e o que a Previdencia reconhece como acidente de trabalho. A base e
aberta e, ao mesmo tempo, estruturalmente cega ao entregador informal -- por
isso o que ela mostra e a **invisibilidade**, nao o risco (D-002, D-030).

Tres coisas moram aqui porque nao podem depender do layout do arquivo, que
muda quatro vezes entre 2019 e 2025 (ver `vcemal.transform.inss`):

* a tabela **especie <-> nome**, porque so o XLSX de 2023 em diante traz o
  codigo numerico; os CSVs anteriores trazem so o nome;
* a classificacao de especie em **acidentaria** (nexo com o trabalho
  reconhecido) ou **previdenciaria** (nao reconhecido);
* a leitura do **CID** e da **UF**, que vem em formatos diferentes por ano.
"""

from __future__ import annotations

import re
import unicodedata

#: Codigo da especie -> nome como aparece nos arquivos (observado em fev/2025,
#: identico ao que os CSVs de 2019-2023 trazem). Nao e o nome do glossario
#: oficial: la a 31 chama "Auxilio por Incapacidade Temporaria"; no dado, nao.
ESPECIES: dict[int, str] = {
    1: "Pensão por Morte de Trabalhador Rural",
    4: "Aposentadoria por Invalidez-Trab. Rural",
    5: "Aposent. Invalidez Acidentária-Trab.Rur.",
    10: "Auxílio Doença Acidentário - Trabalhador Rural",
    13: "Auxílio Doença - Trabalhador Rural",
    18: "Auxílio Inclusão À Pessoa com Deficiência",
    21: "Pensão por Morte Previdenciária",
    23: "Pensão por Morte de Ex-Combatente",
    25: "Auxílio Reclusão",
    30: "Renda Mensal Vitalícia por Incapacidade",
    31: "Auxílio Doenca Previdenciário",
    32: "Aposentadoria Invalidez Previdenciária",
    36: "Auxílio Acidente Previdenciário",
    41: "Aposentadoria por Idade",
    42: "Aposentadoria por Tempo de Contribuição",
    46: "Aposentadoria Especial",
    56: "Pensão Vitalícia Sindrome Talidomida",
    57: "Aposent. Tempo de Serviço de Professor",
    60: "Benefício Indenizatório a Cargo da União",
    80: "Auxílio Salario Maternidade",
    85: "Pensão Vitalícia Seringueiros",
    86: "Pensão Vitalícia Dependentes Seringueiro",
    87: "Amp. Social Pessoa Portadora Deficiencia",
    88: "Amparo Social ao Idoso",
    91: "Auxílio Doenca por Acidente do Trabalho",
    92: "Aposent. Invalidez Acidente Trabalho",
    93: "Pensão por Morte Acidente do Trabalho",
    94: "Auxílio Acidente",
    95: "Auxílio Suplementar Acidente Trabalho",
    96: "Pensao Especial Hanseniase Lei 11520/07",
}

#: Especies em que o INSS **reconheceu** nexo com o trabalho. A serie 9x e a
#: acidentaria urbana (auxilio-doenca 91, invalidez 92, pensao 93,
#: auxilio-acidente 94, suplementar 95); 5 e 10 sao as rurais equivalentes.
ACIDENTARIAS: frozenset[int] = frozenset({5, 10, 91, 92, 93, 94, 95})

#: O mesmo evento -- afastamento, invalidez, morte, sequela -- **sem** nexo
#: reconhecido. E onde cai o entregador que contribui como autonomo/MEI: a
#: especie acidentaria pressupoe empregador.
PREVIDENCIARIAS: frozenset[int] = frozenset({4, 13, 21, 30, 31, 32, 36})

#: Sigla por nome, como o INSS escreve a UF.
UF_SIGLA: dict[str, str] = {
    "Acre": "AC",
    "Alagoas": "AL",
    "Amapá": "AP",
    "Amazonas": "AM",
    "Bahia": "BA",
    "Ceará": "CE",
    "Distrito Federal": "DF",
    "Espírito Santo": "ES",
    "Goiás": "GO",
    "Maranhão": "MA",
    "Mato Grosso": "MT",
    "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG",
    "Pará": "PA",
    "Paraíba": "PB",
    "Paraná": "PR",
    "Pernambuco": "PE",
    "Piauí": "PI",
    "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS",
    "Rondônia": "RO",
    "Roraima": "RR",
    "Santa Catarina": "SC",
    "São Paulo": "SP",
    "Sergipe": "SE",
    "Tocantins": "TO",
}

_CID = re.compile(r"^\s*([A-Z])(\d{2})(?:\.?(\d))?(?![0-9])")
_UF_NO_MUNICIPIO = re.compile(r"^\s*\d+\s*-\s*([A-Za-z]{2})\s*-")


def texto_simples(valor: object) -> str:
    """Minusculas, sem acento, sem pontuacao, espaco simples. Chave de comparacao."""
    sem_acento = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).strip()


#: Nome simplificado -> codigo. Para os arquivos que trazem so o nome.
NOME_PARA_ESPECIE: dict[str, int] = {texto_simples(n): c for c, n in ESPECIES.items()}

_UF_POR_NOME_SIMPLES: dict[str, str] = {texto_simples(n): s for n, s in UF_SIGLA.items()}


def especie_de(valor: object) -> int | None:
    """Codigo da especie a partir do codigo (`"31"`, `31`) ou do nome no arquivo."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if texto.isdigit():
        return int(texto)
    return NOME_PARA_ESPECIE.get(texto_simples(texto))


def classe_de(especie: int | None) -> str | None:
    """`"acidentario"`, `"previdenciario"` ou None (fora do escopo de incapacidade)."""
    if especie is None:
        return None
    if especie in ACIDENTARIAS:
        return "acidentario"
    if especie in PREVIDENCIARIAS:
        return "previdenciario"
    return None


def normalizar_cid(valor: object) -> str | None:
    """CID como o SIH escreve: letra + 2 digitos + 4o digito opcional, sem ponto.

    Aceita `"V29.8 Motociclista Outr Acid"`, `"V298"`, `"V29"` e `"S525"`.
    Devolve None para `"Zerados"`, `"Em Branco"`, `"000000"`, `"{ñ class}"` e
    para codigos numericos de tres digitos (CID-9 residual).
    """
    if valor is None:
        return None
    m = _CID.match(str(valor).upper())
    if not m:
        return None
    letra, categoria, quarto = m.groups()
    return f"{letra}{categoria}{quarto or ''}"


def uf_de_municipio(valor: object) -> str | None:
    """Sigla da UF embutida em `Mun Resid` (`"02009-AL-Belo Monte"` -> `"AL"`).

    E a fonte confiavel: nos CSVs de 2020 e 2021 a coluna `UF` **nao bate** com
    o municipio de residencia (D-030). O campo `Mun Resid` bate em todos os anos.
    """
    if valor is None:
        return None
    m = _UF_NO_MUNICIPIO.match(str(valor))
    return m.group(1).upper() if m else None


def uf_de_nome(valor: object) -> str | None:
    """Sigla a partir do nome por extenso (`"São Paulo"` -> `"SP"`) ou da propria sigla."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if len(texto) == 2 and texto.upper() in UF_SIGLA.values():
        return texto.upper()
    return _UF_POR_NOME_SIMPLES.get(texto_simples(texto))
