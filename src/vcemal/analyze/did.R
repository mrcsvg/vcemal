# Estimador do V2: Callaway & Sant'Anna (2021) e Sun & Abraham (2021).
#
# Funcoes puras sobre o painel de `scripts/did_painel.py`. O que estimar (desfecho,
# amostra, janela) vem de uma `spec`; a lista de specs pre-registradas mora em
# `scripts/did_estimar.R`. Nada aqui le arquivo.
#
# Escolhas que o plano (secao 5) fixa e que estao aqui:
#   - grupo de comparacao not-yet-treated, sem covariaveis;
#   - estimando = media simples de ATT(e), e em [0, +24], janela balanceada;
#   - erro-padrao agrupado em regiao imediata, com municipio ao lado.
# Escolha que o plano nao fixa (D-047): `base_period = "universal"` -- os
# coeficientes pre-tratamento ficam todos contra e = -1, que e o grafico de
# estudo de evento que se le. O pos-tratamento e o mesmo nas duas opcoes.

suppressPackageStartupMessages({
  library(data.table)
  library(did)
})

E_MIN <- -12L
E_MAX <- 24L

#' Recorte da spec sobre o painel. Devolve data.table com `y` e `g` da spec.
amostra <- function(d, spec) {
  s <- modifyList(list(
    grupos = c("datado", "sem_quebra"), t_ini = 19L, t_fim = 132L,
    g_min = 31L, drop_g_lt = NA_integer_, drop_g_gt = NA_integer_,
    precoce_g = NA_integer_, tercil = NA_integer_, g_max_janela = 108L
  ), spec)
  x <- copy(d[grupo_trat %in% s$grupos & periodo >= s$t_ini & periodo <= s$t_fim])
  if (!is.na(s$precoce_g)) x[grupo_trat == "coorte_precoce", g := s$precoce_g]
  # Coorte sem os 12 meses de pre-periodo nao cabe na janela: sai inteira
  # (nem tratada nem comparacao), como as 50 com quebra antes de 2017-07.
  x <- x[g == 0 | g >= s$g_min]
  if (!is.na(s$drop_g_lt)) x <- x[g == 0 | g >= s$drop_g_lt]
  if (!is.na(s$drop_g_gt)) x <- x[g == 0 | g <= s$drop_g_gt]
  if (!is.na(s$tercil)) {
    # H2: so os tratados do tercil; os de fora da janela continuam como
    # not-yet-treated, como no principal.
    x <- x[g == 0 | g > s$g_max_janela | tercil_h2 == s$tercil]
  }
  x[, y := as.numeric(get(s$y))]
  if (anyNA(x$y)) stop(sprintf("%s: %d valores NA no desfecho", spec$id, sum(is.na(x$y))))
  setorder(x, municipio_ibge, periodo)
  x[]
}

#' Erro-padrao agrupado a partir da funcao de influencia do `did`.
#' `inf` e n x k, linhas na ordem de `ids` (municipios ordenados). Devolve a
#' matriz de covariancia k x k.
vcov_cluster <- function(inf, cl) {
  inf <- as.matrix(inf)
  n <- nrow(inf)
  s <- rowsum(inf, cl)
  crossprod(s) / n^2
}

#' Media dos tratados no pre-periodo, e em [-12, -1], so das coortes agregadas.
media_pre <- function(x, coortes) {
  x[g %in% coortes & periodo >= g + E_MIN & periodo <= g - 1L, mean(y)]
}

#' Callaway & Sant'Anna para uma spec. Devolve lista com `resumo` (1 linha) e `es`.
estimar_cs <- function(d, spec) {
  x <- amostra(d, spec)
  balanceada <- is.null(spec$balanceada) || isTRUE(spec$balanceada)
  controle <- if (is.null(spec$controle)) "notyettreated" else spec$controle
  a <- att_gt(
    yname = "y", tname = "periodo", idname = "municipio_ibge", gname = "g", data = x,
    control_group = controle, base_period = "universal", xformla = ~1,
    est_method = "reg", bstrap = FALSE, cband = FALSE, faster_mode = TRUE
  )
  ag <- if (balanceada) {
    aggte(a, type = "dynamic", min_e = E_MIN, max_e = E_MAX, balance_e = E_MAX, bstrap = FALSE)
  } else {
    aggte(a, type = "dynamic", bstrap = FALSE)
  }
  # A funcao de influencia vem na ordem interna do `did`, que ordena as unidades
  # por coorte -- nao por codigo. Casar o cluster pela ordem do `data.table`
  # embaralha as regioes, e o erro-padrao por regiao sai errado sem aviso
  # (o por municipio nao muda: cada unidade e o proprio cluster).
  ordem <- a$DIDparams$time_invariant_data$municipio_ibge
  um <- unique(x[, .(municipio_ibge, regiao_imediata, g)])
  um <- um[match(ordem, um$municipio_ibge)]
  stopifnot(nrow(um) == length(ag$inf.function$dynamic.inf.func), !anyNA(um$municipio_ibge))

  inf <- ag$inf.function$dynamic.inf.func
  se_reg <- sqrt(vcov_cluster(inf, um$regiao_imediata)[1, 1])
  se_mun <- sqrt(vcov_cluster(inf, um$municipio_ibge)[1, 1])

  # Estudo de evento e teste conjunto de pre-tendencia (e de -12 a -2; -1 e a base).
  ife <- ag$inf.function$dynamic.inf.func.e
  v_e <- vcov_cluster(ife, um$regiao_imediata)
  es <- data.table(id = spec$id, e = ag$egt, att = ag$att.egt, se = sqrt(diag(v_e)))
  pre <- which(ag$egt < -1 & ag$egt >= E_MIN)
  wald <- NA_real_
  wald_p <- NA_real_
  if (length(pre)) {
    b <- ag$att.egt[pre]
    w <- tryCatch(as.numeric(t(b) %*% solve(v_e[pre, pre], b)), error = function(e) NA_real_)
    wald <- w
    wald_p <- pchisq(w, df = length(pre), lower.tail = FALSE)
  }

  coortes <- if (balanceada) {
    sort(unique(um$g[um$g > 0 & um$g + E_MAX <= max(x$periodo) & um$g + E_MIN >= min(x$periodo)]))
  } else {
    sort(unique(um$g[um$g > min(x$periodo)]))
  }
  pre_m <- media_pre(x, coortes)
  est <- ag$overall.att
  z <- qnorm(0.975)
  resumo <- data.table(
    id = spec$id, desfecho = spec$y, estimador = "CS",
    att = est, se_regiao = se_reg, ic_inf = est - z * se_reg, ic_sup = est + z * se_reg,
    p_regiao = 2 * pnorm(-abs(est / se_reg)),
    se_municipio = se_mun, p_municipio = 2 * pnorm(-abs(est / se_mun)),
    media_pre_tratados = pre_m, pct = 100 * est / pre_m,
    pct_ic_inf = 100 * (est - z * se_reg) / pre_m, pct_ic_sup = 100 * (est + z * se_reg) / pre_m,
    pre_wald = wald, pre_wald_gl = length(pre), pre_wald_p = wald_p,
    municipios = nrow(um), tratados_agregados = sum(um$g %in% coortes),
    coortes_agregadas = length(coortes), regioes = uniqueN(um$regiao_imediata),
    periodo_ini = min(x$periodo), periodo_fim = max(x$periodo)
  )
  list(resumo = resumo, es = es, att_gt = a, amostra = x, coortes = coortes)
}

#' Tamanho do grupo de comparacao por coorte (plano, secao 5): not-yet-treated
#' disponiveis em e = 0 e em e = +24.
comparacao_por_coorte <- function(x, coortes) {
  um <- unique(x[, .(municipio_ibge, g)])
  rbindlist(lapply(coortes, function(gg) {
    data.table(
      g = gg, tratados = sum(um$g == gg),
      comparacao_e0 = sum(um$g == 0 | um$g > gg),
      comparacao_e24 = sum(um$g == 0 | um$g > gg + E_MAX),
      sem_quebra = sum(um$g == 0)
    )
  }))
}

#' Quais coortes contribuem para cada tempo de evento (versao nao balanceada).
coortes_por_evento <- function(x) {
  um <- unique(x[g > 0, .(municipio_ibge, g)])
  t0 <- min(x$periodo)
  t1 <- max(x$periodo)
  gs <- sort(unique(um$g[um$g > t0]))
  es <- seq(t0 - max(gs), t1 - min(gs))
  rbindlist(lapply(es, function(e) {
    ok <- gs[gs + e >= t0 & gs + e <= t1 & gs - 1 >= t0]
    data.table(e = e, coortes = length(ok), municipios = sum(um$g %in% ok))
  }))
}

#' Sun & Abraham via fixest, na mesma amostra, com os nunca tratados como controle.
estimar_sa <- function(d, spec) {
  suppressPackageStartupMessages(library(fixest))
  x <- amostra(d, spec)
  x <- x[g == 0 | (g >= spec$g_min %||% 31L & g <= 108L)]
  x[, g_sa := fifelse(g == 0, 10000L, g)]
  x[, e := fifelse(g == 0, NA_integer_, periodo - g)]
  x <- x[g == 0 | (e >= E_MIN & e <= E_MAX)]
  m <- feols(y ~ sunab(g_sa, periodo, ref.p = -1) | municipio_ibge + periodo,
             data = x, cluster = ~regiao_imediata)
  cf <- coef(m)
  nm <- names(cf)
  ev <- as.integer(sub("^periodo::(-?[0-9]+)$", "\\1", nm))
  pos <- which(ev >= 0 & ev <= E_MAX)
  w <- rep(1 / length(pos), length(pos))
  est <- sum(w * cf[pos])
  v <- vcov(m)[pos, pos]
  se_reg <- sqrt(as.numeric(t(w) %*% v %*% w))
  v_mun <- vcov(m, cluster = ~municipio_ibge)[pos, pos]
  se_mun <- sqrt(as.numeric(t(w) %*% v_mun %*% w))
  coortes <- sort(unique(x$g[x$g > 0]))
  pre_m <- media_pre(x, coortes)
  z <- qnorm(0.975)
  data.table(
    id = spec$id, desfecho = spec$y, estimador = "SA",
    att = est, se_regiao = se_reg, ic_inf = est - z * se_reg, ic_sup = est + z * se_reg,
    p_regiao = 2 * pnorm(-abs(est / se_reg)),
    se_municipio = se_mun, p_municipio = 2 * pnorm(-abs(est / se_mun)),
    media_pre_tratados = pre_m, pct = 100 * est / pre_m,
    pct_ic_inf = 100 * (est - z * se_reg) / pre_m, pct_ic_sup = 100 * (est + z * se_reg) / pre_m,
    municipios = uniqueN(x$municipio_ibge), tratados_agregados = uniqueN(x$municipio_ibge[x$g > 0]),
    coortes_agregadas = length(coortes), regioes = uniqueN(x$regiao_imediata),
    periodo_ini = min(x$periodo), periodo_fim = max(x$periodo)
  )
}

`%||%` <- function(a, b) if (is.null(a)) b else a

#' Desfecho em proporcao da media pre dos tratados, para comparar dois grupos
#' (placebo, H3) num estimando so: o ATT de `a/pre_a - b/pre_b` e a diferenca
#' dos efeitos percentuais, com a covariancia entre os dois dentro do erro-padrao.
diferenca_proporcional <- function(d, spec, col_a, col_b) {
  base <- modifyList(spec, list(y = col_a))
  xa <- amostra(d, base)
  coortes <- sort(unique(xa$g[xa$g > 0 & xa$g + E_MAX <= max(xa$periodo) &
                               xa$g + E_MIN >= min(xa$periodo)]))
  pa <- media_pre(xa, coortes)
  xb <- amostra(d, modifyList(spec, list(y = col_b)))
  pb <- media_pre(xb, coortes)
  nome <- sprintf("dif_%s_%s", col_a, col_b)
  d[, (nome) := get(col_a) / pa - get(col_b) / pb]
  nome
}
