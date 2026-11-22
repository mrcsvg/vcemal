#!/usr/bin/env python
"""Verifica a evidencia das planilhas da auditoria antes da consolidacao (D-067).

    python scripts/auditoria_verificar.py docs/fontes/cronologia/auditoria_a.csv \
        docs/fontes/cronologia/auditoria_b.csv

Para cada planilha `X.csv` escreve, ao lado:
    X_verificada.csv       versao principal (so `wayback_script` e `confirmado` ficam)
    X_verificada_sens.csv  sensibilidade (as `inacessivel` tambem ficam)
e em `output/auditoria/verificacao.csv` o status de cada linha encontrada.

Cada URL e baixada uma vez (cache em `data/interim/verificacao/`). Se a URL nao
abre, tenta a copia mais recente no Wayback (`web.archive.org/web/2026/<url>`).
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from vcemal import cronologia as cro  # noqa: E402
from vcemal import verificacao as ver  # noqa: E402

log = logging.getLogger("auditoria_verificar")

CACHE = RAIZ / "data" / "interim" / "verificacao"
WAYBACK = RAIZ / "output" / "tabelas" / "cronologia_wayback.csv"
SAIDA = RAIZ / "output" / "auditoria" / "verificacao.csv"
# Navegador comum: varios portais de noticia recusam cliente sem cara de navegador.
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
CABECALHOS = {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}


def _baixar(url: str, timeout: int = 40) -> str | None:
    destino = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".html")
    if destino.exists():
        corpo = destino.read_text(encoding="utf-8", errors="replace")
        return corpo or None
    try:
        pedido = urllib.request.Request(url, headers=CABECALHOS)
        with urllib.request.urlopen(pedido, timeout=timeout) as r:  # noqa: S310
            bruto = r.read()
            cs = r.headers.get_content_charset() or "utf-8"
        corpo = bruto.decode(cs, errors="replace")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
        log.info("falhou %s: %s", url, e)
        corpo = ""
    CACHE.mkdir(parents=True, exist_ok=True)
    destino.write_text(corpo, encoding="utf-8")
    return corpo or None


def _status(r: dict, scripts: set[tuple]) -> tuple[str, str]:
    if ver.chave_wayback(r) in scripts:
        return "wayback_script", ""
    url = str(r["url"]).strip()
    tentativas = [url]
    if "web.archive.org" not in url:
        tentativas.append(f"https://web.archive.org/web/2026/{url}")
    abriu = False
    for u in tentativas:
        corpo = _baixar(u)
        if not corpo:
            continue
        abriu = True
        for texto in (ver.texto_da_pagina(corpo), ver.texto_bruto_normalizado(corpo)):
            if ver.confere(texto, r.get("trecho"), str(r["municipio"])):
                return "confirmado", u
    return ("trecho_ausente" if abriu else "inacessivel"), ""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("planilhas", nargs="+", type=Path)
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    wb = pd.read_csv(WAYBACK, dtype=str).fillna("")
    scripts = {ver.chave_wayback(r) for r in wb.to_dict("records")}

    registro = []
    for caminho in args.planilhas:
        linhas = pd.read_csv(caminho, dtype=str).fillna("").to_dict("records")
        cro.validar(linhas)
        status: list[str | None] = []
        for r in linhas:
            if not ver.encontrada(r):
                status.append(None)
                continue
            s, aberta = _status(r, scripts)
            status.append(s)
            registro.append(
                {
                    "planilha": caminho.name,
                    "municipio_ibge": r["municipio_ibge"],
                    "municipio": r["municipio"],
                    "plataforma": r["plataforma"],
                    "evento": r["evento"],
                    "data_min": r["data_min"],
                    "data_max": r["data_max"],
                    "confianca": r["confianca"],
                    "url": r["url"],
                    "status": s,
                    "url_aberta": aberta,
                }
            )
        versoes = (("_verificada", ver.ACEITOS), ("_verificada_sens", ver.ACEITOS_SENSIBILIDADE))
        for sufixo, aceitos in versoes:
            out = ver.aplicar(linhas, status, aceitos=aceitos)
            cro.validar(out)
            destino = caminho.with_name(caminho.stem + sufixo + ".csv")
            pd.DataFrame(out, columns=cro.COLUNAS).to_csv(destino, index=False)
            log.info("%s -> %s (%d linhas)", caminho.name, destino.name, len(out))

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    reg = pd.DataFrame(registro)
    reg.to_csv(SAIDA, index=False)
    if len(reg):
        print(reg.groupby(["planilha", "status"]).size().unstack(fill_value=0).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
