"""Caminhos do projeto. Nenhum deles e versionado -- ver D-009 em docs/decisoes.md."""

from __future__ import annotations

from pathlib import Path

#: Raiz do repositorio (src/vcemal/paths.py -> src/vcemal -> src -> raiz).
RAIZ = Path(__file__).resolve().parents[2]

DATA = RAIZ / "data"
RAW_SIH = DATA / "raw" / "sih"
#: RD que faltam no espelho do PySUS, baixados do FTP do DATASUS (D-036).
RAW_SIH_ORIGEM = DATA / "raw" / "sih_origem"
#: Dados abertos do CNPJ da Receita, uma pasta por publicacao mensal (D-040).
RAW_CNPJ = DATA / "raw" / "cnpj"
INTERIM = DATA / "interim"
PAINEL = DATA / "painel"

OUTPUT = RAIZ / "output"
TABELAS = OUTPUT / "tabelas"
FIGURAS = OUTPUT / "figuras"

#: Transcricoes curadas de fontes publicadas, versionadas de proposito: cada
#: celula carrega documento, URL e data de acesso.
FONTES = RAIZ / "docs" / "fontes"
FONTE_IFOOD_PROSUS = FONTES / "ifood_prosus.csv"

#: Painel municipio x mes produzido por `scripts/sih_pipeline.py`.
PAINEL_MUNICIPIO_MES = PAINEL / "painel_municipio_mes.parquet"


def garantir(*caminhos: Path) -> None:
    """Cria os diretorios passados, se ainda nao existirem."""
    for caminho in caminhos:
        caminho.mkdir(parents=True, exist_ok=True)
