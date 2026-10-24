# Ukraine — source discovery (Phase A, work in progress)

Research date: 2026-10-24. Related proposal: https://github.com/akitaonrails/worldreports/issues/1

**Status: Phase A. Nine verified curated datasets: official NBU FX (2006–2025), NBU policy rate at year-end (2006–2025), NBU official reserve assets at year-end (2006–2025), Ukrstat real GDP growth (2011–2024), nominal GDP (2010–2024), annual-average CPI (2006–2025), goods-and-services national-accounts trade (2010–2024), whole-economy GFCF (2010–2024), and SSSU present-population January 1 counts (2006–2022 with 2023–2025 suppressed). Other chapters are pending. Ukraine is not registered or published yet.** This folder intentionally lacks `country.yaml` so it is not registered by `core.country.Country.all()` until the required datasets, plate implementation and localization are verified. Follow `SOURCING_A_COUNTRY.md`, `COUNTRIES.md`, `ADDING_A_COUNTRY.md`, `AGENTS.md`, `PLATE_SPINE.md`.

## First accepted curated series: official NBU USD/UAH (2006–2025)

On **2026-10-24**, the NBU `NBU_Exchange/exchange_site` API was successfully queried for **every year from 2006 through 2025**. All 7,305 daily observations passed date/year/currency/quote-unit validation (365 or 366 unique days each year), then were reduced to an **unweighted calendar-day mean of the official daily applicable rate** in UAH per one USD. This is a complete historical official FX series and is committed to `data/markets/fx.csv`, with its publisher, vintage and definitions in `SOURCES.yaml`.

Important quotation pitfall: the NBU's older USD observations have `rate=505, units=100, rate_per_unit=5.05` (2006-01-01), not 505 UAH per dollar. On 2014-01-01 the API has 799.3 per 100 USD, normalized to 7.993. On 2022-01-04 the daily per-unit rate was 27.2782. The derived **annual average** is a different metric: 2022 = 32.36835123 UAH/USD. The shared 2006=100 hryvnia-strength index is defined as `100 * avg_2006 / avg_year`; increasing UAH/USD means a weaker hryvnia and a lower strength index. No partial 2026 year is accepted.

The fetcher `fetch/fetch_nbu_fx.py` writes only the review sidecar `data/markets/fx_from_nbu.csv`. It does not automatically overwrite the accepted snapshot, and failure in any year does not write a partial dataset. Semantic tests pin calendar-day completeness and historical annual anchors.

## Live SSSU SDMX metadata verification — 2026-10-24

The official SDMX 2.1 dataflow endpoint returned **121 dataflows**. The following publisher IDs and revisions were extracted, not inferred from URLs:

| Topic | Exact SSSU dataflow | Version | Structure |
| --- | --- | --- | --- |
| Annual national accounts | `DF_ANNUAL_NATIONAL_ACCOUNTS` | `7.0.0` | `DSD_ANNUAL_NATIONAL_ACCOUNTS` |
| Consumer prices | `DF_PRICE_CHANGE_CONSUMER_GOODS_SERVICE` | `27.2.0` | `DSD_PRICE_CHANGE_CONSUMER_GOODS_SERVICE` |
| Population | `DF_POPULATION_STRUCTURE` | `8.0.1` | `DSD_POPULATION_STR` |
| Annual labour force | `DF_LABOR_FORCE_A` | `2.0.1` | `DSD_LABOR_FORCE_A` |
| Goods trade | `DF_EXTERNAL_TRADE_OF_GOODS` | `6.0.0` | `DSD_EXTERNAL_TRADE_OF_GOODS` |
| Deaths by cause | `DF_POPULATION_DEATH_CAUSE` | `3.0.1` | `DSD_POPULATION_DEATH_CAUSE` |

The national accounts DSD has dimensions in this order: `INDICATOR`, `PRICE_TYPE`, `REGION`, `BREAKDOWN_CATEGORY`, `BREAKDOWN`, `SECTOR_ECONOMY`, `FREQ`, `TIME_PERIOD`. Its concepts come from versioned SSSU concept schemes, not directly enumerated within the DSD.

Official, independently fetched [national-accounts codelists](https://stat.gov.ua/en/node/5823) establish the following IDs:

| Field | Codelist | Confirmed code/definition |
| --- | --- | --- |
| `INDICATOR` | `CL_ANNUAL_NATIONAL_ACCOUNTS_INDICATOR` (1.4.0) | `GDP_CUR_PRC` = gross domestic product; `GDP_PER_CAP` = GDP per capita |
| `PRICE_TYPE` | `CL_PRICE_TYPE` (1.3.0) | `CURR_PRICES` = current prices; `CONST_PRICES_2016` and `CONST_PRICES_2021` = constant price bases; `IDX_VOL_PY` = volume index vs previous year |
| `SECTOR_ECONOMY` | `CL_CIS_UA` (1.0.1) | `S_1` = total economy |
| `FREQ` | `CL_FREQ` (2.0.2; SDMX agency) | `A` = annual |
| `BREAKDOWN_CATEGORY` | `CL_ANNUAL_NATIONAL_ACCOUNTS_BREAKDOWN_CATEGORY` (1.0.0) | 12 published codes; requires selection of appropriate aggregate |
| `BREAKDOWN` | `CL_ANNUAL_NATIONAL_ACCOUNTS_BREAKDOWN` (1.0.0) | 1,603 codes, hierarchical sector/activity detail |
| `REGION` | `CL_KATOTTG` (1.2.19) | **Pending**: oversized API response with current bounded probe; do not guess all-Ukraine identifier |

The precise dataflow/code list references are verifiable in the GitHub Actions artifact for the [successful SDMX research run](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40074160250). **No GDP observations have yet been accepted** from this API. The next step is to establish `REGION`, aggregate `BREAKDOWN` values, all-series attributes and observed coverage via the availability/data endpoints, then cross-check growth (2022: −28.8%) on a consistent statistical vintage.

## Second accepted series: SSSU real GDP growth (2011–2024)

On **2026-10-24**, the exact SDMX-CSV v2 response for `SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0)` was extracted with dimensions `GDP_CUR_PRC.IDX_VOL_PY.UA00000000000000000._T._T.S_1.A`. Its 14 observed annual volume indices cover 2011–2024 inclusive; `UNITS_OF_MEASURE=1010` and `SCALE=0`. The derived annual growth is `volume_index_py - 100`:

- 2014: 93.4 → −6.6%; 2015: 90.2 → −9.8%.
- 2022: 71.2 → **−28.8%**, matching the SSSU official release.
- 2023: 105.5 → +5.5%; 2024: 103.2 → +3.2%.

The precise API response **did not include a 2025 row**, even though the catalog's availability metadata advertised a 2011–2025 window. A separate official 2025 release exists, but the series is not silently joined across publication vintages. There were also no rows for 2006–2010. The curated snapshot is `data/macro/gdp_growth.csv`; `fetch/fetch_sssu_gdp.py` can regenerate the review-only `gdp_growth_from_sssu.csv` sidecar with strict dimension, unit, coverage, and known-value validation. 

The publisher's **territorial scope** notes exclude Crimea/Sevastopol from 2010–2021, parts of occupied Donetsk and Luhansk from 2014–2021, and occupied or certain hostilities-affected regions from 2022–2024. These must be explained; they do not change Ukraine's internationally recognized borders. The 2022 contraction also exceeds the atlas's shared −18% GDP-growth scale and will require a shared scale review and peer-plate regeneration.

Source: [official SSSU SDMX documentation](https://stat.gov.ua/en/development-api/sdmx-api-v3) and [official GDP release](https://stat.gov.ua/uk/news/valovyy-vnutrishniy-produkt-ukrayiny-u-2022-2025-rokakh-dynamika-struktura-ta-chynnyky-zmin).

## Third accepted series: SSSU nominal GDP (2010–2024)

From the same official `SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0)` release, a distinct query with `INDICATOR=GDP_CUR_PRC`, `PRICE_TYPE=CURR_PRICES`, and the same total-economy/Ukraine/annual dimensions returned **15 observations for 2010–2024**. Its unit fields differ from the real growth index: `UNITS_OF_MEASURE=1090` and `SCALE=6`, meaning nominal GDP is reported in **millions of hryvnias**. Source anchors: 2010 = 1,079,346; 2022 = 5,239,114; 2024 = **7,662,376 million UAH**. These were checked against the actual SDMX-CSV and the public 2024 indicator release. No nominal 2006–2009 or 2025 row was returned by this exact selection.

The accepted `data/macro/gdp_nominal.csv` and corresponding `fetch/fetch_sssu_gdp_nominal.py` preserve the source vintage and territorial scope. The fetcher writes only a review sidecar. This nominal local-currency level may support appropriately denominated national indicators, but it must **not** be passed to an international GDP-in-US$ comparison slot as though it had that unit. A comparable USD measure requires separate source verification and a documented conversion.

## Fourth accepted series: official annual-average consumer price inflation (2006–2025)

The exact SSSU SDMX source `DF_PRICE_CHANGE_CONSUMER_GOODS_SERVICE(27.2.0)` was fetched for `INDICATOR=INDEX_CONSUMPRICE`, `BASE_PERIOD=PREV_YEAR`, `REGION=UA00000000000000000`, `GOODS_SERVICES_TYPE=0`, and `FREQ=A`. This is **yearly average consumer-price change compared with the previous year's average**, *not* December-to-December or month-to-month inflation.

The source returned all 20 calendar years 2006–2025 on `UNITS_OF_MEASURE=1010`, `SCALE=0`. The accepted `data/macro/cpi.csv` preserves the underlying index as well as `annual_inflation_pct = cpi_index_prev_year - 100`. Anchors: 2008=25.2%, 2015=48.7%, 2022=20.2%, 2024=6.5%, 2025=12.7%. The source publisher notes territorial collection limitations around 2014 and 2022. The sidecar fetcher is `fetch/fetch_sssu_cpi.py`; CI re-fetches and byte-compares it with the curated snapshot.

## Fifth and sixth accepted series: trade and investment (2010–2024)

The national-accounts dataflow also exposes *exports of goods and services* (`EXPORT_GOODS_SERV`), *imports of goods and services* (`IMPORT_GOODS_SERV`) and whole-economy gross fixed capital formation (`GRS_FIX_CAP_FOR`). We verified **15 observations each**, 2010–2024, with `PRICE_TYPE=CURR_PRICES`, the Ukraine total, `UNITS_OF_MEASURE=1090`, and `SCALE=6` (million UAH). All share the same publication vintage and territory as the curated nominal GDP denominator.

- `data/trade/trade_na.csv` carries exports, imports and their balance **as % of GDP**, plus the publisher's raw million-UAH amounts. Import observations are positive magnitudes even though the national-accounts label includes “(−)”; therefore `balance = exports - imports`. This is *not* customs goods-only trade or a balance-of-payments basis. For 2024, exports=2,273,580 million UAH, imports=3,832,450 million, nominal GDP=7,662,376 million, giving balance **−20.3445% of GDP**.
- `data/spending/investment.csv` contains whole-economy GFCF as a share of same-vintage GDP, with its raw amount. For 2024, GFCF=1,414,286 million UAH or **18.4575% of GDP**. This is **not** general-government GFCF, so the government-investment canonical slot remains unfilled.

The new fetcher `fetch/fetch_sssu_macro_ratios.py` validates all three official series and their denominator before staging separate review-only CSVs. CI re-extracts and byte-compares both with their accepted snapshots.

**New cross-country chart issue:** the current `trade.balance` canonical range is −15% to +15%. Ukraine's accepted national-accounts balance falls below the lower bound in 2022 (−16.5063%), 2023 (−20.9087%) and 2024 (−20.3445%). As with the 2022 real GDP contraction, fix the **shared scale** for all countries together before rendering Ukraine; never clip or privately rescale Ukraine's chart.

## Seventh and eighth accepted series: NBU policy and official reserve assets

- **Policy rate**, `data/markets/policy_rate.csv`: official NBU effective-date change log converted to the rate **actually in effect on each 31 December**, 2006–2025. The archive lists no new decision in 2011, so **7.75% from 2010-08-10** is the correct standing rate on 2011-12-31. Do not mistake this for an annual-average rate. Our markets panel displays it next to **annual-average** consumer-price inflation with both time bases disclosed. Curated anchors: 2022 25.00%, 2024 13.50%, 2025 15.50%.
- **Gross official international reserves**, `data/macro/reserves.csv`: NBU `res` monthly block, `id_api=RES_OffReserveAssets`, unit code `T071USD_7` (USD millions), converted to US$ billions for the canonical `world.reserves` log-scale panel. The **month label is the first day after the reference month**: `dt=20250101` is the 2024 year-end reserve stock **US$43.79535bn**, not a 2025 annual flow; `dt=20260101` gives **2025 year-end US$57.30241bn**. Both anchor totals agree with published NBU/IMF figures. All 20 distinct year-end dates 2006–2025 were checked. Fetchers stage sidecars only, and source CI verifies exact reproduction.

The 2022 policy rate and reserves series are *not* national GDP, household borrowing costs, budget financing, or census records. Their publisher and definition remain separate from SSSU national accounts.

## Ninth accepted source: present population on January 1, with explicit wartime suppression

On **2026-10-24**, the official SSSU SDMX-CSV national total `PNMI_01`
returned 17 unflagged integer observations (2006–2022) for
`INDICATOR=PNMI_01`, `REGION=UA00000000000000000`, `AGE=_T`,
`GENDER=_T`, `TERRAIN_TYPE=_T`, `FREQ=A`, `UNITS_OF_MEASURE=1760`
(persons), `SCALE=0`. On **2023, 2024 and 2025** it returned
`OBS_VALUE` genuinely empty with `OBS_FLAG=c`, citing Ukraine's
statistical-confidentiality and martial-law release restrictions.
Those years are committed with **empty numeric fields**, not zeros.

`data/social/population.csv` preserves all 20 rows and the flags.
`fetch/fetch_sssu_population.py` writes only an official-API review
sidecar; fork research CI has re-fetched it and verified its exact CSV diff.
Observations: **2006-01-01 46,929,525**, **2014-01-01 45,426,249**,
**2015-01-01 42,929,298**, **2022-01-01 41,167,335**.
The marked change in January 2015 is substantially influenced by
excluded occupied territory, **not** automatically deaths, emigration
or a population count for unchanged borders.
The canonical `demography.population` plate rebases Jan-1 present
population to **2006=100** and splits at 2015, with no continuation
for suppressed post-invasion years.

The SSSU national population flow `SSSU:DF_POPULATION_STRUCTURE(8.0.1)` resolves to `SSSU:DSD_POPULATION_STR(3.0.0)`. The publisher's explorer uses `PNMI_01` as an **estimated present-population candidate on 1 January**; `PNMI_02` is a distinct observed indicator code, but its exact label still requires a codelist check before acceptance. The official availability catalog advertises annual and monthly observations spanning 1989–2026, with national region `UA00000000000000000`; this metadata is **not evidence that post-invasion population observations actually exist for the required definitions**.

The SSSU explanatory metadata states that January 2015–2022 population excludes occupied Crimea/Sevastopol and certain Donetsk/Luhansk areas, and data described as January 2023 onward exclude occupied or hostilities-affected areas. These scopes cannot be joined into one uninterrupted all-Ukraine level, particularly for displacement-dependent rates. The original `fetch/probe_population.py` remains a research probe; the exact bounded national total `PNMI_01` has now been source-validated, curated, and tested. No post-invasion national population count was fabricated.

## Confirmed official access routes

* [State Statistics Service of Ukraine (SSSU) SDMX development API](https://stat.gov.ua/en/development-api) and [worked dataflow/DSD/data examples](https://stat.gov.ua/en/node/5823). SSSU documents a machine-readable SDMX 2.1 and 3.0 interface, including CSV/JSON/XML data. **Dataset-specific codes, dimensional keys and historical completeness are not yet established**; do not infer them from a web page title.
* [National Bank of Ukraine API developer documentation](https://bank.gov.ua/en/open-data/api-dev) and [historical daily currency query specification](https://bank.gov.ua/admin_uploads/article/Instr_API_KURS_VAL_data_Full_eng.pdf). The latter describes `https://bank.gov.ua/NBU_Exchange/exchange_site?start=YYYYMMDD&end=YYYYMMDD&valcode=usd&sort=exchangedate&order=asc&json`. Each observed `rate_per_unit` represents UAH per stated currency unit; verify `units` before transforming any series.
* [Open Budget](https://openbudget.gov.ua/en/about-portal), operated by Ukraine's Ministry of Finance, describes a public API; budget-classification releases are **not** automatically equivalent to general-government accrual data.
* [State Customs Service](https://customs.gov.ua/statistika-ta-reiestri) publishes customs trade; **goods** must not be presented as national-accounts goods and services.
* [Official SSSU GDP release](https://stat.gov.ua/uk/news/valovyy-vnutrishniy-produkt-ukrayiny-u-2022-2025-rokakh-dynamika-struktura-ta-chynnyky-zmin), dated 2026-03-24: real annual GDP growth −28.8% (2022), +5.5% (2023), +3.2% (2024), +1.8% (2025). Publication anchors; not yet traced to a single machine-readable national-accounts vintage.
* [Official SSSU Gini indicator](https://sdg.stat.gov.ua/uk/10-1-1/): observed Gini 0.244 for 2021; observations for 2022–2025 not available because household surveys were suspended. The project's Gini chart uses 0–100, so an accepted 0.244 observation converts to 24.4, with conversion documented.

## Canonical topic / source candidate / unresolved requirement

| Topic | Publishers or datasets to verify | Blocking definition or coverage test |
| --- | --- | --- |
| economy | SSSU annual national accounts and CPI; SSSU LFS; WB comparable GDP/person | Nominal/real vintage, CPI annualization, suspended observed unemployment; shared GDP scale |
| fiscal | MoF/Open Budget; IMF general government comparables | Cash vs accrual, consolidated government perimeter, debt vs guarantees, interest paid |
| spending | MoF functional classification; SSSU gross capital formation | Seven COFOG-like categories mapping, general-government GFCF |
| trade | SSSU goods+services in national accounts; Customs goods by partner/product; NBU BoP | Different trade definitions, calendar year vs YTD |
| markets | NBU official key rate, FX; domestic treasury bonds; equity market publisher | Comparable 10y yield, consistent price index and USD conversion; full FX sample |
| credit | NBU household credit/rates/NPL; BIS where appropriate | Household sector vs bank-wide, stock vs origination, NPL level > spine bound |
| people | SSSU living-condition survey, statutory wages; World Bank PIP | Survey suspended after 2021; Gini 0–1 vs 0–100; exchange-rate conversion |
| world | World Bank GDP and reserves, UNDP HDI, Transparency International CPI; NBU reserves | One report vintage, 2012 CPI method break, separate harmonized sources |
| demography | SSSU birth/death/fertility and population; alternative WB/UN populations | Territory/denominator discontinuity after 2014 and 2022 |
| security | Prosecutor recorded offences, SSSU vital deaths, WHO/UNODC | Police-recorded cases vs death certifications; no war casualties as ordinary homicide |
| mortality | SSSU ICD-10 cause of death; WHO | Underlying cause vs involving; excess mortality baseline and censored periods |
| migration | SSSU historical migration and national register, UNHCR/IOM wartime context | Events vs persons, IDPs/refugees vs residents, citizenship vs birthplace |

## Reproducible discovery: initial probe, not a fetcher for curated charts

Run `python3 countries/ukraine/fetch/probe_sources.py --live` only with network access. It queries the **publisher-documented** SDMX dataflow catalog and a bounded NBU USD/UAH historical daily interval, validates response signatures and saves a JSON report to `countries/ukraine/cache/` (ignored). The probe does not promote any data to `data/` or run during builds.

Run offline tests with `python3 -m unittest discover -s countries/ukraine/tests -v`.

## Validation gates before creating country.yaml

1. For each spine slot, record exact source URI/dataflow ID, dimensions, series code, unit, geography, denominator, time frequency, first/last observation, revisions and licenses in `SOURCES.yaml`.
2. Independently verify at least one observation against the publisher's official explanation or a second authoritative release. Distinguish publisher-page anchors from API-extracted facts.
3. Record failures: no measurement, temporarily withheld, retrieval blocked, definition unverified, incompatible proxy, or pipeline defect.
4. Curated CSVs must be reviewed snapshots; refreshers write sidecars, never overwrite accepted records.
5. Solve shared 2022 GDP comparison-scale conflict and Ukrainian language/currency support generically. Re-render/retest every peer affected by shared modifications.
6. Add `country.yaml` only with a coherent minimum atlas, full source manifest, plates/chapter catalogs, generated output and provenance; run the full suite before requesting an upstream PR.
