# Moldova — data notes and publication boundaries

**Research status: Phase A (not a published atlas).** Updated 2026-10-26.

This file records the meanings behind the staged observations in
[SOURCES.yaml](SOURCES.yaml) and the source probes in
[DISCOVERY.md](DISCOVERY.md). It is *not* evidence that Moldova's 12 plates
have been drawn or reviewed.

## What was actually collected

1. **World Bank WDI cross-country layer**: eight curated files, 20 distinct
   indicator codes, 2006–2025 grid, 386 numeric observations. API metadata
   `sourceid=2`, `countryiso3code=MDA`, `lastupdated=2026-10-08`.
   Every missing country/year cell remains blank, not zero or interpolation.
   `fetch/fetch_wdi.py` checks API schema and critical 2024–2025 anchors,
   then writes only `*_from_wb.csv` sidecars.

2. **Moldovan national budget (BNS / Ministry of Finance)**:
   `fiscal/budget_summary.csv` has **two observed calendar-year executions**:
   *2024 FINAL* and *2025 PRELIMINARY*, in **millions of nominal MDL**.
   The BNS [financial indicators page](https://statistica.gov.md/en/statistic_indicator_details/21)
   (updated 2026-08-28) reports:

   | Period | Revenue | Expenditure + non-financial assets | Balance | Edition |
   |---|---:|---:|---:|---|
   | 2024 | 110,338.5 | 122,962.6 | -12,624.1 | final |
   | 2025 | 125,602.0 | 139,856.4 | -14,254.4 | preliminary |

   Each balance equals revenue minus expenditure to the published precision.
   The earlier years **are not** populated in this two-year overview snapshot; a separate, same-publisher historical API series is now curated below.

3. The BNS [FIN010100 PxWeb API metadata](https://statbank.statistica.md/PxWeb/api/v1/en/40%20Statistica%20economica/25%20FIN/FIN010100.px)
   was fetched successfully. The 31 indicator values include revenue code
   `0`, expenditure code `19`, balance code `30`, and ten
   **top-level spending functions** codes `20`–`29`. The four dimensions
   include a time variable; period `3` is **January–December** and unit
   `0` is **million lei**. Codes `1`–`18` are nested components
   that must never be added to headline revenue as if they were peers.

   `fetch/fetch_bns_budget.py` requests the 2016–2025 complete years
   from the table, validates code semantics, accounting identities and
   functional-class totals, then writes review files
   `fiscal/public_budget_from_bns.csv` and
   `fiscal/budget_summary_from_bns.csv`.

   **Verified end-to-end** from a GitHub Actions Ubuntu runner on
   **2026-10-26** ([live source execution, run 40267150660](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40267150660)).
   The official JSON-stat2 POST returned **10 complete annual rows, 2016–2025**,
   with all 13 selected indicators, in million nominal MDL. The guarded
   collector decoded the real response, checked `revenue − expenditure =
   balance` and summed all ten function categories for **every year**.
   The ten category sums equal headline spending to published precision.
   `fiscal/public_budget.csv` contains this carefully reviewed historical
   API edition, separate from `budget_summary.csv` and its separately
   released 2024/25 year-end overview.

   **2024 vintage difference is real and remains unmerged:** the API
   returns **122,962.7 million MDL spending / −12,624.2 balance**,
   while the BNS Finance overview labels **122,962.6 / −12,624.1**
   as 2024 FINAL. Difference **0.1 million MDL** on each measure;
   revenue is 110,338.5 in both. No administrative explanation is
   assumed. The 2024 CSV retains the live API values; the summary CSV
   retains the separately published final overview.

   **Another publication route differs in 2025:** the Ministry of Finance's
   [2025 SDDS workbook](https://mf.gov.md/ro/download/file/fid/38761?language=en)
   and BNS's [SDDS national summary](https://statistica.gov.md/SDDS/NSDP/)
   report **139,857.2** expenditure and **−14,255.2** balance (million MDL),
   versus BNS Finance/PxWeb **139,856.4 / −14,254.4**.
   The difference is **0.8 million MDL** on both measures, with
   revenue 125,602.0 unchanged. These editions are not substituted,
   reconciled by fiat, or called accounting errors without source notes.
   The 2025 national budget is still marked PRELIMINARY in the BNS
   overview; this historical API does not supply a year-by-year finality
   flag for the earlier rows.

## IMF comparable fiscal layer — two original vintages (2026-10-26)

The [IMF DataMapper v2 indicator catalogue](https://www.imf.org/external/datamapper/api/v2/indicators)
is authoritative for *which dataset an indicator actually comes from*.
The full live retrieval and validation ran in [GitHub Actions 40269456831](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40269456831).

- **`fiscal/weo_bal_debt.csv`**: `GGXCNL_NGDP` (general-government net
  lending/borrowing) and `GGXWDG_NGDP` (general-government gross debt),
  both from the **World Economic Outlook, October 2026**, in **percent of GDP**.
  It contains the 2006–2025 pre-projection WEO series; the 2026 values
  exist **only** as explicitly separated `*_proj` columns. 2025's
  pre-projection estimate is not described as an audited final national
  outturn. October-2026 WEO anchors: 2024 balance **−4.0%**, debt **38.8%**;
  2025 balance **−3.9%**, debt **39.2%**; 2026 forecast balance
  **−5.0%**, debt **41.8%**. The older December-2025 IMF mission release
  has different 2025 projected figures, which are **not** silently substituted.
- **`fiscal/fpp_finances.csv`**: `rev`, `exp`, `pb`, `ie`, from
  **Public Finances in Modern History (FPP), December 2025**, **NOT WEO**,
  four annual percent-of-GDP series from **2006 to 2024 only**. It has no
  2025 value. For each year, `rev - exp` reconciles to `pb - ie`
  within source rounding. The FPP 2024 balance implied from its own
  revenue/expenditure is **−3.884449% of GDP**, compared with the
  separate WEO October-2026 2024 balance of **−4.0%**. They are **different
  releases**, and this is not an unexplained algebra bug.
- `fetch/fetch_imf.py` validates the official dataset code, metadata
  source string, percentage-of-GDP unit, Moldova `MDA` country series,
  calendar-year coverage and 2026 forecast boundary. It writes **review
  sidecars only**; the two independently verified CSVs are committed
  curated snapshots.
- `research/render_imf_preview.py` plots the FPP historic indicators
  in its top two panels and the WEO Oct-2026 data, including an explicit
  dashed 2026 forecast, in its bottom two panels. This is a **research
  preview only**: not a production canonical `fiscal` plate, because a
  consistent all-indicator same-vintage fiscal-perimeter presentation
  has not yet been verified, and the required locale/content/render QA is
  still pending.

## Never conflate these series

### Budget perimeter

BNS/MF national public budget **cash execution** and IMF WEO
**general-government** fiscal accounts are not the same measure.
Until their perimeters, consolidation rules and vintages have been
reviewed, do not splice them or treat their differences as errors.
The canonical `fiscal` plate requires one verified comparable fiscal
perimeter and consistent source/vintage treatment. WEO and FPP have now
been fetched as **separately attributed** international layers; they must
not be casually presented as one WEO publication.

### Territorial and population definitions

The [2024 national census](https://statistica.gov.md/en/final-results-of-the-2024-population-and-housing-census-geographical-distributio-10121_61877.html)
reports **2,409,207 usual residents** as of **2024-04-08**,
with **157 localities not enumerated**. The official budget table says
its geographical coverage excludes the left bank of the Nistru and
Bender. These administrative boundaries must be checked
*per indicator*, not applied without evidence to all institutions.

WDI's mid-year 2024 population is **2,402,306**, and its 2025 value
**2,360,527**. A census usually-resident count with an April reference
date is not the same statistical object as a mid-year comparable
population estimate. **Do not calculate migration from their numerical
difference**. Rates using BNS death or crime counts need a matching
population denominator in place, period, and definition.

### Gaps and vintages

- WDI Gini, fertility, crude births/deaths and life expectancy stop in
  **2024**.
- WDI homicide ends **2023**, suicide **2021**, road deaths **2019**.
- International migrant stock exists only for **2010, 2015, 2020, 2024**
  in this WDI snapshot, never as a continuous annual series.
- WDI GDP growth **2025 = 2.416497%**, rounded by BNS to 2.4% in its
  release. The two data sources have distinct attribution.
- BNS 2025 fiscal outturn remains explicitly **preliminary** even though
  2025 is a fully elapsed calendar year. Completed period does not mean
  final publication.

## Quality gates already demonstrated and still pending

- Source CSV year grid, missing-value boundaries, API-shape checks, and
  national fiscal identity/status tests execute via the fork-only
  `.github/workflows/moldova-research.yml`.
- The CI is **offline**, does not contact source APIs, and **does not
  deploy**. Dedicated source-specific tests are tracked in GitHub Actions and include the complete 2016–2025 fiscal identity, source-vintage distinction, and the separate research-preview renderer.
- The live BNS fiscal POST **passed**, 2016–2025 functional cash data is
  committed with exact scope and per-source edition metadata; the 2024/25
  release differences remain documented instead of hidden.
- Pending: resolution of **why** the BNS/API and SDDS release editions differ,
  comparison with the Ministry's final yearbooks, national
  economics/trade/population/credit publishers, fully translated
  Romanian/English/Portuguese atlas, provenance, canonical plate rendering,
  and complete atlas regression. The research-only cash-budget preview
  is *not* a canonical published fiscal plate.

No invented rates, interpolated years, provisional-to-final upgrades
or inferred geography are accepted into published plates.
