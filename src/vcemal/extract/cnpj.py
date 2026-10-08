"""Dados abertos do CNPJ (Receita Federal): estabelecimentos de entrega rapida (D-040).

A Receita publica o cadastro inteiro todo mes num compartilhamento Nextcloud,
lido aqui pelo WebDAV publico (`PROPFIND` para listar, `GET` para baixar, a
senha e vazia e o usuario e o token do compartilhamento). Tres pegadinhas,
todas vistas contra o servidor real em out/2026:

* **Lento e instavel.** ~0,5 a 1,5 MB/s, e a conexao cai no meio de arquivo de
  2 GB. O download retoma com `Range` ate o tamanho anunciado, e so vira o
  arquivo final depois de passar no teste do zip.
* **As 10 partes nao sao faixas de tempo.** Cada ano aparece numa combinacao
  diferente de partes, e a parte 0 tem seis vezes o tamanho das outras: serie
  sem todas as partes nao se compara entre anos.
* **latin-1, sem cabecalho, `;`.** Ha bytes que o leitor latin-1 do DuckDB
  recusa; o pandas le em blocos direto do zip, sem descompactar em disco.

Os baixados ficam no cadastro (situacao 08), com a data de inicio: a contagem de
aberturas nao tem vies de sobrevivencia.
"""

from __future__ import annotations

import base64
import io
import logging
import re
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from vcemal.extract._http import USER_AGENT

log = logging.getLogger("vcemal.extract.cnpj")

WEBDAV = "https://arquivos.receitafederal.gov.br/public.php/webdav"
TOKEN = "YggdBLfdninEJX9"
PARTES = tuple(range(10))

#: Colunas do layout de Estabelecimentos (sem cabecalho), so as usadas.
COLUNAS_ESTABELECIMENTO = {
    0: "cnpj_basico",
    3: "matriz_filial",
    5: "situacao",
    10: "data_inicio",
    11: "cnae_principal",
    12: "cnae_secundaria",
    19: "uf",
    20: "municipio_rf",
}
COLUNAS_SIMPLES = {0: "cnpj_basico", 4: "opcao_mei", 5: "data_opcao_mei", 6: "data_exclusao_mei"}


def _pedido(caminho: str, metodo: str = "GET", cabecalhos: dict | None = None):
    auth = base64.b64encode(f"{TOKEN}:".encode()).decode()
    h = {"User-Agent": USER_AGENT, "Authorization": f"Basic {auth}", **(cabecalhos or {})}
    return urllib.request.Request(f"{WEBDAV}/{caminho.lstrip('/')}", method=metodo, headers=h)


def listar(caminho: str = "") -> dict[str, int | None]:
    """Nome -> tamanho em bytes (None para pasta) do que ha em `caminho`."""
    pedido = _pedido(caminho, "PROPFIND", {"Depth": "1"})
    with urllib.request.urlopen(pedido, timeout=120) as r:  # noqa: S310
        xml = r.read().decode("utf-8")
    itens = {}
    for bloco in re.findall(r"<d:response>(.*?)</d:response>", xml, re.S):
        nome = re.search(r"<d:href>(.*?)</d:href>", bloco).group(1).rstrip("/").split("/")[-1]
        tamanho = re.search(r"<d:getcontentlength>(\d+)", bloco)
        itens[nome] = int(tamanho.group(1)) if tamanho else None
    itens.pop("webdav", None)
    itens.pop(caminho.strip("/").split("/")[-1], None)
    return itens


def ultimo_mes() -> str:
    """A publicacao mais recente, `AAAA-MM`."""
    return max(n for n in listar() if re.fullmatch(r"\d{4}-\d{2}", n))


def zip_integro(arquivo: Path) -> bool:
    try:
        with zipfile.ZipFile(arquivo) as z:
            return z.testzip() is None
    except (zipfile.BadZipFile, OSError):
        return False


def baixar(mes: str, nome: str, destino: Path, tentativas: int = 30, dormir=time.sleep) -> Path:
    """Baixa `mes/nome` para `destino/nome`, retomando onde a conexao caiu."""
    final = destino / nome
    if final.exists() and zip_integro(final):
        return final
    destino.mkdir(parents=True, exist_ok=True)
    parcial = destino / f"{nome}.part"
    alvo = listar(mes).get(nome)
    for i in range(1, tentativas + 1):
        feito = parcial.stat().st_size if parcial.exists() else 0
        if alvo is not None and feito >= alvo:
            break
        try:
            pedido = _pedido(f"{mes}/{nome}", cabecalhos={"Range": f"bytes={feito}-"})
            with urllib.request.urlopen(pedido, timeout=3600) as r, open(parcial, "ab") as f:  # noqa: S310
                if feito and r.status != 206:
                    f.truncate(0)  # servidor ignorou o Range: recomeca do zero
                while bloco := r.read(1 << 20):
                    f.write(bloco)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as erro:
            log.warning("%s: tentativa %d caiu (%s), retomando", nome, i, erro)
            dormir(20)
        log.info("%s: %s de %s bytes", nome, parcial.stat().st_size, alvo)
    if not zip_integro(parcial):
        raise OSError(f"{nome}: download incompleto ou corrompido em {parcial}")
    parcial.rename(final)
    return final


def _ler_zip(arquivo: Path, colunas: dict[int, str], blocos: int = 500_000):
    with zipfile.ZipFile(arquivo) as z, z.open(z.namelist()[0]) as bruto:
        texto = io.TextIOWrapper(bruto, encoding="latin-1", newline="")
        yield from pd.read_csv(
            texto,
            sep=";",
            header=None,
            dtype=str,
            usecols=list(colunas),
            keep_default_na=False,
            chunksize=blocos,
        )


def filtrar_estabelecimentos(arquivo: Path, cnae: str) -> pd.DataFrame:
    """Estabelecimentos com `cnae` como atividade principal ou secundaria."""
    partes = []
    for bloco in _ler_zip(arquivo, COLUNAS_ESTABELECIMENTO):
        bloco = bloco.rename(columns=COLUNAS_ESTABELECIMENTO)
        secundaria = bloco["cnae_secundaria"].str.contains(cnae, regex=False)
        partes.append(bloco[(bloco["cnae_principal"] == cnae) | secundaria])
    saida = pd.concat(partes, ignore_index=True)
    saida["cnae_secundaria_tem"] = saida.pop("cnae_secundaria").str.contains(cnae, regex=False)
    return saida


def filtrar_simples(arquivo: Path, cnpjs: set[str]) -> pd.DataFrame:
    """Opcao pelo MEI dos `cnpjs` (basicos, 8 digitos)."""
    partes = []
    for bloco in _ler_zip(arquivo, COLUNAS_SIMPLES):
        bloco = bloco.rename(columns=COLUNAS_SIMPLES)
        partes.append(bloco[bloco["cnpj_basico"].isin(cnpjs)])
    return pd.concat(partes, ignore_index=True)


def ler_municipios(arquivo: Path) -> dict[str, str]:
    """Codigo de municipio da Receita -> nome. A tabela nao traz UF."""
    (bloco,) = list(_ler_zip(arquivo, {0: "codigo", 1: "nome"}, blocos=100_000))
    return dict(zip(bloco[0], bloco[1], strict=True))
