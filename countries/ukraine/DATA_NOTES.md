# Ukraine — what the numbers mean

The research record is [DISCOVERY.md](DISCOVERY.md); the manifest is
[SOURCES.yaml](SOURCES.yaml). This file carries the judgement calls the
plates depend on.

## Territory

Two different territories are drawn, and never joined:

- **Ukrstat's register** (`demography/population_ukrstat.csv`) excludes the
  temporarily occupied territories from 2015 — Crimea and Sevastopol, and
  from 2022 the occupied parts of Donetsk, Luhansk, Kherson and Zaporizhzhia
  oblasts. The publisher's own note says so. The step from 45,426,249 (2014)
  to 42,929,298 (2015) is that perimeter change, not a demographic event,
  and is annotated on the plate. The series ends at 1 January 2022.
- **The World Bank / UN estimate** (`demography/population.csv`) includes
  Crimea throughout (2021 = 44,298,640; 2025 = 38,980,376).

The atlas draws both as separate labelled lines. No value from one is ever
used to fill a year of the other.

## The shared comparison scale was widened

Ukraine's 2022 real GDP growth is −28.76% (World Bank national accounts;
the IMF WEO says −28.8 on its own vintage). That is outside the atlas-wide
range the economy topic used before this country joined (−18 to +18), and
the register's 2022 index (79.8 on 2006 = 100) is outside the population
slot's old floor of 80. Per PLATE_SPINE the range is widened once in
`core/spine.py` — growth to (−32, 18), population to (75, 150) — and every
country carrying those topics is regenerated. No country overrides its own
scale.

## Derived series

**The price level** on the people plate is derived, not published: the
annual CPI inflation rates in `macro/economy.csv` are chained from 2006 =
100 (`level[t] = level[t−1] × (1 + cpi[t]/100)`), one vintage. 2025 lands at
about 1,006, i.e. 10.1× the 2006 price level. The plate says it is derived.

## Gaps, and why they stay gaps

- **Unemployment** stops in 2021. The World Bank's ILO-modelled estimate has
  no value for 2022–2025 because no labour-force survey was run in the war
  years. The rows are blank, not zero, and the plate labels its last value
  as modelled.
- **Gini** stops in 2020: the household survey behind it was suspended.
- **Births, deaths, fertility, migration**: Ukrstat publishes them to 2022,
  but the cached SDMX dataflow's dimension code list does not identify the
  total series unambiguously. That is incomplete definition research, and
  the panels stay pending rather than drawing a series that might be a
  sub-slice (for example, births to one citizenship group).
- **Poverty, minimum wage**: the survey has not published since 2021; the
  statutory minimum is set in hryvnia and no official monthly US$ series is
  staged.
- **Corruption Perceptions Index**: Transparency International's workbook
  answers 403 to this network.

Each pending slot names its reason on the panel and in `ui.json`; none is
filled with a proxy.

## Fetchers

`fetch/fetch_comparables.py` writes the World Bank, IMF and UNDP sidecars;
`fetch/fetch_ukrstat.py` writes the SSSU population sidecar from the SDMX
dataflow payload (offline from the cache, since stat.gov.ua answers 403 to
this network). Both write `*_from_*` review sidecars only — the curated
CSVs are a separate reviewed step — and both are re-runnable: two offline
runs produce byte-identical sidecars.

## Not drawn, on purpose

Fiscal, trade, markets, credit, security and mortality chapters are not
published as plates yet. Verified Treasury functional expenditure is now curated
for a separate cash-budget enhancement, but it does not establish canonical
IMF fiscal or COFOG slots; no misleading plate has been added. The blocked publishers and their exact failure
modes are in `SOURCES.yaml` `meta.pending`, and the page discloses the
absence in each locale.

## Treasury fiscal data — annual reference dates and scope (2026-10-24)

The **NBU republishes State Treasury cash-budget execution**, not harmonised
IMF general-government accrual statistics. The reviewed data in
`fiscal/treasury_functional.csv` are **2011–2025 consolidated budget (CBU)**
functional outturns, measured in **million nominal UAH**, split into the ten
original top-level Ukrainian budget classification codes `0100`–`1000`.
The reported `gf_budgtef_Total_1` is **expenditure excluding interbudget
transfers**, not an additional category. National functional classes must
not be treated as a checked mapping to the atlas's seven COFOG-like groups.

**Critical date mapping:** in the NBU `budget` cube, an annual record
`dt=20240101` reports the **2023** calendar-year execution.
`dt=20250101` reports **2024**. The previous research probe mistakenly
treated the NBU January date as the same calendar year. It was corrected
rather than imported wholesale. The source date is kept as a separate
column, so this rule can be audited without inferring it from a chart.

The independent cross-check is the **Ministry of Finance** statistical book
[Budget of Ukraine 2024](https://mof.gov.ua/storage/files/Badgef%20of%20Ukraine2024.pdf),
especially section **2.3, pages 34–37**, with:
- **2023:** defence 2,097,621.9 million UAH; consolidated spending
  4,441,364.6 million UAH.
- **2024:** defence 2,305,242.7 million UAH; consolidated spending
  4,945,680.7 million UAH.

All 15 annual ten-category sums reconcile with the same-year functional
total within **0.3 million UAH** (source presentation rounding).
An additional independent source check: the official
[Open Budget consolidated portal](https://openbudget.gov.ua/?budgetType=CONSOLIDATED&month=12&year=2025)
lists **2025 defence = 3,069,857,418,255.98 UAH**, matching the NBU
defence series to 0.1 million. But its displayed **total =
5,999,467.1 million UAH**, versus the NBU functional reported total
**6,006,387.3 million UAH**. The **6,920.2 million UAH difference
is unresolved** (potentially a revision or extraction-vintage issue).
A second, **non-official** public presentation of Treasury totals,
[index.minfin.com.ua](https://index.minfin.com.ua/ua/finance/budget/cons/expense/2025/),
also lists the 5,999,467.1 million total. The 2025 mismatch is
**predominantly in code 0400 (economic affairs)**: NBU
264,998.3 million vs the other presentation's 258,106.1 million
(a 6,892.2 million difference). Remaining differences are
minor: general public services +11.7, culture/recreation +0.3,
and education +16.1 million UAH on the NBU side.
Older years also show deviations in totals, e.g. 2023 +424.4
and 2024 +1,654.6 million UAH (NBU less the non-official index).
The publisher's revision/vintage and inclusion rules must be
confirmed with the Treasury before presenting this series as an
officially *reconciled* outturn. Neither source is silently swapped,
and these gaps are NOT rounding.

The economic-classification total `gf_budgtee_Total` does not agree
exactly (for example, the 2023 fiscal-year observation is 4,433,206.4
million UAH); its variance is not discarded or blended into the
functional time series. Revenue / balance / financing classifications
must receive their own identity verification before use. The signed
`gf_budgtfd_total` is financing with deficit-positive sign — **not** a
general-government primary balance. We stage none of those as fiscal
accounts yet.

**Discontinuities and limits:** the wartime fiscal envelope and territory
of execution may change around 2014 and 2022. This is not a constant-
territory panel; nominal expenditures may change because of prices,
administrative scope or budget priorities. Values are not inflation
adjusted, expressed as GDP shares, reconstructed, interpolated or
converted to USD. Do not infer constant-definition expenditure growth.
The national functional categories remain supplementary **source material**
until a defensible national-only plate is implemented and visually reviewed.

`fetch/fetch_treasury.py` re-fetches the full JSON cube and writes
`fetch/cache/treasury_functional_from_nbu.csv` **only** (a review sidecar).
It validates JSON and field names, annual dates, unit, parent/category
hierarchy, duplicated codes, annual gaps, numeric sanity, Ministry of
Finance anchors and within-year reconciliation. It never overwrites
the committed source-of-truth CSV. Compare the entire historical sidecar
to the curated CSV before accepting revisions.
