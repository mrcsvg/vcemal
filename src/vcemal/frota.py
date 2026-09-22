"""
Quais tipos de veiculo do RENAVAM compoem o denominador de motociclista.

O denominador precisa casar com o numerador. O numerador e V20-V29 do CID-10
(ver `vcemal.cid`), e a nota de inclusao do proprio CID-10 brasileiro diz o que
entra ali:

    V20-V29 Motociclista traumatizado em um acidente de transporte
    Inclui:  bicicleta motorizada
             motocicleta com "side-car"
             motoneta
             patinete motorizado
    Exclui:  triciclo motorizado (V30-V39)
             veiculo motorizado de tres rodas (V30-V39)

-- DATASUS, CID-10 v2008, `www2.datasus.gov.br/cid10/V2008/WebHelp/v20_v29.htm`

Logo o denominador **nao e a coluna MOTOCICLETA sozinha**. Motoneta e side-car
estao nomeados na nota; ciclomotor e a "bicicleta motorizada" / moped da mesma
lista. E triciclo e quadriciclo ficam de fora -- o CID manda tres rodas para
V30-V39, que nao e o desfecho deste projeto.

Usar so MOTOCICLETA subestimaria a frota exposta e inflaria a taxa; somar
TRICICLO e QUADRICICLO contaria veiculo cujo acidente nunca entra no numerador.
Os dois erros enviesam a taxa em direcoes opostas e nenhum aparece no resultado.
Ver D-013 em `docs/decisoes.md`.
"""

from __future__ import annotations

#: Colunas de tipo de veiculo do arquivo "Frota por Municipio e Tipo" (Senatran)
#: que correspondem a V20-V29.
TIPOS_MOTO: tuple[str, ...] = ("MOTOCICLETA", "MOTONETA", "CICLOMOTOR", "SIDE-CAR")

#: Duas rodas ou assemelhados que o CID-10 manda para fora de V20-V29.
#: Ficam registrados aqui para que a exclusao seja deliberada, nao esquecimento.
TIPOS_FORA_DE_V20_V29: dict[str, str] = {
    "TRICICLO": "tres rodas -> V30-V39",
    "QUADRICICLO": "quatro rodas, nao e motocicleta -> fora de V20-V29",
}

#: Nome da coluna agregada que o painel recebe.
COLUNA_FROTA_MOTO = "frota_moto"

#: Coluna de total geral do arquivo do Senatran, util como sanidade.
COLUNA_TOTAL = "TOTAL"


def colunas_esperadas() -> tuple[str, ...]:
    """Colunas de tipo que o parser exige encontrar no arquivo."""
    return TIPOS_MOTO


def conferir_colunas(colunas: list[str]) -> list[str]:
    """Quais dos `TIPOS_MOTO` faltam no arquivo lido.

    Layout do Senatran mudou de nome de coluna ao longo da serie; faltar uma
    coluna e erro para reportar alto, nao para preencher com zero -- zero aqui
    vira frota subestimada e taxa inflada, em silencio.
    """
    presentes = {str(c).strip().upper() for c in colunas}
    return [t for t in TIPOS_MOTO if t not in presentes]
