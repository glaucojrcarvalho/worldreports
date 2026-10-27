# Mortality panel unit correction — isolated fork research

The source atlas metadata specifies `mortality.lens` with a default
unit of **per 100,000 people**. That default is appropriate for certain
country-specific cause-of-death lenses. The Moldova lens instead draws
World Bank WDI **period life expectancy at birth, in YEARS**, so
inheriting the default y-axis label falsely makes years look like a rate.

Only Moldova's OPTIONAL lens now calls `ig.slot(..., unit=False)`
and explicitly labels the vertical axis `years`, translated to
Romanian `ani` and Portuguese `anos`. The three canonical mortality
slots still use their atlas-wide common units. This is a source meaning
and figure-label correction; no numerical series, sourced value,
geography, time axis, or shared cross-country definitions change.

This research branch is not published, registered, merged or deployed.
The fork-only CI executes the real builder, tests the axis units and
all captions, and renders all 12 plates in RO/EN/PT with translation
strictness before retaining preview artifacts.

**Next:** require the focused run green, then integrate only the
Moldova `plates.py`, `i18n.json`, and unit regression test into
`research/moldova-source-audit` after its current global CI and exact
artifact archive have finished. Rerender and inspect `11-mortality`
in each language, run the global Python/JS suite and the registered
rehearsal comparison; keep `country.yaml` unregistered, never touch
`akitaonrails/worldreports`, open PR, merge or deploy.

## SVG-level validation of rendered locale units

A second independent check parses the *actual exported SVG XML*
with Python's standard library. Instead of searching the whole file,
it isolates the exact `<g id="mortality.lens">` group and verifies the
legend/title plus vertical-axis unit `years`, `ani`, or `anos`. The
canonical death-rate and COVID units are checked **in their own SVG
groups**, so a correct 'per 100,000' elsewhere is not treated as an
error. A missing group, repeated unit label, untranslated title, or
unexpected /100k caption fails. The test runs immediately AFTER
rendering all RO/EN/PT output in the isolated branch workflow. No data
changes, source imputation, shared core edits, or publication.

## Registered rehearsal artifact verified independently — 2026-10-27

The nondeployable registered-country rehearsal completed GREEN:
https://github.com/glaucojrcarvalho/worldreports/actions/runs/40501156787
(revision `a622143b5f4d724fabc1efbb4d3330dad8803d84`).
Logs show **3,493 Python tests + 8 subtests, and 20 JavaScript tests**,
a fully constructed RO/EN/PT site, 108 rendered graphic/thumb files
and all 12 plate provenance maps.

Artifact `moldova-release-rehearsal` (ID `12735650657`) was
downloaded and independently inspected using the standard-library
`zipfile`, `hashlib` and `xml.etree.ElementTree` tools.
The **108 generated country output PNG/SVG/thumb files are byte-for-byte
identical to the 108 copied files used by the registered preview site**
(108/108 exact comparisons). The `mortality.lens` SVG XML groups have
these exact expected locale axes/heading labels:

- English: `years`; `Life expectancy at birth (years)`.
- Romanian: `ani`; `Speranța de viață la naștere (ani)`.
- Portuguese: `anos`; `Expectativa de vida ao nascer (anos)`.

The three reviewed `11-mortality` SVG SHA256 digests from that run:
- English: `63019934fd8985e3964bcb999d4ddfc918719fb2fa80c0aa712c693794c1ca44`.
- Romanian: `9387b77f786091b7546dc4d940692bed17fdce0e4e812213db3ccbeedda43716`.
- Portuguese: `d8450cde28c7a83ee91c24460356473f5a4c211ec357f350121ef6cbb0c14317`.

These checks are attached to the isolated registered rehearsal's output,
not an assertion that the candidate was deployed or accepted upstream.
The research source branch contains the same `plates.py` and
`i18n.json` blobs; its own current full run must separately complete
and archive the updated 108 files on that source branch.

**Next:** inspect research Actions run 40504515369 for full green
Python/JS and guarded fork-only source image archive, then verify
that the 11-mortality rendered RO/EN/PT image and provenance have
actually been committed there. Keep both country registration and
upstream untouched until final source/visual/editorial acceptance.
