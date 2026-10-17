#!/usr/bin/env Rscript
# Exploratorias declaradas do V2 (D-048): curva de especificacao e E1-E4.
#
#     make did-exploratorio     # depois de make did
#
# Nada aqui e confirmatorio: o resultado de H1 e o de scripts/did_estimar.R.
# Escreve em `output/tabelas/did/`:
#   curva_especificacao.csv  as 48 especificacoes, todas
#   curva_resumo.csv         a leitura fixada no D-048 (mediana, amplitude, fracoes)
#   exploratorias.csv        E1-E4
#   exploratorias_regiao.csv E1 por grande regiao
# e `output/figuras/did_curva_especificacao.png`.

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
# Grande regiao pelo primeiro digito do codigo IBGE: 1 N, 2 NE, 3 SE, 4 S, 5 CO.
d[, grande_regiao := municipio_ibge %/% 1000000L]

# ---- Curva de especificacao: 2 x 3 x 4 x 2 = 48 (D-048) ---------------------
escalas <- list(
  taxa = list(y = "taxa_moto_transito", t_ini = 19L, g_min = 31L, g_min_nb = 20L),
  contagem = list(y = "moto_internacoes_transito", t_ini = 1L, g_min = 13L, g_min_nb = 2L)
)
comparacoes <- list(
  nyt_todos = list(grupos = c("datado", "sem_quebra"), controle = "notyettreated"),
  nyt_datado = list(grupos = "datado", controle = "notyettreated"),
  nunca_tratados = list(grupos = c("datado", "sem_quebra"), controle = "nevertreated")
)
coortes <- list(
  todas = list(),
  sem_2017 = list(drop_g_lt = 37L),
  sem_pos2020 = list(drop_g_gt = 72L),
  so_2018_2020 = list(drop_g_lt = 37L, drop_g_gt = 72L)
)
janelas <- c(balanceada = TRUE, nao_balanceada = FALSE)

grade <- CJ(escala = names(escalas), comparacao = names(comparacoes),
            coortes = names(coortes), janela = names(janelas), sorted = FALSE)
specs <- lapply(seq_len(nrow(grade)), function(i) {
  g <- grade[i]
  es <- escalas[[g$escala]]
  bal <- janelas[[g$janela]]
  base <- list(id = paste(g$escala, g$comparacao, g$coortes, g$janela, sep = "|"),
               y = es$y, t_ini = es$t_ini, g_min = if (bal) es$g_min else es$g_min_nb,
               balanceada = bal)
  modifyList(modifyList(base, comparacoes[[g$comparacao]]), coortes[[g$coortes]])
})

t0 <- Sys.time()
curva <- rbindlist(mclapply(specs, function(sp) {
  r <- tryCatch(suppressWarnings(estimar_cs(d, sp)), error = function(e) e)
  if (inherits(r, "error")) return(data.table(id = sp$id, erro = conditionMessage(r)))
  r$resumo
}, mc.cores = nucleos), fill = TRUE)
cat(sprintf("curva: %d especificacoes em %.1f min\n", nrow(curva),
            as.numeric(difftime(Sys.time(), t0, units = "mins"))))
curva <- cbind(grade, curva)
fwrite(curva, file.path(saida, "curva_especificacao.csv"))

ok <- curva[is.na(erro %||% NA_character_) | !"erro" %in% names(curva)]
if ("erro" %in% names(curva)) ok <- curva[is.na(erro)]
resumo_curva <- data.table(
  especificacoes = nrow(curva), estimadas = nrow(ok),
  mediana_pct = median(ok$pct), min_pct = min(ok$pct), max_pct = max(ok$pct),
  fracao_positivas = mean(ok$att > 0),
  fracao_p05_positivas = mean(ok$p_regiao < 0.05 & ok$att > 0),
  fracao_p05_negativas = mean(ok$p_regiao < 0.05 & ok$att < 0),
  mediana_mde80_pct = median(ok$mde80_pct)
)
fwrite(resumo_curva, file.path(saida, "curva_resumo.csv"))

# Figura: estimativas ordenadas com IC, e as dimensoes embaixo.
o <- ok[order(pct)]
png(file.path(figuras, "did_curva_especificacao.png"), width = 2000, height = 1500, res = 200)
layout(matrix(1:2, ncol = 1), heights = c(3, 2))
par(mar = c(0.5, 4.5, 2, 1))
plot(seq_len(nrow(o)), o$pct, pch = 19, cex = 0.6, xaxt = "n", xlab = "",
     ylim = range(c(o$pct_ic_inf, o$pct_ic_sup)), ylab = "efeito, % da media pre",
     main = "Curva de especificacao -- exploratoria (D-048)")
arrows(seq_len(nrow(o)), o$pct_ic_inf, seq_len(nrow(o)), o$pct_ic_sup, length = 0,
       col = fifelse(o$p_regiao < 0.05, "firebrick", "grey55"))
abline(h = 0, lty = 2)
par(mar = c(4, 4.5, 0.5, 1))
niveis <- c(paste0("escala:", names(escalas)), paste0("comp:", names(comparacoes)),
            paste0("coortes:", names(coortes)), paste0("janela:", names(janelas)))
plot(NA, xlim = c(1, nrow(o)), ylim = c(0.5, length(niveis) + 0.5), yaxt = "n",
     xlab = "especificacoes, ordenadas pelo efeito", ylab = "")
axis(2, at = seq_along(niveis), labels = niveis, las = 1, cex.axis = 0.55)
marca <- cbind(paste0("escala:", o$escala), paste0("comp:", o$comparacao),
               paste0("coortes:", o$coortes), paste0("janela:", o$janela))
for (j in seq_len(ncol(marca))) points(seq_len(nrow(o)), match(marca[, j], niveis), pch = 15, cex = 0.5)
dev.off()

# ---- E1-E4 sobre o principal (D-048) ---------------------------------------
principal <- list(id = "principal", y = "taxa_moto_transito", t_ini = 19L, g_min = 31L)

r_p <- suppressWarnings(estimar_cs(d, principal))
e1 <- estimar_por_grande_regiao(d, modifyList(principal, list(id = "E1_dentro_grande_regiao")))
r_e2 <- suppressWarnings(estimar_cs(d[grande_regiao %in% c(3L, 4L)],
                                    modifyList(principal, list(id = "E2_sul_sudeste"))))
# E3: tira os sem_quebra de regiao imediata com algum datado da janela.
reg_trat <- unique(d[grupo_trat == "datado" & g >= 31L & g <= 108L, regiao_imediata])
r_e3 <- suppressWarnings(estimar_cs(
  d[!(grupo_trat == "sem_quebra" & regiao_imediata %in% reg_trat)],
  modifyList(principal, list(id = "E3_sem_controle_vizinho"))
))
e4a <- contraste_pre_medio(r_p)
e4a[, id := "E4a_contra_media_pre"]
# E4b: antecipacao de 3 meses. A janela pre precisa de 3 meses a mais de dado.
r_e4b <- tryCatch(suppressWarnings({
  sp <- modifyList(principal, list(id = "E4b_antecipacao_3", g_min = 34L))
  x <- amostra(d, sp)
  a <- att_gt(yname = "y", tname = "periodo", idname = "municipio_ibge", gname = "g", data = x,
              control_group = "notyettreated", base_period = "universal", xformla = ~1,
              est_method = "reg", bstrap = FALSE, cband = FALSE, faster_mode = TRUE,
              anticipation = 3)
  ag <- aggte(a, type = "dynamic", min_e = E_MIN, max_e = E_MAX, balance_e = E_MAX, bstrap = FALSE)
  ordem <- a$DIDparams$time_invariant_data$municipio_ibge
  um <- unique(x[, .(municipio_ibge, regiao_imediata, g)])[match(ordem, municipio_ibge)]
  se <- sqrt(vcov_cluster(ag$inf.function$dynamic.inf.func, um$regiao_imediata)[1, 1])
  coortes_ag <- sort(unique(um$g[um$g > 0 & um$g + E_MAX <= max(x$periodo)]))
  pre_m <- media_pre(x, coortes_ag)
  z <- qnorm(0.975)
  data.table(id = sp$id, att = ag$overall.att, se_regiao = se,
             ic_inf = ag$overall.att - z * se, ic_sup = ag$overall.att + z * se,
             p_regiao = 2 * pnorm(-abs(ag$overall.att / se)), media_pre_tratados = pre_m,
             pct = 100 * ag$overall.att / pre_m, pct_ic_inf = 100 * (ag$overall.att - z * se) / pre_m,
             pct_ic_sup = 100 * (ag$overall.att + z * se) / pre_m,
             mde80_pct = 100 * FATOR_MDE * se / pre_m, tratados_agregados = length(unique(um$municipio_ibge[um$g %in% coortes_ag])))
}), error = function(e) data.table(id = "E4b_antecipacao_3", erro = conditionMessage(e)))

col <- c("id", "att", "se_regiao", "ic_inf", "ic_sup", "p_regiao", "media_pre_tratados",
         "pct", "pct_ic_inf", "pct_ic_sup", "mde80_pct", "pre_wald_p", "tratados_agregados")
pega <- function(x) x[, intersect(col, names(x)), with = FALSE]
expl <- rbindlist(list(pega(r_p$resumo), pega(e1$resumo), pega(r_e2$resumo), pega(r_e3$resumo),
                       pega(e4a), pega(r_e4b)), fill = TRUE)
fwrite(expl, file.path(saida, "exploratorias.csv"))
fwrite(e1$por_regiao, file.path(saida, "exploratorias_regiao.csv"))

cat("\nCurva de especificacao (exploratoria):\n")
print(resumo_curva)
print(ok[order(pct), .(escala, comparacao, coortes, janela, pct = round(pct, 1),
                       ic = sprintf("[%.1f, %.1f]", pct_ic_inf, pct_ic_sup), p = signif(p_regiao, 2),
                       mde = round(mde80_pct, 1))])
cat("\nExploratorias E1-E4 (D-048):\n")
print(expl[, .(id, pct = round(pct, 1), ic = sprintf("[%.1f, %.1f]", pct_ic_inf, pct_ic_sup),
               p = signif(p_regiao, 2), mde = round(mde80_pct, 1), pre_p = signif(pre_wald_p, 2),
               trat = tratados_agregados)])
cat("\nE1 por grande regiao (1 N, 2 NE, 3 SE, 4 S, 5 CO):\n")
print(e1$por_regiao)
