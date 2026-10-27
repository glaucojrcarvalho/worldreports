# Moldova — data notes and publication boundaries

**Research status: Phase C draft (not a published atlas).** Updated 2026-10-27.

This file records the meanings behind the staged observations in
[SOURCES.yaml](SOURCES.yaml) and the source probes in
[DISCOVERY.md](DISCOVERY.md). It is *not* evidence that Moldova's 12 plates
have been drawn or reviewed.

## What was actually collected

1. **World Bank WDI cross-country layer**: eight curated files, 20 distinct
   indicator codes, 2006–2025 grid, 386 numeric observations. API metadata
   `sourceid=2`, `countryiso3code=MDA`, `lastupdated=2026-10-08`.
   Every missing country/year cell remains blank, not zero or interpolation.
   `fetch/fetch_wdi.py` checks API schema and critical 2024–2025 anchors,
   then writes only `*_from_wb.csv` sidecars.

2. **Moldovan national budget (BNS / Ministry of Finance)**:
   `fiscal/budget_summary.csv` has **two observed calendar-year executions**:
   *2024 FINAL* and *2025 PRELIMINARY*, in **millions of nominal MDL**.
   The BNS [financial indicators page](https://statistica.gov.md/en/statistic_indicator_details/21)
   (updated 2026-08-28) reports:

   | Period | Revenue | Expenditure + non-financial assets | Balance | Edition |
   |---|---:|---:|---:|---|
   | 2024 | 110,338.5 | 122,962.6 | -12,624.1 | final |
   | 2025 | 125,602.0 | 139,856.4 | -14,254.4 | preliminary |

   Each balance equals revenue minus expenditure to the published precision.
   The earlier years **are not** populated in this two-year overview snapshot; a separate, same-publisher historical API series is now curated below.

3. The BNS [FIN010100 PxWeb API metadata](https://statbank.statistica.md/PxWeb/api/v1/en/40%20Statistica%20economica/25%20FIN/FIN010100.px)
   was fetched successfully. The 31 indicator values include revenue code
   `0`, expenditure code `19`, balance code `30`, and ten
   **top-level spending functions** codes `20`–`29`. The four dimensions
   include a time variable; period `3` is **January–December** and unit
   `0` is **million lei**. Codes `1`–`18` are nested components
   that must never be added to headline revenue as if they were peers.

   `fetch/fetch_bns_budget.py` requests the 2016–2025 complete years
   from the table, validates code semantics, accounting identities and
   functional-class totals, then writes review files
   `fiscal/public_budget_from_bns.csv` and
   `fiscal/budget_summary_from_bns.csv`.

   **Verified end-to-end** from a GitHub Actions Ubuntu runner on
   **2026-10-26** ([live source execution, run 40267150660](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40267150660)).
   The official JSON-stat2 POST returned **10 complete annual rows, 2016–2025**,
   with all 13 selected indicators, in million nominal MDL. The guarded
   collector decoded the real response, checked `revenue − expenditure =
   balance` and summed all ten function categories for **every year**.
   The ten category sums equal headline spending to published precision.
   `fiscal/public_budget.csv` contains this carefully reviewed historical
   API edition, separate from `budget_summary.csv` and its separately
   released 2024/25 year-end overview.

   **2024 vintage difference is real and remains unmerged:** the API
   returns **122,962.7 million MDL spending / −12,624.2 balance**,
   while the BNS Finance overview labels **122,962.6 / −12,624.1**
   as 2024 FINAL. Difference **0.1 million MDL** on each measure;
   revenue is 110,338.5 in both. No administrative explanation is
   assumed. The 2024 CSV retains the live API values; the summary CSV
   retains the separately published final overview.

   **Another publication route differs in 2025:** the Ministry of Finance's
   [2025 SDDS workbook](https://mf.gov.md/ro/download/file/fid/38761?language=en)
   and BNS's [SDDS national summary](https://statistica.gov.md/SDDS/NSDP/)
   report **139,857.2** expenditure and **−14,255.2** balance (million MDL),
   versus BNS Finance/PxWeb **139,856.4 / −14,254.4**.
   The difference is **0.8 million MDL** on both measures, with
   revenue 125,602.0 unchanged. These editions are not substituted,
   reconciled by fiat, or called accounting errors without source notes.
   The 2025 national budget is still marked PRELIMINARY in the BNS
   overview; this historical API does not supply a year-by-year finality
   flag for the earlier rows.

## IMF comparable fiscal layer — two original vintages (2026-10-26)

The [IMF DataMapper v2 indicator catalogue](https://www.imf.org/external/datamapper/api/v2/indicators)
is authoritative for *which dataset an indicator actually comes from*.
The full live retrieval and validation ran in [GitHub Actions 40269456831](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40269456831).

- **`fiscal/weo_bal_debt.csv`**: `GGXCNL_NGDP` (general-government net
  lending/borrowing) and `GGXWDG_NGDP` (general-government gross debt),
  both from the **World Economic Outlook, October 2026**, in **percent of GDP**.
  It contains the 2006–2025 pre-projection WEO series; the 2026 values
  exist **only** as explicitly separated `*_proj` columns. 2025's
  pre-projection estimate is not described as an audited final national
  outturn. October-2026 WEO anchors: 2024 balance **−4.0%**, debt **38.8%**;
  2025 balance **−3.9%**, debt **39.2%**; 2026 forecast balance
  **−5.0%**, debt **41.8%**. The older December-2025 IMF mission release
  has different 2025 projected figures, which are **not** silently substituted.
- **`fiscal/fpp_finances.csv`**: `rev`, `exp`, `pb`, `ie`, from
  **Public Finances in Modern History (FPP), December 2025**, **NOT WEO**,
  four annual percent-of-GDP series from **2006 to 2024 only**. It has no
  2025 value. For each year, `rev - exp` reconciles to `pb - ie`
  within source rounding. The FPP 2024 balance implied from its own
  revenue/expenditure is **−3.884449% of GDP**, compared with the
  separate WEO October-2026 2024 balance of **−4.0%**. They are **different
  releases**, and this is not an unexplained algebra bug.
- `fetch/fetch_imf.py` validates the official dataset code, metadata
  source string, percentage-of-GDP unit, Moldova `MDA` country series,
  calendar-year coverage and 2026 forecast boundary. It writes **review
  sidecars only**; the two independently verified CSVs are committed
  curated snapshots.
- `research/render_imf_preview.py` plots the FPP historic indicators
  in its top two panels and the WEO Oct-2026 data, including an explicit
  dashed 2026 forecast, in its bottom two panels. This is a **research
  preview only**: not a production canonical `fiscal` plate, because a
  consistent all-indicator same-vintage fiscal-perimeter presentation
  has not yet been verified, and the required locale/content/render QA is
  still pending.

## Never conflate these series

### Budget perimeter

BNS/MF national public budget **cash execution** and IMF WEO
**general-government** fiscal accounts are not the same measure.
Until their perimeters, consolidation rules and vintages have been
reviewed, do not splice them or treat their differences as errors.
The canonical `fiscal` plate requires one verified comparable fiscal
perimeter and consistent source/vintage treatment. WEO and FPP have now
been fetched as **separately attributed** international layers; they must
not be casually presented as one WEO publication.

### Territorial and population definitions

The [2024 national census](https://statistica.gov.md/en/final-results-of-the-2024-population-and-housing-census-geographical-distributio-10121_61877.html)
reports **2,409,207 usual residents** as of **2024-04-08**,
with **157 localities not enumerated**. The official budget table says
its geographical coverage excludes the left bank of the Nistru and
Bender. These administrative boundaries must be checked
*per indicator*, not applied without evidence to all institutions.

WDI's mid-year 2024 population is **2,402,306**, and its 2025 value
**2,360,527**. A census usually-resident count with an April reference
date is not the same statistical object as a mid-year comparable
population estimate. **Do not calculate migration from their numerical
difference**. Rates using BNS death or crime counts need a matching
population denominator in place, period, and definition.

### Gaps and vintages

- WDI Gini, fertility, crude births/deaths and life expectancy stop in
  **2024**.
- WDI homicide ends **2023**, suicide **2021**, road deaths **2019**.
- International migrant stock exists only for **2010, 2015, 2020, 2024**
  in this WDI snapshot, never as a continuous annual series.
- WDI GDP growth **2025 = 2.416497%**, rounded by BNS to 2.4% in its
  release. The two data sources have distinct attribution.
- BNS 2025 fiscal outturn remains explicitly **preliminary** even though
  2025 is a fully elapsed calendar year. Completed period does not mean
  final publication.

## Quality gates already demonstrated and still pending

- Source CSV year grid, missing-value boundaries, API-shape checks, and
  national fiscal identity/status tests execute via the fork-only
  `.github/workflows/moldova-research.yml`.
- The CI is **offline**, does not contact source APIs, and **does not
  deploy**. Dedicated source-specific tests are tracked in GitHub Actions and include the complete 2016–2025 fiscal identity, source-vintage distinction, and the separate research-preview renderer.
- The live BNS fiscal POST **passed**, 2016–2025 functional cash data is
  committed with exact scope and per-source edition metadata; the 2024/25
  release differences remain documented instead of hidden.
- Pending: resolution of **why** the BNS/API and SDDS release editions differ,
  comparison with the Ministry's final yearbooks, national
  economics/trade/population/credit publishers, fully translated
  Romanian/English/Portuguese atlas, provenance, canonical plate rendering,
  and complete atlas regression. The research-only cash-budget preview
  is *not* a canonical published fiscal plate.

No invented rates, interpolated years, provisional-to-final upgrades
or inferred geography are accepted into published plates.


## National Bank of Moldova — official interest-rate and FX histories

**Verified 2026-10-26**, live exporter run
[40273821580](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40273821580).
The NBM's official [base-rate CSV](https://www.bnm.md/en/export-base-rates?limit=1000)
returned **106 rate-setting events** with effective dates between **2001-02-01**
and **2026-09-17**. The export uses semicolons and comma decimals and ends
with the literal publisher footer `Data source:;BNM`. The
`fetch/fetch_nbm.py` importer rejects unexpected schema, units, duplicates,
missing historical coverage, and implausible values.

`data/markets/policy.csv` contains **2006–2025** *completed years* in two
separate measures: the **calendar-day-weighted mean of the base rate in force
throughout the year**, and the **base rate on 31 December**. A mean of the
rate-change events would be wrong because decisions take effect on different
days. Example: 2024 mean **3.810519%**, year-end **3.60%**; 2025 mean
**6.134247%**, year-end **5.00%**. The base-rate series is a
**derived statistic from the official decision dates** and is identified
as derived; it is not described as a directly published annual average.

The official
[NBM average FX export](https://www.bnm.md/en/export-average-rates?date_from=01.01.2025&date_to=31.12.2025)
was queried independently for each completed calendar year 2006–2025.
`data/markets/usd_mdl.csv` stores **MDL per one USD**, derived from the
exported `Rates / Rate` nominal-unit pair where necessary, rather than a
reciprocal USD-per-MDL or an independently sampled spot quote. 2024 annual
average **17.7918 MDL/USD**, 2025 **17.3705 MDL/USD**. In contrast to the
policy mean, this is an average *published by NBM*, not an atlas-calculated
mean of daily observations.

The two files and the corresponding `*_from_nbm.csv` refresh sidecars
are never mixed with each other or with international redistributed
exchange-rate series. No 2026 partial year is presented as a full-year rate.
Their source and conversion semantics are pinned in
`tests/test_moldova_nbm.py` and `SOURCES.yaml`.

**Still absent:** household-specific loan stocks, nonperforming-loan
ratios, lending rates on a consistent borrower/currency perimeter,
10-year government bond yields and equity-index series. Those need their
own definitions and audit before producing the canonical `credit`
or `markets` 2×2 plates. We have **not yet registered Moldova as
a published country** with Romanian/English/Portuguese strings or rendered
the full atlas.


## Market source comparison preview — 2026-10-26

The three-language visualization in `research/render_markets_preview.py`
is **research only**, not an official published `markets` plate. Its
supporting `research/markets_catalog.json` covers Romanian, English and
Brazilian Portuguese. Input checks require complete 2006–2025 observations
from each separately labelled source and prevent accidental country mixing.

- **Panel 1, observed:** National Bank of Moldova (`markets/policy.csv`)
  **calendar-day-weighted effective base rate** next to World Bank WDI
  (`macro/economy.csv`, `FP.CPI.TOTL.ZG`) **annual CPI inflation**.
  Both are percentage rates; sources differ, and their arithmetic
  difference is **not** represented as a forward-looking real interest rate.
  In 2025 the respective rates are **6.134247%** and **7.759041%**.
- **Panel 2, pending:** no source-verified, methodologically compatible
  **10-year government bond yield** series staged.
- **Panel 3, observed:** official NBM **annual-average MDL per USD** is
  inverted and indexed as `100 × (MDL_per_USD_2006 / MDL_per_USD_year)`,
  so **higher = stronger leu**, with 2006 = 100. The 2006 quote
  **13.1319 MDL/USD** and 2025 **17.3705 MDL/USD** imply depreciation
  relative to the index base; the indexed series is a **derived measure**.
  The chart does **not** present MDL/USD nominal amounts as a strength index
  without this inversion.
- **Panel 4, pending:** no independently validated **main equity index
  converted to USD and compared with S&P 500** is staged. This missing
  slot is explicit; no proxy or synthetic market index was invented.

The visualization uses research-specific vertical scales so the observed
lines remain readable; this is explicitly disclosed and it is **not**
claimed to satisfy `PLATE_SPINE.md`'s atlas-wide canonical axis limits.
The expected deliverable in this phase is a faithful preview of the
verified data and the gaps. Partial 2026 observations are excluded.

### Candidate country identity, deliberately unregistered

`research/country_candidate.yaml` stages Moldova's flag-colour palette,
MDL currency, 2006–2026 comparison window, `ro/en/pt` locales,
trilingual SEO/source names and all presently used country-switcher
languages, **without** creating `countries/moldova/country.yaml`.
The project discovers published countries by that exact root filename,
so registering now would fail on **missing final chapters, provenance,
locale chrome and rendered assets** — not on currency syntax.

### Phase B shared number-format contract — 2026-10-26

**Implemented in the shared renderer, without registering Moldova:**
`core/numstyle.py` now declares `ro` with decimal comma and grouped
period (e.g. `1.234.567,89`), in line with Unicode CLDR ro-MD.
`core/i18n.py` handles Romanian numeric/percentage/large-unit plate labels,
recognises `MDL` value labels, and applies a nonbreaking space before the
percent sign. `core/sitebuild.py` declares the corresponding complete
Romanian page-affix table plus MDL currency forms for `ro`, `en` and
`pt`. Money quantities are always explicitly identified as MDL: the
local `lei` word is used for legibility in a mixed-country atlas, rather
than relying on an ambiguous standalone `L` symbol. For example,
`12.345,67 lei` and `291 mld. lei`. This deliberately chooses a full
unit word instead of the shorter CLDR abbreviation.

The regression suite `tests/test_moldova_ro_numstyle.py` checks card/plate
number agreement and loads the candidate under an isolated temporary
directory. The full existing `tests/test_numbers.py` suite is run in CI
to protect the original countries' presentation formats. Neither test
registers `countries/moldova/country.yaml`.

**Remaining promotion steps:** implement Romanian site language chrome,
full Romanian-English-Portuguese chapter catalogs (`i18n.json`, `ui.json`),
canonical plates and chapters, source provenance, committed rendered assets,
and the complete atlas regression suite. Only then move/copy the draft
into the country root as `country.yaml`. The existing three-language
research preview strings are **not** substitutes for final `i18n.json`.

## BNS absolute-consumption-poverty audit — 2026-10-27

The primary BNS national SDG progress report (2024 edition), indicator
**1.2.1**, printed page 17, reports national *absolute consumption*
poverty as percent of persons for **2014–2023**, respectively:
**29.5, 25.4, 26.4, 27.7, 23.0, 25.2, 26.8, 24.5, 31.1, 31.6**.
Publisher PDF: https://statistica.gov.md/files/files/SDG/docs/Raport_ODD_%202024.pdf

The BNS 2024 poverty publication independently confirms **33.6%** in
2024: https://statistica.gov.md/en/statbank-10101_61801.html .
The current 2025 BNS poverty indicator reports **31.1%** in 2025:
https://statistica.gov.md/ro/statistic_indicator_details/58
(source checked 2026-10-27). All numbers retain publisher precision:
**0.1 percentage point**, never artificial extra decimals.

The source's denominator is the **national household consumption-poverty
survey**, **not** an income-relative at-risk-of-poverty series, a World
Bank PPP dollar-line poverty rate, or WDI Gini. BNS explicitly says the
Household Budget Survey methodology was **revised in 2019**:
https://statistica.gov.md/index.php/en/statistic_indicator_details/3 .
The atlas consequently stores 2014–2018 and 2019–2025 in TWO distinct
CSV columns and plots **unconnected** lines: one must not infer a
comparable 2018-to-2019 percentage-point change across the method seam.
2006–2013 remain missing. Territorial and sampling concordance with
other international population/Gini sources remains unresolved.
This fills only the **national absolute poverty** slot; legal minimum
wage is still pending.

## WDI domestic private-sector credit, primary API — 2026-10-27

Verified directly from the World Bank WDI API, sourceid=2, MDA,
indicator FS.AST.PRVT.GD.ZS (lastupdated 2026-10-08). Evidence:
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40428253945 .
Sixteen annual values are observed (2010–2025); 2006–2009 are blank.
Source-precision anchors: 2010 29.497046%, 2024 29.333210%,
2025 33.593935% of GDP. No interpolation or artificial zeros.

**This is not household credit.** The numerator includes financial
corporations' claims on the broad private sector and can include
businesses or certain public enterprises. Credit is shown only in
the fourth credit contextual lens. Household debt, lending rates
and NPL ratios remain pending borrower-matched NBM official records.
Territory concordance with the national perimeter is not established.

## UNDP HDR 2025 Human Development Index — pinned historical release, 2026-10-27

The official UNDP HDR 2025 *complete composite indices time-series* CSV
(`MDA`, one row in its 206-country/aggregate release) was checked by the
read-only GitHub Actions publisher-audit job:
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40436229785 .
The downloaded publisher payload had SHA256
`61ed82e5b66c88dfca8ff9fac775c63981ecab6a254862af97acacc41c143117`.
The exact isolated audit file is archived in that run as
`moldova-undp-2025-hdi-source-review`; `fetch/fetch_undp.py` always writes
a review sidecar rather than silently modifying the curated `world/hdi.csv`.

The curated data covers **2006–2023 only** (18 values, original
three-decimal precision where present), from **0.711 in 2006** to
**0.785 in 2023**. Years 2024 and 2025 are explicitly missing; there is
no 2026 observation. The *complete 2025 vintage* says **2022 = 0.784**,
**2023 = 0.785**, a within-edition change of **0.001** index points.
Separately, [UNDP Moldova's 2025-05-06 press release](
https://www.undp.org/moldova/press-releases/age-ai-moldova-faces-key-choices-ensure-human-development-progress-says-new-undp-report)
says **2022 = 0.763**, **2023 = 0.785** (0.022 points). This **0.021
index-point conflict in 2022** is an official-publication/vintage
discrepancy, not a parsing error. We choose the **single pinned full-data
CSV edition** for every historical year, display its values and explicitly
disclose the press mismatch. No cross-edition splice, extrapolation,
causal interpretation, or year-2025 data claim is justified.

HDI is a composite of health, education and income measures (0–1).
It must not be confused with WDI GDP per person, household inequality
or the separately verified Transparency International Corruption Perceptions Index.
The UNDP historical national statistical perimeter is not assumed to be
identical to BNS's 2024 census or its budget execution geography.

## Transparency International CPI 2025 — audited historical workbook, 2026-10-27

The original 2025 publisher [CPI workbook](https://images.transparencycdn.org/images/CPI2025_Results.xlsx)
was fetched and decoded live, not copied from a third-party aggregator:
[read-only publisher audit 40440734736](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40440734736).
Pinned publisher SHA256: `543a2ad438c4ba9a70367ee10a44a2565de7fae6bcd8a8db0c23d0b993e46e31`.
The score series is exactly:

| Year | Score | Year | Score |
|---:|---:|---:|---:|
| 2012 | 36 | 2019 | 32 |
| 2013 | 35 | 2020 | 34 |
| 2014 | 35 | 2021 | 36 |
| 2015 | 33 | 2022 | 39 |
| 2016 | 30 | 2023 | 42 |
| 2017 | 31 | 2024 | 43 |
| 2018 | 33 | 2025 | 42 |

The 2012 index methodology redesign makes **2006–2011 unavailable** in a
methodologically comparable series; they stay blank (not zero). For 2025
the score is 42, versus 43 in 2024 and 42 in 2023. This is an expert/business
perception index of public-sector corruption (0–100; higher is cleaner),
**not** recorded criminal activity, criminal convictions or household
experience of bribery. Publisher: Transparency International, CC BY-ND 4.0;
[official methodology](https://www.transparency.org/en/news/how-cpi-scores-are-calculated).
The source perimeter is not assumed interchangeable with WDI GDP or BNS
census areas. `fetch/fetch_ti.py` writes a review-only sidecar and rejects
unreviewed publisher-byte changes; it never silently overwrites the curated
`world/cpi.csv`.

## BNS goods-export destinations, official EXT010200 table — 2026-10-27

The BNS Statbank [EXT010200.px](https://statbank.statistica.md/PxWeb/pxweb/en/40%20Statistica%20economica/40%20Statistica%20economica__21%20EXT__EXT010__serii%20anuale/EXT010200.px)
publisher table provides customs **goods** exports, in thousand US dollars,
for 89 coded country/group categories over 1997–2025. The independent
[primary-source audit 40446267708](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40446267708)
downloaded the 2006–2025 cube (1,780 partner-year cells) and retained the
original data and codebook as a read-only Actions artifact.
Source JSON-stat2 SHA256:
`5e1fc55f430c4e75a07c172b99a7b60501217fbfd6816e3dc5a5a32a97454fa4`.
Publisher metadata SHA256:
`1adfac120905d511a5246b524ed0a8c957e48da88fe9c9a41f4ee76a36d186e7`.

`data/trade/destinations.csv` contains observed 2006–2025 percentages of
**total customs goods exports** for the five largest *individual-country*
destinations in **2025**. The actual 2025 shares (source precision derived
as same-year country / BNS all-partner Total) are Romania **29.007597%**,
Turkey **9.950060%**, Italy **9.226514%**, Czechia **8.218765%** and Ukraine
**7.919070%**. Codes 35, 86, 27 and 17 refer to the first four; Ukraine's
country code is 11 through 2023, then 87 from 2024. The source changed
Ukraine from **CIS** to **other countries** group in 2024; that group's
aggregate is **not** added to any country share. Country groups 1, 13
and 42 reconcile to the official Total (0), accounting only for source
rounding. No partner-group membership series is spliced into a country
series. No years have been interpolated.

The 2025 **current Statbank** Total is **US$3,780.8639 million**; the
independent, *preliminary* BNS 2025 release reported US$3,782.7 million
(difference US$1.8361 million, **0.049%**), a documented edition difference,
not a licence to substitute an inconsistent denominator. BNS's customs
territory excludes companies on the left bank of the Nistru and Bender.
This is separate from WDI *goods and services* as percent GDP and is
never combined with it. The live source audit regenerates a
`destinations_from_bns.csv` sidecar and compares it byte-for-byte with the
committed curated dataset, failing closed on source revisions.

## Government statutory minimum wage and NBM annual USD conversion — 2026-10-27

This previously pending canonical `people.minimum_wage` slot now has
**three comparable full-calendar-year observations only (2023–2025)**.
The Moldovan Government approved a unified full-time gross monthly
statutory wage of **MDL 4,000 effective 2023-01-01**, **MDL 5,000
effective 2024-01-01**, and **MDL 5,500 effective 2025-01-01**:

- [2023 Government decision, 2022-12-07](https://old.gov.md/ro/content/salariul-minim-pe-tara-va-fi-majorat-pana-la-4000-de-lei)
- [2024 Government decision, 2023-12-06](https://old.gov.md/ro/content/salariul-minim-pe-tara-anul-2024-va-constitui-5000-lei-mai-mare-cu-1000-de-lei-decat-2023)
- [2025 Government decision, 2024-12-18](https://old.gov.md/ro/content/salariul-mediu-lunar-pe-economie-prognozat-pentru-anul-2025-va-constitui-16-100-de-lei)

The [Ministry of Labour's 2022-07-22 announcement](https://social.gov.md/comunicare/comunicate/din-1-septembrie-2022-salariul-minim-va-fi-unificat-in-toate-institutiile-din-tara/)
explicitly dates public/private sector unification to **2022-09-01**.
Even though the Government also reports MDL 3,500 for 2022, it is NOT
a full-year identical-scope legal floor. Years **2006–2022 remain blank**,
not zero, backfilled or joined to an earlier sector-specific minimum.

The conversion is strictly the shared-spine nominal **US$/month**,
computed `legal_MDL_per_month / NBM_annual_average_MDL_per_USD`
using separately audited official annual NBM quotes in
`data/markets/usd_mdl.csv`: 2023 **18.160700**, 2024 **17.791800**,
2025 **17.370500**. The curated
`data/people/minimum_wage.csv` retains the legal value, exact
annual-average FX denominator and a six-decimal derived USD value.
This is a nominal conversion of a *legal floor*, not an observed wage,
median earnings, tax net amount, PPP or real purchasing power.
The Government's 2026 MDL 6,300 minimum is deliberately omitted
because **2026 is not a completed FX calendar year**. No 2026 average
or projected wage is passed off as a full-year observation.
Territorial equivalence to the BNS household poverty survey and WDI
population series is **not asserted**.

The strict trilingual plate and site now distinguish this short valid
run from the excluded 2006–2022 history. `tests/test_moldova_minimum_wage.py`
checks the Government anchors, exact WDI/BNM-style currency arithmetic,
missing-year contract, manifest, source provenance, translations and plate.

## National Bank of Moldova — original prudential bank-wide NPL year-end reports, 2026-10-27

The NBM publishes **bank-wide**, **prudential** non-performing loans as a
share of total gross prudential loans, NOT borrower-defined household-only
NPL. Original year-end publisher reports give **6.4% at 2022-12-31**
([2022](https://bnm.md/en/content/financial-situation-banking-sector-year-2022)),
**5.6% at 2023-12-31** ([2023](https://bnm.md/ru/node/66762)),
**4.1% at 2024-12-31** ([2024](https://bnm.md/en/content/financial-situation-banking-sector-2024))
and **4.1% at 2025-12-31** ([2025](https://bnm.md/ro/node/69800)).
The 2022–24 reports expressly describe substandard, doubtful and
compromised credit; the 2025 report explicitly calls it prudential.
Overdue loans and IFRS-impaired loans are NOT synonymous with this ratio.
Banking assets span both corporations and households.

A publisher-publication distinction remains unresolved: the **2024**
release says 2023-to-2024 NPL fell **1.4 pp**, whereas the separately
published rounded 2023 rate **5.6%** less 2024 **4.1%** is **1.5 pp**.
Rounding or a later revision *might* explain it; neither is confirmed.
No numerical adjustment or alleged methodological break is fabricated.
The canonical panel connects 2022–23 and 2024–25 **within** their dated
source editions but does not connect the two pairs across that difference.
2006–2021 and partial 2026 remain blank; all values are December 31 levels,
never calendar-year averages. The data path is `credit/prudential_npl.csv`.
It is not a substitute for household debt stocks/new-loan rates, which
remain unavailable, or for WDI's broader private-credit lens.

The guarded standard-library source refresher `fetch/fetch_nbm_npl.py`
extracts one explicitly dated prudential NPL ratio from each original HTML
bulletin and checks all four year/precision anchors before writing ONLY
`credit/prudential_npl_from_nbm.csv` and an evidence JSON sidecar. It
refuses inconsistent dates, ambiguous metrics, and changed rates without
editing the canonical `prudential_npl.csv`. A fork-only read-only GitHub
Actions publisher audit uses that path for repeatable live verification.
