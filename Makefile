.PHONY: help setup painel diagnostico denominadores custo lacuna pnad lucro contraste cronologia wayback mei lint test limpar

PYTHON ?= python

UFS   ?= PR SP BA
INI   ?= 2015-01
# frota municipal so existe a partir de 2016-07 (D-015)
DEN_INI ?= 2016-07
# serie mensal de beneficios concedidos do INSS comeca em 2018-12 (D-030)
INSS_INI ?= 2018-12
FIM   ?= 2025-12

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "};{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

setup: ## instala o pacote em modo editavel com deps de dev
	$(PYTHON) -m pip install -e ".[dev]" && pre-commit install

painel: ## baixa SIH e monta o painel municipio x mes
	$(PYTHON) scripts/sih_pipeline.py --ufs $(UFS) --inicio $(INI) --fim $(FIM)

diagnostico: ## preenchimento do CAR_INT por ano (roda so com o painel ja pronto)
	$(PYTHON) scripts/diagnostico_car_int.py

denominadores: ## frota de moto (Senatran) e populacao (IBGE) -- so precisa de HTTPS
	$(PYTHON) scripts/denominadores.py --inicio $(DEN_INI) --fim $(FIM)

custo: ## val_tot deflacionado (IPCA) e custo social (Ipea) por ano e UF -- so baixa o IPCA
	$(PYTHON) scripts/custo.py

lacuna: ## beneficios do INSS com CID V20-V29 contra internacoes do SIH, por UF e ano -- so HTTPS
	$(PYTHON) scripts/lacuna_inss.py --inicio $(INSS_INI) --fim $(FIM)

pnad: ## modulo de plataformas da PNAD Continua: informalidade, previdencia, jornada e renda-hora -- so HTTPS
	$(PYTHON) scripts/pnad_plataformas.py

lucro: ## receita e resultado do iFood (Prosus) em reais constantes, ano fiscal e civil -- so baixa cambio e IPCA
	$(PYTHON) scripts/lucro.py

contraste: ## figura iFood x SUS no mesmo eixo, R$ constantes (roda so com custo e lucro prontos) -- sem rede
	$(PYTHON) scripts/contraste.py

cronologia: ## F3: concordancia e consolidacao das planilhas dos dois codificadores -- sem rede
	$(PYTHON) scripts/cronologia.py consolidar

wayback: ## F3: listas de cidades atendidas no Wayback -> intervalo de entrada (tipo 3) -- rodar fora da nuvem
	$(PYTHON) scripts/cronologia.py wayback

mei: ## F3: mes de chegada do entregador pela quebra nas aberturas de MEI de entrega (D-040) -- ~6 GB de HTTPS
	$(PYTHON) scripts/mei.py $(ARGS)

lint:
	ruff check . && ruff format --check .

test:
	$(PYTHON) -m pytest -q

limpar: ## remove intermediarios, preserva data/raw
	rm -rf data/interim/* data/painel/* output/tabelas/* output/figuras/*
