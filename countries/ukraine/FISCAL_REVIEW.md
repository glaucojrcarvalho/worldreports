# Ukraine Treasury fiscal contribution — reviewer handoff

Status: **verified source contribution and national chart candidate; not a
published canonical fiscal chapter**. This review is scoped to the four-chapter
Ukraine implementation Akita already shipped. Do not merge the older
`feat/ukraine-atlas` branch or alter shared comparison scales.

## Why this source and what it measures

The computing institution is the **State Treasury Service of Ukraine**.
The National Bank of Ukraine republishes the Treasury cash-budget execution
cube at:

```
https://bank.gov.ua/NBUStatService/v1/statdirectory/budget?json
```

The committed `data/fiscal/treasury_functional.csv` retains **2011–2025**,
one row for each *calendar-year execution* and the original ten national
functional categories plus the Treasury functional total. Dimensions:

| Cube field | Accepted value | Why |
|---|---|---|
| `freq` | `Y` | Annual observation, never monthly or YTD |
| `mcr200p` | `CBU` | Consolidated budget, never `SBU` state budget |
| `tzep` | `F_M_VC` | Nominal million UAH, not % GDP |
| `id_api` | `gf_budgtef_0100`…`1000` | Ten direct national functional groups |
| `id_api` | `gf_budgtef_Total_1` | Total **less interbudget transfers** |
| `leveli`/`parent` | 2/`budgtef_Total_1` for groups; 1/`budgtef_Total_2` for total | Guards against hierarchy revisions |
| `dt` | `YYYY0101` | **January 1 stamps the prior year**: 20240101 = 2023 outturn |

The original research script had misread the last dimension and attributed
2023 values to 2024. It is **not** reused in this contribution.

The ten functional amounts sum to `Total_1` within 0.3 **million** UAH for
each of the 15 complete years (single-decimal source rounding). No interpolation,
splicing, annualization, currency conversion or inflation adjustment is used.

The data are **Treasury consolidated-budget cash execution**, not IMF GFS
general-government accrual expenditure, balance, debt or a validated COFOG
classification. These are substantively different fiscal perimeters, not
alternative labels for the same measurements. Consequently, the CSV is
**not read by any canonical fiscal/spending plate** and the trilingual
`treasury_preview.py` is an **offline supplementary review visualization**.

## Independent source-year and value anchors

Ministry of Finance, *Budget of Ukraine 2024*, functional expenditure tables
(section 2.3, pages 34–37):
https://mof.gov.ua/storage/files/Badgef%20of%20Ukraine2024.pdf

| Calendar year | Defence, million UAH | Functional total, million UAH |
|---|---:|---:|
| 2022 | 1,143,163.6 | 3,043,871.4 |
| 2023 | 2,097,621.9 | 4,441,364.6 |
| 2024 | 2,305,242.7 | 4,945,680.7 |

The last two years are pinned in `fetch/fetch_treasury.py` as exact
publisher-revision anchors. **Do not move those anchors forward one year.**

### Unresolved secondary-publisher difference

Independent official portal:
https://openbudget.gov.ua/?budgetType=CONSOLIDATED&month=12&year=2025

The 2025 Open Budget page shows total executed consolidated spending
**5,999,467,111,646.19 UAH** (5,999,467.11164619 million); NBU functional
`Total_1` gives **6,006,387.3 million**, a difference of
**6,920.18835381 million UAH**. Within that difference, national
code `0400` (economic affairs) accounts for **6,892.205393 million**.
Defence is effectively identical at NBU's rounding precision. The portal's
ten groups reconcile to its *own* total exactly.

This discrepancy is **not rounding**. Exact official explanation for the
portal/NBU version or accounting-base difference remains **unverified**.
The repository preserves both observations without replacing the
officially reviewed NBU vintage. The portal observations are stored as
`fetch/reference_openbudget_2025.csv`, and
`fetch/audit_open_budget.py` produces a deterministic diff sidecar. The
discrepancy is visible in Ukrainian, English and Portuguese descriptions
and on every review graph. The historical time series must not be described
as independently reconciled to the portal for 2025.

## Reproduction and fail-closed gates

The renderer uses **committed CSV only**. Fetchers cannot write to
`data/`. The NBU fetcher checks HTTP status, JSON MIME and encoding,
record schema, code lists, parent/level hierarchy, currency unit,
reporting dates, duplicates, gaps, numeric sanity, annual identities
and independent publication anchors.

To stage, *without promoting* source data:

```sh
python3 countries/ukraine/fetch/fetch_treasury.py
python3 countries/ukraine/fetch/audit_open_budget.py
```

The GitHub Actions workflow `ukraine-fiscal-review-fetch.yml` retrieves
the live source, runs the strict parser, computes a **full-history
byte-level diff and SHA-256s**, and uploads the staged CSV and diff. On
2026-10-24 the live result was **byte-identical** to curated history.
Its execution:
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40143540040

Offline checks and trilingual review artifacts:

```sh
python3 -m pytest countries/ukraine/tests/test_treasury.py countries/ukraine/tests/test_treasury_reconciliation.py -q
python3 -m pytest countries/ukraine/tests/test_plates.py tests/test_spine.py -q
python3 countries/ukraine/treasury_preview.py --output /tmp/ukraine-treasury-preview
python3 -m core.page --out _site
python3 -m pytest -q
node --test tests/js/*.test.js
```

`.github/workflows/ukraine-fiscal-candidate.yml` performs all offline
checks with the same CJK fonts as the upstream pages workflow. The
review-only generated SVGs and the cross-publisher diff are uploaded as
Actions artifacts; they are not copied into published `output/` or
`provenance.json` until an approved country plate actually consumes them.

## Publication gate / what is still missing

1. **Fiscal slot definition:** Ukraine's four canonical fiscal panels need
   their own harmonized, source-verified, same-unit general-government
   datasets and atlas-wide scale review before an IMF-style fiscal plate
   can be published. Treasury cash-budget figures must remain a separate
   national annex/lens, not a canonical substitute.
2. **2025 portal versus NBU:** obtain a publisher-level explanation or
   define a precise edition/vintage boundary. For source-only publication
   it may suffice to disclose the unresolved difference prominently;
   for a fully reconciled national panel it remains a caveat.
3. **Final visual/editorial review:** confirm the generated Ukrainian,
   English and Portuguese charts and site/manifest statements against the
   exact branch tip, then attach the GitHub Actions gate result. Do not
   regenerate unrelated plates or modify the maintainer's repository.

The intended eventual PR is a **focused Treasury fiscal source
enhancement**, not a replacement 12-chapter Ukraine atlas. A site-ready
fifth canonical plate is explicitly **not** claimed yet.
