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

The NBM banking-sector NPL collector `fetch/fetch_nbm_npl.py` now has an
offline DOM/text parser contract and a separate read-only publisher-audit
workflow `moldova-nbm-npl-live.yml`. This source auditor creates review
sidecars, checks 2022–25 original rates and reference dates and refuses to
silently change curated figures or the country registry. Review the live
workflow's source evidence and its response hashes before final release.


## Trilingual generated-asset and data-lineage integrity gate — 2026-10-27

The last completed isolated Moldova workflow (40453006770) PASSED all
source, rendering, provenance, layout, Python and browser-JavaScript stages.
The archive bot committed 36 reviewed-source Moldova plate PNGs, 36 thumbs,
36 corresponding vector SVGs and 12 provenance mappings in
research/moldova-source-audit at 6100e706. The NBM primary-source audit
40453006876 also PASSED for all four prudential reports. Neither action
published a country; the root country.yaml intentionally remains absent.

New countries/moldova/research/audit_candidate_assets.py performs an
independent release-candidate integrity audit after each CI re-render,
and again before the research bot archives images. It checks the exact
12 x 3 PNG/SVG/thumb inventory, decodes each PNG, inspects actual SVG
viewports and topic-specific panel IDs, compares every visible English
annotation against the rendered Romanian and Portuguese SVG strings,
rejects English fallbacks, statically traces each plate's literal CSV
readers independently of runtime provenance, and requires publisher
metadata and data files for every referenced CSV. The gate is read-only.
It will fail the research run and prevent the asset commit on any
discrepancy; it is not a substitute for human visual QA.

Next: inspect the new run, including this gate's summary and full Python/
JavaScript results, then visually review final PNGs and peer-language
contact sheets for clipping/legibility (the prior 414-peer-file archive
was already committed to the fork). The largest unresolved *data*
requirements are government COFOG/GFCF, household-specific banking,
long-bond yield and a defensible local equity index, comparable excess
mortality and registered migration flows. Keep these slots pending until
their source definitions and periods are independently verified.
Only after review consider promoting the candidate configuration to the
root country.yaml on the fork research branch, running final suite with
registration enabled; never deploy, merge or modify upstream automatically.


## Period life expectancy definition correction — 2026-10-27

Independent review of the World Bank SP.DYN.LE00.IN metadata found a
specific methodological mislabel: the Moldova mortality-plate caption
had called life expectancy at birth a "birth-cohort estimate". The
official indicator is instead a synthetic PERIOD life table under
current age-specific mortality rates, not observed longevity of a cohort.
The English, Romanian and Portuguese source footer, source manifest,
data notes and a regression guard now use the correct interpretation.
The curated annual values are unchanged. The official methodology is
https://databank.worldbank.org/metadataglossary/millennium-development-goals/series/SP.DYN.LE00.IN

The trilingual rendered-asset auditor must pass again on the changed
mortality SVGs before archiving. Keep country.yaml unregistered until the
complete fork-only quality gate and outstanding human visual review pass.

## Phase C — 2016–2025 official BNS functional budget / matched nominal GDP, 2026-10-27

A blocking source gap for the `spending` chapter has been resolved without
filling missing figures with exchange-rate proxies or merging incompatible
IMF FPP/WEO fiscal vintages. Original BNS GDP 2016–2024 comes from the
`CNT208100.px` current-price thousand-MDL national accounts API,
**independently fetched live and verified** in [read-only audit
40460281083](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40460281083),
with full nine-year review sidecar. The 2025 nominal GDP
**353,520.9 million MDL** is from the separately dated **2026-03-11
preliminary GDP publication**, not fabricated from missing PxWeb values.

The reviewed `data/fiscal/nominal_gdp_bns.csv` supplies the common
2016–2025 same-territory denominator for ten BNS FIN010100 national
cash-budget functions; the plate groups them into seven atlas categories
and renders both `spending.by_function` (stacked shares of GDP) and
`spending.social_protection` (social versus other). Each source-year
sum and two external BNS anchors (**2024 38.0%**, **2025 39.6%**) are
asserted. The source/territory/publication differences and 2025
preliminary status are documented in `SOURCES.yaml`, `DATA_NOTES.md`,
and the three-language charts/site cards/notes. The **public investment**
panel remains pending pending actual government GFCF, and all IMF
comparable fiscal panels remain separate from national cash execution.

Changed code and data:
`fetch/fetch_bns_gdp.py`, `data/fiscal/nominal_gdp_bns.csv`,
`plates.py`, `chapters.py`, `i18n.json`, `ui.json`,
`tests/test_moldova_bns_gdp.py`, `tests/test_moldova_plate_design.py`,
`tests/test_moldova_research.py`, updated localized source regression
checks, `.github/workflows/moldova-bns-gdp-live.yml`, and
`.github/workflows/moldova-research.yml`. Existing automated asset
archive will regenerate the three-language PNGs/SVGs, 36 thumbnails
and provenance ONLY IF the complete quality gate succeeds; it refuses
stale non-fast-forward pushes. Moldova remains intentionally unregistered.

**Mandatory next work:** confirm the current head's COMPLETE research
quality gate and full 3,400+ Python/Node tests, not just the successful
BNS live source audit. Inspect its 36 SVG, PNG, thumbnail, 12 exact
data-lineage traces and 3 generated local site pages; fix any trilingual
glyph/layout issues from the denser stacked function legend.
Verify the research asset archive commit has landed after the new
nominal GDP and review the updated spending chart in all three languages.
Check the original BNS 2025 nominal GDP source and the published ratios
again if publisher edition changes. Check upstream divergence anew
before considering review; do not automatically register Moldova or
create/merge a PR against `akitaonrails/worldreports`, deploy or modify
published peers. Remaining major data gaps are government GFCF, household
bank lending/stock, 10-year yield/equity, registered migration flows,
and territory-matched excess mortality/COVID underlying deaths.

## Source-manifest reconciliation and research QA — 2026-10-27

The dataset-level source entries had moved forward, but the `SOURCES.yaml`
top-level `meta.pending` ledger still erroneously listed the prudential NPL
ratio as *unverified*. Corrected that contradiction: **bank-wide** NPL
2022–2025 is independently source-audited; borrower-specific household
credit, household new-loan rates, and 10-year sovereign yield remain
pending, with no household inference from either bank-wide NPL or WDI
private-credit totals. Added five traceable, dataset-linked records to
`meta.verified` for BNS nominal GDP + budget functions, BNS customs
partner shares, BNM prudential NPL, UNDP HDR 2025 HDI and TI CPI 2025.
Each links to the existing publisher-audit CI evidence and discloses
vintage/method/territorial restrictions. The offline manifest regression
now verifies existence, publisher metadata, evidence URLs, uniqueness
and no contradiction between the verified NPL and pending routes.

**Next mandatory:** inspect the newest green full-trilingual CI on this
SHA and its autoarchived assets: the prior committed `03-spending`
provenance still listed ONLY WDI macro investment because the 2016–2025
matched-BNS-GDP/functional-spending change had not yet been archived.
Successful isolated regeneration must include `fiscal/public_budget.csv`
and `fiscal/nominal_gdp_bns.csv` in its `03-spending` provenance,
alongside WDI `macro/economy.csv`. Review localized stacked-area legends
at full size, 36 PNG/SVG/thumb sets, 12 mappings, all Python/JS/layout/site
checks. Keep root `country.yaml` unregistered until those gates pass.
No upstream changes, PR, merge, or deploy.


## Phase C — verified foreign-country-of-birth census snapshot and protected source lane, 2026-10-27

The migration canonical `migration.foreign_born` was previously pending because the WDI/UN migrant stock does not guarantee a birthplace definition. The *BNS final census* directly publishes a separate, official **2024-04-08 foreign-born share of 4.4%**, alongside an approximate 106.7 thousand persons (published **2025-08-25**). We have added **one source-defined census point** rather than silently treating the UN stock as foreign-born, or creating an annual series. It is drawn with a scatter mark, not a line. Previous/next years are blank. Its territorial limitation (157 unenumerated localities) and non-identical WDI mid-year denominator are explicit. This does NOT resolve year-comparable immigration/emigration rates, which stay pending.

Files: `data/migration/foreign_born_census.csv`, guarded official-HTML fetcher with SHA256 sidecar, read-only live-source workflow and offline synthetic parser tests; chart, 3-language catalog/chapters/site notes, source manifest, data notes, lineage and semantic design tests updated.

**Next hard gates:** check BOTH the independent BNS live workflow (the source HTML parser must pass with the actual 2025 BNS publication) and the full branch-only Moldova research quality gate. The latter must pass trilingual strict render; full PNG/SVG/thumb and static-vs-observed provenance including this new CSV; site, layout, Python and JS regressions; and safely archive the resulting 36 translated assets. Review `12-migration.{ro,pt}.png` and `03-spending.{ro,pt}.png` visually. Also confirm the prior automated provenance refresh for BNS spending is present. Only after all gates and human visual QA consider registration as a candidate on the fork. Never contact upstream, merge, deploy or fabricate missing immigration/emigration observations.

## Reproducible fork-only artifact provenance handoff — 2026-10-27

Audited the branch CI and found an archive reproducibility risk: the
post-QA job rerendered SVG/PNG/thumbs instead of committing the EXACT
output that had passed strict ro/en/pt source, lineage, site/layout and
global Python/Node gates. Rendering may differ across jobs because of
font installations, Matplotlib caches, or metadata timestamps, even
with an unchanged Git SHA. The updated workflow now uploads a **success-
only, run-scoped validated-asset artifact** after the whole suite;
the archive job downloads it from that same workflow run, restores only
36 SVG, 36 PNG, 36 thumbnails plus provenance, checks byte-for-byte
identity, reruns `audit_candidate_assets.py`, removes temporary
`country.yaml`, and commits only those validated outputs to the fork
research branch. The non-fast-forward safety gate remains unchanged.
A new offline CI-contract regression prevents accidental restoration
of independent rerendering. No deployment or upstream write permitted.

**Next iteration:** verify the quality gate and new artifact-transfer
steps on their final SHA, and check the post-QA bot actually archives
`03-spending` provenance with both BNS fiscal CSVs plus WDI macro.
Review all three spending and migration PNGs, including the new BNS
census foreign-born snapshot (subject to the independent publisher
live audit). If either quality gate is red, use actual failed-step logs,
fix source/render semantics, and repeat before any registration.


## Canonical migration-slot semantics correction — 2026-10-27

The first implementation placed the BNS **single 2024 foreign-born census observation** in the canonical `migration.foreign_born` slot. Rechecked `PLATE_SPINE.md` §1 rule 2: isolated snapshots are permitted in a *country lens*, not as canonical annual time series. Moved that genuine observation (4.4%, BNS census reference **2024-04-08**) into `migration.lens` as a **separate red diamond**, next to four **teal UN migrant-stock snapshot dots** (2010/2015/2020/2024) and with a bilingual/trilingual legend identifying distinct definitions. The canonical foreign-born time-series slot is explicitly pending again; neither UN stock nor a single census reference date is misrepresented as an annual series. Provenance still records the BNS census CSV and UN/WDI data as separately sourced. The release candidate, three-language i18n/site notes, semantic tests and the peer comparison invariant reflect this correction.

**Next:** monitor BNS live HTML audit and most recent full trilingual CI, archive source-valid 36 PNG/SVG/thumb sets with exact provenance, review 03-spending and 12-migration PNGs at full scale and confirm upstream delta. Never auto-register, merge, PR, deploy or change upstream.


## Original census publisher audit passed — 2026-10-27

[Read-only BNS workflow https://github.com/glaucojrcarvalho/worldreports/actions/runs/40463501640](https://github.com/glaucojrcarvalho/worldreports/actions/runs/40463501640) passed **8 source/parser tests** and the publisher HTML download. Its saved sidecar confirms 2024 **4.4%**, all other atlas years blank, source digest `e9da05a2fab871578d1e6a62db93fc45480966ab20cbde889b7a7307ceae488b`. Added the digest and Actions evidence to `SOURCES.yaml` and `DATA_NOTES.md`; this is a real independently checked BNS snapshot, **not** a fabricated foreign-born annual series or a household/emigration count. The canonical annual foreign-born panel remains pending under the spine snapshot rule and the 2024 point belongs only to the migration lens. Check the latest full research CI and generated SVG/PNG migration legends before publication clearance.


## Full trilingual visual-review evidence — 2026-10-27

Added \`research/visual_review.py\` and an offline test suite to turn all
12 Moldova rendered plate topics into **RO / EN / PT side-by-side
contact sheets**, with identical panel sizing for reviewers. The script
does not download, infer, regenerate or publish any data. Its machine-readable
visual-review-manifest.json SHA256-fingerprints every PNG, SVG and thumbnail
(108 files), associates each plate with its observed provenance, and refuses
to proceed if either new BNS fiscal source is absent from \`03-spending\` or
the separately verified 2024 birthplace census source is absent from
\`12-migration\`. Source tests cover the exact inventory, lost locale
assets, and stale BNS provenance. The archive still consumes original
fully-tested rendering artifacts, not the downsampled contact sheets.

**Next:** inspect the latest CI \`moldova-visual-review\` artifact,
especially the full 03-spending and 12-migration pages, and verify
the \`moldova-validated-assets\` archive job actually commits the current
spending/migration SVG/PNG/thumbs and provenance. Require successful
full Python + JS and all 12 source-lineage mappings before candidate
registration. Preserve all remaining source and territorial limitations,
do not modify upstream, and do not merge/deploy.


## New source lane: national BNS unemployment and 2025 method break

Found the BNS official 2019–2025 LFS unemployment PxWeb table and its
explicit 2025 household-survey break (new EMDOS 3, 2024 census weights,
changed LFS method). The pre-2019 survey is separately marked discontinued;
BNS also publishes a new 2026 EU-aligned methodology. This national
series must never be conflated with WDI modelled unemployment. Added a
read-only discovery fetcher, test contract and fork-only official codebook
audit. **No BNS unemployment year-series values were invented or promoted.**
Next run should inspect that independent BNS workflow and retrieve the
publisher's actual category codes/annual national rates, then consider
two *disconnected national* observations/segments only after original
source verification. The official BNS 2025 annual release says 3.8%.
Keep existing data/spine and research country registration unchanged.

Also verify the newest full atlas gate including the visual-review
contact sheets, exact image SHA256 report, 36 plates and thumbs,
observed BNS budget/census provenance, Node/Python site/layout tests,
and archive-bot push. If the preceding full suite was cancelled by
this source-only commit, rerun on the current branch SHA. Never touch
the upstream repository or deploy.


## Source-audit continuation: exact BNS annual rate extraction (2026-10-27)

The **first official live BNS codebook audit passed**:
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40469103972
and directly returned source SHA256
\`e32d58d6278434a20a4c316d22c420c0f0b7cd342e2c80cb0c9dc706fcb849e0\`.
Publisher dimension codes: \`Sexe\` = 0 "Both sexes"; \`Medii\` = 0 "Whole
country"; \`Ani\` = 2019–2025; \`Trimestre\` = 0 "Annual average".
The real API path is
\`/PxWeb/api/v1/en/30%20Statistica%20sociala/03%20FM/03%20MUN/MUN060/MUN160100_2025.px\`.

On this evidence, implemented a *separate read-only annual collector*
(\`fetch_bns_lfs_annual.py\`) selecting ONLY the four audited code
dimensions, checking seven years and a real BNS publisher anchor
**2025 unemployment 3.8%**, and recording raw original JSON-stat SHA256.
It writes a **review sidecar only**:
\`data/macro/national_lfs_from_bns.csv\`, with disconnected 2019–2024
and 2025 columns because BNS revised survey/census weights in 2025.
An isolated push-triggered GitHub Actions workflow performs offline
malformed-schema tests then queries the original BNS API and preserves
the candidate numerical CSV; no plotted WDI rate or other curated
file is touched.

**Next:** inspect the live annual query before trusting ANY extracted
values. If BNS JSON-stat schema/indices differ, fix its parser from
the actual log; if the 2025 3.8% anchor differs, fail closed and
investigate publication vintage rather than adjusting 3.8 arbitrarily.
Only after the live audit is green consider a separate official national
series, never connected through the 2025 break or spliced to old LFS
or WDI ILO-modelled rates. Also check the newest full atlas QA and visual
artifact archives; no upstream modification, merge, PR or deployment.


## National unemployment source successfully adopted as separate BNS line — 2026-10-27

The exact national annual BNS LFS source query PASSED independently:
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40469496895 .
Seven verified 2019–2025 official observations, original metadata and
JSON-stat data SHA256 and the 2025 3.8% external BNS anchor were
collected without inference. Curated \`data/macro/national_lfs.csv\`
now provides 2019–24 only in an EMDOS2 segment and an isolated 2025
EMDOS3/2024-census-reweighted diamond in \`economy.unemployment\`.
The WDI modelled rate remains intact as the international comparison.
Romanian, English and Portuguese legends, chapter summaries and
site notes now explain the breaks. Source inventory, case-specific
tests and visual review \`01-economy\` provenance are updated.

**Next gate:** full branch CI including original source regression, strict
RO/EN/PT rendered SVG translation, 36 plates/thumbs, source provenance
for BNS annual unemployment, fiscal spending and 2024 foreign-born
census, layout and Python/Node regressions. Visually audit the economy
panel's three-series legend and 2025 disconnected dot. Have the
research bot archive EXACT validated images without any new rerender
or production registration. Moldova country.yaml remains unregistered.
Never merge, deploy, PR or change the upstream repository.
