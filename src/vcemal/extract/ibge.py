"""
IBGE: lista de municipios e estimativa populacional municipal.

API publica, sem chave, sobre HTTPS -- ao contrario do SIH, roda em qualquer
ambiente com rede.

**Buraco conhecido na serie.** O agregado 6579 (Populacao residente estimada)
publica 2001-2021 e depois **pula 2022 e 2023**, voltando em 2024: 2022 foi ano
de Censo e a estimativa nao foi divulgada para esses anos. Quem precisa de 2022
tem que ir ao Censo (agregado proprio, outra definicao de populacao); 2023 nao
tem estimativa oficial por municipio nesta serie. `populacao` reporta os anos
que faltaram em vez de devolver linha faltando em silencio. Ver D-014.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

from vcemal.extract._http import get_json as _get_json

log = logging.getLogger("vcemal.extract.ibge")

BASE = "https://servicodados.ibge.gov.br"

#: Populacao residente estimada, por municipio.
AGREGADO_POPULACAO = "6579"
VARIAVEL_POPULACAO = "9324"


def _uf_de(municipio: dict) -> str | None:
    """Sigla da UF. Municipio novo vem sem `microrregiao`, so com regiao imediata."""
    for caminho in (
        ("microrregiao", "mesorregiao", "UF"),
        ("regiao-imediata", "regiao-intermediaria", "UF"),
    ):
        no = municipio
        for chave in caminho:
            no = (no or {}).get(chave)
        if no:
            return no["sigla"]
    return None


def _regiao_imediata_de(municipio: dict) -> int | None:
    """Codigo da regiao imediata do IBGE, ou None.

    E o nivel de agrupamento dos erros-padrao (D-024): a geografia em que o
    entregador e o paciente circulam, e onde `MUNIC_RES` diverge do municipio do
    acidente. Presente nos 5.571 municipios; sao 510 regioes.
    """
    regiao = municipio.get("regiao-imediata") or {}
    return int(regiao["id"]) if regiao.get("id") is not None else None


def listar_municipios() -> list[dict]:
    """Todos os municipios, com UF e regiao imediata.

    `{"id": 4106902, "nome": "Curitiba", "uf": "PR", "regiao_imediata": 410001}`
    """
    bruto = _get_json(f"{BASE}/api/v1/localidades/municipios")
    municipios = [
        {
            "id": int(m["id"]),
            "nome": m["nome"],
            "uf": _uf_de(m),
            "regiao_imediata": _regiao_imediata_de(m),
        }
        for m in bruto
        if _uf_de(m) is not None
    ]
    sem_regiao = sum(1 for m in municipios if m["regiao_imediata"] is None)
    if sem_regiao:
        log.warning("%d municipios sem regiao imediata -- cluster fica incompleto", sem_regiao)
    log.info("municipios IBGE: %d", len(municipios))
    return municipios


def periodos_disponiveis() -> list[str]:
    """Anos que a serie de estimativa populacional realmente publica."""
    url = f"{BASE}/api/v3/agregados/{AGREGADO_POPULACAO}/periodos"
    return [str(p["id"]) for p in _get_json(url)]


def linhas_populacao(bruto: list[dict]) -> list[dict]:
    """Resposta de um agregado por municipio -> `[{"municipio_ibge", "ano", "populacao"}]`."""
    linhas: list[dict] = []
    for variavel in bruto:
        for resultado in variavel.get("resultados", []):
            for serie in resultado.get("series", []):
                codigo = int(serie["localidade"]["id"])
                for ano, valor in serie.get("serie", {}).items():
                    if valor in (None, "", "-", "..."):
                        continue
                    linhas.append(
                        {"municipio_ibge": codigo, "ano": int(ano), "populacao": int(valor)}
                    )
    return linhas


#: Populacao residente do Censo 2022, por municipio. E o que define o universo
#: da cronologia de entrada (D-033): a estimativa anual (6579) pula 2022.
AGREGADO_CENSO_2022 = "4709"
VARIAVEL_CENSO = "93"


def populacao_censo_2022() -> list[dict]:
    """Populacao do Censo 2022 nos 5.570 municipios."""
    url = (
        f"{BASE}/api/v3/agregados/{AGREGADO_CENSO_2022}"
        f"/periodos/2022/variaveis/{VARIAVEL_CENSO}?localidades=N6[all]"
    )
    linhas = linhas_populacao(_get_json(url))
    log.info("censo 2022: %d municipios", len(linhas))
    return linhas


def populacao(anos: list[int] | list[str]) -> tuple[list[dict], list[str]]:
    """Populacao estimada por municipio para os anos pedidos.

    Devolve `(linhas, anos_sem_dado)`, com `linhas` no formato
    `{"municipio_ibge": 4106902, "ano": 2021, "populacao": 1963726}`.

    Os anos ausentes voltam na segunda posicao de proposito: 2022 e 2023 nao
    existem nesta serie, e um denominador com buraco precisa gritar.
    """
    pedidos = [str(a) for a in anos]
    disponiveis = set(periodos_disponiveis())
    faltando = [a for a in pedidos if a not in disponiveis]
    usar = [a for a in pedidos if a in disponiveis]
    if faltando:
        log.warning("sem estimativa populacional para: %s", ", ".join(faltando))
    if not usar:
        return [], faltando

    periodo = quote("|".join(usar), safe="")
    url = (
        f"{BASE}/api/v3/agregados/{AGREGADO_POPULACAO}"
        f"/periodos/{periodo}/variaveis/{VARIAVEL_POPULACAO}?localidades=N6[all]"
    )
    linhas = linhas_populacao(_get_json(url))
    log.info("populacao: %d linhas para %s", len(linhas), ", ".join(usar))
    return linhas, faltando


#: IPCA numero-indice (base dez./1993 = 100), mensal, Brasil. SIDRA tabela 1737.
SIDRA = "https://apisidra.ibge.gov.br/values"
TABELA_IPCA = "1737"
VARIAVEL_IPCA = "2266"


def linhas_ipca(bruto: list[dict]) -> list[dict]:
    """Resposta do SIDRA -> `[{"periodo": "202301", "indice": 6508.4}, ...]`.

    A primeira linha da resposta e o cabecalho (nomes das colunas), nao dado.
    """
    linhas = []
    for r in bruto[1:]:
        valor = r.get("V")
        if valor in (None, "", "-", "...", "X"):
            continue
        linhas.append({"periodo": str(r["D3C"]), "indice": float(valor)})
    return linhas


def ipca() -> list[dict]:
    """Serie mensal completa do IPCA numero-indice, desde dezembro de 1979."""
    url = f"{SIDRA}/t/{TABELA_IPCA}/n1/all/v/{VARIAVEL_IPCA}/p/all"
    linhas = linhas_ipca(_get_json(url))
    if not linhas:
        raise ValueError("SIDRA devolveu a serie do IPCA vazia")
    log.info("IPCA: %d meses, ate %s", len(linhas), linhas[-1]["periodo"])
    return linhas
