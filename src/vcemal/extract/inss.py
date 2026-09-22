"""INSS: beneficios concedidos, mes a mes, pelo portal de dados abertos.

Tres conjuntos no CKAN cobrem a serie, e o layout muda entre eles e dentro
deles (`vcemal.transform.inss` le todos):

* `inss-beneficios-concedidos` -- dez/2018 a mai/2023, CSV solto (2019-2021)
  ou ZIP com CSV, JSON e XML (2021-2023);
* `beneficios-concedidos-plano-de-dados-abertos-jun-2023-a-jun-2025` --
  jun/2023 em diante, XLSX (o titulo do conjunto ficou; ele segue ate 2027);
* `beneficios-concedidos-dez-2012-a-nov-2018-...` -- um ZIP por ano. **Nao
  integrado**: e formato anual e o SIH do projeto comeca em 2016; fica
  declarado no anexo A.

O nome do recurso ("Beneficios concedidos fevereiro 2025") e a chave estavel;
a URL nao e -- muda de pasta, de grafia e de sufixo (`_consulta60939491`).
A busca do CKAN (`package_search`) estava quebrada no servidor em set/2026;
`package_show` funciona e e o que se usa.
"""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path

from vcemal.extract._http import baixar as _baixar
from vcemal.extract._http import get_json as _get_json
from vcemal.extract.senatran import mes_do_arquivo

log = logging.getLogger("vcemal.extract.inss")

CKAN = "https://dadosabertos.inss.gov.br/api/3/action/package_show?id="

#: Conjuntos mensais, do mais antigo ao mais novo.
CONJUNTOS: tuple[str, ...] = (
    "inss-beneficios-concedidos",
    "beneficios-concedidos-plano-de-dados-abertos-jun-2023-a-jun-2025",
)

_ANO = re.compile(r"(20\d{2})")


def _competencia_do_nome(nome: str) -> tuple[int, int] | None:
    """`"Beneficios concedidos fevereiro 2025"` -> `(2025, 2)`."""
    mes = mes_do_arquivo(nome)
    anos = _ANO.findall(nome)
    if mes is None or not anos:
        return None
    return int(anos[-1]), mes


def indice() -> dict[tuple[int, int], str]:
    """(ano, mes) -> URL do arquivo do mes, varrendo os conjuntos mensais.

    Quando o mesmo mes aparece em dois conjuntos, o mais novo manda.
    """
    saida: dict[tuple[int, int], str] = {}
    for conjunto in CONJUNTOS:
        bruto = _get_json(f"{CKAN}{conjunto}")
        if not bruto.get("success"):
            raise RuntimeError(f"CKAN nao devolveu o conjunto {conjunto}: {bruto.get('error')}")
        n = 0
        for recurso in bruto["result"].get("resources", []):
            chave = _competencia_do_nome(recurso.get("name", ""))
            if chave is None or not recurso.get("url"):
                continue
            saida[chave] = recurso["url"]
            n += 1
        log.info("%s: %d competencias", conjunto, n)
    return saida


def _extensao(url: str) -> str:
    return Path(url.split("?")[0]).suffix.lower() or ".csv"


def baixar_mes(
    ano: int, mes: int, cache: Path, indice_urls: dict[tuple[int, int], str]
) -> Path | None:
    """Baixa o arquivo do mes para `cache` e devolve o caminho do dado tabular.

    ZIP e aberto e so o CSV de dentro fica (o JSON e o XML sao o mesmo dado,
    tres vezes maior). Devolve None se o mes nao existe no indice.
    """
    cache.mkdir(parents=True, exist_ok=True)
    base = f"concedidos_{ano:04d}{mes:02d}"
    for ext in (".csv", ".xlsx", ".xls"):
        pronto = cache / f"{base}{ext}"
        if pronto.exists():
            return pronto

    url = indice_urls.get((ano, mes))
    if url is None:
        log.warning("%04d-%02d: sem arquivo no cache nem no portal", ano, mes)
        return None

    ext = _extensao(url)
    bruto = cache / f"{base}{ext}"
    log.info("%04d-%02d: baixando %s", ano, mes, url)
    bruto.write_bytes(_baixar(url))

    if ext != ".zip":
        return bruto
    with zipfile.ZipFile(bruto) as z:
        membros = [m for m in z.namelist() if m.lower().endswith(".csv")]
        if not membros:
            raise ValueError(f"{bruto.name}: ZIP sem CSV dentro ({z.namelist()})")
        destino = cache / f"{base}.csv"
        with z.open(membros[0]) as origem, destino.open("wb") as saida:
            saida.write(origem.read())
    bruto.unlink()
    return destino
