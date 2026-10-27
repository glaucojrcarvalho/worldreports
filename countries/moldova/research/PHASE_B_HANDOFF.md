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

## Phase C: global CI repairs and contextual WDI credit — 2026-10-27

Previous global test gate 40422585628: 3380 passed, 10 skipped, 12
failed. Ten failures were missing CJK fonts because Matplotlib cached
its font list before the late Noto install; CJK fonts now install
before ALL Python rendering and a smoke test checks script families.
A second failure asserted research/country.yaml absent even during the
isolated CI trial registration; temporary copies are now allowed only
when byte-identical to the candidate, while the separate candidate
test still refuses committed registration. The final failure was
an empty 06-credit provenance record: solved by adding independently
verified WDI broad private-sector data to ONLY the credit lens.
Publisher API evidence:
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40428253945

Outstanding: await fresh full-suite tests and browser JS; inspect
generated trilingual PNGs/SVGs and full provenance and peer-axis
regeneration; source-audit NBM household/NPL/bonds, legal wages, UNDP
HDI, TI CPI and census concordance before any root country.yaml
registration. Do not merge, deploy or contact upstream.


## Peer comparison-scale release rehearsal — 2026-10-27

The last isolated trilingual candidate full-suite quality gate passed:
[GitHub Actions 40429317411](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40429317411)
reported **3,406 Python tests passed**, 8 subtests passed, and **20 Node
tests passed**, with no Moldovan layout faults in ro/en/pt. The subsequent
assets archiver recorded 36 PNG plates, 36 thumbnails and 12 observed source
provenance mappings in the **unregistered** research branch.

To address the still-open global shared-axis regeneration requirement,
`research/peer_scale_gate.py` and the isolated
`.github/workflows/moldova-peer-scales.yml` now rebuild **trade and world
plates for every published country and its own locales**, without changing
the single-country source data. The gate asserts the three shared-scale
contracts; requires precisely one trade and one world declarative plate per
peer; records per-locale old/new SHA256, decoded pixel-difference bounds,
image dimensions and full coverage; and generates **old-versus-new English
contact sheets** for all peers. A disposable runner stages regenerated
PNG/SVG/thumb assets *only for validation*, then builds the whole atlas site,
runs source/catalog and browser checks, and uploads regenerated assets plus
comparison report. **This workflow has read-only repository permission and
does not commit, push, merge, register Moldova or deploy.**

Next run: inspect the peer-scale workflow's result, downloadable comparison
contact sheets and delta manifest. If green and visually cleared, commit
only the regenerated peer outputs on the research fork branch, then repeat
the full source, catalog, render, layout, provenance and site tests with
Moldova registered in an isolated branch runner. Do not add the root
`country.yaml` until the peer assets and semantic audits are approved.
Unfilled HDI/CPI, household credit, bond/equity, COFOG and national labour
routes still need actual publisher evidence or explicit pending descriptions.

## UNDP source-audit lane — 2026-10-27

The UNDP Human Development Report Office offers the **official** 2025
composite-indices historical release at
https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Composite_indices_complete_time_series.csv.
The site documents a time series through **2023**, not through 2025.
UNDP Moldova's May 6, 2025 release independently confirms **HDI 0.763
(2022)** and **0.785 (2023)**. Earlier HDR vintages are revised: NEVER
splice them into this 2025 restatement. A separate guarded,
Windows-1252-aware source fetcher, offline tests and a no-write-back
GitHub Actions live audit now capture the official MDA 2006–2023 values
as `hdi_from_undp.csv` for review, not as a published plate series.
The script enforces schema, complete-release row count, country identity,
missing-year behavior, 2022–2023 publication anchors and raw SHA256.

Next run: inspect the new independent UNDP workflow; do **not** add
HDI to the atlas until the publisher fetch and sidecar checks pass.
Then curate a separate world HDI CSV, extend SOURCES.yaml/DATA_NOTES.md,
draw the canonical `world.hdi` slot, add Romanian/Portuguese strings,
provenance and strict regression tests. CPI and household-credit gaps
remain separate. No upstream changes or release until verified.

## HDR 2025 official release mismatch discovered live — 2026-10-27

The **first successful real UNDP CSV download** from the official 2025
historical file exposed a genuine contradiction: source
`MDA.hdi_2022 = 0.784`, but the **UNDP Moldova May 6, 2025 press release**
prints **0.763** for 2022. The same publications agree on
**2023 = 0.785**. This is NOT a parser rounding issue (0.021 difference)
and is not licence to interpolate. The first live audit intentionally
**failed closed**:
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40436059535.
The guarded fetcher now anchors the **complete time-series CSV** at 0.784
for 2022 and 0.785 for 2023 while explicitly disclosing the conflicting
press release; the later live run must independently confirm the full
dataset before any publication. Never characterize the 2022–23 change
as 0.022 points without specifying the *press-release* edition. In the
2025 full historical CSV it is 0.001 points.

## Phase C: UNDP HDI promoted into observed world spine — 2026-10-27

Independent official-source audit
[40436229785](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40436229785)
passed all seven parser tests, downloaded and verified the official 2025
HDR CSV, and archived its complete country-MDA 2006–2023 sidecar.
The pinned source bytes SHA256 is
`61ed82e5b66c88dfca8ff9fac775c63981ecab6a254862af97acacc41c143117`.
Curated `world/hdi.csv` now fills canonical `world.hdi` through 2023.
The same 2025 vintage yields 2022=0.784 and 2023=0.785; UNDP Moldova's
2025 press-release 2022=0.763 remains a **documented 0.021 discrepancy**,
not a substituted datapoint. Site notes, chapter cards and all three
languages distinguish this issue, show no 2024–2025 HDI, and retain
only Transparency International CPI as pending in that section.
Source manifest, observed provenance, translations and offline regression
tests are updated with the identical source lane.

**Next gates:** confirm the next complete quality-gate run passes
(strict trilingual render, 36 figures and thumbs, full Python/Node tests,
layout, site and provenance); inspect generated HDI panel images across
ro/en/pt. Validate the read-only peer-scale regeneration workflow and
archive peer output only after pixel/contact-sheet review. Further
pending primary-source slots: TI CPI methodology, BNS labour/legal
minimum wage, NBM borrower-consistent household/NPL, government COFOG
and capital spending, customs trade destinations, bond/equity.
Do NOT register the country, deploy, merge, or modify upstream.
