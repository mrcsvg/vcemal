"""
Senatran: frota de veiculos por municipio e tipo.

**Por que nao o RENAVAM do portal de dados abertos.** O dataset
`registro-nacional-de-veiculos-automotores-renavam` traz
`UF; Municipio; Marca Modelo; Ano Fabricacao; Qtd. Veiculos` -- **sem coluna de
tipo de veiculo** -- em ~136 MB por mes. Derivar "motocicleta" dali exigiria
classificar dezenas de milhares de strings de marca/modelo, e o erro dessa
classificacao entraria direto no denominador. A pagina de estatisticas do
Senatran publica "Frota por Municipio e Tipo", ~1,2 MB por mes, ja com uma
coluna por tipo. E essa que serve. Ver D-013.

**O nome do arquivo nao e chave.** Ao longo da serie o mesmo relatorio aparece
como `frota_por_municipio_e_tipo-dez_16.xlsx`,
`frota_munic_modelo_dezembro_2019.xls`, `FrotaporMunicipioetipoDEZEMBRO2025.xlsx`
e `copy2_of_Frota_por_municipio_tipo_Maro_2025.xlsx` -- sem separador, em caixa
alta, com prefixo de copia do gerenciador de conteudo, com `Municpio` escrito
errado e com `Marco` sem o cedilha. Ha ate arquivo de outro ano solto na pagina.
O **rotulo do link** e a unica coisa estavel, e e por ele que localizamos o mes.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from html import unescape
from pathlib import Path

from vcemal.extract._http import baixar as _baixar

log = logging.getLogger("vcemal.extract.senatran")

BASE = "https://www.gov.br/transportes"
INDICE_ANO = f"{BASE}/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-{{ano}}"

#: Grafias do mes vistas no nome do arquivo. `maro` e `marco` com o cedilha
#: comido pelo encoding do portal.
GRAFIAS_MES: dict[str, int] = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "maro": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

#: Abreviacoes de tres letras, usadas ate 2016. So casam como token inteiro.
ABREVIACOES_MES: dict[str, int] = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}

#: Trechos que o rotulo do link precisa conter, ja normalizado.
ROTULO_ALVO = ("frota por municipio", "tipo")
EXTENSOES = (".xls", ".xlsx")

_ANO_NO_NOME = re.compile(r"20\d{2}")


def _texto_simples(valor: str) -> str:
    """Minusculas, sem acento, sem pontuacao, espaco simples."""
    sem_acento = unicodedata.normalize("NFKD", unescape(str(valor)))
    sem_acento = sem_acento.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).strip()


def mes_do_arquivo(arquivo: str) -> int | None:
    """Mes a partir do nome do arquivo, tolerando grafia, caixa e abreviacao."""
    simples = _texto_simples(arquivo)
    colado = simples.replace(" ", "")
    for grafia, mes in GRAFIAS_MES.items():
        if grafia in colado:
            return mes
    for token in simples.split():
        if token in ABREVIACOES_MES:
            return ABREVIACOES_MES[token]
    return None


def ano_confere(arquivo: str, ano: int) -> bool:
    """Descarta arquivo de outro ano solto na pagina do ano.

    Quando o nome nao traz ano de 4 digitos -- 2016 usa `-dez_16` -- aceita,
    porque a pagina ja e a do ano pedido.
    """
    anos = _ANO_NO_NOME.findall(arquivo)
    return str(ano) in anos if anos else True


def indice_do_ano(ano: int) -> dict[int, str]:
    """Mes (1-12) -> URL do arquivo "Frota por Municipio e Tipo" daquele ano."""
    html = _baixar(INDICE_ANO.format(ano=ano)).decode("utf-8", "replace")
    achados: dict[int, str] = {}
    for href, bruto in re.findall(r'href="([^"]+)"[^>]*>(.*?)</a>', html, re.S | re.I):
        rotulo = _texto_simples(re.sub(r"<[^>]+>", " ", bruto))
        if not all(parte in rotulo for parte in ROTULO_ALVO):
            continue
        url = unescape(href)
        arquivo = url.rsplit("/", 1)[-1]
        if not arquivo.lower().endswith(EXTENSOES) or not ano_confere(arquivo, ano):
            continue
        mes = mes_do_arquivo(arquivo)
        if mes is not None and mes not in achados:
            achados[mes] = url if url.startswith("http") else f"https://www.gov.br{url}"
    log.info("%d: %d meses de frota por municipio e tipo", ano, len(achados))
    return achados


def baixar_mes(
    ano: int, mes: int, destino: Path, indice: dict[int, str] | None = None
) -> Path | None:
    """Baixa um mes de frota por municipio e tipo. None se o mes nao existir.

    `indice` evita rebaixar a pagina do ano a cada mes.
    """
    urls = indice if indice is not None else indice_do_ano(ano)
    url = urls.get(mes)
    if url is None:
        log.warning("sem arquivo de frota por municipio para %04d-%02d", ano, mes)
        return None

    destino.mkdir(parents=True, exist_ok=True)
    sufixo = Path(url.split("?")[0]).suffix or ".xls"
    caminho = destino / f"frota_munic_{ano}_{mes:02d}{sufixo}"
    caminho.write_bytes(_baixar(url))
    log.info("%04d-%02d: %.1f MB -> %s", ano, mes, caminho.stat().st_size / 1e6, caminho)
    return caminho
