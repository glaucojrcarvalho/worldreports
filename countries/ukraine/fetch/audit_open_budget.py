#!/usr/bin/env python3
"""Read-only audit of two official publications of 2025 Treasury cash outturns.

NBU curated functional figures and Open Budget's observed 2025 December
consolidated-budget dashboard are checked independently. The audit never
normalizes one publisher's total into the other or writes into data/.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
NBU_CSV = BASE / "data" / "fiscal" / "treasury_functional.csv"
OPEN_BUDGET_CSV = Path(__file__).resolve().parent / "reference_openbudget_2025.csv"
REPORT = Path(__file__).resolve().parent / "cache" / "treasury_reconciliation_check.csv"
CODES = {
    "gf_budgtef_0100": "general_public_services_million_uah",
    "gf_budgtef_0200": "defence_million_uah",
    "gf_budgtef_0300": "public_order_safety_judiciary_million_uah",
    "gf_budgtef_0400": "economic_affairs_million_uah",
    "gf_budgtef_0500": "environment_million_uah",
    "gf_budgtef_0600": "housing_community_million_uah",
    "gf_budgtef_0700": "health_million_uah",
    "gf_budgtef_0800": "culture_recreation_religion_million_uah",
    "gf_budgtef_0900": "education_million_uah",
    "gf_budgtef_1000": "social_protection_million_uah",
    "gf_budgtef_Total_1": "total_million_uah",
}
HEADERS = ("year", "classification", "nbu_million_uah",
           "open_budget_million_uah", "nbu_minus_open_budget_million_uah",
           "reconciliation_status")
HALF_ROUND_UNIT = Decimal("0.05")  # NBU rounds nominal million UAH to 0.1


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError(f"Empty fiscal evidence: {path.name}")
    return rows


def _number(value: str) -> Decimal:
    try:
        d = Decimal(value)
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise ValueError("Non-numeric official fiscal observation") from exc
    if not d.is_finite() or d < 0:
        raise ValueError("Negative or nonfinite fiscal expenditure")
    return d


def reconcile(nbu: list[dict[str, str]],
              open_budget: list[dict[str, str]]) -> list[dict[str, str]]:
    # This is a same-year classification cross-check, NOT a comparable-GG
    # account and NOT a license to overwrite the NBU source of truth.
    year_nbu = [r for r in nbu if r.get("year") == "2025"]
    if len(year_nbu) != 1 or year_nbu[0].get("source_dt") != "20260101":
        raise ValueError("NBU 2025 year-end mapping changed")
    row = year_nbu[0]
    if len(open_budget) != len(CODES):
        raise ValueError("Open Budget reference missing or unexpected classifications")
    reference: dict[str, Decimal] = {}
    for item in open_budget:
        code = item.get("publisher_classification_code")
        if code not in CODES:
            raise ValueError(f"Unknown Open Budget functional category: {code}")
        if code in reference:
            raise ValueError(f"Duplicate Open Budget category: {code}")
        if item.get("year") != "2025" or item.get("perimeter") != "CBU":
            raise ValueError("Reference period/perimeter mismatch")
        if item.get("publisher") != "Open Budget (State portal)" or (
            "budgetType=CONSOLIDATED" not in item.get("reference_url", "")
            or "year=2025" not in item.get("reference_url", "")
        ):
            raise ValueError("Official source attribution or query changed")
        reference[code] = _number(item.get("value_million_uah", ""))
    if set(reference) != set(CODES):
        raise ValueError("Incomplete Open Budget functional categories")
    # The independent dashboard's categories must account for its own total
    # to 0.01 UAH (0.00000001 million), not just NBU's rounded precision.
    parts = sum((v for c, v in reference.items()
                 if c != "gf_budgtef_Total_1"), Decimal(0))
    if abs(parts - reference["gf_budgtef_Total_1"]) > Decimal("0.00000001"):
        raise ValueError("Open Budget hierarchy does not reconcile internally")
    result = []
    for code, col in CODES.items():
        current = _number(row.get(col, ""))
        other = reference[code]
        diff = current - other
        result.append({
            "year": "2025", "classification": code,
            "nbu_million_uah": str(current),
            "open_budget_million_uah": str(other),
            "nbu_minus_open_budget_million_uah": str(diff),
            "reconciliation_status": ("within_nbu_rounding"
                                      if abs(diff) <= HALF_ROUND_UNIT
                                      else "publisher_discrepancy_review_required"),
        })
    return result


def csv_text(rows: list[dict[str, str]]) -> str:
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def main() -> None:
    rows = reconcile(_read(NBU_CSV), _read(OPEN_BUDGET_CSV))
    output = csv_text(rows)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    tmp = REPORT.with_suffix(".tmp")
    tmp.write_text(output, encoding="utf-8")
    tmp.replace(REPORT)
    outstanding = [r for r in rows
                   if r["reconciliation_status"] == "publisher_discrepancy_review_required"]
    print(f"Fiscal audit: {len(rows)} checked; {len(outstanding)} require publisher review.")
    print(f"Review-only report: {REPORT}")


if __name__ == "__main__":
    main()
