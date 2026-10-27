"""Inspect actual exported SVG group for life expectancy, not other panels.

Matplotlib serializes text labels in SVG <g> groups as <!-- comments -->
when using its usual glyph-font export. This test looks INSIDE the
mortality.lens group, not anywhere on the figure: the canonical slots
legitimately mention rates per 1,000 or per 100,000 inhabitants.
"""
import os
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

# Full atlas QA reads freshly rendered candidate assets inside the source
# tree; isolated work can instead pass an explicit temporary output folder.
ROOT = Path(__file__).resolve().parents[1] / "countries/moldova"
OUTPUT = Path(os.environ.get("MOLDOVA_MORTALITY_SVG_DIR", str(ROOT / "output")))
EXPECTED = {
    "en": ("11-mortality.svg", "years", "Life expectancy at birth (years)"),
    "ro": ("11-mortality.ro.svg", "ani", "Speranța de viață la naștere (ani)"),
    "pt": ("11-mortality.pt.svg", "anos", "Expectativa de vida ao nascer (anos)"),
}


def group_comments(path: Path, gid: str) -> list[str]:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.parse(path, parser=parser).getroot()
    groups = [element for element in root.iter()
              if element.attrib.get("id") == gid]
    assert len(groups) == 1, (path, gid, len(groups))
    return [element.text.strip()
            for element in groups[0].iter()
            if element.tag is ET.Comment and element.text]


@pytest.mark.parametrize("lang", ["ro", "en", "pt"])
def test_rendered_life_expectancy_lens_uses_correct_locale_unit(lang):
    name, unit, heading = EXPECTED[lang]
    path = OUTPUT / name
    assert path.is_file(), path
    content = group_comments(path, "mortality.lens")
    assert unit in content, (lang, content)
    assert heading in content, (lang, content)
    assert "per 100,000" not in content, lang
    assert "per 1,000 people" not in content, lang
    assert content.count(unit) == 1, (lang, content)
    assert all(not label.endswith(" /100,000") for label in content)


def test_canonical_mortality_rates_remain_other_panels():
    path = OUTPUT / "11-mortality.svg"
    death = group_comments(path, "mortality.death_rate")
    covid = group_comments(path, "mortality.covid")
    lens = group_comments(path, "mortality.lens")
    assert "per 1,000 people" in death
    assert "per 100,000" in covid
    assert "years" in lens
    assert "per 100,000" not in lens
