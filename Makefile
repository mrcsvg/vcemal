.PHONY: help setup painel diagnostico denominadores custo lacuna pnad lucro contraste cronologia wayback mei auditoria did did-exploratorio did-decomposicao did-h5 sim h4 lint test limpar

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

AUD = docs/fontes/cronologia
auditoria: ## F3: consolida as planilhas da auditoria do MEI e da o veredito por estrato (D-041) -- sem rede
	$(PYTHON) scripts/cronologia.py consolidar $(AUD)/auditoria_a.csv $(AUD)/auditoria_b.csv \
		--desempates $(AUD)/auditoria_desempates.csv --saida output/auditoria
	$(PYTHON) scripts/cronologia.py auditoria-avaliar output/auditoria/tratamento_municipio.csv

did: ## V2: painel de estimacao e Callaway & Sant'Anna das especificacoes do plano (R: did, fixest) -- sem rede
	$(PYTHON) scripts/did_painel.py
	Rscript scripts/did_estimar.R

did-exploratorio: ## V2: curva de especificacao e exploratorias E1-E4, declaradas no D-048 (roda depois de make did) -- sem rede
	Rscript scripts/did_exploratorio.R

did-decomposicao: ## V2: decomposicao taxa x contagem na mesma amostra, declarada no D-050 (roda depois de make did) -- sem rede
	Rscript scripts/did_decomposicao.R

did-h5: ## H5: obitos do SIM pelo estimando principal, contagem e taxa, com e sem 2025 (D-055; depois de make sim e make did) -- sem rede
	Rscript scripts/did_h5.R

sim: ## H5 e H4: obitos do SIM por municipio x mes, direto do FTP do DATASUS (D-053) -- ~1,5 GB de FTP
	$(PYTHON) scripts/sim_pipeline.py

h4: ## H4: nexo de trabalho registrado no SIH e no SIM por UF e ano, com a PNAD ao lado (D-057; depois de painel, sim e pnad) -- sem rede
	$(PYTHON) scripts/h4.py

lint:
	ruff check . && ruff format --check .

test:
	$(PYTHON) -m pytest -q

limpar: ## remove intermediarios, preserva data/raw
	rm -rf data/interim/* data/painel/* output/tabelas/* output/figuras/*
