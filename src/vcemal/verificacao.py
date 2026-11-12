"""Verificacao mecanica da evidencia citada pelos codificadores da auditoria (D-067).

Os codificadores da auditoria sao agentes de IA. Um agente pode citar uma URL que
nao existe ou um trecho que a pagina nao contem. Antes da consolidacao, cada linha
encontrada (`confianca` A a D) passa por aqui: a pagina e baixada (por
`scripts/auditoria_verificar.py`) e o trecho tem de estar nela.

Sem pandas e sem rede: as regras sao testadas em `tests/test_verificacao.py`.

Status de uma linha:

* `wayback_script` -- a mesma URL, municipio e plataforma estao em
  `cronologia_wayback.csv`, que o `make wayback` gerou lendo a pagina (D-038).
* `confirmado` -- todos os fragmentos do trecho estao na pagina. Sem trecho
  (tipos 3 e 5), o nome do municipio tem de estar.
* `trecho_ausente` -- a pagina abriu e o trecho nao esta nela.
* `inacessivel` -- nem a URL nem a copia mais recente no Wayback abriram.

Na versao principal so `wayback_script` e `confirmado` ficam. As linhas
`trecho_ausente` sempre viram `N`, e as `inacessivel` so ficam na sensibilidade.
"""

from __future__ import annotations

import html
import re
import unicodedata

ACEITOS = ("wayback_script", "confirmado")
ACEITOS_SENSIBILIDADE = ("wayback_script", "confirmado", "inacessivel")

#: Fragmento menor que isso nao discrimina pagina nenhuma e e ignorado.
FRAGMENTO_MINIMO = 15

_RE_SCRIPT = re.compile(r"<(script|style|noscript)\b.*?</\1\s*>", re.I | re.S)
_RE_TAG = re.compile(r"<[^>]+>")
_RE_NAO_ALNUM = re.compile(r"[^0-9a-z]+")
_RE_RETICENCIAS = re.compile(r"\[\s*\.\.\.\s*\]|\.\.\.|…")


def _vazio(v) -> bool:
    return v is None or (isinstance(v, float) and v != v) or str(v).strip() in ("", "nan")


def normalizar(texto: str) -> str:
    """Minusculas, sem acento, sem pontuacao, espacos colapsados."""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return _RE_NAO_ALNUM.sub(" ", t).strip()


def texto_da_pagina(corpo_html: str) -> str:
    """Texto visivel de uma pagina, normalizado. Atributos (title, alt, meta) ficam de fora."""
    sem_script = _RE_SCRIPT.sub(" ", corpo_html)
    return normalizar(html.unescape(_RE_TAG.sub(" ", sem_script)))


def texto_bruto_normalizado(corpo: str) -> str:
    """Corpo inteiro normalizado, com tags e atributos (pagina que traz o texto em JSON)."""
    return normalizar(html.unescape(corpo))


def fragmentos(trecho: str) -> list[str]:
    """Pedacos do trecho entre reticencias, normalizados, com o tamanho minimo."""
    partes = [normalizar(p) for p in _RE_RETICENCIAS.split(trecho)]
    longos = [p for p in partes if len(p) >= FRAGMENTO_MINIMO]
    if longos:
        return longos
    inteiro = normalizar(trecho)
    return [inteiro] if inteiro else []


def confere(pagina_normalizada: str, trecho, municipio: str) -> bool:
    """O trecho (ou, sem trecho, o nome do municipio) esta na pagina normalizada?"""
    if _vazio(trecho):
        alvo = normalizar(municipio)
        return bool(alvo) and f" {alvo} " in f" {pagina_normalizada} "
    frags = fragmentos(str(trecho))
    return bool(frags) and all(f in pagina_normalizada for f in frags)


def encontrada(linha: dict) -> bool:
    return str(linha.get("confianca", "")).strip() != "N"


def chave_wayback(linha: dict) -> tuple[str, str, str]:
    return (
        str(linha["municipio_ibge"]).strip(),
        str(linha["plataforma"]).strip(),
        str(linha["url"]).strip(),
    )


def aplicar(linhas: list[dict], status: list[str | None], aceitos=ACEITOS) -> list[dict]:
    """Planilha verificada: o que nao passou vira `N` (entrada) ou sai (saida).

    `status[i]` e o status da linha i, ou None para as linhas `N`, que nao se verificam.
    Uma entrada rebaixada leva junto as saidas do mesmo municipio x plataforma: saida
    sem entrada nao tem leitura (protocolo, secao 7).
    """
    if len(status) != len(linhas):
        raise ValueError("um status por linha")

    def par_de(r: dict) -> tuple[str, str]:
        return (str(r["municipio_ibge"]).strip(), str(r["plataforma"]).strip())

    def entrada(r: dict) -> bool:
        return str(r["evento"]).strip() == "entrada"

    # pares com ao menos uma entrada encontrada que passou
    com_entrada = {
        par_de(r)
        for r, s in zip(linhas, status, strict=True)
        if entrada(r) and encontrada(r) and s in aceitos
    }

    saida: list[dict] = []
    vistos_n: set[tuple[str, str]] = set()
    for r, s in zip(linhas, status, strict=True):
        par = par_de(r)
        if not entrada(r):
            if s in aceitos and par in com_entrada:
                saida.append(dict(r))
            continue
        if encontrada(r) and s in aceitos:
            saida.append(dict(r))
            continue
        # N original ou entrada rebaixada: uma linha N por par, e so se nada passou
        if par in com_entrada or par in vistos_n:
            continue
        vistos_n.add(par)
        if not encontrada(r):
            saida.append(dict(r))
            continue
        n = dict(r)
        buscas = "" if _vazio(r.get("buscas")) else str(r["buscas"]).strip()
        motivo = f"verificacao D-067: {s} ({str(r['url']).strip()})"
        n.update(
            data_min="",
            data_max="",
            tipo_evidencia=0,
            confianca="N",
            fonte="",
            url="",
            trecho="",
            buscas=f"{buscas}; {motivo}" if buscas else motivo,
        )
        obs = "" if _vazio(r.get("observacao")) else str(r["observacao"]).strip()
        rotulo = "rebaixada pela verificacao"
        n["observacao"] = f"{obs}; {rotulo}" if obs else rotulo
        saida.append(n)
    return saida
