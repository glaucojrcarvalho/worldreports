# Ukraine Treasury functional expenditure — focused follow-up research

**Status:** source parsed and definition-checked; **not yet an atlas contribution or PR**. The published Ukraine edition and maintainer's [issue #1](https://github.com/akitaonrails/worldreports/issues/1#issuecomment-6389662426) are the baseline, not our earlier unpublished 12-plate branch.

## Official source and exact extraction

- Computing institution: State Treasury Service of Ukraine, republished by the **National Bank of Ukraine** (`budget` cube).
- Source: `https://bank.gov.ua/NBUStatService/v1/statdirectory/budget?json`
- Filter: `freq=Y`, `dt=YYYY0101`, `mcr200p=CBU` (**consolidated budget**, not central/state `SBU`), `tzep=F_M_VC`, `id_api` begins `gf_budgtef_`.
- Twelve complete calendar years: **2014–2025**. No 2026 partial annual result is admitted.
- Output of `probe_treasury_functional.py`: a review-only staged CSV (132 rows: ten categories + total for each year), not the canonical `data/` folder.
- Unit: **millions of nominal Ukrainian hryvnia**. `20240101` in this annual cube is the record for calendar year **2024** (unlike NBU international reserves, where `20250101` represents the stock at 2024 year-end).

## Cross-checks

For **2024**, the consolidated-budget functional classification reports:

- **Defence:** 2,097,621.9 million UAH (`gf_budgtef_0200`)
- **Functional total, less interbudget transfers:** 4,441,364.6 million UAH (`gf_budgtef_Total_1`)

Ten functional components reconcile to the reported total within 0.3 million UAH rounding for each of 2014–2025, as independently inspected from the live endpoint on October 24, 2026.

Source definitions are kept distinct: `gf_budgtee_Total` is the **economic expenditure total** (2024 CBU 4,433,206.4 million UAH), not the functional total above. The two values must not be silently interchanged; further verification is needed to explain their accounting difference.

## What this does *not* establish

**CBU consolidated Treasury cash-budget expenditure is not the canonical accrual-basis general-government revenue, expenditure, fiscal balance or gross debt.** This source is a good candidate for a **functional spending** chapter or an explicitly labeled national cash-budget lens, NOT a substitute for general-government IMF fiscal aggregates.

The publisher's functional headings resemble COFOG group names, but the ten `gf_budgtef_` codes are Ukrainian Treasury classifications and require a documented mapping before using the atlas's seven shared category colors. Do not combine functional total, state-budget `SBU` expenditure and consolidated `CBU` totals.

## Follow-up required before upstream PR

1. Check the source's licensing terms, accounting definitions, interbudget transfer treatment and 2024 published annual Treasury table independently.
2. Decide whether the publisher's ten categories can be mapped losslessly into the seven canonical spending groups; retain unmappable categories explicitly rather than silently merging them.
3. Compare with the *published upstream* Ukraine country configuration and source manifests, and rebase only the compatible validated contribution—not the obsolete 12-plate implementation.
4. Add a source manifest, country-specific integration tests and trilingual editor notes to the updated upstream country tree.
5. Render and visually inspect all three locales, verify full-site provenance and run the complete CI suites, then submit one focused PR for Akita to review.

Run the local offline research tests with:

```bash
python -m unittest discover -s research/ukraine-fiscal/tests -p 'test_*.py' -v
```

For a live read-only refresh (does not modify published data):

```bash
python research/ukraine-fiscal/probe_treasury_functional.py
```
