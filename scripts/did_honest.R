#!/usr/bin/env Rscript
# Sensibilidade as tendencias paralelas, Rambachan & Roth (D-061). Robustez
# declarada fora do plano; nao muda veredito de H1 nem de H5.
#
#     make did-honest     # depois de make did e make sim
#
# Reestima as quatro especificacoes do D-061 (as mesmas de did_estimar.R e
# did_h5.R) e escreve em `output/tabelas/did/`:
#   honest_original.csv  IC convencional, para comparar
#   honest_rm.csv        magnitudes relativas, um IC por Mbar (`na_borda`: nao limitado)
#   honest_sd.csv        suavidade, um IC por M (em % da media pre por mes^2)
# e `output/figuras/did_honest.png`.

suppressPackageStartupMessages({
  library(data.table)
  library(did)
  library(parallel)
})
args <- commandArgs(trailingOnly = FALSE)
raiz <- normalizePath(file.path(dirname(sub("^--file=", "", args[grep("^--file=", args)])), ".."))
source(file.path(raiz, "src", "vcemal", "analyze", "did.R"))

saida <- file.path(raiz, "output", "tabelas", "did")
figuras <- file.path(raiz, "output", "figuras")
dir.create(saida, recursive = TRUE, showWarnings = FALSE)
nucleos <- as.integer(Sys.getenv("NUCLEOS", "4"))

d <- fread(file.path(raiz, "data", "painel", "estimacao_municipio_mes.csv"))
if (!"obitos_moto_transito" %in% names(d)) stop("painel sem o SIM: rode make sim e make did")

TAXA <- list(t_ini = 19L, g_min = 31L)
CONTAGEM <- list(t_ini = 1L, g_min = 13L)
sp <- function(id, y, escala) modifyList(list(id = id, y = y), escala)
specs <- list(
  sp("contagem", "moto_internacoes_transito", CONTAGEM),
  sp("principal", "taxa_moto_transito", TAXA),
  sp("h5a_contagem", "obitos_moto_transito", CONTAGEM),
  sp("h5b_contagem", "obitos_moto_transito_fora_saude", CONTAGEM)
)

# Grades do D-061.
MBAR <- c(0, 0.25, 0.5, 0.75, 1, 1.5, 2)
M_SD_PCT <- c(0, 0.025, 0.05, 0.1, 0.2)

t0 <- Sys.time()
rodadas <- mclapply(specs, function(s) {
  r <- suppressWarnings(estimar_cs(d, s))
  m_sd <- M_SD_PCT / 100 * r$resumo$media_pre_tratados
  avisos <- 0L
  h <- withCallingHandlers(
    sensibilidade_honest(r, mbar = MBAR, m_sd = m_sd),
    warning = function(w) {
      avisos <<- avisos + 1L
      invokeRestart("muffleWarning")
    }
  )
  h$sd[, M_pct := M_SD_PCT]
  h$avisos <- avisos
  h$resumo <- r$resumo
  h
}, mc.cores = nucleos)
cat(sprintf("HonestDiD: %d especificacoes em %.1f min\n", length(specs),
            as.numeric(difftime(Sys.time(), t0, units = "mins"))))
falhou <- vapply(rodadas, inherits, logical(1), "try-error")
if (any(falhou)) stop(paste(unlist(rodadas[falhou]), collapse = "\n"))

junta <- function(k) rbindlist(lapply(rodadas, `[[`, k), fill = TRUE)
original <- junta("original")
original <- merge(original, junta("resumo")[, .(id, att, pct, mde80_pct, pre_wald_p)], by = "id")
rm_ <- junta("rm")
sd_ <- junta("sd")
fwrite(original, file.path(saida, "honest_original.csv"))
fwrite(rm_, file.path(saida, "honest_rm.csv"))
fwrite(sd_, file.path(saida, "honest_sd.csv"))
for (r in rodadas) if (r$avisos) cat(sprintf("%s: %d avisos do solver\n", r$resumo$id, r$avisos))

# Figura: IC em % da media pre, convencional a esquerda e a grade a direita.
ordem <- vapply(specs, `[[`, "", "id")
png(file.path(figuras, "did_honest.png"), width = 2200, height = 1400, res = 200)
par(mfrow = c(2, 4), mar = c(4, 4, 2.5, 0.5))
desenha <- function(x, chave, rotulo, o) {
  xs <- seq_len(nrow(x) + 1)
  lb <- c(o$lb_pct, x$lb_pct)
  ub <- c(o$ub_pct, x$ub_pct)
  plot(NA, xlim = range(xs) + c(-0.5, 0.5), ylim = range(c(lb, ub)), xaxt = "n",
       xlab = rotulo, ylab = "% da media pre", main = paste(o$id, "--", chave), cex.main = 0.8)
  axis(1, at = xs, labels = c("conv", format(x[[chave]])), cex.axis = 0.7)
  borda <- c(FALSE, if ("na_borda" %in% names(x)) x$na_borda else rep(FALSE, nrow(x)))
  # IC na borda da grade nao e limitado: seta aberta, em vermelho.
  arrows(xs, lb, xs, ub, length = ifelse(borda, 0.05, 0), code = 3, lwd = 2,
         col = ifelse(borda, "firebrick", c("grey40", rep("steelblue", nrow(x)))))
  abline(h = 0, lty = 2)
}
for (k in c("rm", "sd")) for (i in ordem) {
  o <- original[id == i]
  if (k == "rm") desenha(rm_[id == i], "Mbar", "Mbar (magnitudes relativas)", o)
  else desenha(sd_[id == i], "M_pct", "M, % da media pre (suavidade)", o)
}
dev.off()

cat("\nIC convencional (% da media pre):\n")
print(original[, .(id, pct = round(pct, 1), lb = round(lb_pct, 1), ub = round(ub_pct, 1),
                   mde80 = round(mde80_pct, 1), pre_p = signif(pre_wald_p, 2))])
cat("\nMagnitudes relativas (% da media pre):\n")
print(rm_[, .(id, Mbar, lb = round(lb_pct, 1), ub = round(ub_pct, 1), na_borda)])
cat("\nSuavidade (% da media pre):\n")
print(sd_[, .(id, M_pct, lb = round(lb_pct, 1), ub = round(ub_pct, 1))])
