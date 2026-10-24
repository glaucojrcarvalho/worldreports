# Ukraine atlas — readiness tracker

Snapshot: 2026-10-24. Proposal: https://github.com/akitaonrails/worldreports/issues/1
Development is **fork-only** on `feat/ukraine-atlas`. Nothing here implies that
the entire atlas is publishable. `country.yaml` is intentionally withheld until
country-specific charts and localization pass the repository's gates.

## Curated source snapshots

| Source CSV | Publisher / exact measure | Covered calendar years | Validation |
|---|---|---|---|
| `data/markets/fx.csv` | NBU official daily USD/UAH, calendar-day annual average | 2006–2025 | Full daily coverage, quotation lots/units, spot anchors, offline tests |
| `data/markets/policy_rate.csv` | NBU key monetary-policy rate **effective on 31 December**, dated decisions | 2006–2025 | Publisher event chronology, year-end step-function carry, 2011 no-change check, source anchors and offline tests |
| `data/macro/reserves.csv` | NBU gross official international reserves, **year-end stock in US$ bn** | 2006–2025 | 20 total-asset January 1 snapshots mapped to previous 31 December; official NBU/IMF anchors, tests and live diff |
| `data/social/population.csv` | SSSU estimated present population **on 1 January**; NOT a census or year-end stock | 2006–2022 observed; 2023–2025 suppressed | Exact PNMI_01 national/age/gender/terrain key, January 2015 territorial seam, published `c` flags for 2023–25, live API CSV diff |
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

## Implementation milestones added (not publication-ready)

- Accepted ninth source snapshot: Ukrstat Jan-1 **present population**
  2006–2022 (17 observed integers), with publisher's suppressed c flags
  and empty values for 2023–2025. The 2015 occupied-territory scope break
  is explicitly drawn as separate index segments; no post-2022 census,
  rates from mismatched denominators, interpolation or refugee proxy.
- Demography panel 1 uses `index_2006` (2006=100, not FX inversion),
  and the chapter has Ukrainian/English/Portuguese January-date copy.
- Accepted eighth curated national series: NBU gross official reserve assets
  at every 31 December 2006–2025, valued in US$ billions. API snapshots
  labeled January 1 belong to the preceding year-end; verified against NBU
  and IMF published values. Plotted in `world.reserves`, with chart and
  chapter headline, maintaining the canonical US$ unit and log scale.
- Added a seventh accepted source dataset: official NBU policy rate at
  each calendar-year end, reconstructed from dated effective changes (2006–2025).
  The 2011 value legitimately retains the last 2010 decision; the chart
  explicitly distinguishes year-end interest from annual-average CPI.
- Market plate slot 1 and chapter card now draw/read the policy rate.
- Twelve declarative, canonical-spine chart builders in `plates.py`. Six
  source-backed slots use reviewed GDP, CPI, trade, investment and FX data;
  the other required slots are visibly research-pending.
- Chart lines split at missing years and documented territorial measurement
  seams rather than connecting data across a discontinuity.
- Twelve localized chapter cards in `chapters.py` and accessible page
  explanations in `ui.json` (Ukrainian, English and Portuguese).
- `i18n.json` translates canonical spine panel labels, units, source
  disclosures, chart subtitles and accessible plate descriptions into
  Ukrainian and Portuguese.
- `events.py` separates historically dated context from the changing
  geographic scope of statistical measurements.
- Shared Ukrainian `uk` number style, hryvnia affixes, native chart-unit
  wording and Cyrillic-capable fonts added without hard-coding Ukraine in core.
- Fork CI now covers offline source/translation tests and installs the
  declared atlas dependencies for Ukrainian number-style integration tests.
  The changes still need full suite rerun and real plate visual checks.

## The 12 spine chapters and remaining requirements

Here **accepted** means verified dataset, **pending** means not yet
chart-ready. One accepted panel does not make a completed chapter.

| Topic | Accepted partial coverage | Missing / definition verification |
|---|---|---|
| 01 Economy | Real GDP growth (2011–24); CPI annual-average inflation (2006–25) | GDP/person harmonized USD source; observed ILO unemployment and wartime gaps; 2006–10/2025 GDP continuity |
| 02 Fiscal | — | General-government revenue/expenditure, balance, primary balance, gross debt, interest on consistent perimeter; state cash budget is not accrual general government |
| 03 Spending | Whole-economy GFCF (2010–24) | COFOG-like functional spending, social protection shares, *government* GFCF. General government final consumption is not government investment |
| 04 Trade | National-accounts goods+services exports/imports and balance %GDP (2010–24) | Goods-only destination shares, product composition lens, early years/2025 continuity; distinct customs definitions |
| 05 Markets | Official USD/UAH annual-average FX (2006–25), canonical 2006=100 inverted chart, and NBU **year-end policy rate** (2006–25) alongside annual-average CPI | Comparable 10-year sovereign bond yield and main equity index in USD; year-end rate is not annual average or a bond yield; label unofficial market datasets |
| 06 Credit | — | Household debt/GDP, household lending rate, NPL/delinquency with explicit sector; check wartime method and data gaps |
| 07 People | Gini 2021=0.244 *anchor only*, not a curated series | Full historical national inequality and poverty, documented household survey suspension after 2021, statutory wage series in comparable USD |
| 08 World | Verified NBU official international reserves (US$ bn, **year-end stock**, 2006–25); chart and chapter headline wired | Comparable GDP US$ (not nominal UAH), UNDP HDI one vintage, Corruption Perceptions Index score; additional source reconciliation |
| 09 Demography | SSSU national **present population Jan-1** estimates (2006–22) and suppressed 2023–25 rows; 2006-base chart split at 2015 territorial seam | Total fertility, crude birth/death, natural increase and migration with matched population denominator; no verified 2023–25 headcounts |
| 10 Security | — | National homicide vs WHO/UNODC, suicide and traffic-death rates, non-interchangeable police/vital sources |
| 11 Mortality | — | Crude rate, valid 2015–19 excess mortality denominator, underlying-cause COVID deaths, optional national lens; wartime suppression |
| 12 Migration | — | Comparable arrivals/departures, stock by citizenship/birthplace; IDP/refugee administrative/survey estimates separate |

### Blocking integration constraints

- **Two shared comparison-scale conflicts:** 2022 GDP growth **−28.8%** vs the global **−18…18%** `economy.growth` axis; trade balance **−20.9087% (2023)** and **−20.3445% (2024)** vs the **−15…15%** `trade.balance` axis. Widen shared scales and regenerate/review all peers; never clip Ukraine or add a country-only axis.
- **Geographic coverage varies.** National accounts and CPI exclude different occupied/hostilities-affected territories across 2014/2022. Statistical scope is *not* Ukraine's internationally recognized territory.
- **Observed, estimated, and missing remain distinct.** SDMX metadata availability is not guaranteed observed data. Actual GDP API selection lacks 2006–10 (growth), 2006–09 (nominal), and 2025 even though a separate 2025 publication exists. No blind splicing or filling.
- **Ukrainian localization drafted, not render-approved.** The fork now has reusable `uk` number formatting, UAH currency affixes, Cyrillic fonts, `i18n.json`, trilingual chapter cards, page UI notes and accessible descriptions. Dedicated translation/locale tests exist, but completed rendered pages still need visual/font review. No `slug == "ukraine"` branch is permitted in shared core.
- **Research-stage rendering code is drafted; actual rendering/publishing is not started.** The fork now has `plates.py` (twelve spine-based builders), `chapters.py` (trilingual cards), `ui.json`, `i18n.json` and `events.py`. It still has **no** `country.yaml`, generated SVG/PNG plates or thumbnails, or `provenance.json`. Incomplete panels remain explicitly pending. Leave the country unregistered until the missing source, rendering, localization and visual gates are met.

### Merge readiness (all unchecked until truly run)

- [ ] Resolve/document every applicable canonical slot as observed, strictly unavailable, or disclosed pending with evidence and translations.
- [ ] Source-wise test each plotted fact and its denominators, gaps, vintages, break annotations and non-official labeling.
- [ ] Add Ukrainian/English/Portuguese localized plates and accessible page copy.
- [ ] Make generic shared axis/locale changes and regenerate every affected country.
- [ ] Run `make C=ukraine charts thumbs provenance`, `make site`, `make test`, `git diff --check`.
- [ ] Visually inspect all three language editions and comparison overlays; confirm every source and sidecar contract.
- [ ] Remove fork-only research workflow/probes, caches and unreviewed files from upstream diff; keep tested source manifests and supported fetchers.
- [ ] Review a complete PR description per `AGENTS.md`, then submit **one** PR only after Akita's issue feedback and completed validation.
