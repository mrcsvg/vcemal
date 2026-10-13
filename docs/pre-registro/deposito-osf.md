# Texto para o depósito no OSF

> **Como usar.** Modelo: **OSF Preregistration** (OSF Registries → "Add new" →
> "OSF Preregistration"). Cada seção abaixo corresponde a um campo do formulário,
> na ordem dele; o texto, em inglês, é para colar. O documento normativo é o
> `plano-de-analise.md` (em português), anexado ao depósito com a tradução
> `plano-de-analise.en.md` — este texto o resume e aponta para ele, e onde
> divergirem vale o plano em português.
>
> **Antes de depositar**, falta só uma coisa: o hash do commit para onde a tag
> `pre-registro-v1` aponta, no campo Description (⚠️). As decisões que o formulário exigia e o plano não tinha
> estão no D-043 e já constam do plano.
>
> **Embargo:** o OSF permite até 4 anos. O timestamp vale do mesmo jeito.

---

## Title

Delivery platforms and motorcyclist hospitalizations in Brazil's public health
system (SUS): the effect of entry in Brazilian municipalities

## Description

Observational study on a municipality × month panel of Brazilian
municipalities, 2015–2025. It estimates the effect of the arrival of couriers
paid per delivery (food-delivery platforms with their own courier fleet) on
hospitalizations of motorcyclists injured in traffic accidents in Brazil's
public health system (SUS). The arrival date is the structural break in new
micro-entrepreneur (MEI) registrations under activity code CNAE 5320-2/02
("express delivery services") in the federal company registry, detected by a
rule frozen before any linkage with the outcome. Outcome: SIH/SUS admissions per
100,000 registered motorcycles; motorcyclist deaths (mortality information
system, SIM) as a secondary outcome. Identification by staggered-adoption
difference-in-differences (Callaway & Sant'Anna, 2021). The analysis plan
(Portuguese original, which prevails, and English translation), the
treatment-audit protocol and the decision log are attached and in
`github.com/mrcsvg/vcemal`, tag `pre-registro-v1` (commit ⚠️ hash of the
commit the tag points to: `git rev-parse pre-registro-v1^{commit}`).

## Hypotheses

- **H1 (confirmatory).** The arrival of platform couriers in a municipality
  increases the rate of hospitalizations of motorcyclists injured in traffic
  accidents (ICD-10 V20–V29, traffic) per 100,000 registered motorcycles.
  Predicted direction: positive.
- **H2 (secondary).** The effect increases with the intensity of platform
  operation. Order volume by municipality is private data; the proxy is the
  number of new MEI registrations under CNAE 5320-2/02 per 1,000 inhabitants in
  the 12 months starting at the break, in terciles among treated municipalities
  in the balanced window. Prediction: effect monotonically increasing across
  terciles. Declared bias: MEI registrations cover a minority of couriers (D-031),
  so the proxy measures intensity with error, which flattens the gradient — the
  test is conservative.
- **H3 (mechanism test).** The effect concentrates among men aged 18–39, the
  demographic profile of delivery work. An effect of similar magnitude in the
  complement indicates a general traffic trend within motorcyclists, not
  platformization.
- **H4 (descriptive, outside the causal design).** The occupational link of
  these injuries and deaths is systematically under-recorded in SIH (field
  `CAR_INT`) and SIM (field `ACIDTRAB`). Measured by year and state, among men
  aged 18–39, as the share of records with a work link among those with the
  field filled in, with completeness reported alongside; no test.
- **H5 (secondary).** The effect also shows up in motorcyclist deaths, which
  SIH only partly sees. Same estimand as H1, on SIM deaths (underlying cause
  V20–V29, traffic) per 100,000 motorcycles: H5a, total deaths; H5b, deaths
  outside a health facility (field `LOCOCOR`), which never enter SIH.
  Predicted direction: positive for both. Declared low power (small monthly
  counts); absence of an effect does not refute H5.

## Design Plan

### Study type

Observational Study — secondary administrative data.

### Blinding

No blinding is involved in this study.

### Is there any additional blinding in this study?

Yes, in the construction of the treatment. (1) The break-detection rule and its
parameters were chosen only against a pre-platform placebo (January–June 2016)
and against entry dates observed in the Wayback Machine (Rappi and Uber Eats),
without consulting hospitalization data; the treatment file was frozen with
SHA-256 `128999bd21de00854c717e181657f5d1832ce78222ec9ef6dd99a3bd8a7654a2`.
(2) An audit by independent search (75 municipalities) is carried out after this
registration by two coders blind to SIH, to the break date and to each
municipality's group (the list includes decoys with no break); the consequence
of each audit verdict is declared in the plan before the search starts.

### Study design

Staggered-adoption difference-in-differences. Unit: municipality × month,
January 2015 to December 2025 (rate per fleet from July 2016, start of the
municipal fleet series). Absorbing treatment: a municipality becomes treated in
the month of its break. Universe: the 1,710 municipalities with 20,000 or more
inhabitants in the 2022 Census, split into three groups by the frozen rule:

- `datado` (dated, 640): under 100,000 inhabitants, with a break — the treated,
  with treatment months from 2017-01 to 2025-06;
- `sem_quebra` (no break, 751): under 100,000, no break — untreated as far as
  MEI registrations can see; part of the comparison group;
- `coorte_precoce` (early cohort, 319): 100,000 inhabitants or more — excluded
  from the main estimation (the break does not date them: the placebo fires in a
  quarter of them).

Comparison group: not-yet-treated (including `sem_quebra`). Event window
`e ∈ [−12, +24]` months, balanced: cohorts from 2017-07 to 2023-12 (478
municipalities). Details and rationale: sections 4 and 5 of the plan.

### Randomization

No randomization. (The only random draw is the sample for the treatment audit,
with fixed seed 20261011, already executed and versioned.)

## Sampling Plan

### Existing Data

Registration prior to analysis of the data.

### Explanation of existing data

All data exist; all but SIM have been downloaded. What has and has not been
done with them:

- **SIH (outcome).** Downloaded and aggregated into a municipality × month
  panel. **Descriptive** national and state-level analyses were run and are
  public in the repository: deflated cost of hospitalizations, gap between SIH
  and social-security disability benefits (INSS), completeness of `CAR_INT`,
  national series next to iFood's operating result. None of them uses treatment
  timing.
- **CNPJ (treatment).** Downloaded and processed; break rule applied and frozen.
  Validated against the 2016 placebo and against the Wayback Machine, never
  against SIH (code and outputs in `scripts/mei.py`, decision D-040).
- **SIM (secondary outcome, H4 and H5).** Not yet downloaded at the date of
  registration. It will be extracted afterwards by the same route as SIH
  (D-044); the version used is recorded with its date, and a year still
  preliminary is flagged.
- **Never done:** any linkage of treatment with outcome, in a table, model or
  exploratory plot (rule D-006, in force since 2026-09-12). The estimation script
  does not exist yet.

### Data collection procedures

Public sources, rebuilt by the repository code (`Makefile`):

- SIH/SUS, reduced admission records (RD), from the DATASUS FTP via PySUS, with
  missing months recovered from the FTP (D-034 to D-036). Case: code V20–V29 in
  any secondary or principal diagnosis field, traffic read from the fourth
  character according to each category's table (D-010, D-017); municipality of
  residence.
- Fleet: Senatran monthly municipal fleet, vehicle types matching V20–V29
  (D-013), from July 2016.
- SIM, death certificates (DO files), from the DATASUS FTP via PySUS. Case:
  underlying cause V20–V29, traffic by the same fourth-character rule;
  municipality of residence; month of death; place of occurrence (`LOCOCOR`)
  and work-accident flag (`ACIDTRAB`).
- Population: IBGE (2022 Census for the universe; annual estimates as control).
- Treatment: CNPJ open data, September 2026 release, head-office establishments
  with primary CNAE 5320-2/02, including closed ones (D-040).

### Sample size

1,391 municipalities in the main estimation (640 `datado` + 751 `sem_quebra`),
132 months (January 2015 – December 2025). In the balanced window, 478 treated
municipalities.

### Sample size rationale

No sample size was chosen: it is the universe of municipalities with 20,000 or
more inhabitants in which the break rule is valid (under 100,000). No power
analysis was performed.

### Stopping rule

Not applicable: administrative data with a closed period (panel ends December
2025, fixed before registration).

## Variables

### Manipulated variables

None (observational study). The observed treatment is the month of the break in
new delivery MEI registrations: the first candidate month `t` (2017-01 to
2025-06) in which registrations in `[t, t+5]` are at least 5, at least twice the
baseline of the previous 24 months, and unlikely under it (Poisson, p < 0.01);
the break is the first month in that window with a registration. Code:
`src/vcemal/mei.py`.

### Measured variables

- **Primary outcome:** 100,000 × hospitalizations of motorcyclists in traffic
  accidents (V20–V29, `internacoes_transito`) / municipal motorcycle fleet in the
  month (`frota_moto`). This is not the panel column `taxa_por_frota`, which
  counts all hospitalizations in the group, including non-traffic ones.
- **Subgroups and tests:** hospitalizations of men aged 18–39 and of the
  complement (H3); of male drivers aged 18–39 (secondary, low power, D-023);
  cyclists V10–V19, as counts (mechanism); car occupants V40–V49 (placebo);
  `frota_moto` as outcome (endogenous-denominator test); SIM deaths of
  motorcyclists in traffic per 100,000 motorcycles, total and outside a health
  facility (H5).
- Full data dictionary: `docs/dicionario-painel.md`.

### Indices

No composite indices.

## Analysis Plan

### Statistical models

Callaway & Sant'Anna (2021), not-yet-treated comparison group, group × time
effects aggregated into an event study over `e ∈ [−12, +24]`, balanced.
Standard errors clustered by IBGE immediate geographic region; clustering by
municipality reported side by side in the main table. Sun & Abraham (2021) as
robustness.

Primary estimand for H1: the simple average of ATT(e) over `e ∈ [0, +24]` in the
balanced window, without covariates (unconditional parallel trends), also
reported as a percentage of the treated units' pre-treatment mean. H2: the same
estimand, by tercile of the intensity proxy.

### Transformations

Rate per 100,000 motorcycles, in levels. Cyclist hospitalizations as counts
(bicycles have no registry denominator). In the count version, municipality
fixed effects.

### Inference criteria

H1 is tested two-sided at 5% with a 95% confidence interval; it is supported if
the primary estimand is positive and the interval excludes zero. H1 is the only
confirmatory hypothesis, with no multiple-comparison correction; H2, H3, the
mechanism test and the placebo are read by the criteria pre-declared in the
plan, with 95% intervals. H5a and H5b are each supported if the estimand is
positive and the 95% interval excludes zero.

Pre-declared design-failure tests (section 6 of the plan):

1. Effect on car occupants indistinguishable from the effect on motorcyclists →
   the design captures a general traffic trend.
2. Non-parallel pre-trends over `e ∈ [−12, −1]` → report and do not interpret
   causally.
3. Endogenous denominator: if the effect on `frota_moto` is distinguishable
   from zero **and** at least half of the percentage effect on
   hospitalizations, the main result becomes the count with municipality fixed
   effects.

### Data exclusion

- Municipalities under 20,000 inhabitants (outside the universe) and the early
  cohort (100,000 or more): excluded from the main estimation.
- Audit consequences, applied mechanically (section 4 of the plan): failure in
  the `2017` or `2021-2025` stratum removes those breaks from the main
  estimation; failure in `2018-2020` keeps the estimation but withdraws the
  "platform effect" interpretation; failure in the state-capitals stratum
  cancels the robustness check that uses the early cohort.
- Platform exits (reverse treatment) are not observable in CNPJ data and are not
  included (D-041).

### Missing data

Municipality-months without fleet data have an undefined rate and drop out of
the rate estimation; in the balanced window, a cohort with any event time
missing the outcome drops out entirely. Nothing is imputed (D-015): a missing
denominator stays missing.

### Exploratory analysis

Declared as exploratory (section 7 of the plan): hourly distribution of crashes
in RENAEST; completeness of `CAR_INT`; spillover to controls (excluding
not-yet-treated municipalities in the immediate region of a treated one);
anticipation at `e = −1, −2, −3`; coincident coding changes around 2018.
Pre-declared robustness: without `sem_quebra` in the comparison group; without
breaks before 2018-01; without breaks after 2020-12; unbalanced version; counts
instead of rates.

## Other

**Why the coefficient is a lower bound:** the design is ecological (treatment at
the municipality level, outcome over all motorcyclists), the pre-period is
partly contaminated by the marketplace phase (D-021), and a fleet that grows
with treatment attenuates the rate (D-027). The three reasons will be reported
separately. An effect on deaths outside a health facility (H5b) would add a
fourth: harm that SIH cannot see by construction.

**Deviations** from this plan after registration go to `docs/decisoes.md` with
date and reason, and the affected analyses become declared exploratory
analyses.

**Attachments:** `plano-de-analise.md` (analysis plan, Portuguese original,
authoritative) and `plano-de-analise.en.md` (its English translation); in
Portuguese only: `protocolo-cronologia-entrada.md`
(coding protocol, version 1.1); `tratamento_mei_municipio.csv` (frozen
treatment, hash above); `auditoria_municipios.csv` (audit sample);
`decisoes.md` (decision log).
