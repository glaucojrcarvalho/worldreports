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
