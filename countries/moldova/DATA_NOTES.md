# Moldova — data notes and publication boundaries

**Research status: Phase A (not a published atlas).** Updated 2026-10-26.

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
   The earlier years **are not** populated in the curated table.

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

   **Not yet end-to-end verified:** the PxWeb browser table successfully
   displayed the variable selectors (including the correct Jan–Dec period,
   years, and units), but the exploratory interactive run did *not* return
   the cell data/export. Therefore the **full 2016–2025** fiscal history
   has **not** been collected, and the fiscal fetcher has only passed
   fixture-based offline decoder tests. No ten-function actual series has
   been curated.

## Never conflate these series

### Budget perimeter

BNS/MF national public budget **cash execution** and IMF WEO
**general-government** fiscal accounts are not the same measure.
Until their perimeters, consolidation rules and vintages have been
reviewed, do not splice them or treat their differences as errors.
The canonical `fiscal` plate requires the harmonised series to be
fetched and separately labelled.

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
  deploy**. Most recently, 30 source-specific tests passed.
- Pending: a live BNS data POST with validated 2016–2025 cells,
  reconciliation against the Ministry's final yearbooks, national
  economics/trade/population/credit publishers, fully translated
  Romanian/English/Portuguese atlas, provenance, plate rendering, and
  complete atlas regression.

No invented rates, interpolated years, provisional-to-final upgrades
or inferred geography are accepted into published plates.
