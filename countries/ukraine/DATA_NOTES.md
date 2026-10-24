# Ukraine — source and methodology notes (research phase)

**Not an assertion that the atlas is publication-ready.** These notes preserve the research decisions that must eventually be reconciled with `SOURCES.yaml` and the country-specific tests.

### Geography

Ukraine is defined with its internationally recognized territory, including Crimea and other territories under Russian occupation. A statistical observation, however, covers **only the people or production actually measured by its publisher**. Record each source's effective geographic scope and survey coverage, and do not combine a reduced-area numerator with an all-Ukraine denominator to compute rates. Method breaks around 2014 and 2022 require evidence per indicator, not a blanket splice.

### Live national-accounts statistical-scope metadata (verified 2026-10-24)

The State Statistics Service's [SDMX annual national-accounts metadata](https://stat.gov.ua/sdmx/workspaces/default:integration/registry/sdmx/3.0/data/dataflow/SSSU/DF_ANNUAL_NATIONAL_ACCOUNTS/7.0.0/*?c%5BINDICATOR%5D=GDP_CUR_PRC&c%5BPRICE_TYPE%5D=IDX_VOL_PY&c%5BFREQ%5D=A&c%5BSECTOR_ECONOMY%5D=S_1&firstNObservations=5) gives these explicit, publisher-authored scope exclusions:

- For **2010–2021**: excludes occupied Crimea and Sevastopol.
- For **2014–2021**: also excludes parts of occupied Donetsk and Luhansk oblasts.
- For **2022–2024**: excludes Russian-occupied territory and some locations with ongoing or prior hostilities.

The same API's availability metadata identifies **2011–2025** as the currently accessible time span for one annual total-economy GDP volume-index selection. This is **not** evidence that earlier years had the same underlying statistical geography, or that all intermediate years are populated. The 2025 territorial footnote needs separate confirmation before finalizing a comparable 2011–2025 annual series. Do not extrapolate this flow backward to 2006 or infer comparable denominators.

These are *statistical measurement boundaries*, not any change to Ukraine's internationally recognized borders. Such source metadata must travel with the CSV and appear in the atlas where series comparability is affected.

### Accepted GDP volume-index series (2011–2024)

The `data/macro/gdp_growth.csv` file contains the 14 available annual rows from SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0), using `GDP_CUR_PRC`, `IDX_VOL_PY`, `REGION=UA00000000000000000`, total breakdowns, `S_1`, and annual frequency. The source's annual volume index is reduced by 100 to calculate real growth (2022: 71.2 − 100 = **−28.8%**). This preserves the official observation and the exact methodological meaning of the number.

The live endpoint returned no values for 2006–2010 or 2025. Although metadata lists a broader availability window, **no observation is fabricated or spliced**. The growth series is reviewable against its sidecar from `fetch/fetch_sssu_gdp.py`. The publisher's stated territorial coverage varies after the 2014 and 2022 occupation/invasion shocks, and the published chart must annotate those comparability breaks. The 2022 contraction cannot fit the existing shared −18 to +18 growth range; a global range change requires regenerating and reviewing all affected peer charts.

### Observed data and missing values

2022–2025 Gini observations are **missing** in the SSSU SDG publication after suspension of the household survey, not equal to zero. The 2021 observation is reported as 0.244 on a 0–1 scale; a 0–100 display would be 24.4. Historical survey unemployment should not be joined to registered-unemployed counts or projections. Refugee registrations, border crossings, IDP survey estimates and national immigration flows must remain different populations and definitions.

### First curated publisher series (reviewed 2026-10-24)

`data/markets/fx.csv` contains official National Bank of Ukraine daily-rate **calendar-year averages**, 2006–2025. The country fetcher requests every full year, checks each daily exchange date, ISO 840 currency, quote units (some records represent 100 USD), nonzero rates, and independent dated spot anchors, then stages `fx_from_nbu.csv`. The accepted CSV is kept unchanged unless reviewed. The 20-year coverage of 7,305 daily dates was verified during initial extraction; derived annual averages are not end-of-year rates or representative of executable market quotes.

This rate series alone does not make the Markets plate complete; the 10-year sovereign bond yield and equity index remain pending. For the canonical currency panel, the annual average UAH per USD must be **inverted and rebased** to 2006=100 before plotting, so the line rises when the hryvnia strengthens.

## Cross-country comparison contract

The upstream `core/spine.py` slot `economy.growth` is bounded at (-18, 18). SSSU's real GDP growth for 2022 is -28.8%; a valid Ukraine plate therefore requires a shared scale decision and re-generation of all compared peers. Do not clip, substitute a proxy, hide the value, or widen the axis only for Ukraine.

### Government, trade and money

Ministry of Finance state-budget cash reporting, state/state-guaranteed debt, and IMF general-government accounts are not interchangeable. Customs goods trade is not the national accounts/BoP goods-and-services total. Rates and FX stocks or daily market prices must never be labelled as completed annual flow values. Check whether the NBU FX rate is expressed per one currency unit; the API includes a `units` field.

### Source workflow

The official publisher is preferred where it computes the measure. Keep harmonized/market providers separately labelled and `official: false` where required. A successful transport probe only confirms schema access—not the statistical meaning, revisions, coverage or fitness of a series. Network I/O belongs exclusively in `fetch/`, output in review-only sidecars or cache, and chart render remains offline.

As of 2026-10-24, two curated datasets have been verified: NBU USD/UAH annual averages (2006–2025) and SSSU GDP real growth from one annual SDMX dataflow (2011–2024). GDP 2006–2010 and 2025, plus CPI, population, fiscal, migration and the other statistical series, remain pending. See `DISCOVERY.md` and `SOURCES.yaml`.
