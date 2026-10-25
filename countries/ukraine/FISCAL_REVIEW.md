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

### Annual 2025 independently confirmed; earlier December edition revised

The Ministry of Finance's official **2025 annual consolidated-budget**
workbook (sheet `2025 рік`) is at:
https://www.mof.gov.ua/storage/files/4_%D0%97%D0%91_%D1%80%D1%96%D0%BA_%D1%81%D0%B0%D0%B9%D1%82_25.xlsx

| Official edition | Total, million UAH | Economic affairs, million UAH |
|---|---:|---:|
| MoF December 2025 | 5,999,467.11164619 | 258,106.09460700 |
| MoF annual 2025 | 6,006,387.27484437 | 264,998.32655720 |
| NBU annual 2025 (rounded) | 6,006,387.3 | 264,998.3 |

**All 10 functional groups and the total in the MoF annual edition
agree with NBU within 0.05 million UAH**, the NBU's reporting
precision. MoF publishes group `0100` as two lines (general public
services excluding debt payments + debt service). The two parts sum to
512,192.25565216 million UAH and reconcile to the NBU's 512,192.3.

The portal's [earlier December edition](https://openbudget.gov.ua/?budgetType=CONSOLIDATED&month=12&year=2025)
is **6,920.16319818 million UAH below the later annual edition**.
Most of that change (**6,892.23195020 million UAH**) is in
`0400` economic affairs. It is not a rounding problem, but a
**cross-publication revision**. The precise administrative
transactions responsible for the revision are not verified; we make
no claim about their cause. The December snapshot is preserved as
`fetch/reference_openbudget_2025.csv`; the later MoF source is
`fetch/reference_mof_2025_annual.csv`. The reference CSVs and
`fetch/audit_open_budget.py` compare both editions without replacing
any curated data. The three-language national preview discloses this
difference, not a supposed unresolved same-vintage discrepancy.

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
2. **December-to-annual explanation:** the exact official annual
   and December editions are now identified, and the later annual
   confirms NBU to one-decimal precision. A detailed administrative
   explanation of individual revised bookings is not proven and must
   not be invented. This is a documented publisher-edition seam, not a
   same-vintage cross-source blocker for a source-only PR.
3. **Final visual/editorial review:** confirm the generated Ukrainian,
   English and Portuguese charts and site/manifest statements against the
   exact branch tip, then attach the GitHub Actions gate result. Do not
   regenerate unrelated plates or modify the maintainer's repository.

The intended eventual PR is a **focused Treasury fiscal source
enhancement**, not a replacement 12-chapter Ukraine atlas. A site-ready
fifth canonical plate is explicitly **not** claimed yet.
