"""Source-audited Moldova national consumption poverty; no false 2019 join.

BNS national SDG 2024 report indicator 1.2.1 p.17 supplies 2014–2023;
2024 and 2025 are from publisher poverty reports. The 2019 Household
Budget Survey methodology revision prevents a continuous series.
"""
from __future__ import annotations

import csv
from pathlib import Path
import json
import yaml

ROOT = Path(__file__).resolve().parents[1] / "countries/moldova"
OLD = {2014: 29.5, 2015: 25.4, 2016: 26.4, 2017: 27.7, 2018: 23.0}
NEW = {2019: 25.2, 2020: 26.8, 2021: 24.5, 2022: 31.1,
       2023: 31.6, 2024: 33.6, 2025: 31.1}


def test_bns_observed_values_are_exact_and_missing_early_years_stay_blank():
    with (ROOT / "data/people/absolute_poverty.csv").open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(
            line for line in stream if not line.lstrip().startswith("#")))
    assert [int(row["year"]) for row in rows] == list(range(2006, 2026))
    a = {int(r["year"]): float(r["pre_2019_pct"]) for r in rows
         if r["pre_2019_pct"]}
    b = {int(r["year"]): float(r["post_2019_pct"]) for r in rows
         if r["post_2019_pct"]}
    assert a == OLD
    assert b == NEW
    assert set(a).isdisjoint(b)
    assert all(not row["pre_2019_pct"] and not row["post_2019_pct"]
               for row in rows[:8])


def test_poverty_panel_is_drawn_in_two_independent_segments():
    source = (ROOT / "plates.py").read_text(encoding="utf-8")
    panel = source.split('ig.slot("people.poverty"', 1)[1].split(
        'ig.slot("people.minimum_wage"', 1)[0]
    assert '"pre_2019_pct"' in panel and '"post_2019_pct"' in panel
    assert panel.count("ctx.line(") == 2
    assert "ctx.pending(ax)" not in panel
    assert "methodology break in 2019" in panel


def test_manifest_and_three_locales_disclose_bns_edition_and_method_break():
    manifest = yaml.safe_load((ROOT / "SOURCES.yaml").read_text(encoding="utf-8"))
    dataset = manifest["people"]["absolute_poverty.csv"]
    assert dataset["official"] is True
    assert "National Bureau of Statistics" in dataset["source"]
    assert "Raport_ODD_" in dataset["url"]
    assert "2019" in dataset["notes"] and "2025" in dataset["notes"]
    catalog = json.loads((ROOT / "i18n.json").read_text(encoding="utf-8"))
    for label in ("BNS survey, 2014–2018", "BNS revised survey, 2019–2025",
                  "BNS consumption poverty; methodology break in 2019"):
        assert set(catalog[label]) == {"ro", "pt"}
    ui = json.loads((ROOT / "ui.json").read_text(encoding="utf-8"))
    for language in ("ro", "en", "pt"):
        # TI CPI moved from pending to source-verified; 9 definitions remain unavailable.
        assert len(ui[language]["unavailable"]) == 9
        assert any("2019" in x and "2025" in x for x in ui[language]["notes"])
    assert "people/absolute_poverty.csv" in (ROOT / "chapters.py").read_text(encoding="utf-8")
