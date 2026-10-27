"""The observed mortality lens is life expectancy in YEARS, not /100,000.

The canonical mortality panels intentionally keep their shared units.
No country.yaml is registered: this test loads the review candidate as
an in-memory Country and executes the actual four-panel builder.
"""
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt

from core.country import Country
from core.context import Context
from core import spine
from countries.moldova.plates import plate_mortality
import json

ROOT = Path(__file__).resolve().parents[1] / "countries/moldova"
CANDIDATE = ROOT / "research/country_candidate.yaml"


def candidate_country():
    original_read = Path.read_text

    def read(self, *args, **kwargs):
        if self == ROOT / "country.yaml":
            return original_read(CANDIDATE, encoding="utf-8")
        return original_read(self, *args, **kwargs)

    with patch.object(Path, "read_text", read):
        return Country.from_dir(ROOT, "moldova")


def test_mortality_lens_carries_years_not_shared_rate_unit():
    country = candidate_country()
    ctx = Context(country)
    ig = ctx.fig("Moldova mortality", "Observed WDI only", topic="mortality")
    try:
        plate_mortality(ctx, ig)
        death, excess, covid, expectancy = ig.axes_flat
        assert death.get_ylabel() == spine.SLOTS["mortality.death_rate"].unit
        assert excess.get_ylabel() == spine.SLOTS["mortality.excess_deaths"].unit
        assert covid.get_ylabel() == spine.SLOTS["mortality.covid"].unit
        assert spine.SLOTS["mortality.lens"].unit == "per 100,000"
        assert expectancy.get_ylabel() == "years"
        assert "years" in expectancy.get_title(loc="left")
        assert expectancy.get_ylabel() != covid.get_ylabel()
        assert len(expectancy.get_lines()) == 1
        assert len(expectancy.get_lines()[0].get_ydata()) >= 15
        assert "per 100,000" not in expectancy.get_ylabel()
    finally:
        plt.close(ig.fig)


def test_ro_pt_unit_translation_is_explicit():
    catalog = json.loads((ROOT / "i18n.json").read_text(encoding="utf-8"))
    assert catalog["years"] == {"ro": "ani", "pt": "anos"}
    assert catalog["Life expectancy at birth (years)"] == {
        "ro": "Speranța de viață la naștere (ani)",
        "pt": "Expectativa de vida ao nascer (anos)",
    }


def test_only_moldova_optional_lens_override_and_no_core_change():
    source = (ROOT / "plates.py").read_text(encoding="utf-8")
    block = source.split("def plate_mortality(ctx, ig):", 1)[1].split(
        "def plate_migration(ctx, ig):", 1)[0]
    assert 'ig.slot("mortality.lens", "Life expectancy at birth (years)",' in block
    assert "unit=False" in block
    assert 'ax.set_ylabel("years", fontsize=8.6, color=p.muted)' in block
    assert 'ig.slot("mortality.covid", "COVID deaths, underlying cause (/100,000)")' in block
    registered = ROOT / "country.yaml"
    # During the full atlas suite CI intentionally registers a temporary
    # copy of the candidate. It must match exactly; the original research
    # branch without that CI-only copy remains unregistered.
    if registered.exists():
        assert registered.read_bytes() == CANDIDATE.read_bytes()
