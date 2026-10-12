# Analysis plan — preregistration (English translation)

> **Translation.** This is a faithful English translation of
> `plano-de-analise.md`, prepared for the OSF registration on 2026-10-11. The
> Portuguese original is authoritative: if the two differ, the Portuguese text
> prevails. Codes such as D-040 refer to entries in the project's decision log
> (`docs/decisoes.md`, in Portuguese). Variable and group names are kept as they
> appear in the code (`datado`, `sem_quebra`, `coorte_precoce`, …), with a gloss
> on first use.
>
> **Ready for registration (2026-10-11).** No open `[ ]` sections. After
> registration this file is frozen — any change goes to the decision log as a
> declared exploratory analysis.

## 1. Question and hypotheses

- **H1** — the entry of a delivery platform into a municipality increases the
  incidence of hospitalizations of motorcyclists injured in transport
  accidents.
- **H2** — the effect increases with operating intensity. `[x]` **Partially
  identified**: order volume by municipality is private data. **Proxy (D-043):**
  new MEI (individual micro-entrepreneur) registrations under CNAE 5320-2/02 per
  1,000 inhabitants (2022 Census) in the 12 months starting at the break, in
  terciles among treated municipalities in the balanced window; the primary
  estimand (section 5) is estimated by tercile. **Prediction:** effect
  monotonically increasing from the first to the third tercile. **Sign of the
  bias:** MEI registrations cover a minority of couriers (D-031), so the proxy
  measures intensity with error, and misclassification across terciles flattens
  the gradient — the test is conservative. Absence of a gradient does not refute
  H2; a gradient supports it.
- **H3** — the effect concentrates in the **demographic profile of delivery
  work**: men aged 18 to 39. If the effect is of similar magnitude outside that
  profile, the design is capturing a general traffic trend *within* the
  motorcyclist group, not platformization.
  **Orthogonal to the placebo:** the placebo (V40–V49) tests for a general trend
  **across** vehicle types; H3 tests for a general trend **within**
  motorcyclists. The two can fail independently.
  **Operationalization:** `homem_18_39` (men 18–39) against the complement
  (`internacoes − homem_18_39`), both in the panel.
  **Secondary, with declared low power:** the same test restricted to drivers
  (`condutor_homem_18_39`). The fourth character `.4` is only **9.4%** of
  motorcyclist hospitalizations — `.9`, unspecified, is 69.5% — so the subgroup
  keeps ~5% of the outcome. Worse than the loss of power: **who codes `.4`
  instead of `.9` varies by hospital and by state**, and that practice tends to
  track urbanization, which is what drives platform entry. It is potential
  confounding, not just noise. Report, do not interpret in isolation.
- **H4** — the occupational link is systematically under-recorded in SIH.

## 2. Data

See `docs/anexo-a-inventario-fontes-de-dados.md`. Sources for the main
estimation: SIH/SUS (outcome; hospital admission records of Brazil's public
health system), RENAVAM motorcycle fleet (denominator), IBGE (population), CNPJ
open data (federal company registry; treatment: the break in delivery MEI
registrations — see section 4).

## 3. Case definition

| Group | ICD-10 | Role |
|---|---|---|
| Motorcyclist | V20–V29 **in traffic** (`internacoes_transito`) | Outcome |
| Cyclist | V10–V19 | Mechanism test |
| Car occupant | V40–V49 | Placebo |

**The outcome rate is computed in the estimation**, as 100,000 ×
`internacoes_transito` / `frota_moto` (motorcycle fleet). The panel column
`taxa_por_frota` uses `internacoes`, which includes non-traffic cases, and is
not the outcome.

The fourth character is not read the same way in every category: V19, V29 and
V49 use a different table, in which `.3` is a **non**-traffic accident. The rule
is in `src/vcemal/cid.py` and the rationale in D-010.

**The outcome is not restricted to drivers.** An earlier version of this table
said "fourth character for driver in traffic", which would restrict the main
outcome to `.4` — **9.4%** of motorcyclist hospitalizations, because `.9`
(unspecified) is 69.5%. Besides discarding nine tenths of cases, conditioning on
`.4` conditions on a coding practice that varies by hospital and state and tends
to track urbanization — the same factor that drives platform entry. Drivers
enter as a declared secondary subgroup (see H3), never as the main outcome.

## 4. Treatment construction

**The event is the arrival of couriers paid per delivery, not the arrival of the
app.** iFood operated as a marketplace from 2011 to 2017 — order through the
app, delivery by the restaurant's own courier — and only started delivering
with its own courier fleet in 2018. Pay per delivery, which is the project's
hypothesis, only exists from then on. See D-020.

`[x]` **Source: the break in delivery MEI registrations (D-040).** By
municipality of residence and month, new head-office establishments with
primary activity code CNAE 5320-2/02 ("express delivery services") in the CNPJ
open data (September 2026 release, including closed CNPJs). The treatment is the
month of the **break**: the first candidate month `t`, from 2017-01 to 2025-06,
in which registrations in `[t, t+5]` are at least 5, at least twice the baseline
of the previous 24 months, and unlikely under it (Poisson, p < 0.01); the break
is the first month in the window with a registration. Rule and parameters in
`vcemal.mei`, chosen only against a 2016 placebo and against the Wayback
Machine, never against hospitalizations. What is measured is the arrival of a
supply of formalized couriers — the break date is used, not the level, because
MEI registrations cover a minority of couriers (D-031).

`[x]` **Frozen file.** `docs/fontes/cronologia/tratamento_mei_municipio.csv`,
SHA-256 `128999bd21de00854c717e181657f5d1832ce78222ec9ef6dd99a3bd8a7654a2`,
produced by `make mei` before any linkage with SIH (D-006, D-041). After
registration, no date changes.

**Groups, by municipality in the universe (1,710 with 20,000 or more
inhabitants):**

| Group | N | Rule | Role |
|---|---|---|---|
| `datado` (dated) | 640 | under 100,000 inhabitants, with a break | treated; `mes_tratamento` = month of the break. This is where the variation over time comes from |
| `sem_quebra` (no break) | 751 | under 100,000, no break | untreated as far as can be seen — **not** "never treated": there may be a platform with too few MEI couriers for the test to detect. Part of the comparison group; a robustness check excludes them |
| `coorte_precoce` (early cohort) | 319 | 100,000 or more | outside the main estimation. All had the iFood app in 2019 (D-038, D-039); that the own courier fleet had arrived by 2018 is a premise, tested by the audit's state-capitals stratum. The placebo fires in a quarter of them: the break does not date them |

Municipalities under 20,000 inhabitants are not included: the rule was not
validated for them.

**Risks specific to this source, and what each one triggers:**

- **Spurious break.** The placebo (a break in January–June 2016, before any
  platform) fires in 0.7% of municipalities of 20–50 thousand and in 3.8% of
  those of 50–100 thousand. The rule takes the *first* break: an early spurious
  one hides the true one. This is the risk of **2017**: 83 breaks before iFood's
  own fleet (2018-01), in a year when only Uber Eats and Rappi had fleets, and
  only in state capitals.
- **Late contamination.** After 2021 the neighbouring code 5320-2/01 explodes
  with e-commerce delivery; 5320-2/02 may share that channel. It weighs on the
  breaks from **2021 to 2025**.
- **It is not platform X.** The break dates the arrival of a supply of
  formalized couriers, from any platform. A by-platform robustness check does
  not exist with this source.

`[x]` **Audit by independent search, with consequences declared in advance
(D-041).** A sample drawn with a fixed seed (`vcemal.auditoria`, seed 20261011)
of 6 `datado` municipalities per population band (20–50 thousand, 50–100
thousand) in each break-year stratum — `2017`, `2018-2020`, `2021-2025` —, 6
`sem_quebra` decoys per band and, mandatorily, the 27 state capitals: 75
municipalities mixed in a single list
(`docs/fontes/cronologia/auditoria_municipios.csv`). Two coders search for
platform entry following the protocol `docs/protocolo-cronologia-entrada.md`,
version 1.1, blind to SIH, to the break and to the stratum; tie-breaking by rule
and adjudication as in the protocol.

- **Agreement:** the break falls in the coded interval `[data_min, data_max]`
  of the earliest entry, widened by 6 months on each side. For the capitals,
  which are `coorte_precoce` and are not dated by the break, the test is the
  cohort's premise: the coded interval, widened the same way, starts by
  December 2018. A municipality with no evidence found (`N`) counts neither for
  nor against.
- **Verdict by stratum:** *passes* with at least 2/3 of the found cases
  agreeing; *fails* below that; *inconclusive* with fewer than 6 found cases.
  The verdict is by break-year stratum; the result by population band is
  reported alongside, without a verdict. Decoys are only described: the share
  of them with a platform found is reported.
- **Consequence, applied mechanically:**
  - `2017` fails → the 2017 breaks leave the main estimation (neither treated
    nor comparison) and return only as robustness;
  - `2021-2025` fails → the same for breaks from 2021 onwards;
  - `2018-2020` fails → the break does not date platform arrival where it
    matters most. The estimation runs as declared, but the result is reported
    as the effect of the arrival of formalized couriers, and the "platform
    effect" reading is declared unsupported;
  - `capital` fails → the premise "early cohort treated by 2018" falls, and the
    robustness check that uses `coorte_precoce` as a 2018 cohort is not run;
  - inconclusive → the rule stays as it is, and the stratum is declared
    unaudited.
- **Pre-declared robustness, whatever the verdict:** exclude breaks before
  2018-01 and, separately, breaks after 2020-12.

The plan is registered **before** the audit starts; the verdict only applies the
consequence already written here. `make auditoria` consolidates the coding
sheets and prints the verdict.

**Municipality-by-municipality coding (protocol 1.0, D-033) is no longer the
source of the treatment.** Its risk — two coders agreeing, with a high kappa, on
the arrival of the *app* instead of the *fleet* — still applies within the
audit, and is handled by section 1 of the protocol.

**Exits are not observable with this source.** The break dates entries; the
exit of Uber Eats (March 2022) and 99Food (2023) does not appear in the CNPJ.
The reverse treatment foreseen in the previous version of this plan leaves the
estimation: a municipality that lost one platform almost always kept another,
and the break does not distinguish the two cases. Deviation recorded in D-041.

## 5. Specification

Staggered-adoption difference-in-differences. Callaway & Sant'Anna (2021)
estimator as the main one, given timing heterogeneity and the known
inconsistency of TWFE in this case. Sun & Abraham as robustness.

**Primary estimand for H1 (D-043):** the simple average of ATT(e) over
`e ∈ [0, +24]` in the balanced window, without covariates (unconditional
parallel trends), also reported as a percentage of the treated units'
pre-treatment mean (`e ∈ [−12, −1]`).

**Inference criterion (D-043):** two-sided test at 5% and 95% interval. H1 is
supported if the primary estimand is positive and the interval excludes zero.
H1 is the only confirmatory hypothesis, with no multiple-comparison correction;
H2, H3, the mechanism test and the failure tests in section 6 are read by the
criteria declared in each, with 95% intervals.

- Unit: municipality × month
- Fixed effects: municipality and calendar month
- Comparison group: **not-yet-treated** (D-022), among the `datado` and
  `sem_quebra` municipalities of section 4. Municipalities under 20,000
  inhabitants are not included: they are small and rural by construction, and
  comparing them with the treated would compare urbanization, not platforms —
  urbanization moves motorization, traffic and hospital supply all at once.
  **Robustness:** not-yet-treated `datado` only, without `sem_quebra` (which may
  have a platform the MEI data did not see). Divergence between the two is a
  diagnostic of control contamination, not a failure.
  **Report the size of the comparison group by cohort**: saturation shrinks the
  set at the end of the window.
- Standard errors: **clustered by IBGE immediate geographic region** (510
  regions, median of 9 municipalities). Municipality as robustness.
  **Reason:** treatment is assigned at the municipality, but couriers and
  patients move across the region. The panel's own data dictionary records that
  `municipio_res` (municipality of residence) ≠ municipality of the accident,
  and that in metropolitan areas the divergence is material — the same spillover
  that blurs the outcome's geography correlates the errors. Clustering by
  municipality would understate the standard error. With 510 clusters the
  asymptotics are comfortable; wild cluster bootstrap is reserved for
  cohort-level estimates with few clusters.
  **An effect that only survives with municipality clustering is not robust** —
  the comparison between the two levels goes into the main table, not an
  appendix.
- Event window: **e ∈ [−12, +24] months, balanced** — only cohorts with all 37
  event times observed.
  **Who fits in it:** the fleet denominator starts in July 2016 (D-015) and the
  SIH panel ends in December 2025, so the balanced window admits cohorts from
  **2017-07 to 2023-12**: 478 of the 640 `datado`. Left out: 50 with a break
  before 2017-07 and 112 with a break after 2023-12.
  **Why −12 and no more:** with the MEI break the earliest cohort is 2017-01,
  not 2018-01 (as the previous version of this plan assumed). Widening the
  window backwards costs the 2017 cohorts, which are already the ones at risk of
  spurious breaks (section 4); narrowing it forwards costs the 2024–2025 ones,
  the ones at risk of contamination. +24 months is the effect of interest: pay
  per delivery acts through accumulated exposure.
  **Robustness:** unbalanced version, using all available periods per cohort,
  with the table of which cohorts contribute at each event time; and the count
  of hospitalizations (with municipality fixed effects) instead of the rate,
  which recovers the cohorts before 2017-07 because SIH starts in 2015-01.

## 6. Pre-declared design-failure tests

1. Effect on car occupants indistinguishable from the effect on motorcyclists →
   the design captures a general traffic trend.
2. Non-parallel pre-trends in the pre-treatment window → report and do not
   interpret causally.
3. **Endogenous denominator.** Run the same estimator with `frota_moto` **as the
   outcome**. If platform entry raises the registered motorcycle fleet — people
   buying a motorcycle to work —, numerator and denominator move together and
   the rate no longer measures risk.
   **Pre-declared failure criterion:** if the effect on `frota_moto` is
   statistically distinguishable from zero **and** its percentage change is of
   an order comparable to that of hospitalizations — **at least half of the
   percentage effect on hospitalizations** (D-043) —, the rate is not
   interpretable. In that case the main result becomes the **count** of
   hospitalizations with municipality fixed effects, and the rate goes to the
   appendix with the caveat.
   **The bias is signable, and that matters:** a fleet rising with treatment
   *attenuates* the rate. If the test fails in that direction, the rate estimate
   is a lower bound — adding to the two other lower-bound reasons already
   declared (D-001, dilution over all motorcyclists; D-021, contamination of the
   pre-period by the marketplace phase). The three must appear separately.
   **It is the only one of the risks raised that destroys the estimand instead
   of merely biasing it** — which is why it becomes a pre-declared test, and not
   anticipation or spillover, which remain as robustness in section 7.

## 7. Exploratory analyses (declared as such)

- Shift of the hourly distribution of motorcycle crashes in RENAEST towards
  delivery peak hours, conditional on the hour field existing.
- Completeness of `CAR_INT` by year and by municipality.
- **Spillover to controls.** Re-estimate excluding the *not-yet-treated* in the
  same immediate region as an already-treated municipality. If the effect grows,
  the main one was attenuated by control contamination — likely, given that
  `municipio_res` is not the municipality of the accident.
- **Anticipation.** Coefficients at `e = −1, −2, −3`. Sharper than pre-trend test
  2, and largely redundant with it; read off the same event-study plot, not run
  as a separate test.
- **Coincident coding change.** National series of the share of admissions with
  a V code in any `DIAGSEC` field and of the composition of `campo_causa`. A
  discontinuity around 2018 would confound outcome with measurement. Cheap — one
  query — and the tool already exists in `vcemal.extract.bigquery`.

## 8. Deviations

Any deviation from this plan goes to the decision log (`docs/decisoes.md`) with
date and reason.
