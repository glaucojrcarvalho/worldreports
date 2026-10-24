# Ukraine — source discovery (Phase A, work in progress)

Research date: 2026-10-24. Related proposal: https://github.com/akitaonrails/worldreports/issues/1

**Status: Phase A. One verified national FX dataset is accepted (`data/markets/fx.csv`, 2006–2025); the remaining chapters are exploratory. There is no published country atlas yet.** This folder intentionally lacks `country.yaml` so it is not registered by `core.country.Country.all()` until the required datasets, plate implementation and localization are verified. Follow `SOURCING_A_COUNTRY.md`, `COUNTRIES.md`, `ADDING_A_COUNTRY.md`, `AGENTS.md`, `PLATE_SPINE.md`.

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
