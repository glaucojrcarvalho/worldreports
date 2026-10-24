#!/usr/bin/env python3
"""Stage 2006–2025 NBU end-of-calendar-year official reserve assets.

Publisher: National Bank of Ukraine (NBU) OpenData "res" dataset.
Source: https://bank.gov.ua/NBUStatService/v1/statdirectory/res

CRUCIAL date basis: the NBU labels monthly reserve stocks at the *start*
of the following month. The API record dt=20250101 is the year-end 2024
stock; dt=20241201 is the previous month's stock, NOT year-end 2024.
For year Y fetch date=(Y+1)0101, not Y1201.

The total is id_api=RES_OffReserveAssets (units code T071USD_7, millions
of US dollars). This is a stock of gross official reserve assets, NOT
a monthly or annual flow. Divide by 1,000 to report canonical US$ bn.

Only stages data/macro/reserves_from_nbu.csv for review. Never overwrites
the curated data/macro/reserves.csv. Does not fabricate missing years.
"""
from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "macro" / "reserves_from_nbu.csv"
URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/res"
FIRST = 2006
LAST = 2025
TOTAL_ID = "RES_OffReserveAssets"
UNIT_CODE = "T071USD_7"
ANCHORS = {
    2006: Decimal("22358.10"),
    2014: Decimal("7533.33"),
    2022: Decimal("28494.46"),
    2024: Decimal("43795.35"),
    2025: Decimal("57302.41"),
}


def snapshot_date(year: int) -> str:
    if not FIRST <= year <= LAST:
        raise ValueError("Year outside reviewed 2006–2025 window")
    return f"{year + 1}0101"


def source_url(year: int) -> str:
    return f"{URL}?date={snapshot_date(year)}&json"


def fetch(year: int) -> bytes:
    req = urllib.request.Request(source_url(year), headers={
        "Accept": "application/json",
        "User-Agent": "WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(req, timeout=40) as response:
        status = response.status
        mime = response.headers.get("Content-Type", "").lower()
        payload = response.read(120_001)
    if status != 200 or not payload or len(payload) > 120_000:
        raise ValueError(f"NBU reserve observation for {year} missing/oversized")
    if "json" not in mime or payload.lstrip().startswith(b"<"):
        raise ValueError("NBU reserves endpoint returned an unexpected format")
    return payload


def parse_annual_record(year: int, payload: bytes) -> dict[str, str]:
    try:
        items = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("NBU did not return valid UTF-8 JSON") from exc
    if not isinstance(items, list) or len(items) < 2:
        raise ValueError("NBU reserves response missing components")
    if any(not isinstance(item, dict) for item in items):
        raise ValueError("NBU reserves must contain JSON objects only")
    snap = snapshot_date(year)
    for item in items:
        if item.get("dt") != snap:
            raise ValueError(f"NBU reserves date changed for {year}")
        if item.get("tzep") != UNIT_CODE or item.get("freq") != "M":
            raise ValueError(f"NBU reserves units/frequency changed for {year}")
    totals = [item for item in items if item.get("id_api") == TOTAL_ID]
    if len(totals) != 1:
        raise ValueError(f"NBU reserves must have one aggregate in {year}")
    total = totals[0]
    if total.get("leveli") != 1 or total.get("txten") != "Official reserve assets":
        raise ValueError("NBU reserves hierarchy / aggregate label changed")
    try:
        value = Decimal(str(total["value"]))
    except (KeyError, InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("NBU reserves total is missing or nonnumeric") from exc
    if not value.is_finite() or not Decimal(0) < value < Decimal(250_000):
        raise ValueError(f"Invalid US$ million reserve assets in {year}")
    if year in ANCHORS and value != ANCHORS[year]:
        raise ValueError(f"NBU reserves year-end anchor revised in {year}")
    return {
        "year": str(year),
        "usd_bn": f"{value / 1000:.5f}",
        "source_snapshot_dt": snap,
    }


def render(rows: list[dict[str, str]]) -> str:
    if [int(row["year"]) for row in rows] != list(range(FIRST, LAST + 1)):
        raise ValueError("NBU reserves year-end snapshots incomplete/unsorted")
    stream = StringIO()
    writer = csv.DictWriter(
        stream,
        fieldnames=("year", "usd_bn", "source_snapshot_dt"),
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def main() -> None:
    rows = [parse_annual_record(year, fetch(year))
            for year in range(FIRST, LAST + 1)]
    content = render(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(OUTPUT)
    print(f"NBU official year-end reserves: {FIRST}–{LAST}, US$ billions")
    print(f"Review-only sidecar: {OUTPUT}")


if __name__ == "__main__":
    main()
