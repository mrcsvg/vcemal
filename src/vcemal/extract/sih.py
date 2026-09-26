"""Download dos arquivos RD do SIH/SUS via PySUS.

Unico modulo do pacote que toca a rede, junto com os demais `extract/`.

**API do PySUS 2.x.** A versao 0.x expunha `pysus.ftp.databases.sih.SIH().load()`
com `get_files` e `download`; a 2.x substituiu isso por uma funcao por base,
`pysus.ftp.sih(uf, ano, mes, group=...)`, e `pysus.ftp` deixou de ser pacote.
O codigo anterior foi escrito contra a 0.x e nunca rodou contra a base real --
quebrava com `No module named 'pysus.ftp.databases'`. Ver D-034.

**Cache.** A 2.x guarda o parquet baixado em `~/pysus/downloads/` e serve dali
nas chamadas seguintes. Isso e o que torna a serie nacional viavel: um download
interrompido retoma de onde parou, e reprocessar nao volta a rede. O caminho sai
de `pysus.CACHEPATH` e pode ser trocado com `pysus.set_cache`.

**Origem.** Por padrao a 2.x le o espelho do catalogo (S3), nao o FTP do DATASUS
diretamente. E mais rapido e menos sujeito a queda; `source="origin"` forca o
servidor de origem, quando se quiser conferir contra a fonte primaria.

**O filtro `group="RD"` do PySUS nao pode ser usado.** No catalogo, o campo
`group` do arquivo vem **nulo** -- assim como `year`, `month` e `state` --, ainda
que o caminho os codifique (`.../sih/RD/2015/08/AC/RDAC1508.parquet`). Pedir
`group="RD"` compara contra campo nulo e devolve colecao vazia para parte das
competencias, de forma inconsistente: 73 das 216 primeiras competencias da serie
nacional voltaram "sem arquivo RD" quando o arquivo existia. Isso nao levanta
erro -- produziria um painel silenciosamente incompleto. Aqui o RD e escolhido
pelo **nome do arquivo**, unico sinal confiavel, e so ele e baixado. Ver D-034.

**O espelho nao tem tudo.** Na serie nacional 2015-2025, 103 competencias
voltaram sem RD no catalogo e existiam no FTP do DATASUS (PI 22, TO 19, MT 16,
...). `source="origin"` nao resolve: consulta o mesmo indice, que lista ER, RJ e
SP da competencia e nao o RD. Por isso `baixar_ano` busca o `.dbc` que faltar
direto no FTP e o converte pelo proprio PySUS, o mesmo caminho que gerou o
espelho -- mesmas colunas, mesmos tipos. Ver D-036.
"""

from __future__ import annotations

import ftplib
import logging
import re
from pathlib import Path

import pandas as pd

from vcemal.paths import RAW_SIH, RAW_SIH_ORIGEM

log = logging.getLogger("vcemal.extract.sih")

#: Grupo do SIH que carrega a AIH reduzida -- e o arquivo do projeto.
GRUPO_RD = "RD"


def _sih():
    """Funcao de busca do SIH no PySUS 2.x. Import adiado: o pacote roda sem PySUS."""
    from pysus import ftp

    return ftp.sih


def caminho_do_cache() -> Path:
    """Onde o PySUS guarda os arquivos baixados. So para log e diagnostico."""
    import pysus

    return Path(pysus.CACHEPATH)


def e_arquivo_rd(arquivo) -> bool:
    """O arquivo e da AIH reduzida? Decidido pelo nome; `group` vem nulo (D-034)."""
    nome = getattr(arquivo, "basename", None) or getattr(arquivo, "name", None) or ""
    return str(nome).upper().startswith(GRUPO_RD)


def baixar_mes(uf: str, ano: int, mes: int) -> pd.DataFrame | None:
    """Baixa `RD<UF><AAMM>` e devolve o DataFrame bruto, ou None se nao houver.

    Consulta o catalogo sem baixar (`download=False`), escolhe o RD pelo nome e
    so entao baixa esse arquivo -- os outros tres grupos da competencia (ER, RJ,
    SP) nao interessam ao projeto e baixa-los quadruplicaria a serie nacional.

    Competencia ainda nao publicada devolve colecao vazia, sem excecao -- por
    isso o None aqui e explicito, e nao um try/except largo que engoliria erro
    de rede e viraria buraco silencioso no painel.
    """
    catalogo = _sih()(uf, ano, mes, download=False)
    indices = [i for i, arq in enumerate(catalogo) if e_arquivo_rd(arq)]
    if not indices:
        log.warning("sem arquivo RD para %s %04d-%02d", uf, ano, mes)
        return None
    if len(indices) > 1:
        log.warning(
            "%s %04d-%02d: %d arquivos RD no catalogo, usando todos", uf, ano, mes, len(indices)
        )

    df = catalogo.download(indexes=indices).to_dataframe()
    if df is None or df.empty:
        log.warning("RD de %s %04d-%02d veio vazio", uf, ano, mes)
        return None
    return df


#: `RDDF1509.parquet` -> grupo RD, UF DF, ano 15, mes 09.
_NOME_RD = re.compile(r"^RD(?P<uf>[A-Z]{2})(?P<ano>\d{2})(?P<mes>\d{2})\.", re.IGNORECASE)


def mes_do_arquivo(nome: str) -> int | None:
    """Mes codificado no nome do arquivo RD, ou None se o nome nao casar."""
    achou = _NOME_RD.match(str(nome))
    if not achou:
        return None
    mes = int(achou.group("mes"))
    return mes if 1 <= mes <= 12 else None


def baixar_ano(uf: str, ano: int, meses: list[int] | None = None) -> dict[int, Path]:
    """Caminhos locais dos 12 RD do ano, baixados **em paralelo**. Chave = mes.

    E por aqui que a serie nacional roda. Pedir mes a mes custa uma consulta ao
    catalogo por competencia (~5s x 3.564) e deixa o download sequencial, entao
    uma travada do servidor -- medimos ate 19 minutos num arquivo so -- para a
    fila inteira. Pedindo o ano de uma vez, e uma consulta e o PySUS baixa os
    doze concorrentemente, o que absorve as travadas. Ver D-035.

    Mes de `meses` (padrao: os doze) ausente do catalogo e buscado no FTP do
    DATASUS (D-036). So some do dicionario o que tambem nao existe la -- mes
    ainda nao publicado.
    """
    catalogo = _sih()(uf, [ano], list(range(1, 13)), download=False)
    indices = [i for i, arq in enumerate(catalogo) if e_arquivo_rd(arq)]

    caminhos: dict[int, Path] = {}
    if indices:
        for arquivo in catalogo.download(indexes=indices):
            nome = getattr(arquivo, "basename", None) or getattr(arquivo, "name", "")
            mes = mes_do_arquivo(nome)
            if mes is None:
                log.warning("nome de arquivo RD fora do padrao, ignorado: %s", nome)
                continue
            caminhos[mes] = Path(arquivo.path)

    for mes in meses if meses is not None else range(1, 13):
        if mes in caminhos:
            continue
        local = baixar_da_origem(uf, ano, mes)
        if local is None:
            log.warning("sem arquivo RD para %s %04d-%02d, nem no FTP", uf, ano, mes)
            continue
        log.warning("%s %04d-%02d: RD ausente do espelho, recuperado do FTP", uf, ano, mes)
        caminhos[mes] = local
    return caminhos


# --- FTP do DATASUS, para o que falta no espelho (D-036) -------------------

FTP_DATASUS = "ftp.datasus.gov.br"
#: Diretorio dos RD desde 2008. A serie do projeto comeca em 2015.
FTP_DIR_SIH = "/dissemin/publicos/SIHSUS/200801_/Dados"


def nome_rd(uf: str, ano: int, mes: int, extensao: str = "dbc") -> str:
    """`RDDF1604.dbc` -- como o DATASUS nomeia o RD da competencia."""
    return f"RD{uf.upper()}{ano % 100:02d}{mes:02d}.{extensao}"


def _baixar_ftp(nome: str, destino: Path) -> bool:
    """Baixa `nome` do diretorio do SIH. False se o arquivo nao existe (550).

    Qualquer outro erro sobe: falha de rede nao pode virar "mes sem dado".
    """
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    try:
        with ftplib.FTP(FTP_DATASUS, timeout=300) as ftp:
            ftp.login()
            ftp.cwd(FTP_DIR_SIH)
            with parcial.open("wb") as saida:
                ftp.retrbinary(f"RETR {nome}", saida.write)
    except ftplib.error_perm as e:
        parcial.unlink(missing_ok=True)
        if str(e).startswith("550"):
            return False
        raise
    except BaseException:
        parcial.unlink(missing_ok=True)
        raise
    parcial.rename(destino)
    return True


def _dbc_para_parquet(dbc: Path) -> Path:
    """Converte pelo PySUS -- o mesmo caminho que produziu o espelho."""
    import anyio
    from pysus.api.extensions import ExtensionFactory

    async def converter() -> Path:
        arquivo = await ExtensionFactory.instantiate(dbc)
        return Path((await arquivo.to_parquet()).path)

    return anyio.run(converter)


def baixar_da_origem(uf: str, ano: int, mes: int) -> Path | None:
    """Parquet do RD baixado do FTP do DATASUS, ou None se ainda nao publicado.

    Fica em `data/raw/sih_origem/`, separado do cache do PySUS: a procedencia
    diferente tem que continuar visivel. Arquivo ja convertido nao volta a rede.
    """
    parquet = RAW_SIH_ORIGEM / nome_rd(uf, ano, mes, "parquet")
    if parquet.exists():
        return parquet
    RAW_SIH_ORIGEM.mkdir(parents=True, exist_ok=True)
    dbc = parquet.with_suffix(".dbc")
    if not _baixar_ftp(dbc.name, dbc):
        return None
    convertido = _dbc_para_parquet(dbc)
    dbc.unlink(missing_ok=True)
    return convertido


def salvar_bruto(df: pd.DataFrame, uf: str, ano: int, mes: int) -> Path:
    """Grava as AIH ja filtradas, particionadas por UF/ano/mes."""
    pasta = caminho_do_bruto(uf, ano, mes).parent
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / "parte.parquet"
    df.to_parquet(caminho, index=False)
    return caminho


def caminho_do_bruto(uf: str, ano: int, mes: int) -> Path:
    """Onde `salvar_bruto` grava a competencia. Existir e o sinal de ja processada."""
    return RAW_SIH / f"uf={uf}" / f"ano={ano}" / f"mes={mes:02d}" / "parte.parquet"


def meses(inicio: str, fim: str) -> list[tuple[int, int]]:
    """Competencias de `AAAA-MM` a `AAAA-MM`, inclusive nas duas pontas."""
    return [(p.year, p.month) for p in pd.period_range(inicio, fim, freq="M")]
