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


## TI CPI 2025 primary-source audit lane — 2026-10-27

Added \`fetch/fetch_ti.py\` and an isolated, non-publishing workflow
\`.github/workflows/moldova-ti-live.yml\` to audit Transparency
International's official **CPI2025_Results.xlsx** time-series tab.
The 2025 workbook was released 2026-02-10 and contains scores under the
**2012-and-newer comparable methodology only**. A constrained
standard-library OOXML parser checks the workbook relation, sheet name,
country identity, all 14 years, whole-number 0–100 values and publisher
anchors 2023=42, 2024=43, 2025=42. An offline OOXML fixture suite tests
truncated XLSX, malformed/missing values and method/vintage boundaries.
The fetcher writes **only** \`world/cpi_from_ti.csv\` for review, with
original-byte SHA256; the workflow has read-only contents permission and
does not publish or modify curated assets. Publisher:
https://images.transparencycdn.org/images/CPI2025_Results.xlsx ;
method/source attribution:
https://www.transparency.org/en/news/how-cpi-scores-are-calculated .
TI lists the content licence as **CC BY-ND 4.0**. If publisher data
are reused in visualization, verify attribution/licence requirements;
do not mislabel these *perception* scores as measured corruption.

**Next step**: inspect the new publisher-audit run and its sidecar before
adding any CPI series to \`world/cpi.csv\`, \`SOURCES.yaml\`, trilingual
labels, provenance or the world plate. If the publisher workbook schema
differs, adapt the parser using actual worksheet evidence and rerun the
offline contract tests. Keep CPI panel explicitly pending until the
publisher-side audit actually passes. Do not commit output to upstream,
register Moldova or deploy.

## Full-suite peer-selection gate correction — 2026-10-27

The previous full-atlas run
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40437548930
exercised **3,418 passing Python tests plus 8 subtests** before one
test failed: \`test_shared_range_and_complete_peer_selection\` assumed
Moldova could not have a \`country.yaml\`, contradicting the runner's
intentionally temporary registration for full-atlas verification. This
was a **test-harness context collision**, not an observed plate failure.
The test now excludes the *candidate* from the published peer set,
regardless of the temporary isolated registration. The independent
candidate-only test and dedicated peer audit continue to enforce that
the actual repository does not register Moldova. The new TI source
test likewise avoids incorrectly failing on the disposable registration.
The full suite must rerun green before promotion.

## Phase C: original Transparency International CPI 2025 scores promoted — 2026-10-27

The real original publisher XLSX was **successfully** decoded and verified:
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40440734736 .
The 14 CPI scores (2012–2025) are SHA256-pinned to publisher bytes
`543a2ad438c4ba9a70367ee10a44a2565de7fae6bcd8a8db0c23d0b993e46e31` and curated to `world/cpi.csv`.
The world CPI canonical panel now plots **verified observations**, with
2006–2011 blank because of the 2012 methodology change. Source manifest,
provenance, all three locales, chapter text, notes and regression contracts
were updated coherently. CPI measures *perceived* public-sector corruption,
not proven crimes, and the publisher has CC BY-ND 4.0 attribution/licensing.

**Next:** the full research gate must pass strict ro/en/pt rendering, all
36 figures and thumbnails, source/provenance, 9 genuinely unavailable items,
global Python/JS tests, and site layout. Review peer-axis contact sheets and
regenerate published peer images only after explicit visual signoff. Keep
Moldova unregistered, do not deploy, merge or modify upstream.

## Phase C source discovery: BNS customs export partners — 2026-10-27

The upstream source catalogue has now been narrowed to an **actual named
official BNS table**: `EXT010200.px`, exports of goods by countries
**and country groups**, updated 2026-06-30, original publisher unit
**thousand USD**, reference years 1997–2025. Its territorial universe
excludes enterprises on the left bank of the Nistru and Bender. The
2025 BNS release reports **US$3,782.7 million** of merchandise exports,
including both domestic exports and re-exports; this amount is NOT
WDI national-accounts goods-and-services exports. BNS also changed
Ukraine's CIS/other-country grouping starting with year 2024.

A new guarded, **read-only** live-source audit
(`fetch/fetch_bns_trade.py` + `moldova-bns-trade-live.yml`) discovers
the official API table, validates publisher coded metadata, fetches the
2006–2025 partner-year cube, decodes JSON-stat2 regardless of dimension
order, preserves blanks, checks the 2025 published total and archives
a source-codebook + original-payload SHA256 evidence file and a separate
`exports_partner_from_bns.csv` **review sidecar**. Offline parser tests
are included. The table contains overlapping *country groups, totals
and member countries*: no ranking, group share or partner summation is
permitted before checking its actual publisher taxonomy. This preliminary
audit does **not** alter curated WDI trade, plates, registry or site.

Publisher:
https://statbank.statistica.md/PxWeb/pxweb/en/40%20Statistica%20economica/40%20Statistica%20economica__21%20EXT__EXT010__serii%20anuale/EXT010200.px

2025 BNS release:
https://statistica.gov.md/index.php/en/international-trade-of-goods-of-the-republic-of-moldova-in-december-2025-9539_62323.html

**Next task:** check the initial live workflow's actual API traversal and
metadata, fix only observed schema/path issues, and review 89 raw BNS
partner/group codes and year-specific values. Determine additive country-only
rows vs overlapping group aggregates before curating a new official
merchandise partner dataset and contextual trade panel. Do not
substitute customs series for WDI goods-and-services GDP shares.
Then complete shared peer-asset signoff and human visual QA. The last
full atlas gate 40441289491 passed **3,431 Python tests + 8 subtests,
20 Node tests**, 36 Moldova plates, 36 thumbs and 12 provenance records.
The read-only 40440531390 peer audit regenerated **138 peer-localized
trade/world charts** and found 414 corresponding modified PNG/SVG assets.
Those peer assets have NOT been committed to this branch, and require
careful review before release registration. No merge/deploy or upstream PR.

## BNS trade-partner promotion and next release gates — 2026-10-27

New official [BNS publisher audit 40446267708](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40446267708)
passed 89 coded partner/group categories over 20 years. Committed
`data/trade/destinations.csv` and filled canonical
`trade.destinations` with five *actual individual destination* share
series (Romania, Turkey, Italy, Czechia, Ukraine) in Romanian, English and
Portuguese. Data notes and `SOURCES.yaml` pin official payload hashes,
customs territory, 2024 Ukraine group reclassification and the difference
between the current BNS 2025 Total and earlier preliminary news release.
WDI goods-and-services GDP shares remain an independent dataset.

**New gates:** inspect live BNS source-diff job and full research quality gate
at this new commit; strict tri-locale rendering must pass, 36 images and
thumbs, all source provenance, layout, Python and Node regressions.
Review newly generated trade PNGs in ro/en/pt for legends and clipping.
Last earlier green [research gate 40441289491](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40441289491)
passed 3,431 Python tests, 20 Node tests, and complete candidate QA.
Separately, the [read-only peer shared-axis gate 40440531390](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40440531390)
passed 25 countries and 138 locale-specific peer plates (414 files);
those images are not yet committed. Keep Moldova unregistered until peer
assets and full-source/locale QA are approved. Do not open upstream PR,
merge or deploy.

## Peer shared-axis asset archive — bounded write gate, 2026-10-27

The earlier **read-only** peer regeneration at
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40440531390
has been reviewed: 25 published countries, 138 locale-specific world/trade
plates and 414 changed peer PNG/SVG/thumb assets, with changed decoded
pixels about 4–9% and image dimension drift no more than 1 px. English
side-by-side contact sheets have been visually inspected at contact-sheet
resolution; these comparisons show intended shared-axis rescaling without
obvious label overflow, not a claim to pixel-perfect review of every locale.

A separate fork-only **write** workflow
`.github/workflows/moldova-peer-archive.yml` now reruns the same
source-neutral rebuild on an isolated runner, requires *exactly* the
138/414 expected artifacts, nontrivial but bounded <=12% pixel changes,
<=2-pixel dimension drift, source/catalog/site and Node tests, and stages
only approved peer output paths. It makes one non-forced commit to the
research branch, optionally safely rebased over Moldova-only work; if
published peer or core sources changed concurrently, it aborts. It does
NOT register Moldova, deploy, contact or modify upstream. The workflow
must finish successfully before marking this release gate closed.

## Phase C: government unified minimum wage fills legal floor, 2026-10-27

Three **verified, full-year comparable** legal wage floors are now staged
as `people/minimum_wage.csv`: 2023 MDL 4,000, 2024 MDL 5,000 and
2025 MDL 5,500, sourced to the Republic of Moldova Government's dated
decisions, translated to nominal USD/month using the **already audited
annual NBM MDL/USD** dataset. The Ministry of Labour explicitly dates
public/private unification to **September 1, 2022**, so 2006–2022 stay
blank rather than splicing earlier sector-specific minima or treating
the partial 2022 statutory regime as a full-year observation.
The incomplete 2026 calendar FX is likewise excluded. See
`DATA_NOTES.md` for source URLs, scope and numerical method.
This change fills `people.minimum_wage` and updates source manifest,
Romanian/English/Portuguese captions, chapter text, site notes, immutable
provenance and offline integrity regression tests. No unsupported
bond/equity/household-credit, COFOG or Covid values were introduced.

**Next mandatory gate:** inspect the new `moldova-research.yml`
full-atlas green status after this commit, check 36 full + 36 thumbnails,
source-to-plate provenance and localized visual layout, and inspect the
concurrent 414-file peer-axis archival workflow. The peer bot is allowed
to push *only* reviewed binaries into this fork research branch; audit
its exact path inventory and rendered pages. Keep Moldova unregistered
until global peer output and visual signoff. No upstream PR, merge, deploy
or upstream modification.

## Phase C — official bank-wide NBM NPL replaces one credit pending slot, 2026-10-27

Transcribed four original NBM year-end **bank-wide prudential** credit-quality
bulletins into `data/credit/prudential_npl.csv` (2022=6.4%, 2023=5.6%,
2024=4.1%, 2025=4.1%) and filled `credit.npl` without claiming that
business loans are household debt. Preserved the publisher's 2024
**1.4 pp** stated change versus **1.5 pp** subtraction of the separately
rounded values by plotting two unconnected report-edition segments.
Updated manifest, trilingual titles/legends/footnote, chapter/UI text,
data notes and offline tests; no missing years fabricated.

The fork-only peer-axis archive workflow
[40447785568](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40447785568)
was successful and committed 414 peer PNG/SVG/thumb files at 296c0ddd.
**Next mandatory:** verify full Python/Node CI and generated 36 plates,
36 thumbnails, 12 provenance mappings after this source change; verify the
new credit source is traced to plate 06; review all three localized NPL
panels visually, along with global peer axis image contact sheets. Keep
Moldova unregistered and do not merge/deploy or contact upstream.
