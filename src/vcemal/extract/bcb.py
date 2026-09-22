"""Banco Central: cambio R$/US$ medio mensal (SGS 3698).

API publica, sem chave, sobre HTTPS. E a taxa de venda media do periodo,
"Taxa de cambio - Livre - Dolar americano (venda) - media de periodo -
mensal". Serve para levar a reais a receita que a Prosus reporta em dolar,
pela media do ano fiscal -- que e o que a propria Prosus faz na nota de
moedas do relatorio anual.
"""

from __future__ import annotations

import logging

from vcemal.extract._http import get_json as _get_json

log = logging.getLogger("vcemal.extract.bcb")

BASE = "https://api.bcb.gov.br/dados/serie"
#: Dolar (venda), media de periodo, mensal.
SERIE_CAMBIO_MEDIO = "3698"


def linhas_cambio(bruto: list[dict]) -> list[dict]:
    """Resposta do SGS -> `[{"periodo": "2018-04", "cambio": 3.4075}, ...]`."""
    linhas = []
    for r in bruto:
        valor = r.get("valor")
        if valor in (None, "", "-"):
            continue
        dia, mes, ano = str(r["data"]).split("/")
        linhas.append({"periodo": f"{ano}-{mes}", "cambio": float(valor)})
    return linhas


def cambio_mensal(inicio: str, fim: str) -> list[dict]:
    """Serie mensal entre as competencias `AAAA-MM` (inclusive)."""
    ai, mi = inicio.split("-")
    af, mf = fim.split("-")
    url = (
        f"{BASE}/bcdata.sgs.{SERIE_CAMBIO_MEDIO}/dados?formato=json"
        f"&dataInicial=01/{mi}/{ai}&dataFinal=28/{mf}/{af}"
    )
    linhas = linhas_cambio(_get_json(url))
    log.info("cambio medio mensal (SGS %s): %d meses", SERIE_CAMBIO_MEDIO, len(linhas))
    return linhas
