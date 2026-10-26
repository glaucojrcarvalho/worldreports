# Moldova Phase B/C handoff — draft plates

**2026-10-27**. The fork-only branch `research/moldova-source-audit` now
contains `countries/moldova/plates.py`: **12 declarative spine plates**
covering 12 standard topics, with real WDI, NBM, WEO, FPP observations and
explicit `ctx.pending` slots for definitions/sources not yet verified.

## What was implemented

- Macro growth, income, inflation and ILO-modelled unemployment.
- IMF FPP December-2025 revenue, spending, primary balance and interest
  **separate** from IMF WEO October-2026 overall balance/debt.
  Both are explicitly named; 2026 WEO forecast columns are never rendered
  as historical annual observations, and FPP's 2025 gap stays empty.
- WDI full-economy investment; every national functional BNS budget share
  remains pending until same-scope GDP in MDL and accounting mappings pass.
- Goods-and-services exports, imports, and the **complete canonical
  trade deficit series**. A verified **−52.8% GDP in 2008** required the
  **shared** trade.balance range to change from [-30,40] to [-60,40],
  not a Moldova-only override.
- The draft English CI uncovered two other globally incompatible low
  levels: **US$3.408bn GDP** and **US$0.775bn reserves** in 2006.
  The same shared spine now starts world.gdp at **US$1bn**, and reserves
  at **US$0.1bn**, updating both log tick ladders.
  **GLOBAL REGEN GATE:** All existing countries' world and trade plates,
  thumbs, site and provenance must be regenerated together and visually
  checked before registration/merge. These changes have been committed
  only in the research fork branch; existing generated peer assets may
  still use the old axes until that gate is complete.
- Official NBM day-weighted effective policy averages and WDI CPI,
  official annual-average MDL/USD **inverted** to 2006=100 strength,
  pending 10-year yields/equities.
- WDI Gini, GDP in US$, reserves, midyear-population index, fertility,
  crude birth/death rates, UN-modelled net migration over matching WDI
  population, UNODC/WHO safety rates and life expectancy.
- **UN international migrant stock shown as scatter snapshots in a lens**
  (2010, 2015, 2020, 2024), not a line or an asserted foreign-born series.
- `tests/test_moldova_plate_design.py` checks 12 topics, cross-source
  boundaries, cash-vs-GDP integrity, projections, FX inversion, snapshots
  and shared spine range correctness.

## Publication status and next steps

Moldova is **still not registered** because `country.yaml` is absent.
This is deliberate: the draft has no finished trilingual `i18n.json`,
`ui.json`, `chapters.py`, source provenance or committed rendered
output. The quality-gate workflow is intended to temporarily install the
candidate configuration within CI to render English only and inspect
render errors without deploying or claiming the site has been published.

Next iteration should (a) inspect the latest English draft CI result and fix
any remaining render errors; (b) regenerate peer plates after the intentional
shared-range correction; (c) generate complete Romanian and Portuguese translation
catalogs including all shared spine units, all caption/legend/source
strings and page chrome; (c) implement chapters, trilingual UI,
provenance and full output; (d) validate the site against the full suite;
and (e) only then promote `research/country_candidate.yaml` to the root
`country.yaml` and remove/adjust the guard in
`tests/test_moldova_country_candidate.py`.

Do **not** push to, comment on or open a PR in `akitaonrails/worldreports`,
or merge/deploy even the user's fork. Before release-ready status, revisit
other published official routes: BNS national labour/CPI/nominal GDP,
Ministry finance national accounts/SDDS edition seams, COFOG, customs,
NBM credit/10-year yields and securities, UNDP HDI and TI CPI. Any
fillable slot must be fetched rather than permanently marked pending.

## Next Phase C groundwork — 2026-10-27

`countries/moldova/chapters.py` now supplies 12 source-derived cards and
seven headline readings in Romanian/English/Portuguese, with every numeric
value resolved from the same curated CSVs as the draft plates, not hardcoded
in descriptions. `countries/moldova/ui.json` has locale-equivalent
masthead, source limitations, editorial notes, ten explicit gap disclosures
and five publisher colophon entries for each locale. Shared `site/ui.json`
now has Romanian chrome for every English key. The branch-only runner
temporarily copies `country_candidate.yaml` into place, verifies the card
and locale contracts, renders English plates and uploads them as private
review artifacts. Country remains **unregistered in the branch** until full
trilingual graphic catalog, chart/thumb/provenance/site/global-regeneration
gate. `events.py` includes only two evidence-based publication markers;
recession dates are not fabricated from annual data.

The research CI now contains a **non-blocking diagnostic** which attempts
the full Romanian and Portuguese plate render and logs exact untranslated
strings. This is intentionally not the publication gate; the real gate must
be strict and green before registration. Its PNGs are stored as review-only
artifacts. `i18n.json` is a starter catalog and needs to be filled from
the diagnostic log without English fallback.

## Phase C source addition — 2026-10-27: BNS absolute poverty

National absolute-consumption poverty is now observed in `people.poverty`:
2014–2023 from BNS's 2024 SDG report; 2024 **33.6%** and 2025 **31.1%**
from BNS poverty releases. A documented **2019 Household Budget Survey
methodology revision** is preserved as two disconnected series, never a
spliced 2018–2019 trend. `SOURCES.yaml` names the official BNS publisher,
`DATA_NOTES.md` records the complete anchor list, the three-language
catalog/site/cards explain the break and explicitly distinguish consumption
poverty from experimental relative poverty and international dollar lines.
`tests/test_moldova_bns_poverty.py` pins all observations, blanks,
methodology and locale metadata. Minimum wage remains pending.

**Next gate:** inspect the latest CI: offline source tests, strict ro/en/pt
plate render, 36 full plates + 36 thumbs, 12 provenance records including
the new `people/absolute_poverty.csv` on `07-people`, localized pages,
layout fault audit and the full atlas/browser-JS regression. Human visual
QA and global regeneration of changed shared-spine peer images remain
necessary before registering `country.yaml`. The archival workflow now
tolerates stale concurrent non-fast-forward *without force-pushing* older
binary figures; a newer source commit must generate its own images.
Do not merge/deploy the fork or modify upstream automatically.
