# Ukraine atlas — readiness tracker

Snapshot: 2026-10-24. Proposal: https://github.com/akitaonrails/worldreports/issues/1
Development is **fork-only** on `feat/ukraine-atlas`. Nothing here implies that
the entire atlas is publishable. `country.yaml` is intentionally withheld until
country-specific charts and localization pass the repository's gates.

## Curated source snapshots

| Source CSV | Publisher / exact measure | Covered calendar years | Validation |
|---|---|---|---|
| `data/markets/fx.csv` | NBU official daily USD/UAH, calendar-day annual average | 2006–2025 | Full daily coverage, quotation lots/units, spot anchors, offline tests |
| `data/macro/gdp_growth.csv` | SSSU prior-year **real volume index** −100 | 2011–2024 | Pinned SDMX dimensions, official anchors, live diff, missing years preserved |
| `data/macro/gdp_nominal.csv` | SSSU **current-price nominal GDP**, million UAH | 2010–2024 | Pinned SDMX dimensions and units, source anchors, live diff |
| `data/macro/cpi.csv` | SSSU headline CPI, **annual average versus preceding year** | 2006–2025 | Exact CPI base/frequency/commodity total, source anchors, live diff |
| `data/trade/trade_na.csv` | SSSU goods **and services** exports/imports, % same-vintage GDP | 2010–2024 | Checked positive import magnitudes, denominators, source anchors and live diff |
| `data/spending/investment.csv` | SSSU *whole-economy* GFCF, % same-vintage GDP | 2010–2024 | Checked source/denominator/sector and live diff |

All fetchers write review-only `*_from_<publisher>.csv` sidecars and
never overwrite the curated source of truth. Every accepted CSV is declared
in `SOURCES.yaml`. Live source preflight and Python 3.11/3.13 tests:
[GitHub Actions](https://github.com/glaucojrcarvalho/worldreports/actions/workflows/ukraine-preflight.yml).
Do not include temporary discovery workflow, raw probes or cache in the
eventual upstream PR.

## The 12 spine chapters and remaining requirements

Here **accepted** means verified dataset, **pending** means not yet
chart-ready. One accepted panel does not make a completed chapter.

| Topic | Accepted partial coverage | Missing / definition verification |
|---|---|---|
| 01 Economy | Real GDP growth (2011–24); CPI annual-average inflation (2006–25) | GDP/person harmonized USD source; observed ILO unemployment and wartime gaps; 2006–10/2025 GDP continuity |
| 02 Fiscal | — | General-government revenue/expenditure, balance, primary balance, gross debt, interest on consistent perimeter; state cash budget is not accrual general government |
| 03 Spending | Whole-economy GFCF (2010–24) | COFOG-like functional spending, social protection shares, *government* GFCF. General government final consumption is not government investment |
| 04 Trade | National-accounts goods+services exports/imports and balance %GDP (2010–24) | Goods-only destination shares, product composition lens, early years/2025 continuity; distinct customs definitions |
| 05 Markets | Annual official FX rate (2006–25), pending 2006-base inversion for chart | Policy-rate history vs inflation, comparable 10-year sovereign bond yield, main equity index in USD; label unofficial market datasets |
| 06 Credit | — | Household debt/GDP, household lending rate, NPL/delinquency with explicit sector; check wartime method and data gaps |
| 07 People | Gini 2021=0.244 *anchor only*, not a curated series | Full historical national inequality and poverty, documented household survey suspension after 2021, statutory wage series in comparable USD |
| 08 World | — | Comparable GDP US$ (not nominal UAH), UNDP HDI one vintage, CPI corruption score, official reserves US$ |
| 09 Demography | — | Territorial-scope-correct population, TFR, natality/mortality, net migration; 2022 displacement is not a census |
| 10 Security | — | National homicide vs WHO/UNODC, suicide and traffic-death rates, non-interchangeable police/vital sources |
| 11 Mortality | — | Crude rate, valid 2015–19 excess mortality denominator, underlying-cause COVID deaths, optional national lens; wartime suppression |
| 12 Migration | — | Comparable arrivals/departures, stock by citizenship/birthplace; IDP/refugee administrative/survey estimates separate |

### Blocking integration constraints

- **Two shared comparison-scale conflicts:** 2022 GDP growth **−28.8%** vs the global **−18…18%** `economy.growth` axis; trade balance **−20.9087% (2023)** and **−20.3445% (2024)** vs the **−15…15%** `trade.balance` axis. Widen shared scales and regenerate/review all peers; never clip Ukraine or add a country-only axis.
- **Geographic coverage varies.** National accounts and CPI exclude different occupied/hostilities-affected territories across 2014/2022. Statistical scope is *not* Ukraine's internationally recognized territory.
- **Observed, estimated, and missing remain distinct.** SDMX metadata availability is not guaranteed observed data. Actual GDP API selection lacks 2006–10 (growth), 2006–09 (nominal), and 2025 even though a separate 2025 publication exists. No blind splicing or filling.
- **Ukrainian localization not started.** Add reusable `uk` number formatting, UAH currency affixes, Ukrainian shared UI and country-specific i18n, fonts and accessibility checks. No `slug == "ukraine"` code in shared core.
- **Rendering/publishing not started.** The country has no `country.yaml`, `plates.py`, `chapters.py`, `ui.json`, `i18n.json`, `events.py`, output plates/thumbnails, or provenance yet. Leave country unregistered until consistently implemented.

### Merge readiness (all unchecked until truly run)

- [ ] Resolve/document every applicable canonical slot as observed, strictly unavailable, or disclosed pending with evidence and translations.
- [ ] Source-wise test each plotted fact and its denominators, gaps, vintages, break annotations and non-official labeling.
- [ ] Add Ukrainian/English/Portuguese localized plates and accessible page copy.
- [ ] Make generic shared axis/locale changes and regenerate every affected country.
- [ ] Run `make C=ukraine charts thumbs provenance`, `make site`, `make test`, `git diff --check`.
- [ ] Visually inspect all three language editions and comparison overlays; confirm every source and sidecar contract.
- [ ] Remove fork-only research workflow/probes, caches and unreviewed files from upstream diff; keep tested source manifests and supported fetchers.
- [ ] Review a complete PR description per `AGENTS.md`, then submit **one** PR only after Akita's issue feedback and completed validation.
