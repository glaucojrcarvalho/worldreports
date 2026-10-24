"""Cross-publisher Treasury audit: preserve, and never conceal, disagreement."""
from __future__ import annotations

from decimal import Decimal
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "fetch" / "audit_open_budget.py"
spec = importlib.util.spec_from_file_location("treasury_portal_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def evidence():
    return audit._read(audit.NBU_CSV), audit._read(audit.OPEN_BUDGET_CSV)


def test_official_dashboard_matches_its_own_functional_total():
    nbu, portal = evidence()
    rows = audit.reconcile(nbu, portal)
    assert len(rows) == 11
    assert {r["year"] for r in rows} == {"2025"}
    assert sum(Decimal(r["open_budget_million_uah"])
               for r in rows if r["classification"] != "gf_budgtef_Total_1") == (
                   Decimal("5999467.11164619"))


def test_NBU_and_open_budget_are_not_falsely_marked_reconciled():
    rows = {r["classification"]: r for r in audit.reconcile(*evidence())}
    assert rows["gf_budgtef_0200"]["reconciliation_status"] == "within_nbu_rounding"
    assert rows["gf_budgtef_0400"]["reconciliation_status"] == (
        "publisher_discrepancy_review_required")
    assert Decimal(rows["gf_budgtef_0400"]["nbu_minus_open_budget_million_uah"]) == (
        Decimal("6892.20539300"))
    assert Decimal(rows["gf_budgtef_Total_1"]["nbu_minus_open_budget_million_uah"]) == (
        Decimal("6920.18835381"))
    unresolved = [r for r in rows.values() if "review_required" in r["reconciliation_status"]]
    assert len(unresolved) == 5, "Publisher-diff baseline changed: investigate"


def test_schema_and_source_perimeter_mismatches_fail():
    for field, value, pattern in (
        ("publisher_classification_code", "COFOG_04", "Unknown"),
        ("year", "2024", "period/perimeter"),
        ("perimeter", "SBU", "period/perimeter"),
        ("value_million_uah", "-99", "Negative"),
        ("reference_url", "https://example.com/2025", "attribution"),
    ):
        nbu, portal = evidence()
        portal[0] = {**portal[0], field: value}
        with pytest.raises(ValueError, match=pattern):
            audit.reconcile(nbu, portal)


def test_duplicates_and_missing_functional_groups_fail():
    nbu, portal = evidence()
    with pytest.raises(ValueError, match="duplicate|Duplicate"):
        audit.reconcile(nbu, [*portal[:-1], portal[0]])
    with pytest.raises(ValueError, match="missing"):
        audit.reconcile(nbu, portal[:-1])


def test_independent_portal_accounting_identity_is_strict():
    nbu, portal = evidence()
    portal[0] = {**portal[0], "value_million_uah": "512181.58289890"}
    with pytest.raises(ValueError, match="does not reconcile"):
        audit.reconcile(nbu, portal)


def test_no_live_network_or_curated_csv_write_paths():
    assert audit.REPORT.parent.name == "cache"
    assert audit.REPORT.name.endswith("_check.csv")
    assert audit.NBU_CSV.name == "treasury_functional.csv"
    assert audit.NBU_CSV.parent.name == "fiscal"
    assert audit.OPEN_BUDGET_CSV.parent.name == "fetch"
    assert "general_government" not in audit.csv_text(audit.reconcile(*evidence()))


def test_2025_calendar_mapping_is_nonnegotiable():
    nbu, portal = evidence()
    nbu[-1] = {**nbu[-1], "source_dt": "20250101"}
    with pytest.raises(ValueError, match="year-end mapping"):
        audit.reconcile(nbu, portal)
