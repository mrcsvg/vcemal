"""Download das declaracoes de obito do SIM direto do FTP do DATASUS.

Um arquivo por UF de residencia e ano, `DO<UF><AAAA>.dbc`. O ano definitivo
mora em `SIM/CID10/DORES/`; o preliminar, em `SIM/PRELIM/DORES/`. Procura-se
primeiro no definitivo, e so o 550 (arquivo inexistente) manda ao preliminar --
qualquer outro erro do servidor sobe, como no SIH (D-036).

**Por que nao o espelho do PySUS.** Ele nao tem 2025 e nao diz de que versao do
arquivo veio, e o plano pede a versao do SIM registrada com data: ano definitivo
e republicado no FTP (D-053). Por isso cada download devolve o tamanho e a data
de modificacao do arquivo no servidor, que vao ao manifesto.

A conversao do `.dbc` e a do proprio PySUS, a mesma do D-036.
"""

from __future__ import annotations

import ftplib
import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

log = logging.getLogger("vcemal.extract.sim")

FTP_DATASUS = "ftp.datasus.gov.br"
FTP_DIR_DEFINITIVO = "/dissemin/publicos/SIM/CID10/DORES"
FTP_DIR_PRELIMINAR = "/dissemin/publicos/SIM/PRELIM/DORES"

#: Os downloads podem correr em paralelo; a conversao do PySUS, por cautela, nao.
_CONVERSAO = threading.Lock()


@dataclass(frozen=True)
class Baixado:
    """Um `DO<UF><AAAA>` ja convertido, com a procedencia que vai ao manifesto."""

    caminho: Path
    diretorio: str
    arquivo: str
    tamanho: int
    modificado_ftp: str
    preliminar: bool


def nome_do(uf: str, ano: int, extensao: str = "dbc") -> str:
    """`DOSP2024.dbc` -- como o DATASUS nomeia a DO por UF de residencia e ano."""
    return f"DO{uf.upper()}{ano:04d}.{extensao}"


def _modificado(ftp: ftplib.FTP, nome: str) -> str:
    """Data de modificacao no servidor (`MDTM`), ISO. Vazio se o servidor recusar."""
    try:
        resposta = ftp.sendcmd(f"MDTM {nome}")
    except ftplib.error_perm:
        return ""
    return datetime.strptime(resposta.split()[-1][:14], "%Y%m%d%H%M%S").isoformat()


def _baixar_ftp(nome: str, destino: Path) -> tuple[str, int, str] | None:
    """Baixa `nome` do definitivo ou, se nao houver, do preliminar.

    Devolve (diretorio, tamanho, modificado) ou None se nao existe em nenhum dos
    dois. So o 550 e "nao existe"; o resto sobe.
    """
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    try:
        with ftplib.FTP(FTP_DATASUS, timeout=300) as ftp:
            ftp.login()
            ftp.voidcmd("TYPE I")
            for diretorio in (FTP_DIR_DEFINITIVO, FTP_DIR_PRELIMINAR):
                ftp.cwd(diretorio)
                try:
                    tamanho = ftp.size(nome) or 0
                except ftplib.error_perm as e:
                    if str(e).startswith("550"):
                        continue
                    raise
                modificado = _modificado(ftp, nome)
                with parcial.open("wb") as saida:
                    ftp.retrbinary(f"RETR {nome}", saida.write)
                parcial.rename(destino)
                return diretorio, tamanho, modificado
    except BaseException:
        parcial.unlink(missing_ok=True)
        raise
    return None


def _dbc_para_parquet(dbc: Path) -> Path:
    """Converte pelo PySUS -- o mesmo caminho do SIH (D-036)."""
    import anyio
    from pysus.api.extensions import ExtensionFactory

    async def converter() -> Path:
        arquivo = await ExtensionFactory.instantiate(dbc)
        return Path((await arquivo.to_parquet()).path)

    return anyio.run(converter)


def baixar(uf: str, ano: int, pasta: Path) -> Baixado | None:
    """Baixa e converte a DO de `uf` e `ano` em `pasta`. None se nao publicada.

    O parquet convertido fica em `pasta` e e responsabilidade de quem chama
    apaga-lo: o pipeline guarda so o filtrado.
    """
    pasta.mkdir(parents=True, exist_ok=True)
    dbc = pasta / nome_do(uf, ano)
    achou = _baixar_ftp(dbc.name, dbc)
    if achou is None:
        return None
    diretorio, tamanho, modificado = achou
    with _CONVERSAO:
        convertido = _dbc_para_parquet(dbc)
    dbc.unlink(missing_ok=True)
    return Baixado(
        caminho=convertido,
        diretorio=diretorio,
        arquivo=dbc.name,
        tamanho=tamanho,
        modificado_ftp=modificado,
        preliminar=diretorio == FTP_DIR_PRELIMINAR,
    )
