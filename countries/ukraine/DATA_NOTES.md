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
- **Registered births/deaths, crude rates and total fertility**: now
  verified from official SSSU dataflows and the publisher's dimension and
  unit codelists. There are 20 annual observed live-birth and death counts
  for 2006–2025. Crude natality/mortality rates per 1,000 *present* people
  and total fertility per woman are observed only through 2021; in the
  2022–2025 SDMX rows the numeric field is BLANK and OBS_FLAG=c.
  The published rates are used directly, without combining the count with
  a World Bank/UN population denominator.
- **Territorial change in 2014 and wartime**: the civil-status register's
  geographic scope excludes some occupied areas from the 2014–2021
  dataflow footnotes, with further hostilities-affected exclusions after
  the full-scale invasion. Rate charts are split at 2014 and end in 2021.
  Wartime count levels are recorded in the source CSV, not plotted as
  rates, nor interpreted as a same-territory trend or war casualties.
- **Resident migration**: remains pending. Border crossing transactions,
  refugee stocks and internally displaced persons are not resident net
  migration on the canonical definition.
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

The new `fetch/fetch_vital_sdmx.py` accesses the publisher's five exact
annual vital indicators from its two SDMX dataflows. Its source selections
pin `SSSU:CL_POPULATION_INDICATOR(6.0.1)`:
`PNMI_17` (registered live births), `PNMI_19` (registered deaths),
`PNMI_32` (crude birth rate), `PNMI_46` (crude death rate), and
`PNMI_3341` (total fertility). Official measurement units are
`1760`=persons, `2860`=per 1,000 present people, and `2840`=per
woman. `CITIZENSHIP=_Z` is NOT APPLICABLE for the aggregate mortality
series — substituting `_T` returns empty data. All other total/not
applicable filters are pinned in the script. This fetcher never alters
the committed `data/demography/vital_ukrstat.csv`; live CI checks its
review sidecar against that CSV byte for byte. The source API may still
block other build networks, so drawing always uses offline inputs.

## Not drawn, on purpose

Fiscal, trade, markets, credit, security and mortality chapters are not
published at all this pass rather than assembled from a different perimeter
or a partner's mirror data. The blocked publishers and their exact failure
modes are in `SOURCES.yaml` `meta.pending`, and the page discloses the
absence in each locale.
