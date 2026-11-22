# Nota de desvios para o OSF

> **Como usar.** No registro (doi: 10.17605/OSF.IO/V82JE), a nota entra como
> *update* do registro ("Update" → justificativa de mudanças) ou como arquivo
> anexado ao projeto ligado ao registro. O texto abaixo, em inglês, é para
> colar. Ele resume e aponta para o log de decisões (`docs/decisoes.md`), que é
> o documento normativo; onde divergirem, vale o log.
>
> **Antes de enviar:** trocar `<COMMIT>` pelo hash do commit que estiver no
> `main` depois do merge do PR #8, e conferir que a URL do repositório abre para
> quem não tem acesso de escrita.
>
> Rascunho de 2026-11-22. Cobre o D-046 ao D-069 e o adendo de 2026-11-22 ao D-064.

---

## Transparent changes and results since registration

This note lists every change to the registered analysis plan, every analysis
added after registration, and the status of each registered hypothesis. Each
item points to a dated entry (D-xxx) in the decision log,
`docs/decisoes.md`, at commit `<COMMIT>` of
`https://github.com/mrcsvg/vcemal`. The registered plan is
`docs/pre-registro/plano-de-analise.md` at tag `pre-registro-v1`. The treatment
file has not changed since registration (SHA-256 `128999bd…7654a2`).

### 1. Status of the registered hypotheses

- **H1 (main), not supported.** Test 3 (endogenous denominator) fired, so by the
  rule in section 6 of the plan the main result became the **count** of
  hospitalizations with municipality fixed effects: +7.8% of the pre-treatment
  mean, 95% CI −1.4% to +17.0%, p = 0.098, 528 treated municipalities (D-049).
  The registered rate outcome gives +1.1%, CI −13% to +15% (D-047). Test 3 fired
  in a degenerate way: the rule was written for an effect distinguishable from
  zero, and with an effect near zero any movement in the motorcycle fleet
  fires it. The rule was applied as written, and this caveat is reported next to
  it (D-049). Test 1 (car-occupant placebo) also fires: the CI of the
  motorcycle − car difference contains zero (D-047, D-049).
- **H2 (intensity gradient), not supported:** by tertile of MEI openings, the
  effects are +5.2%, +3.7% and −6.5% of the pre-treatment mean, all with CIs
  that contain zero, and they do not increase with intensity
  (`output/tabelas/did/estimativas.csv`, specification of D-047).
- **H3 (men aged 18–39), not supported:** the difference against the complement
  is +11.2 percentage points, 95% CI −4.5 to +26.8.
- **H5a and H5b (deaths, SIM), not supported**, in either scale and with or
  without the preliminary year 2025 (D-055, D-056). Minimum detectable effects
  at 80% power are about 25% (H5a) and 34% (H5b).
- **H4 (descriptive):** the SIH records work-relatedness in 1 in about 24,500
  hospitalizations of men aged 18–39; the SIM records it in 7.7% of the death
  certificates where the field is filled (D-057, D-058).

### 2. Changes to the registered plan

1. **Operational choices the plan did not fix**, all declared before the first
   estimation on the outcome (D-047): universal base period; analytic clustered
   standard errors from the influence function; placebo (test 1) estimated in
   counts, as a difference of percentage effects; H2 tertiles exclude the other
   tertiles' treated units; early cohort coded as 2018-01 in the robustness
   check; Sun & Abraham specification.
2. **Estimation ran before the audit verdict** (D-047). The audit coders had no
   access to the estimates, and the verdict only selects among sample versions
   that were all pre-declared and always estimated.
3. **The audit coders are AI agents, not people** (D-067). The two coders and the
   adjudicator became AI agents of two different models (Claude Opus 5.5 and
   Claude Sonnet 5.5), under protocol v1.2. Sample, event rules, evidence rules,
   tie-breaking, verdict rule and consequences did not change. Two things were
   added: a mechanical check that every quoted excerpt appears at the cited URL,
   and effort floors and ceilings per search. Blinding was by instruction, not by
   system permission. Agreement between two models of the same family is not
   equivalent to inter-human reliability. The first round was stopped by a
   search-quota limit and was discarded as a pilot before any comparison. The
   valid round used a different search tool (first and second addenda to D-067).
4. **Audit result** (D-068), by the frozen rule: the 2017 stratum passes (4 of 6
   findings agree, exactly at the 2/3 threshold) and capitals pass (23 of 27).
   The 2018–2020 and 2021–2025 strata are inconclusive (fewer than 6 findings),
   so they count as not audited. No stratum failed, and no break was removed
   from the main estimation. Limitation found after the verdict: the agreeing
   2017 findings, and all findings in the other two strata, are a wide Wayback
   interval (71 months), which the frozen rule does not penalize. The 2017
   "pass" is therefore not informative. In municipalities of 20,000–100,000
   inhabitants, the search found no fine date for any platform.
5. **The treatment is read as the arrival of platform delivery work, not of a
   named company** (D-069, declared after D-068). The rule, the hash, the sample
   and all estimates are unchanged. Platform registration rules show that parcel
   platforms (Loggi, Shopee, Mercado Livre since 2021-08, Amazon since 2025-06)
   require a delivery MEI, while food platforms accept a personal tax ID
   (`docs/fontes/requisitos_cadastro_plataformas.csv`). So 2021+ breaks have a
   documented mechanism and are read as part of the treatment, not as
   contamination. The 2017–2020 breaks are not explained by registration rules.

### 3. Analyses added after registration (exploratory)

All were declared in the log before they were run, unless noted. None replaces
a registered result.

- Power (MDE at 80%), a 48-specification curve, and exploratory analyses E1–E4
  (within-region comparison, South and Southeast only, spillover, base-period
  dip) (D-048, D-049).
- Rate × count decomposition: the gap between scales is weighting by
  municipality size, not sample or denominator (D-050, D-051).
- Coincident coding change in the SIH: no discontinuity near 2018 (D-059,
  D-060).
- Sensitivity to parallel trends (Rambachan & Roth): no robust CI excludes zero
  (D-061, D-062).
- Count without the 2017 breaks (D-065, D-066): it meets the H1 criterion
  narrowly (+9.95%, CI +0.10% to +19.81%), but test 1 fires and the effect is
  fragile to clustering by municipality (p = 0.051). The declaration was written
  before running but committed after. The record of the order is a local log
  with file hashes, a weaker record than a prior commit.
- Checks of non-hospital data sources (SIA, CIHA, CMD, SINAN). None measures
  the total, and nothing was crossed with the treatment (D-064 and its
  2026-11-22 addendum).

### 4. Hypotheses suggested by the data

Patterns seen after looking at the data are not reported as findings. They are
listed as future work with what a test would require (D-052;
`docs/proximos-trabalhos.md`, PT-01 to PT-06): size heterogeneity, the
Center-West region, non-hospital emergency care, work accidents in the SINAN,
dating platform arrival in small municipalities, and intermediaries hiring
couriers as MEI in 2017–2020.
