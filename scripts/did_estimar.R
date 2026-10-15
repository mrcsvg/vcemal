#!/usr/bin/env Rscript
# Estimacao do V2: as especificacoes do plano de analise, numa rodada so.
#
#     make did
#
# Le `data/painel/estimacao_municipio_mes.csv` (scripts/did_painel.py) e escreve
# em `output/tabelas/did/`:
#   estimativas.csv           uma linha por especificacao (CS e SA)
#   estudo_evento.csv         ATT(e), e em [-12, +24], por especificacao
#   comparacao_por_coorte.csv tamanho do grupo de comparacao por coorte (secao 5)
#   coortes_por_evento.csv    quem contribui em cada e na versao nao balanceada
#   testes.csv                testes de falha da secao 6 e hipoteses, com o criterio declarado
# e `output/figuras/did_estudo_evento.png`.
#
# O veredito da auditoria (secao 4) escolhe a especificacao principal entre
# `principal`, `sem_2017` e `sem_pos2020`; as tres rodam sempre (D-047).

suppressPackageStartupMessages({
  library(data.table)
  library(did)
  library(parallel)
})
args <- commandArgs(trailingOnly = FALSE)
raiz <- normalizePath(file.path(dirname(sub("^--file=", "", args[grep("^--file=", args)])), ".."))
source(file.path(raiz, "src", "vcemal", "analyze", "did.R"))

entrada <- file.path(raiz, "data", "painel", "estimacao_municipio_mes.csv")
saida <- file.path(raiz, "output", "tabelas", "did")
figuras <- file.path(raiz, "output", "figuras")
dir.create(saida, recursive = TRUE, showWarnings = FALSE)
dir.create(figuras, recursive = TRUE, showWarnings = FALSE)
nucleos <- as.integer(Sys.getenv("NUCLEOS", "4"))

d <- fread(entrada)
cat(sprintf("painel: %d linhas, %d municipios\n", nrow(d), uniqueN(d$municipio_ibge)))

# Periodos (2015-01 = 1): 2016-01 = 13, 2016-07 = 19, 2017-07 = 31, 2018-01 = 37,
# 2020-12 = 72, 2023-12 = 108, 2025-12 = 132.
TAXA <- list(t_ini = 19L, g_min = 31L)       # frota existe de 2016-07 (D-015)
CONTAGEM <- list(t_ini = 1L, g_min = 13L)    # SIH existe de 2015-01

# A spec sobrescreve o padrao (`g_min` da nao balanceada, por exemplo).
taxa <- function(id, y, ...) modifyList(modifyList(list(id = id, y = y), TAXA), list(...))
cont <- function(id, y, ...) modifyList(modifyList(list(id = id, y = y), CONTAGEM), list(...))

# Desfechos em diferenca proporcional (placebo e H3): calculados antes do fork.
dif_placebo <- diferenca_proporcional(
  d, cont("x", "moto_internacoes_transito"), "moto_internacoes_transito", "auto_internacoes_transito"
)
dif_h3 <- diferenca_proporcional(d, taxa("x", "taxa_moto_h1839"), "taxa_moto_h1839", "taxa_moto_resto")

specs <- list(
  # H1 -- estimando principal e as duas versoes que o veredito da auditoria pode escolher
  taxa("principal", "taxa_moto_transito"),
  taxa("sem_2017", "taxa_moto_transito", drop_g_lt = 37L),
  taxa("sem_pos2020", "taxa_moto_transito", drop_g_gt = 72L),
  # Robustez da secao 5
  taxa("so_datado", "taxa_moto_transito", grupos = "datado"),
  taxa("nao_balanceada", "taxa_moto_transito", balanceada = FALSE, g_min = 20L),
  cont("contagem", "moto_internacoes_transito"),
  taxa("precoce_2018", "taxa_moto_transito",
       grupos = c("datado", "sem_quebra", "coorte_precoce"), precoce_g = 37L),
  # Secao 6 -- testes de falha
  cont("t1_auto_contagem", "auto_internacoes_transito"),
  cont("t1_dif_moto_auto", dif_placebo),
  taxa("t3_frota", "frota_moto"),
  # Mecanismo, H2, H3
  cont("mecanismo_ciclista", "cicl_internacoes_transito"),
  taxa("h2_tercil1", "taxa_moto_transito", tercil = 1L),
  taxa("h2_tercil2", "taxa_moto_transito", tercil = 2L),
  taxa("h2_tercil3", "taxa_moto_transito", tercil = 3L),
  taxa("h3_homem_18_39", "taxa_moto_h1839"),
  taxa("h3_complemento", "taxa_moto_resto"),
  taxa("h3_dif", dif_h3),
  taxa("h3_condutor_homem_18_39", "taxa_moto_condutor_h1839")
)

t0 <- Sys.time()
rodadas <- mclapply(specs, function(sp) {
  r <- tryCatch(suppressWarnings(estimar_cs(d, sp)), error = function(e) e)
  if (inherits(r, "error")) return(list(erro = conditionMessage(r), id = sp$id))
  r$att_gt <- NULL
  r
}, mc.cores = nucleos)
cat(sprintf("CS: %d especificacoes em %.1f min\n", length(specs),
            as.numeric(difftime(Sys.time(), t0, units = "mins"))))
erros <- Filter(function(r) !is.null(r$erro), rodadas)
for (e in erros) cat(sprintf("ERRO %s: %s\n", e$id, e$erro))
rodadas <- Filter(function(r) is.null(r$erro), rodadas)
names(rodadas) <- vapply(rodadas, function(r) r$resumo$id, "")

sa <- tryCatch(estimar_sa(d, modifyList(specs[[1]], list(id = "sun_abraham"))),
               error = function(e) { cat("ERRO sun_abraham:", conditionMessage(e), "\n"); NULL })

# Conferencia: o erro-padrao do principal pelo bootstrap agrupado do proprio `did`.
x <- rodadas$principal$amostra
set.seed(20261014)
a_bs <- suppressWarnings(att_gt(
  yname = "y", tname = "periodo", idname = "municipio_ibge", gname = "g", data = x,
  control_group = "notyettreated", base_period = "universal", xformla = ~1, est_method = "reg",
  bstrap = TRUE, biters = 999, cband = FALSE, clustervars = "regiao_imediata", faster_mode = TRUE
))
ag_bs <- aggte(a_bs, type = "dynamic", min_e = E_MIN, max_e = E_MAX, balance_e = E_MAX)

est <- rbindlist(c(lapply(rodadas, `[[`, "resumo"), list(sa)), fill = TRUE)
est[, se_bootstrap_did := fifelse(id == "principal", ag_bs$overall.se, NA_real_)]
proporcional <- est$id %in% c("t1_dif_moto_auto", "h3_dif")
# Nos desfechos de diferenca proporcional o ATT ja e a diferenca de efeitos em
# proporcao da media pre: x100 sao pontos percentuais, e `pct` nao se aplica.
est[proporcional, `:=`(pct = 100 * att, pct_ic_inf = 100 * ic_inf, pct_ic_sup = 100 * ic_sup,
                       media_pre_tratados = NA_real_)]
fwrite(est, file.path(saida, "estimativas.csv"))
fwrite(rbindlist(lapply(rodadas, `[[`, "es")), file.path(saida, "estudo_evento.csv"))
fwrite(comparacao_por_coorte(rodadas$principal$amostra, rodadas$principal$coortes),
       file.path(saida, "comparacao_por_coorte.csv"))
fwrite(coortes_por_evento(rodadas$nao_balanceada$amostra), file.path(saida, "coortes_por_evento.csv"))

# Criterios declarados (secoes 5 e 6, D-043), aplicados mecanicamente.
g <- function(i, col) est[id == i & estimador == "CS"][[col]]
sig <- function(i) g(i, "p_regiao") < 0.05
testes <- rbindlist(list(
  data.table(teste = "H1", especificacao = "principal",
             criterio = "estimando positivo e IC 95% exclui zero",
             resultado = g("principal", "att") > 0 & g("principal", "ic_inf") > 0),
  data.table(teste = "H1 so com cluster em municipio?", especificacao = "principal",
             criterio = "efeito que so sobrevive com cluster em municipio nao foi robusto",
             resultado = g("principal", "p_municipio") < 0.05 & !sig("principal")),
  data.table(teste = "T1 placebo", especificacao = "t1_dif_moto_auto",
             criterio = "falha se o efeito sobre auto e indistinguivel do de moto (dif. proporcional com IC contendo zero)",
             resultado = !sig("t1_dif_moto_auto")),
  data.table(teste = "T2 pre-tendencia", especificacao = "principal",
             criterio = "falha se o teste conjunto de e em [-12,-2] rejeita a 5%",
             resultado = g("principal", "pre_wald_p") < 0.05),
  data.table(teste = "T3 denominador", especificacao = "t3_frota",
             criterio = "falha se frota distinguivel de zero E efeito % >= metade do % das internacoes",
             resultado = sig("t3_frota") & g("t3_frota", "pct") >= 0.5 * g("principal", "pct")),
  data.table(teste = "H2 gradiente", especificacao = "h2_tercil1..3",
             criterio = "efeito monotonicamente crescente do 1o ao 3o tercil",
             resultado = g("h2_tercil1", "att") < g("h2_tercil2", "att") &
               g("h2_tercil2", "att") < g("h2_tercil3", "att")),
  data.table(teste = "H3 perfil", especificacao = "h3_dif",
             criterio = "efeito % no perfil maior que no complemento (dif. proporcional > 0, IC exclui zero)",
             resultado = g("h3_dif", "att") > 0 & g("h3_dif", "ic_inf") > 0)
))
testes[, leitura := fifelse(
  startsWith(teste, "T"), fifelse(resultado, "falha do desenho", "nao falha"),
  fifelse(startsWith(teste, "H1 so"), fifelse(resultado, "nao robusto", "ok"),
          fifelse(resultado, "sustentada", "nao sustentada")))]
fwrite(testes, file.path(saida, "testes.csv"))

# Figura: estudo de evento do principal, com o placebo ao lado em %.
es <- rodadas$principal$es
png(file.path(figuras, "did_estudo_evento.png"), width = 1800, height = 1000, res = 200)
par(mar = c(4, 4.5, 2, 1))
z <- qnorm(0.975)
plot(es$e, es$att, pch = 19, cex = 0.7, ylim = range(c(es$att - z * es$se, es$att + z * es$se)),
     xlab = "meses desde a quebra do MEI", ylab = "ATT(e), internacoes por 100 mil motos",
     main = "Motociclista em transito -- Callaway & Sant'Anna, not-yet-treated")
arrows(es$e, es$att - z * es$se, es$e, es$att + z * es$se, length = 0, col = "grey40")
abline(h = 0, lty = 2)
abline(v = -0.5, col = "grey70")
dev.off()

cat("\n")
print(est[, .(id, estimador, att = signif(att, 3), ic_inf = signif(ic_inf, 3), ic_sup = signif(ic_sup, 3),
              pct = round(pct, 1), p_reg = signif(p_regiao, 2), p_mun = signif(p_municipio, 2),
              pre_p = signif(pre_wald_p, 2), trat = tratados_agregados, mun = municipios)])
cat(sprintf("\nprincipal: ep analitico %.4f, bootstrap do did %.4f\n",
            g("principal", "se_regiao"), ag_bs$overall.se))
cat("\n")
print(testes[, .(teste, leitura)])
if (length(erros)) quit(status = 1)
