#!/usr/bin/env python3
"""Stage official NBU USD/UAH annual daily-average history for human review.

The NBU exchange_site endpoint reports rate for 'units' of foreign currency.
Older rows commonly have units=100; never read their 'rate' as UAH for 1 USD.
The normalized 'rate_per_unit' is preferred and cross-checked where present.

Output is a review-only *_from_nbu.csv sidecar, never an accepted chart CSV.
Usage:
    python3 countries/ukraine/fetch/fetch_nbu_fx.py --from-year 2006 --to-year 2025
Network access is confined to this fetcher, never part of a site render.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
import json
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "markets" / "fx_from_nbu.csv"
URL = "https://bank.gov.ua/NBU_Exchange/exchange_site"
START_YEAR, LAST_FULL_YEAR = 2006, 2025

# Checked against the NBU's live archive on 2026-10-24.
# Date: normalized official rate for ONE USD in UAH, not the quoted lot value.
ANCHORS = {
    "2006-01-01": Decimal("5.05"),   # NBU quoted 505.00 for 100 USD
    "2014-01-01": Decimal("7.993"),  # NBU quoted 799.30 for 100 USD
    "2022-01-04": Decimal("27.2782"),
}
TOLERANCE = Decimal("0.00015")


def make_url(year: int) -> str:
    if not START_YEAR <= year <= LAST_FULL_YEAR:
        raise ValueError(f"Only complete, historical {START_YEAR}–{LAST_FULL_YEAR} years allowed")
    params = urllib.parse.urlencode({
        "start": f"{year}0101",
        "end": f"{year}1231",
        "valcode": "usd",
        "sort": "exchangedate",
        "order": "asc",
    })
    return f"{URL}?{params}&json"


def fetch_bytes(url: str, *, max_bytes: int = 4_000_000) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "WorldReports-Ukraine-Fetch/0.1",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        code = response.getcode()
        ctype = response.headers.get("Content-Type", "").lower()
        raw = response.read(max_bytes + 1)
    if code != 200 or not raw or len(raw) > max_bytes:
        raise ValueError("NBU returned missing, non-200 or oversized response")
    if "html" in ctype or raw.lstrip().lower().startswith((b"<html", b"<!doctype")):
        raise ValueError("NBU endpoint returned HTML, not exchange rate JSON")
    return raw


def read_daily_rates(raw: bytes, year: int) -> dict[date, Decimal]:
    """Fail on any incomplete year, duplicate date, currency or unit mismatch."""
    try:
        rows = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{year}: NBU returned invalid JSON") from exc
    if not isinstance(rows, list):
        raise ValueError(f"{year}: expected a JSON list")
    dates: dict[date, Decimal] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{year}: malformed row")
        if row.get("cc") != "USD" or int(row.get("r030", 840)) != 840:
            raise ValueError(f"{year}: wrong currency/ISO numeric code")
        try:
            observed = datetime.strptime(row["exchangedate"], "%d.%m.%Y").date()
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{year}: invalid exchange date") from exc
        if observed.year != year:
            raise ValueError(f"{year}: off-year daily observation")
        if observed in dates:
            raise ValueError(f"{year}: duplicate observation {observed}")
        try:
            units = Decimal(str(row["units"]))
            quoted = Decimal(str(row["rate"]))
            per_one = Decimal(str(row.get("rate_per_unit", quoted / units)))
        except (KeyError, TypeError, InvalidOperation, ZeroDivisionError) as exc:
            raise ValueError(f"{year}: invalid rate or quote units") from exc
        if units <= 0 or quoted <= 0 or per_one <= 0 or not per_one.is_finite():
            raise ValueError(f"{year}: invalid nonpositive/nonfinite rate")
        # API values are rounded; flag discrepancies not explained by rounding.
        if abs(per_one - quoted / units) > TOLERANCE:
            raise ValueError(f"{year}: normalized rate inconsistent with units")
        anchor = ANCHORS.get(observed.isoformat())
        if anchor is not None and abs(per_one - anchor) > TOLERANCE:
            raise ValueError(f"{observed}: official reference check failed")
        dates[observed] = per_one
    first = date(year, 1, 1)
    last = date(year, 12, 31)
    days = (last - first).days + 1
    if len(dates) != days or any(first + timedelta(days=i) not in dates for i in range(days)):
        raise ValueError(f"{year}: incomplete daily time series ({len(dates)}/{days}); no annual average")
    return dates


def annual_average(values: dict[date, Decimal]) -> Decimal:
    if not values:
        raise ValueError("Cannot average empty FX observations")
    return sum(values.values()) / Decimal(len(values))


def stage_all(years: range, *, fetch=fetch_bytes) -> str:
    """Only return the CSV after EVERY requested year validates successfully."""
    results = []
    for year in years:
        rates = read_daily_rates(fetch(make_url(year)), year)
        results.append((year, annual_average(rates), len(rates)))
    out = StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["year", "avg_uah_per_usd", "daily_observations"])
    for year, avg, days in results:
        writer.writerow([year, f"{avg:.8f}", days])
    return out.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-year", type=int, default=START_YEAR)
    parser.add_argument("--to-year", type=int, default=LAST_FULL_YEAR)
    args = parser.parse_args()
    if not START_YEAR <= args.from_year <= args.to_year <= LAST_FULL_YEAR:
        parser.error("Only fully completed 2006–2025 years are supported")
    staged = stage_all(range(args.from_year, args.to_year + 1))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(staged, encoding="utf-8")
    tmp.replace(OUTPUT)
    print(f"Staged {args.from_year}–{args.to_year} NBU FX sidecar: {OUTPUT}")
    print("Review definitions, coverage, anchors and derived 2006=100 index before promotion.")


if __name__ == "__main__":
    main()
