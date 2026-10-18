#!/usr/bin/env Rscript
# H5 (secundaria): obitos de motociclista no SIM, pelo estimando principal (D-055).
#
#     make did-h5     # depois de make sim e make did (o painel precisa ter o SIM)
#
# Leitura principal na contagem, pelo T3 que disparou sobre a mesma frota (D-049);
# a taxa sai ao lado. Robustez sem o ano preliminar: painel cortado em 2024-12.
# Escreve em `output/tabelas/did/`:
#   h5_estimativas.csv   uma linha por especificacao
#   h5_estudo_evento.csv ATT(e), e em [-12, +24]
#   h5_testes.csv        criterio do plano, aplicado mecanicamente

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
nucleos <- as.integer(Sys.getenv("NUCLEOS", "4"))

d <- fread(file.path(raiz, "data", "painel", "estimacao_municipio_mes.csv"))
if (!"obitos_moto_transito" %in% names(d)) stop("painel sem o SIM: rode make sim e make did")

TAXA <- list(t_ini = 19L, g_min = 31L)
CONTAGEM <- list(t_ini = 1L, g_min = 13L)
ULTIMO_DEFINITIVO <- 120L  # 2024-12 (D-054)

sp <- function(id, y, escala, ...) {
  modifyList(modifyList(list(id = id, y = y), escala), list(...))
}
specs <- list(
  sp("h5a_contagem", "obitos_moto_transito", CONTAGEM),
  sp("h5b_contagem", "obitos_moto_transito_fora_saude", CONTAGEM),
  sp("h5a_taxa", "taxa_obito_moto_transito", TAXA),
  sp("h5b_taxa", "taxa_obito_moto_fora_saude", TAXA),
  sp("h5a_contagem_ate2024", "obitos_moto_transito", CONTAGEM, t_fim = ULTIMO_DEFINITIVO),
  sp("h5b_contagem_ate2024", "obitos_moto_transito_fora_saude", CONTAGEM, t_fim = ULTIMO_DEFINITIVO),
  sp("h5a_taxa_ate2024", "taxa_obito_moto_transito", TAXA, t_fim = ULTIMO_DEFINITIVO),
  sp("h5b_taxa_ate2024", "taxa_obito_moto_fora_saude", TAXA, t_fim = ULTIMO_DEFINITIVO)
)

t0 <- Sys.time()
rodadas <- mclapply(specs, function(s) {
  r <- tryCatch(suppressWarnings(estimar_cs(d, s)), error = function(e) e)
  if (inherits(r, "error")) return(list(erro = conditionMessage(r), id = s$id))
  r[c("resumo", "es")]
}, mc.cores = nucleos)
cat(sprintf("H5: %d especificacoes em %.1f min\n", length(specs),
            as.numeric(difftime(Sys.time(), t0, units = "mins"))))
for (r in Filter(function(r) !is.null(r$erro), rodadas)) cat(sprintf("ERRO %s: %s\n", r$id, r$erro))
rodadas <- Filter(function(r) is.null(r$erro), rodadas)

est <- rbindlist(lapply(rodadas, `[[`, "resumo"), fill = TRUE)
fwrite(est, file.path(saida, "h5_estimativas.csv"))
fwrite(rbindlist(lapply(rodadas, `[[`, "es"), fill = TRUE), file.path(saida, "h5_estudo_evento.csv"))

g <- function(i, col) est[id == i][[col]]
criterio <- function(h, i, papel) {
  data.table(hipotese = h, especificacao = i, papel = papel,
             criterio = "estimando positivo e IC 95% exclui zero",
             sustentada = g(i, "att") > 0 & g(i, "ic_inf") > 0,
             t2_pre_rejeita = g(i, "pre_wald_p") < 0.05)
}
testes <- rbindlist(list(
  criterio("H5a", "h5a_contagem", "principal (T3, D-055)"),
  criterio("H5b", "h5b_contagem", "principal (T3, D-055)"),
  criterio("H5a", "h5a_taxa", "anexo: taxa, T3 disparou"),
  criterio("H5b", "h5b_taxa", "anexo: taxa, T3 disparou"),
  criterio("H5a", "h5a_contagem_ate2024", "robustez: sem 2025 preliminar"),
  criterio("H5b", "h5b_contagem_ate2024", "robustez: sem 2025 preliminar"),
  criterio("H5a", "h5a_taxa_ate2024", "robustez: sem 2025 preliminar, taxa"),
  criterio("H5b", "h5b_taxa_ate2024", "robustez: sem 2025 preliminar, taxa")
))
fwrite(testes, file.path(saida, "h5_testes.csv"))

cat("\nH5 (secundaria, D-055):\n")
print(est[, .(id, att = signif(att, 3), pct = round(pct, 1),
              ic = sprintf("[%.1f, %.1f]", pct_ic_inf, pct_ic_sup), p = signif(p_regiao, 2),
              mde = round(mde80_pct, 1), pre_p = signif(pre_wald_p, 2),
              media_pre = signif(media_pre_tratados, 3), trat = tratados_agregados)])
cat("\n")
print(testes)
