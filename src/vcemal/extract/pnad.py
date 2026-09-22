"""PNAD Continua: microdado trimestral com o modulo de plataformas, pelo FTP do IBGE.

Os arquivos vivem em `Anual/Microdados/Trimestre/Trimestre_<t>/` -- e nao em
`Trimestral/Microdados/`, que traz o questionario basico sem o suplemento.
O nome do ZIP carrega a data de divulgacao (`PNADC_2024_trimestre3_20260904.zip`),
entao a pasta e listada e o arquivo e escolhido por ano. O dicionario e um por
trimestre, cobrindo todos os anos; o deflator e um por ano-trimestre.

Tudo HTTPS. O ZIP tem ~230 MB e o `.txt` de largura fixa dentro dele, de 1,9 a
3,5 GB: o cache guarda so o `.txt`.
"""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path

import pandas as pd

from vcemal.extract._http import baixar as _baixar
from vcemal.extract._http import baixar_para as _baixar_para

log = logging.getLogger("vcemal.extract.pnad")

BASE = (
    "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
    "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Trimestre"
)

_ZIP = re.compile(r'href="(PNADC_(\d{4})_trimestre(\d)_\d{8}\.zip)"')
_DIC = re.compile(r'href="(dicionario_PNADC_microdados_trimestre\d_\d{8}\.xls)"')


def _pasta(trimestre: int, sub: str) -> str:
    return f"{BASE}/Trimestre_{trimestre}/{sub}/"


def listar_dados(trimestre: int) -> dict[int, str]:
    """Ano -> URL do ZIP do microdado daquele trimestre."""
    html = _baixar(_pasta(trimestre, "Dados")).decode("utf-8", "replace")
    saida = {}
    for nome, ano, t in _ZIP.findall(html):
        if int(t) == trimestre:
            saida[int(ano)] = _pasta(trimestre, "Dados") + nome
    log.info("trimestre %d: %d anos com microdado", trimestre, len(saida))
    return saida


def url_dicionario(trimestre: int) -> str:
    html = _baixar(_pasta(trimestre, "Documentacao")).decode("utf-8", "replace")
    nomes = sorted(set(_DIC.findall(html)))
    if not nomes:
        raise ValueError(f"trimestre {trimestre}: sem dicionario na pasta de documentacao")
    return _pasta(trimestre, "Documentacao") + nomes[-1]


def url_deflator(ano: int, trimestre: int) -> str:
    return _pasta(trimestre, "Documentacao") + f"deflator_PNADC_{ano}_trimestre{trimestre}.xls"


def baixar_rodada(ano: int, trimestre: int, cache: Path) -> tuple[Path, Path, Path]:
    """Devolve `(txt, dicionario, deflator)` no cache, baixando o que faltar."""
    cache.mkdir(parents=True, exist_ok=True)
    txt = cache / f"PNADC_{ano}_trimestre{trimestre}.txt"
    dicionario = cache / f"dicionario_trimestre{trimestre}.xls"
    deflator = cache / f"deflator_{ano}_trimestre{trimestre}.xls"

    if not dicionario.exists():
        _baixar_para(url_dicionario(trimestre), dicionario)
    if not deflator.exists():
        _baixar_para(url_deflator(ano, trimestre), deflator)
    if not txt.exists():
        urls = listar_dados(trimestre)
        if ano not in urls:
            raise FileNotFoundError(f"{ano} T{trimestre}: sem microdado no FTP ({sorted(urls)})")
        zipado = cache / f"PNADC_{ano}_trimestre{trimestre}.zip"
        log.info("%d T%d: baixando %s", ano, trimestre, urls[ano])
        _baixar_para(urls[ano], zipado)
        with zipfile.ZipFile(zipado) as z:
            membros = [m for m in z.namelist() if m.lower().endswith(".txt")]
            if len(membros) != 1:
                raise ValueError(f"{zipado.name}: esperava um .txt, achei {membros}")
            with z.open(membros[0]) as origem, txt.open("wb") as saida:
                import shutil

                shutil.copyfileobj(origem, saida, length=1 << 20)
        zipado.unlink()
    return txt, dicionario, deflator


def layout(dicionario: Path) -> dict[str, tuple[int, int]]:
    """Variavel -> (posicao inicial 1-based, largura), lido do dicionario `.xls`.

    O dicionario tem uma linha por variavel com a posicao na coluna A, a
    largura na B e o codigo na C; as linhas de categoria repetem a variavel com
    A e B vazias. So as linhas com posicao numerica entram.
    """
    bruto = pd.read_excel(dicionario, header=None, dtype=str)
    saida: dict[str, tuple[int, int]] = {}
    for inicio, largura, nome in bruto.iloc[:, :3].itertuples(index=False):
        if isinstance(inicio, str) and inicio.strip().isdigit() and isinstance(nome, str):
            saida[nome.strip()] = (int(inicio), int(str(largura).strip()))
    if "V1028" not in saida:
        raise ValueError(f"{dicionario.name}: nao parece um dicionario da PNADC (sem V1028)")
    return saida


def deflator(caminho: Path) -> pd.DataFrame:
    """`Ano, trim, UF, Habitual, Efetivo` -- fator que leva a reais do trimestre de referencia."""
    df = pd.read_excel(caminho, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df["Ano"] = df["Ano"].astype(int)
    df["UF"] = df["UF"].astype(str).str.strip()
    df["Habitual"] = pd.to_numeric(df["Habitual"])
    return df[["Ano", "trim", "UF", "Habitual"]]
