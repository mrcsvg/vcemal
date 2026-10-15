# Teste do estimador do V2 sobre DGP sintetico com efeito conhecido.
# Roda via `tests/test_did_r.py` (pytest), ou direto: Rscript tests/did_sintetico.R
#
# O DGP tem adocao escalonada, efeito fixo de unidade e de tempo, choque comum
# por regiao e mes, efeito dinamico conhecido e um desvio do efeito por regiao,
# de media zero -- e ele que faz o cluster em regiao importar. Nada aqui
# foi ajustado ate passar: as tolerancias sao 4 erros-padrao e 15% entre o
# erro-padrao analitico e o do bootstrap do proprio `did`.

suppressPackageStartupMessages({
  library(data.table)
  library(did)
})
args <- commandArgs(trailingOnly = FALSE)
aqui <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
source(file.path(aqui, "..", "src", "vcemal", "analyze", "did.R"))

falhas <- character()
confere <- function(ok, msg) {
  cat(if (ok) "ok   " else "FALHA", msg, "\n")
  if (!ok) falhas <<- c(falhas, msg)
}

gerar <- function(n = 600, t = 60, efeito = function(e) 2 + 0.1 * e, semente = 20261014) {
  set.seed(semente)
  regioes <- 60
  u <- data.table(
    municipio_ibge = 1:n,
    regiao_imediata = sample(1:regioes, n, replace = TRUE),
    g = sample(c(0L, 13:48), n, replace = TRUE, prob = c(0.4, rep(0.6 / 36, 36)))
  )
  u[, grupo_trat := fifelse(g == 0, "sem_quebra", "datado")]
  u[, alfa := rnorm(.N, 10, 2)]
  desvio <- rnorm(regioes, 0, 1)
  u[, desvio_reg := desvio[regiao_imediata]]
  u[, tercil_h2 := NA_integer_]
  choque_reg <- CJ(regiao_imediata = 1:regioes, periodo = 1:t)[, c_rt := rnorm(.N, 0, 1)]
  x <- u[CJ(municipio_ibge = 1:n, periodo = 1:t), on = "municipio_ibge"]
  x <- choque_reg[x, on = c("regiao_imediata", "periodo")]
  x[, e := fifelse(g > 0, periodo - g, NA_integer_)]
  x[, tau := fifelse(!is.na(e) & e >= 0, efeito(e) + desvio_reg, 0)]
  x[, ysint := alfa + 0.05 * periodo + c_rt + tau + rnorm(.N)]
  x[]
}

spec <- list(id = "sintetico", y = "ysint", t_ini = 1L, t_fim = 60L, g_min = 13L,
             g_max_janela = 36L)

# 1. Recupera o efeito: estimando = media de 2 + 0,1 e para e em 0..24 = 3,2.
d <- gerar()
r <- estimar_cs(d, spec)
verdade <- mean(2 + 0.1 * 0:24)
dist <- abs(r$resumo$att - verdade) / r$resumo$se_regiao
confere(dist < 4, sprintf("ATT %.3f contra %.3f (%.1f ep)", r$resumo$att, verdade, dist))
confere(r$resumo$coortes_agregadas == 24, sprintf("coortes balanceadas 13..36: %d", r$resumo$coortes_agregadas))

# 2. O erro-padrao analitico bate com o bootstrap agrupado do proprio `did`
#    -- confere a escala da funcao de influencia e a ordem das unidades.
x <- amostra(d, spec)
for (cl in c("municipio_ibge", "regiao_imediata")) {
  cv <- if (cl == "municipio_ibge") NULL else cl
  set.seed(1)
  a <- att_gt(yname = "y", tname = "periodo", idname = "municipio_ibge", gname = "g", data = x,
              control_group = "notyettreated", base_period = "universal", xformla = ~1,
              est_method = "reg", bstrap = TRUE, biters = 2000, cband = FALSE,
              clustervars = cv, faster_mode = TRUE)
  ag <- aggte(a, type = "dynamic", min_e = E_MIN, max_e = E_MAX, balance_e = E_MAX)
  meu <- if (cl == "municipio_ibge") r$resumo$se_municipio else r$resumo$se_regiao
  razao <- meu / ag$overall.se
  confere(abs(razao - 1) < 0.15, sprintf("ep analitico / bootstrap (%s): %.3f", cl, razao))
}
confere(r$resumo$se_regiao > r$resumo$se_municipio,
        "choque regional: ep por regiao maior que por municipio")

# 3. Sem efeito, o teste conjunto de pre-tendencia nao rejeita.
d0 <- gerar(efeito = function(e) 0 * e, semente = 7)
d0[, ysint := ysint - fifelse(!is.na(e) & e >= 0, desvio_reg, 0)]
r0 <- estimar_cs(d0, spec)
confere(r0$resumo$pre_wald_p > 0.01, sprintf("pre-tendencia sob nulo: p = %.3f", r0$resumo$pre_wald_p))
confere(abs(r0$resumo$att) / r0$resumo$se_regiao < 4, sprintf("ATT sob nulo: %.3f", r0$resumo$att))

# 4. Pre-tendencia linear nos tratados e detectada.
d1 <- gerar(efeito = function(e) 0 * e, semente = 8)
d1[, ysint := ysint - fifelse(!is.na(e) & e >= 0, desvio_reg, 0)]
d1[g > 0 & periodo < g, ysint := ysint + 0.15 * (periodo - g)]
r1 <- estimar_cs(d1, spec)
confere(r1$resumo$pre_wald_p < 0.01, sprintf("pre-tendencia plantada: p = %.2g", r1$resumo$pre_wald_p))

# 5. Sun & Abraham recupera o mesmo efeito.
s <- estimar_sa(d, spec)
confere(abs(s$att - verdade) / s$se_regiao < 4, sprintf("SA %.3f contra %.3f", s$att, verdade))

# 6. Diferenca proporcional: dois desfechos com o mesmo efeito percentual -> zero.
d[, ydobro := 2 * ysint]
nome <- diferenca_proporcional(d, spec, "ysint", "ydobro")
rd <- estimar_cs(d, modifyList(spec, list(id = "dif", y = nome)))
confere(abs(rd$resumo$att) < 1e-8, sprintf("diferenca proporcional de desfechos proporcionais: %.2g", rd$resumo$att))

if (length(falhas)) {
  cat("\n", length(falhas), "falha(s)\n")
  quit(status = 1)
}
cat("\ntudo ok\n")
