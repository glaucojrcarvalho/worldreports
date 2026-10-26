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
