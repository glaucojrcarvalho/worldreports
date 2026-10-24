# Ukraine — source and methodology notes (research phase)

**Not an assertion that the atlas is publication-ready.** These notes preserve the research decisions that must eventually be reconciled with `SOURCES.yaml` and the country-specific tests.

### Geography

Ukraine is defined with its internationally recognized territory, including Crimea and other territories under Russian occupation. A statistical observation, however, covers **only the people or production actually measured by its publisher**. Record each source's effective geographic scope and survey coverage, and do not combine a reduced-area numerator with an all-Ukraine denominator to compute rates. Method breaks around 2014 and 2022 require evidence per indicator, not a blanket splice.

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

As of 2026-10-24, the official USD/UAH annual series is accepted and validated against complete NBU daily API responses; most other exact national dataset IDs and historical series are **pending live response validation**. See `DISCOVERY.md` and `SOURCES.yaml`.
