"""Wayback Machine: snapshots das paginas de cobertura das plataformas (F3, tipo 3).

A pagina de "cidades atendidas" do portal de entregadores lista onde a
plataforma recruta entregador proprio. Comparar a lista entre snapshots data a
entrada de centenas de municipios de uma vez, como intervalo -- e o caminho
escalavel da secao 3 do protocolo (`docs/protocolo-cronologia-entrada.md`).

Duas chamadas, ambas so leitura:

* **CDX** (`/cdx/search/cdx`): o indice de snapshots de uma URL, com timestamp,
  status e `digest` (hash do conteudo). Snapshots com o mesmo `digest` tem o
  mesmo HTML: baixa-se um por digest, mas **todos os timestamps contam** para
  apertar o intervalo.
* **Snapshot bruto** (`/web/<timestamp>id_/<url>`): o `id_` devolve o HTML
  original, sem a barra de navegacao que o Wayback injeta.

**Nao roda de nuvem.** Em out/2026 o `web.archive.org` derrubava toda conexao
vinda do ambiente de nuvem da sessao, e a API do `archive.org` respondia 429.
De uma maquina comum responde. Por isso o cache em `data/interim/wayback/`:
snapshot ja baixado nao volta a rede, e a etapa pode ser rodada uma vez e
reaproveitada.

**Educacao com o servidor.** O Internet Archive limita a taxa por IP. Ha uma
pausa fixa entre downloads e nova tentativa com espera crescente em 429 e 5xx;
qualquer outro erro sobe -- snapshot que falhou nao pode virar "cidade
ausente".
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from vcemal.extract._http import baixar

log = logging.getLogger("vcemal.extract.wayback")

CDX = "https://web.archive.org/cdx/search/cdx"
BRUTO = "https://web.archive.org/web/{timestamp}id_/{original}"
VISIVEL = "https://web.archive.org/web/{timestamp}/{original}"

#: Paginas de cobertura com frota propria, por plataforma. So entra aqui pagina
#: cujo snapshot foi visto no indice: a do iFood aparece em set/2019. As das
#: demais plataformas ficam para o piloto confirmar (`--pagina` acrescenta).
PAGINAS: dict[str, tuple[str, ...]] = {
    "ifood": ("entregador.ifood.com.br/cidades-atendidas",),
}

#: Pausa entre downloads, em segundos.
PAUSA = 3.0
#: Esperas antes de cada nova tentativa em 429 ou 5xx, em segundos.
ESPERAS = (5, 15, 45, 120)


@dataclass(frozen=True)
class Snapshot:
    timestamp: str  # AAAAMMDDhhmmss
    original: str
    digest: str

    @property
    def mes(self) -> str:
        return f"{self.timestamp[:4]}-{self.timestamp[4:6]}"

    @property
    def url(self) -> str:
        """Endereco para citar na planilha: a pagina como o Wayback a mostra."""
        return VISIVEL.format(timestamp=self.timestamp, original=self.original)


def _caminho(url: str) -> str:
    """Host e caminho sem esquema, `www.`, barra final, query nem fragmento."""
    partes = urllib.parse.urlsplit(url if "://" in url else f"http://{url}")
    host = partes.netloc.lower().split(":")[0].removeprefix("www.")
    return f"{host}{partes.path.rstrip('/')}"


def e_a_pagina(original: str, pagina: str) -> bool:
    """O snapshot e da pagina pedida, e nao de outra que comece igual.

    O CDX e consultado por prefixo para pegar `/cidades-atendidas/` e
    `/cidades-atendidas?utm=...`, mas o prefixo tambem traz
    `/cidades-atendidas-sp`, que e outra pagina.
    """
    return _caminho(original) == _caminho(pagina)


def ler_cdx(linhas: list[list[str]], pagina: str) -> list[Snapshot]:
    """Resposta JSON do CDX -> snapshots com status 200 da pagina, em ordem de tempo.

    A primeira linha da resposta e o cabecalho com os nomes dos campos.
    """
    if not linhas:
        return []
    campos, *dados = linhas
    snapshots = []
    for valores in dados:
        r = dict(zip(campos, valores, strict=False))
        if r.get("statuscode") != "200" or not e_a_pagina(r["original"], pagina):
            continue
        snapshots.append(Snapshot(r["timestamp"], r["original"], r["digest"]))
    return sorted(snapshots, key=lambda s: s.timestamp)


def _baixar_com_paciencia(url: str, dormir=time.sleep) -> bytes:
    for tentativa, espera in enumerate((*ESPERAS, None), start=1):
        try:
            return baixar(url, timeout=120)
        except urllib.error.HTTPError as e:
            if espera is None or not (e.code == 429 or e.code >= 500):
                raise
            log.warning("HTTP %d em %s; tentativa %d, espera %ds", e.code, url, tentativa, espera)
        except urllib.error.URLError as e:
            if espera is None:
                raise
            log.warning("%s em %s; tentativa %d, espera %ds", e.reason, url, tentativa, espera)
        dormir(espera)
    raise AssertionError("inalcancavel")


def listar(
    pagina: str, cache: Path | None = None, offline: bool = False, dormir=time.sleep
) -> list[Snapshot]:
    """Todos os snapshots com status 200 da pagina, do mais antigo ao mais novo.

    Com `cache`, a resposta do CDX fica em `cache/cdx.json`; `offline` le de la
    sem ir a rede, para refazer a leitura com o indice da ultima consulta.
    """
    guardado = cache / "cdx.json" if cache is not None else None
    if offline:
        if guardado is None or not guardado.exists():
            raise FileNotFoundError(f"sem indice guardado para {pagina} em {guardado}")
        corpo = guardado.read_bytes()
    else:
        consulta = urllib.parse.urlencode(
            {
                "url": pagina,
                "matchType": "prefix",
                "output": "json",
                "fl": "timestamp,original,statuscode,digest",
                "filter": "statuscode:200",
            }
        )
        corpo = _baixar_com_paciencia(f"{CDX}?{consulta}", dormir)
        if guardado is not None:
            guardado.parent.mkdir(parents=True, exist_ok=True)
            guardado.write_bytes(corpo)
    linhas = json.loads(corpo.decode("utf-8")) if corpo.strip() else []
    snapshots = ler_cdx(linhas, pagina)
    log.info(
        "%s: %d snapshots, %d conteudos distintos",
        pagina,
        len(snapshots),
        len({s.digest for s in snapshots}),
    )
    return snapshots


def caminho_do_cache(cache: Path, snapshot: Snapshot) -> Path:
    """Um arquivo por digest: conteudo igual nao se baixa duas vezes."""
    return cache / f"{snapshot.digest}.html"


def baixar_snapshots(
    snapshots: list[Snapshot], cache: Path, pausa: float = PAUSA, dormir=time.sleep
) -> dict[str, Path]:
    """Baixa um snapshot por digest para `cache`. Devolve digest -> arquivo.

    Arquivo ja em disco nao volta a rede. Grava em `.parcial` e renomeia, para
    um download interrompido nao passar por snapshot completo.
    """
    cache.mkdir(parents=True, exist_ok=True)
    arquivos: dict[str, Path] = {}
    for s in snapshots:
        if s.digest in arquivos:
            continue
        destino = caminho_do_cache(cache, s)
        if not destino.exists():
            corpo = _baixar_com_paciencia(
                BRUTO.format(timestamp=s.timestamp, original=s.original), dormir
            )
            parcial = destino.with_suffix(".parcial")
            parcial.write_bytes(corpo)
            parcial.rename(destino)
            log.info("%s: %.0f kB -> %s", s.timestamp, len(corpo) / 1e3, destino.name)
            dormir(pausa)
        arquivos[s.digest] = destino
    return arquivos
