#!/usr/bin/env Rscript
# Testes na contagem sem as quebras de 2017 (D-065). Exploratoria declarada antes
# de rodar; nao muda o veredito de H1 nem a especificacao principal.
#
#     make did-sem2017     # depois de make did e make did-exploratorio
#
# Escreve em `output/tabelas/did/`, sem sobrescrever as saidas existentes:
#   sem2017_estimativas.csv    uma linha por especificacao (CS e SA)
#   sem2017_estudo_evento.csv  ATT(e), e em [-12, +24]
#   sem2017_testes.csv         criterios do D-065, aplicados mecanicamente
#   sem2017_honest_{original,rm,sd}.csv  grades do D-061 sobre a contagem

suppressPackageStartupMessages({
  library(data.table)
  library(did)
  library(parallel)
})
args <- commandArgs(trailingOnly = FALSE)
raiz <- normalizePath(file.path(dirname(sub("^--file=", "", args[grep("^--file=", args)])), ".."))
source(file.path(raiz, "src", "vcemal", "analyze", "did.R"))

saida <- file.path(raiz, "output", "tabelas", "did")
nucleos <- as.integer(Sys.getenv("NUCLEOS", "4"))

d <- fread(file.path(raiz, "data", "painel", "estimacao_municipio_mes.csv"))

# Periodos como em did_estimar.R: 2016-01 = 13, 2016-07 = 19, 2017-07 = 31, 2018-01 = 37.
TAXA <- list(t_ini = 19L, g_min = 31L)
CONTAGEM <- list(t_ini = 1L, g_min = 13L)
SEM_2017 <- 37L
taxa <- function(id, y, ...) modifyList(modifyList(list(id = id, y = y), TAXA), list(...))
cont <- function(id, y, ...) modifyList(modifyList(list(id = id, y = y), CONTAGEM), list(...))

dif_placebo <- diferenca_proporcional(
  d, cont("x", "moto_internacoes_transito", drop_g_lt = SEM_2017),
  "moto_internacoes_transito", "auto_internacoes_transito"
)

specs <- list(
  cont("contagem_sem2017", "moto_internacoes_transito", drop_g_lt = SEM_2017),
  taxa("taxa_sem2017", "taxa_moto_transito", drop_g_lt = SEM_2017),
  cont("t1_auto_sem2017", "auto_internacoes_transito", drop_g_lt = SEM_2017),
  cont("t1_dif_sem2017", dif_placebo, drop_g_lt = SEM_2017),
  taxa("t3_frota_sem2017", "frota_moto", drop_g_lt = SEM_2017)
)

t0 <- Sys.time()
rodadas <- mclapply(specs, function(sp) {
  r <- suppressWarnings(estimar_cs(d, sp))
  r$att_gt <- NULL
  r$amostra <- NULL
  r
}, mc.cores = nucleos)
falhou <- vapply(rodadas, inherits, logical(1), "try-error")
if (any(falhou)) stop(paste(unlist(rodadas[falhou]), collapse = "\n"))
names(rodadas) <- vapply(rodadas, function(r) r$resumo$id, "")
cat(sprintf("CS: %d especificacoes em %.1f min\n", length(specs),
            as.numeric(difftime(Sys.time(), t0, units = "mins"))))

# Conferencia do D-065: tem de reproduzir a curva do D-048.
curva <- fread(file.path(saida, "curva_especificacao.csv"))
confere <- function(id_curva, r) {
  ref <- curva[id == id_curva]
  stopifnot(nrow(ref) == 1L)
  if (abs(ref$pct - r$resumo$pct) > 1e-6) {
    stop(sprintf("%s nao reproduz a curva: %.6f contra %.6f", id_curva, r$resumo$pct, ref$pct))
  }
  cat(sprintf("confere %s: %.3f%%\n", id_curva, r$resumo$pct))
}
confere("contagem|nyt_todos|sem_2017|balanceada", rodadas$contagem_sem2017)
confere("taxa|nyt_todos|sem_2017|balanceada", rodadas$taxa_sem2017)

sa <- rbindlist(lapply(list(
  cont("sa_contagem_sem2017", "moto_internacoes_transito", drop_g_lt = SEM_2017),
  taxa("sa_taxa_sem2017", "taxa_moto_transito", drop_g_lt = SEM_2017),
  cont("sa_contagem_todas", "moto_internacoes_transito")
), function(sp) suppressWarnings(estimar_sa(d, sp))))

est <- rbindlist(c(lapply(rodadas, `[[`, "resumo"), list(sa)), fill = TRUE)
# Na diferenca proporcional o ATT ja esta em proporcao da media pre (did_estimar.R).
est[id == "t1_dif_sem2017", `:=`(pct = 100 * att, pct_ic_inf = 100 * ic_inf, pct_ic_sup = 100 * ic_sup,
                                 media_pre_tratados = NA_real_)]
fwrite(est, file.path(saida, "sem2017_estimativas.csv"))
fwrite(rbindlist(lapply(rodadas, `[[`, "es")), file.path(saida, "sem2017_estudo_evento.csv"))

# Criterios do D-065.
g <- function(i, col) est[id == i & estimador == "CS"][[col]]
sig <- function(i) g(i, "p_regiao") < 0.05
testes <- rbindlist(list(
  data.table(teste = "criterio de H1", especificacao = "contagem_sem2017",
             criterio = "estimando positivo e IC 95% exclui zero (so vale se a auditoria reprovar 2017)",
             resultado = g("contagem_sem2017", "att") > 0 & g("contagem_sem2017", "ic_inf") > 0),
  data.table(teste = "agrupamento por municipio", especificacao = "contagem_sem2017",
             criterio = "p < 0,05 tambem com cluster em municipio",
             resultado = g("contagem_sem2017", "p_municipio") < 0.05),
  data.table(teste = "T1 placebo", especificacao = "t1_dif_sem2017",
             criterio = "dispara se o IC da diferenca moto - auto contem zero",
             resultado = !sig("t1_dif_sem2017")),
  data.table(teste = "T2 pre-tendencia", especificacao = "contagem_sem2017",
             criterio = "dispara se o Wald de e em [-12,-2] rejeita a 5%",
             resultado = g("contagem_sem2017", "pre_wald_p") < 0.05),
  data.table(teste = "T3 denominador", especificacao = "t3_frota_sem2017 x taxa_sem2017",
             criterio = "dispara se frota distinguivel de zero E efeito % >= metade do % da taxa",
             resultado = sig("t3_frota_sem2017") & g("t3_frota_sem2017", "pct") >= 0.5 * g("taxa_sem2017", "pct")),
  data.table(teste = "T3, ao lado", especificacao = "t3_frota_sem2017 x contagem_sem2017",
             criterio = "mesma conta contra a contagem, sem efeito mecanico (D-049)",
             resultado = sig("t3_frota_sem2017") & g("t3_frota_sem2017", "pct") >= 0.5 * g("contagem_sem2017", "pct"))
))
fwrite(testes, file.path(saida, "sem2017_testes.csv"))

print(est[, .(id, estimador, pct = round(pct, 2), lb = round(pct_ic_inf, 2), ub = round(pct_ic_sup, 2),
              p_reg = signif(p_regiao, 3), p_mun = signif(p_municipio, 3), mde = round(mde80_pct, 1),
              pre_p = signif(pre_wald_p, 3), trat = tratados_agregados, mun = municipios)])
print(testes[, .(teste, especificacao, resultado)])

# HonestDiD: grades do D-061, grade de theta do D-062.
MBAR <- c(0, 0.25, 0.5, 0.75, 1, 1.5, 2)
M_SD_PCT <- c(0, 0.025, 0.05, 0.1, 0.2)
r <- rodadas$contagem_sem2017
t0 <- Sys.time()
avisos <- 0L
h <- withCallingHandlers(
  sensibilidade_honest(r, mbar = MBAR, m_sd = M_SD_PCT / 100 * r$resumo$media_pre_tratados),
  warning = function(w) {
    avisos <<- avisos + 1L
    invokeRestart("muffleWarning")
  }
)
h$sd[, M_pct := M_SD_PCT]
fwrite(h$original, file.path(saida, "sem2017_honest_original.csv"))
fwrite(h$rm, file.path(saida, "sem2017_honest_rm.csv"))
fwrite(h$sd, file.path(saida, "sem2017_honest_sd.csv"))
cat(sprintf("HonestDiD: %.1f min, %d avisos do solver\n",
            as.numeric(difftime(Sys.time(), t0, units = "mins")), avisos))
print(h$original[, .(lb = round(lb_pct, 1), ub = round(ub_pct, 1))])
print(h$rm[, .(Mbar, lb = round(lb_pct, 1), ub = round(ub_pct, 1), na_borda)])
print(h$sd[, .(M_pct, lb = round(lb_pct, 1), ub = round(ub_pct, 1))])
