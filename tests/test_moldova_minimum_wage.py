"""Official statutory minimum wage: avoid a fictitious 2006-2022 history.

The government set countrywide unified legal floors for completed years
2023-2025; the public/private unification took effect on 2022-09-01.
The USD translation uses the independently sourced annual NBM exchange
rate, never year-end spot or World Bank PPP data.
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1] / "countries/moldova"
FLOOR = {2023: Decimal("4000"), 2024: Decimal("5000"), 2025: Decimal("5500")}
FX = {2023: Decimal("18.160700"), 2024: Decimal("17.791800"),
      2025: Decimal("17.370500")}


def rows(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(s for s in f if not s.startswith("#")))


def test_government_decisions_and_nominal_nbm_conversion_are_exact():
    wage = rows(ROOT / "data/people/minimum_wage.csv")
    bank = rows(ROOT / "data/markets/usd_mdl.csv")
    assert [int(r["year"]) for r in wage] == list(range(2006, 2026))
    assert list(wage[0]) == [
        "year", "minimum_wage_mdl", "nbm_mdl_per_usd_annual_avg", "usd_per_month"
    ]
    bank_fx = {int(r["year"]): Decimal(r["mdl_per_usd_annual_avg"]) for r in bank}
    observed = {}
    for row in wage:
        year = int(row["year"])
        if year not in FLOOR:
            assert row["minimum_wage_mdl"] == ""
            assert row["nbm_mdl_per_usd_annual_avg"] == ""
            assert row["usd_per_month"] == ""
            continue
        legal = Decimal(row["minimum_wage_mdl"])
        denominator = Decimal(row["nbm_mdl_per_usd_annual_avg"])
        usd = Decimal(row["usd_per_month"])
        assert legal == FLOOR[year]
        assert denominator == FX[year] == bank_fx[year]
        assert denominator > 0
        assert abs(usd - legal / denominator) < Decimal("0.0000006")
        observed[year] = usd
    assert list(observed) == [2023, 2024, 2025]
    assert Decimal("220") < observed[2023] < Decimal("221")
    assert Decimal("280") < observed[2024] < Decimal("282")
    assert Decimal("316") < observed[2025] < Decimal("317")
    assert all(Decimal("0") < x < Decimal("3000") for x in observed.values())


def test_government_legal_source_and_2022_scope_break_are_disclosed():
    manifest = yaml.safe_load((ROOT / "SOURCES.yaml").read_text(encoding="utf-8"))
    entry = manifest["people"]["minimum_wage.csv"]
    assert entry["official"] is True
    assert entry["source"].startswith("Government of the Republic of Moldova")
    assert "old.gov.md" in entry["url"]
    assert all(x in entry["notes"] for x in (
        "2023=4000", "2024=5000", "2025=5500", "2022-09-01",
        "2026", "BLANK", "ANNUAL" if False else "annual"
    ))
    notes = (ROOT / "DATA_NOTES.md").read_text(encoding="utf-8")
    assert "2022-09-01" in notes
    assert "2006–2022 remain blank" in notes
    assert "usd_mdl.csv" in notes and "2026 is not a completed FX" in notes
    csv_notes = (ROOT / "data/people/minimum_wage.csv").read_text(encoding="utf-8")
    assert "social.gov.md" in csv_notes and "2022-09-01" in csv_notes
    assert csv_notes.count("old.gov.md") == 3


def test_trilingual_plates_chapters_site_and_provenance_are_source_specific():
    chart = (ROOT / "plates.py").read_text(encoding="utf-8")
    section = chart.split('ig.slot("people.minimum_wage"', 1)[1].split(
        '_finish(ig)', 1)[0]
    assert '"people/minimum_wage.csv"' in section
    assert '"usd_per_month"' in section
    assert "ctx.line(" in section and "_pending(" not in section
    assert "NBM annual USD/MDL" in section
    chapter = (ROOT / "chapters.py").read_text(encoding="utf-8")
    assert '"people/minimum_wage.csv"' in chapter
    assert "2023–2025" in chapter
    catalog = json.loads((ROOT / "i18n.json").read_text(encoding="utf-8"))
    for key in (
        "Govt minimum 2023–25 / NBM annual USD/MDL",
        "WDI Gini, BNS poverty and 2023–25 statutory minimum wage",
        "World Bank WDI; BNS poverty; Moldova Government wage; NBM FX",
        "Household inequality and BNS poverty with a 2019 method break; verified legal minimum 2023–25.",
    ):
        assert set(catalog[key]) == {"ro", "pt"}
        assert all(catalog[key].values())
    ui = json.loads((ROOT / "ui.json").read_text(encoding="utf-8"))
    for lang in ("ro", "en", "pt"):
        assert len(ui[lang]["unavailable"]) == 7
        assert any("2023" in s and "2025" in s and "2022" in s
                   for s in ui[lang]["notes"])
        assert any("2022" in u["detail"] for u in ui[lang]["unavailable"])
    provenance = json.loads((ROOT / "provenance.json").read_text(encoding="utf-8"))
    assert "people/minimum_wage.csv" in provenance["07-people"]
    assert "markets/usd_mdl.csv" in provenance["05-markets"]
