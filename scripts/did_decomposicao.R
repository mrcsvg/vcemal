#!/usr/bin/env Rscript
# Decomposicao taxa x contagem na mesma amostra, declarada no D-050.
#
#     make did-decomposicao     # depois de make did
#
# Exploratoria: o resultado principal e o do D-049. Escreve
# `output/tabelas/did/decomposicao.csv` (A-D) e `decomposicao_contrastes.csv`.

suppressPackageStartupMessages({
  library(data.table)
  library(did)
  library(parallel)
})
args <- commandArgs(trailingOnly = FALSE)
raiz <- normalizePath(file.path(dirname(sub("^--file=", "", args[grep("^--file=", args)])), ".."))
source(file.path(raiz, "src", "vcemal", "analyze", "did.R"))

saida <- file.path(raiz, "output", "tabelas", "did")
dir.create(saida, recursive = TRUE, showWarnings = FALSE)

d <- fread(file.path(raiz, "data", "painel", "estimacao_municipio_mes.csv"))
# C: frota de 2016-07 (periodo 19), anterior a toda coorte da amostra da taxa.
frota_fixa <- d[periodo == 19L, .(municipio_ibge, frota_fixa = frota_moto)]
d <- frota_fixa[d, on = "municipio_ibge"]
d[, taxa_moto_frota_fixa := fifelse(frota_fixa > 0, 1e5 * moto_internacoes_transito / frota_fixa, NA_real_)]

TAXA <- list(t_ini = 19L, g_min = 31L)
specs <- list(
  modifyList(TAXA, list(id = "A_taxa_frota_corrente", y = "taxa_moto_transito")),
  modifyList(TAXA, list(id = "B_contagem_amostra_taxa", y = "moto_internacoes_transito")),
  modifyList(TAXA, list(id = "C_taxa_frota_fixa", y = "taxa_moto_frota_fixa")),
  list(id = "D_contagem", y = "moto_internacoes_transito", t_ini = 1L, g_min = 13L)
)
r <- mclapply(specs, function(sp) suppressWarnings(estimar_cs(d, sp))$resumo,
              mc.cores = as.integer(Sys.getenv("NUCLEOS", "4")))
est <- rbindlist(r, fill = TRUE)
fwrite(est, file.path(saida, "decomposicao.csv"))

p <- setNames(est$pct, substr(est$id, 1, 1))
contr <- data.table(
  contraste = c("B - D: amostra", "C - B: escala e ponderacao", "A - C: denominador no tempo",
                "A - D: total"),
  pp = c(p[["B"]] - p[["D"]], p[["C"]] - p[["B"]], p[["A"]] - p[["C"]], p[["A"]] - p[["D"]])
)
fwrite(contr, file.path(saida, "decomposicao_contrastes.csv"))

print(est[, .(id, pct = round(pct, 1), ic = sprintf("[%.1f, %.1f]", pct_ic_inf, pct_ic_sup),
              p = signif(p_regiao, 2), pre_p = signif(pre_wald_p, 2), mde = round(mde80_pct, 1),
              trat = tratados_agregados, mun = municipios)])
print(contr[, .(contraste, pp = round(pp, 1))])
