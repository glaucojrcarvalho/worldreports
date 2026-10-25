# Moldova — source discovery and perimeter audit

**Status:** research only, **not an atlas edition**.  
**Survey date:** 2026-10-26.  
**Proposed slug:** `moldova`. **National locale:** `ro` (Romanian), plus `en` and `pt`. **Currency:** MDL.  
**Repository baseline:** upstream `main` `ff9171c5290a68cfc92f3788542674f0a76dd13a`.  
**Suggested common window:** 2006–2026. **Last completed calendar year:** 2025; several 2025 releases remain *preliminary*, and 2026 is partial.

This is the first step described in [SOURCING_A_COUNTRY.md](../../SOURCING_A_COUNTRY.md), not a claim that Moldova's plates are source-complete. No `country.yaml`, curated CSV, graph, or shared code is introduced here; `Country.all()` intentionally does not register this folder. Do **not merge as a published country**. Once the audits below are complete, this document should be preserved as the edition's source-discovery history, and verified datasets and a complete `SOURCES.yaml` added before render code.

## 1. Source inventory — publications actually opened

| Institution | Exact source | What was confirmed | Remaining ingestion work |
|---|---|---|---|
| National Bureau of Statistics (BNS) | [Statbank](https://statbank.statistica.md/PxWeb/pxweb/en/) and [API description](https://statistica.gov.md/en/statistical-databank-78.html) | PxWeb topics and a per-table API are advertised | Identify **specific table IDs, selected dimensions, units, years, territory and API response**; test exports and snapshots |
| BNS | [2025 GDP release](https://statistica.gov.md/ro/produsul-intern-brut-in-trimestrul-iv-si-anul-2025-9497_62357.html) and [national accounts overview](https://statistica.gov.md/index.php/en/statistic_indicator_details/12) | 2025 GDP, annual real growth, and 2024 comparator | Select one consistent historical vintage in Statbank; do not build a whole time series from press releases |
| BNS | [National public budget indicators](https://statistica.gov.md/en/statistic_indicator_details/21) | 2024 final and 2025 preliminary revenue, expenditure, deficit and share of GDP | Identify underlying budget-execution tables and reconcile with Finance Ministry; separate national public budget cash perimeter from IMF general government |
| Ministry of Finance | [Budget execution visualisation](https://buget.mf.gov.md/en), [functional report generator](https://buget.mf.gov.md/en/rapoartebugetare), and [execution portal](https://peb.mf.gov.md/ro) | Portal exposes national budget history from 2016 and functional-report controls; execution portal identifies ministry as operator | Validate a machine-readable download for **annual completed** spending by function; do not treat current July 2026 YTD as full-year |
| National Bank of Moldova (NBM) | [Interactive statistical database](https://www.bnm.md/en/search?search_name=exchange+rate) and [average FX generator](https://www.bnm.md/bdi/pages/reports/dovre/DOVRE8.xhtml?lang=en) | Official exchange-rate, loans, deposit, reserves and policy-rate report routes exist | Resolve export POST/GET parameters, date semantics and daily-to-annual rules. No series downloaded yet |
| BNS | [2025 goods-trade release](https://statistica.gov.md/index.php/en/international-trade-of-goods-of-the-republic-of-moldova-in-december-2025-9539_62323.html) | Annual 2025 customs goods exports and partner-group share | Find partner table IDs, denominators, re-export handling, and distinct WB goods-and-services NA series |
| BNS | [2024 census: final geographic results](https://statistica.gov.md/en/final-results-of-the-2024-population-and-housing-census-geographical-distributio-10121_61877.html) | Census estimate and **explicit territorial exclusions** | Validate comparability of historic population, births and deaths before any per-capita calculation |
| BNS / National Public Health Agency | [Natural movement/cause-of-death source description](https://statistica.gov.md/index.php/en/statistic_indicator_details/33) and [2025 deaths](https://statistica.gov.md/ro/mortalitatea-generala-dupa-principalele-clase-ale-cauzelor-de-deces-in-anul-2025-9696_62463.html) | 2025 deaths are provisional, and publisher identifies underlying cause-of-death data | Get machine-readable ICD/category tables and denominators; distinguish mortality counts from modeled rates |
| IMF | [October 2026 WEO database](https://data.imf.org/datasets/WEO) | One dated, documented comparable vintage for GDP/inflation/fiscal aggregates | Pull Moldova-only series, observed-vs-projected flags, and source definitions; do **not** splice vintages |
| WHO | [Moldova country data](https://data.who.int/countries/498) | Comparable mortality and traffic series/metadata exposed | Verify downloadable yearly observations and definition for each indicator |
| World Bank | [Moldova population indicator](https://data.worldbank.org/indicator/SP.POP.TOTL?locations=MD) | Comparable country series is listed | Probe API, population/geographic definition, and cross-check against BNS territorial perimeter |

**Not yet audited:** national police/interior crime statistics, national poverty and Gini survey series, UNDP HDI vintage, Transparency International CPI workbook, government securities 10-year yield, equity-market benchmark, historical COFOG concordance, and individual migration definitions.

## 2. Reproducible source-snapshot checks

These are **published observations**, not a substituted time-series dataset. Amounts are **million nominal Moldovan lei (MDL)**.

| Year | GDP at current prices (BNS) | Real GDP growth (BNS, %) | National public budget revenue | Expenditure and non-financial assets | Budget balance |
|---|---:|---:|---:|---:|---:|
| 2024 | 323,932.5 | 0.3 | 110,338.5 | 122,962.6 | −12,624.1 |
| 2025 | 353,520.9 (preliminary) | 2.4 (preliminary) | 125,602.0 (preliminary) | 139,856.4 (preliminary) | −14,254.4 (preliminary) |

**Arithmetic assertions** (all from the publications above, checked to their displayed precision):

- 2024: `110338.5 - 122962.6 == -12624.1`; 2024 deficit ÷ 2024 GDP = **−3.897%** (BNS rounds to −3.9%).
- 2025: `125602.0 - 139856.4 == -14254.4`; 2025 deficit ÷ 2025 GDP = **−4.032%** (BNS rounds to −4.0%).
- 2025: GDP growth **+2.4%** is a change in *real* GDP, not the change between the two *nominal* GDP figures.

The [IMF's December 2025 Article IV mission note](https://www.imf.org/en/news/articles/2025/12/16/cs-republic-of-moldova-staff-concluding-statement-of-the-2025-article-iv-mission) reported a **2024 general-government fiscal balance of −4.1% of GDP**, while the BNS national public budget cash-basis snapshot above reports **−3.9%**. **Do not “reconcile” this away**: publication vintages, definitions and accounting perimeters must first be matched. For the canonical fiscal spine, test the IMF WEO general-government series; preserve the national budget series as a separately labelled national perimeter.

Other checked snapshots:

- **2025 goods exports (BNS):** **US$3,782.7 million**, of which **US$2,554.4 million** to EU-27 (**67.5%** of goods exports). The goods-only customs measure is **not** the spine's national-accounts goods-and-services share of GDP. Source: [BNS release, 2026-02-16](https://statistica.gov.md/index.php/en/international-trade-of-goods-of-the-republic-of-moldova-in-december-2025-9539_62323.html).
- **2025 registered deaths (BNS):** roughly **32,100**, explicitly *provisional*, about **1,500 fewer than 2024**. The release rounds counts and should not be used as an exact annual mortality denominator. Source: [BNS release, 2026-05-27](https://statistica.gov.md/en/general-mortality-by-main-causes-of-death-in-2025-9696_62463.html).
- **2024 census population (BNS):** **2,409,207** *usually resident* people on **2024-04-08**, including adjustment for estimated missed usual residents. Source: [final BNS results, 2025-07-15](https://statistica.gov.md/en/final-results-of-the-2024-population-and-housing-census-geographical-distributio-10121_61877.html).

## 3. Geographic scope is a non-negotiable gate

The 2024 census covered **1,525 of 1,682 localities**. It did **not** enumerate **157** localities not under the constitutional authorities' de facto control, including Transnistria/left bank of the Dniester and Bender (Tighina), with specific exceptions described in the original BNS notes. Its 2,409,207 usual-resident estimate is **not** an all-territories figure.

**Do not** compare a BNS observed resident-population numerator to any national/WB/UN series with a different territory and call the difference emigration or a demographic break. Each published count/rate should record `territory`, `population_definition`, `reference_date`, `vintage`, and `publisher`. When scopes differ, stage parallel series with a visible seam or leave a panel pending. Likewise, do not manufacture homicide/death rates using a population denominator that excludes places the numerator includes.

The 2014/2024 census comparison should only be charted from the BNS's *own comparable usual-residence estimates*, with the published 2024 geographic exclusions attached; population census counts are not interchangeable with population registers, citizenship stocks, or UN estimates.

## 4. Chapter-by-chapter source route (no fabricated completeness)

| Spine topic | Candidate accountable source | Audit status / obstacle |
|---|---|---|
| Economy | BNS annual national accounts + Statbank CPI/LFS; WB comparison | **Snapshot checked** (GDP 2024/25); historical table IDs/CPI and labour definitions pending |
| Fiscal | IMF WEO general government; BNS/MF national public budget as distinct layer | **Two years arithmetically checked**; fiscal-perimeter comparison and complete WEO vintage pending |
| Spending | MF functional execution 2016+; BNS whole-economy investment | **Portal confirmed**, functional-class download/COFOG seven-group crosswalk unverified |
| Trade | WB national accounts exports+imports of goods and services; BNS customs goods by partner | **2025 goods snapshot checked**; do not conflate customs goods and NA goods+services |
| Markets | NBM official policy rate, official daily/average MDL/USD, bonds; equity benchmark separately marked nonofficial | **Report routes found**, machine-readability and index availability untested |
| Credit | NBM household lending rates, loan stocks and NPL series | **Report routes found**, household vs all-sectors, stock vs flow and NPL denominators unverified |
| People | BNS household survey poverty/Gini, labour survey, statutory wage | **Discovery pending**; do not substitute modeled national Gini or a different poverty threshold silently |
| World | WB nominal GDP/reserves; UNDP HDI; Transparency International CPI | **Publishers identified**, editions, historic availability, source downloads untested |
| Demography | BNS census/Statbank births, deaths, fertility; WB/UN comparison | **2024 census checked**; ***territorial-scope gate*** mandatory |
| Security | National police/interior homicide counts vs WHO/UNODC, WHO traffic/suicide | **WHO source identified**; national definition and territory not verified |
| Mortality | BNS and National Public Health Agency deaths by cause; WHO comparable estimates | **2025 deaths snapshot checked**; ICD causes, age-adjustment and rates pending |
| Migration | BNS Statbank flows/stock; national register & border/permit agencies | **Statbank migration topic found**; Moldova is not an EU member; do not assume full EU Eurostat `migr_*` series availability |

## 5. Implement in this order

1. Resolve **geography first** for BNS national accounts, LFS, census, migration, mortality, and population denominator. Record published territory/definition; choose a base geography or explicit parallel series. Do not assume they match.
2. Probe concrete **BNS PxWeb tables** by API (dataset/table metadata, dimensions, unit, year span), the **NBM export generator**, Ministry functional reports, and World Bank/IMF series. Capture HTTP/content-type/schema/sample rows and record blocked sources as pending, not as zeros.
3. Construct `countries/moldova/SOURCES.yaml` **before** curated CSVs: file, publisher, exact route, units, frequencies, revision policy, scope, coverage, and `official: false` where appropriate.
4. Fetch machine-readable time series, write *sidecars only*, manually curate the accepted files and assert a publisher-to-publisher sample check without forcing differing definitions to agree.
5. Add `country.yaml`, Romanian/English/Portuguese catalogs and the canonical plates with the shared 2006–2026 spine, no country-specific shared-core hacks. Existing `core.numstyle` and currency-affix tests will require a **general** `ro` style and MDL support, implemented and tested without another country's hard-coded path.
6. Add Moldova-specific **semantic assertions** (budget arithmetic, 2024 census geography, trade denominator/2025 goods scope, full-year vs provisional), render all locales, run `make C=moldova charts thumbs provenance`, `make site` and `make test` before proposing a mergeable edition.

### Acceptance boundary

Research here is **verified at the level of publisher pages and the arithmetic above**, *not* at API-row completeness or a working published plate. A proper country PR must carry independently reviewable source CSVs and figures, provenance, international/national series labels, translation, and all passing quality gates. Leave missing topics documented rather than inventing a plausible proxy.
