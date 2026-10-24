#!/usr/bin/env python3
"""Stage NBU-republished Treasury annual functional expenditure for audit.

This is a research-only tool. It MUST NOT update an atlas dataset or plot
a canonical general-government fiscal series.

Publisher: NBU OpenData budget cube (Treasury republication):
  https://bank.gov.ua/NBUStatService/v1/statdirectory/budget?json
Actual NBU keys: freq=Y, dt=YYYY0101, mcr200p=CBU (consolidated budget),
tzep=F_M_VC; the functional code prefix is gf_budgtef_.
Annual records are reported with January-1 labels of the SAME year,
unlike the NBU reserve stock labels. Preserve that distinction.

CBU is consolidated CASH BUDGET execution, not SNA/IMF general-government
accrual expenditure. Functional total is expenditure less interbudget
transfers. Never add SBU to CBU or sum this result with another series.
Output: review sidecar (not committed unless explicitly audited).
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
import json
from pathlib import Path
import urllib.request

URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/budget?json"
HERE = Path(__file__).resolve().parent
OUT = HERE / "cache" / "treasury_functional_candidate.csv"
PERIMETER = "CBU"
KIND = "F_M_VC"
START, END = 2014, 2025
# Ten direct functional groups, kept in publisher classification, NOT
# silently converted into COFOG without a separately validated mapping.
FUNCTIONS = {
    "gf_budgtef_0100": "general_public_services",
    "gf_budgtef_0200": "defence",
    "gf_budgtef_0300": "public_order_and_safety",
    "gf_budgtef_0400": "economic_affairs",
    "gf_budgtef_0500": "environment",
    "gf_budgtef_0600": "housing_and_community",
    "gf_budgtef_0700": "health",
    "gf_budgtef_0800": "recreation_culture_religion",
    "gf_budgtef_0900": "education",
    "gf_budgtef_1000": "social_protection",
}
TOTAL = "gf_budgtef_Total_1"  # excluding interbudget transfers
FIELDS = ("year", "nbu_code", "publisher_category", "functional_category",
          "perimeter", "value_uah_million", "source_dt")
ANCHORS = {(2024, "gf_budgtef_0200"): Decimal("2097621.9"),
           (2024, TOTAL): Decimal("4441364.6")}


def fetch() -> bytes:
    request = urllib.request.Request(
        URL, headers={"Accept": "application/json",
                      "User-Agent": "worldreports-ukraine-fiscal-research/0.1"})
    with urllib.request.urlopen(request, timeout=75) as response:
        body = response.read(16_000_001)
        mime = response.headers.get("Content-Type", "").lower()
        status = response.status
    if status != 200 or not body or len(body) > 16_000_000 or "json" not in mime:
        raise ValueError("NBU Treasury response missing, oversized, or non-JSON")
    return body


def parse(raw: bytes) -> list[dict[str, str]]:
    try:
        items = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("NBU Treasury endpoint returned invalid JSON") from exc
    if not isinstance(items, list) or len(items) < 100:
        raise ValueError("NBU Treasury dataset absent/incomplete")
    selected = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Unexpected NBU Treasury row")
        code = item.get("id_api")
        if code not in FUNCTIONS and code != TOTAL:
            continue
        if item.get("freq") != "Y" or item.get("mcr200p") != PERIMETER:
            continue
        date_str = item.get("dt")
        if not isinstance(date_str, str) or len(date_str) != 8 or not date_str.isdigit():
            raise ValueError(f"Invalid NBU Treasury annual date: {date_str!r}")
        year = int(date_str[:4])
        if not START <= year <= END:
            continue
        if date_str != f"{year}0101" or item.get("tzep") != KIND:
            raise ValueError(f"Unexpected date or unit convention: {code}, {year}")
        key = (year, code)
        if key in selected:
            raise ValueError(f"Duplicate NBU Treasury category: {key}")
        try:
            number = Decimal(str(item["value"]))
        except (KeyError, InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid NBU Treasury value at {key}") from exc
        if not number.is_finite() or number < 0 or number > 50_000_000:
            raise ValueError(f"Implausible NBU Treasury category {key}")
        if key in ANCHORS and number != ANCHORS[key]:
            raise ValueError(f"NBU Treasury published 2024 anchor changed: {key}")
        label = item.get("txten")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"Missing publisher category label: {key}")
        selected[key] = {
            "year": str(year), "nbu_code": code,
            "publisher_category": label.strip(),
            "functional_category": FUNCTIONS.get(code, "total_excluding_transfers"),
            "perimeter": PERIMETER,
            "value_uah_million": str(number),
            "source_dt": date_str,
        }
    # Entire 2014–2025 cross-tab MUST be present. No extrapolation
    # from CBU monthly observations or SBU state-budget rows.
    for year in range(START, END + 1):
        missing = (set(FUNCTIONS) | {TOTAL}) - {
            code for (yy, code) in selected if yy == year}
        if missing:
            raise ValueError(f"{year}: incomplete consolidated functional series: {sorted(missing)}")
        parts = sum(Decimal(selected[(year, code)]["value_uah_million"])
                    for code in FUNCTIONS)
        total = Decimal(selected[(year, TOTAL)]["value_uah_million"])
        # Rounded publisher figures sum approximately; a large difference
        # means wrong perimeter, duplicate transfers, or an API revision.
        if abs(parts - total) > Decimal("5.0"):
            raise ValueError(f"{year}: functional component/total mismatch "
                             f"{parts} vs {total} million UAH")
    return [selected[key] for key in sorted(selected)]


def as_csv(rows: list[dict[str, str]]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main() -> None:
    data = as_csv(parse(fetch()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix(".tmp")
    temp.write_text(data, encoding="utf-8")
    temp.replace(OUT)
    print(f"Reviewed candidate: {OUT}; {START}–{END}, "
          "CBU Treasury cash execution only (NOT government accrual).")


if __name__ == "__main__":
    main()
