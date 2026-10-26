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
