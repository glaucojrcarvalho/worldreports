"""Semantic checks for the reviewed Moldova BNS FIN010100 cash budget.

Use year-keyed values from the *current API snapshot*. The separately
published 2024 FINAL overview is intentionally NOT overwritten by this API
vintage (a real 0.1 million MDL disagreement).
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
MOLDOVA = ROOT / "countries" / "moldova"
API_FILE = MOLDOVA / "data/fiscal/public_budget.csv"
OVERVIEW_FILE = MOLDOVA / "data/fiscal/budget_summary.csv"
FUNCTIONS = (
    "general_services_mdl_mn",
    "defense_mdl_mn",
    "public_order_mdl_mn",
    "economic_affairs_mdl_mn",
    "environment_mdl_mn",
    "housing_mdl_mn",
    "health_mdl_mn",
    "culture_mdl_mn",
    "education_mdl_mn",
    "social_protection_mdl_mn",
)


def read(path: Path) -> dict[int, dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        table = csv.DictReader(line for line in handle
                               if not line.startswith("#"))
        assert "year" in table.fieldnames
        parsed = {
            int(row["year"]): {
                key: (float(value) if key != "edition" else value)
                for key, value in row.items() if key != "year"
            }
            for row in table
        }
        return parsed


def test_history_is_observed_complete_calendar_years_only() -> None:
    values = read(API_FILE)
    assert list(values) == list(range(2016, 2026))
    assert 2026 not in values
    assert len(values[2016]) == 13
    assert all(set(FUNCTIONS).issubset(v) for v in values.values())
    note = API_FILE.read_text(encoding="utf-8")
    assert "Perioade=3" in note
    assert "Unitatea de masura=0" in note
    assert "2016-2025" in note
    assert "left-bank Nistru" in note


@pytest.mark.parametrize("year", range(2016, 2026))
def test_cash_balance_and_functional_totals_reconcile(year: int) -> None:
    row = read(API_FILE)[year]
    assert row["revenue_mdl_mn"] - row["expenditure_mdl_mn"] == pytest.approx(
        row["balance_mdl_mn"], abs=0.11)
    assert sum(row[name] for name in FUNCTIONS) == pytest.approx(
        row["expenditure_mdl_mn"], abs=0.11)
    assert all(row[name] >= 0 for name in FUNCTIONS)


def test_research_values_pin_official_snapshot_anchors() -> None:
    values = read(API_FILE)
    assert values[2016]["revenue_mdl_mn"] == 45953.9
    assert values[2020]["balance_mdl_mn"] == -10619.8
    assert values[2023]["revenue_mdl_mn"] == 102299.2
    assert values[2023]["expenditure_mdl_mn"] == 117871.1
    assert values[2025]["expenditure_mdl_mn"] == 139856.4
    assert values[2025]["social_protection_mdl_mn"] == 54056.0
    assert values[2025]["education_mdl_mn"] == 22271.1


def test_2024_vintage_discrepancy_remains_visible_not_silently_spliced() -> None:
    actual = read(API_FILE)
    overview = read(OVERVIEW_FILE)
    assert overview[2024]["edition"] == "final"
    assert overview[2025]["edition"] == "preliminary"
    assert actual[2024]["revenue_mdl_mn"] == overview[2024]["revenue_mdl_mn"]
    assert actual[2024]["expenditure_mdl_mn"] == 122962.7
    assert overview[2024]["expenditure_mdl_mn"] == 122962.6
    assert actual[2024]["balance_mdl_mn"] == -12624.2
    assert overview[2024]["balance_mdl_mn"] == -12624.1
    assert actual[2025]["expenditure_mdl_mn"] == overview[2025]["expenditure_mdl_mn"]
    assert actual[2025]["balance_mdl_mn"] == overview[2025]["balance_mdl_mn"]
    assert "DIFFERS by 0.1" in API_FILE.read_text(encoding="utf-8")


def test_manifest_records_disagreement_and_non_imf_perimeter() -> None:
    manifest = yaml.safe_load((MOLDOVA / "SOURCES.yaml").read_text("utf-8"))
    full = manifest["fiscal"]["public_budget.csv"]
    summary = manifest["fiscal"]["budget_summary.csv"]
    assert full["official"] is True and summary["official"] is True
    assert "122962.7" in full["notes"] and "122962.6" in full["notes"]
    assert "Bender" in full["notes"]
    assert "PRELIMINARY" in full["notes"]
    assert "not imf" in full["notes"].lower()
