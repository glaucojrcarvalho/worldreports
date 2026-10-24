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

### Accepted nominal GDP level (2010–2024)

`data/macro/gdp_nominal.csv` comes from the **same SSSU annual national-accounts dataflow version** as real GDP growth, but a different price-type key (`CURR_PRICES` instead of `IDX_VOL_PY`). The publisher's unit is `UNITS_OF_MEASURE=1090` with `SCALE=6`, so values are millions of UAH. For example, 2024 = **7,662,376 million UAH**. Never label these current-price levels as real growth, constant-price output, or an international US-dollar comparable. Nominal 2006–2009 and 2025 are absent from the exact extracted series, and no source merging was performed.

The regional aggregate code `UA00000000000000000` identifies Ukraine in the source, while the source notes document periods when portions of internationally recognized Ukrainian territory were omitted from actual measurements. The curated file and sidecar refresher `fetch/fetch_sssu_gdp_nominal.py` retain these semantics separately from the real GDP series.

### Official monetary-policy decisions (NBU, 2006–2025)

The NBU's official [historical policy-rate archive](https://bank.gov.ua/en/monetary/archive-rish) publishes **effective-dated changes**, not annual average rates. For each calendar-year end, the accepted `data/markets/policy_rate.csv` selects the last decision *effective by 31 December*. The 2011 row records **7.75% effective from 2010-08-10**, even though there is no 2011 decision in the publisher's archive: this is an active standing rate, **not** interpolation, a provisional estimate, or an absent survey observation. The date used is retained in `last_change_date`.

The annual source anchors include **22.00% (2015), 25.00% (2022), 13.50% (2024) and 15.50% (2025)**. The editor's chart compares the December 31 NBU rate with SSSU **annual-average CPI inflation**, two explicitly different annual time conventions. Do **not** describe this as an annual-average rate, average borrowing cost, 10-year bond yield, real policy rate or a rate effective throughout the year. `fetch/fetch_nbu_policy_rate.py` stages an exact reviewer sidecar; the fork's live `[research]` CI checks byte-for-byte equality with the accepted CSV.

### Consumer prices, trade, fixed investment: verified sources

The accepted `data/macro/cpi.csv` uses SSSU's `INDEX_CONSUMPRICE` with annual frequency and `BASE_PERIOD=PREV_YEAR`, which measures **annual-average CPI compared with the previous calendar year's average**. Values are a base-100 index, converted to inflation by subtracting 100; the 2022 observation is 120.2 → 20.2%. This must not be confused with December-to-December inflation. The publisher's 2014/2022 territorial restrictions are carried in `SOURCES.yaml`.

`data/trade/trade_na.csv` uses SSSU goods-**and-services** national-accounts exports and imports (not merchandise customs or BoP) divided by the same-vintage current-price nominal GDP. Imported goods and services are reported as *positive magnitudes* despite the national-accounts minus label; the trade balance is exports minus imports. The 2022–2024 deficit ratios fall below the atlas-wide `trade.balance` axis of −15%; Ukraine-only clipping or rescaling is prohibited. All country comparison peers will need regeneration once the shared scale is widened.

`data/spending/investment.csv` is gross fixed capital formation for the **whole economy** as % of GDP, not general-government capital investment. Treat government consumption and government GFCF as distinct and leave their canonical panels pending until compatible source data are collected.

All three sources span their actual observed years only, with no automatic 2025 national-accounts substitution. Their fetchers write review sidecars; live CI compares re-fetched datasets against the curated snapshot byte-for-byte.

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

As of 2026-10-24, seven curated datasets have been verified: NBU USD/UAH annual averages (2006–2025); Ukrstat GDP growth (2011–2024), nominal GDP (2010–2024), CPI annual-average inflation (2006–2025), trade in goods and services as a share of GDP (2010–2024), and whole-economy GFCF as a share of GDP (2010–2024). These do not constitute a finished 12-chapter atlas; specific missing years, other chapters, and all full render/localization gates remain pending. See `DISCOVERY.md` and `SOURCES.yaml`.
