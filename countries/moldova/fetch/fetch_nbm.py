#!/usr/bin/env python3
"""Retrieve Moldova's official NBM policy-rate and USD/MDL annual FX history.

Only *_from_nbm.csv REVIEW SIDECARS are generated, never curated tables.
These are two distinct official NBM publications:
  policy changes: https://www.bnm.md/en/export-base-rates?limit=1000
  period-average FX: https://www.bnm.md/en/export-average-rates?date_from=...
Annual *policy* rate is derived as a time-weighted mean of the effective
daily policy setting (not mean of decisions); the year-end setting is a
separate field. Annual *FX* rate is the period average PUBLISHED BY NBM,
NOT a mean of nominal exchange-rate quotes or a sample of dates.

Official currency CSV reports 'Rate' nominal units and 'Rates' nominal
MDL quote: MDL per 1 USD = Rates / Rate. Do not confuse with a market rate.
2026 is deliberately not fetched as a full-year annual observation.

Run: python3 countries/moldova/fetch/fetch_nbm.py
"""
from __future__ import annotations

import csv
import io
import math
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
START, END = 2006, 2025
BASE = "https://www.bnm.md/en/export-base-rates?limit=1000"
FX = ("https://www.bnm.md/en/export-average-rates?"
      "date_from=01.01.{year}&date_to=31.12.{year}")
HEADERS = {"User-Agent": "worldreports-moldova-sourcing/1.0",
           "Accept": "text/csv,text/plain,*/*"}
COLS = ("Valid from:", "Overnight deposits",
        "Basic rate (rate applied on the main short-term monetary policy operation)",
        "Repo rate", "Overnight credits")


def fetch(url: str) -> str:
    """Fetch an official CSV, fail closed on HTML/errors/redirects."""
    for attempt in range(3):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=45) as resp:
                final = resp.geturl()
                if not final.startswith(("https://www.bnm.md/", "https://bnm.md/")):
                    raise ValueError("NBM export redirected outside official domain")
                data = resp.read(1_500_001)
                content_type = resp.headers.get("Content-Type", "").lower()
                if "csv" not in content_type and "text/plain" not in content_type:
                    raise ValueError(f"Unexpected NBM export content type: {content_type}")
                if len(data) > 1_500_000 or len(data) < 20:
                    raise ValueError("NBM CSV response unexpectedly sized")
                text = data.decode("utf-8-sig")
                if text.lstrip().lower().startswith(("<html", "<!doctype")):
                    raise ValueError("NBM HTML error page instead of CSV")
                return text
        except (OSError, ValueError, UnicodeError) as exc:
            if attempt == 2:
                raise RuntimeError(f"NBM source failed, no sidecar written: {url}") from exc
            time.sleep(attempt + 1)
    raise RuntimeError("unreachable")


def as_decimal(value: str) -> float:
    """Accept NBM European decimal or dot, never thousands ambiguity."""
    value = value.strip().replace(",", ".")
    if not value or any(c not in "-0123456789." for c in value):
        raise ValueError(f"Invalid NBM numeric cell: {value!r}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite NBM number")
    return number


def parse_policy(body: str) -> list[tuple[date, float]]:
    rows = list(csv.reader(io.StringIO(body), delimiter=";"))
    if not rows or tuple(s.strip() for s in rows[0]) != COLS:
        raise ValueError(f"NBM base-rate CSV columns unexpectedly changed: {rows[:1]}")
    events: dict[date, float] = {}
    for fields in rows[1:]:
        if not fields or not any(f.strip() for f in fields):
            continue
        # BNM appends a two-field footer after its published rate decisions.
        # Accept that publisher signature only *after* the data, not a
        # generic malformed row which might hide a truncated export.
        if len(fields) == 2 and fields[0].strip() == "Data source:":
            if fields[1].strip() != "BNM" or len(events) < 40:
                raise ValueError("NBM footer misplaced or unexpected")
            break
        if len(fields) != 5:
            raise ValueError(f"Malformed policy-rate row {fields}")
        day, month, year = (int(n) for n in fields[0].strip().split("."))
        when = date(year, month, day)
        rate = as_decimal(fields[2])
        if not 0 <= rate <= 100:
            raise ValueError(f"Implausible policy rate {rate}")
        # Validate all *other* rate cells, even though they are not drawn.
        for i in (1, 3, 4):
            if fields[i].strip():
                as_decimal(fields[i])
        if when in events:
            raise ValueError(f"Duplicate NBM policy date {when}")
        events[when] = rate
    sorted_events = sorted(events.items())
    if len(events) < 40 or sorted_events[0][0] > date(START, 1, 1):
        raise ValueError("Not enough policy history to compute 2006 mean")
    if sorted_events[-1][0] < date(2025, 12, 1):
        raise ValueError("Recent base-rate events missing; review release before publishing")
    # Anchor from the NBM publication, not a proxy:
    expected = {date(2025, 12, 11): 5.0,
                date(2025, 2, 5): 6.5,
                date(2024, 5, 7): 3.6,
                date(2026, 9, 17): 9.0}
    for when, rate in expected.items():
        if events.get(when) != rate:
            raise ValueError(f"NBM policy official rate anchor changed: {when}")
    return sorted_events


def policy_by_year(events: list[tuple[date, float]]) -> dict[int, tuple[float, float]]:
    """Calendar-day weighted policy setting and Dec 31 setting."""
    out = {}
    for year in range(START, END + 1):
        lo, hi = date(year, 1, 1), date(year + 1, 1, 1)
        prev = [(d, v) for d, v in events if d <= lo]
        if not prev:
            continue
        last_rate = prev[-1][1]
        last_day = lo
        area = 0.0
        for effective, rate in events:
            if not lo < effective < hi:
                continue
            area += (effective - last_day).days * last_rate
            last_day = effective
            last_rate = rate
        area += (hi - last_day).days * last_rate
        days = (hi - lo).days
        avg = area / days
        if not 0 <= avg <= 100:
            raise ValueError("Annual policy mean outside plausible bounds")
        out[year] = (avg, last_rate)
    if set(out) != set(range(START, END + 1)):
        raise ValueError("NBM policy historical years are incomplete")
    if out[2025][1] != 5.0 or out[2024][1] != 3.6:
        raise ValueError("NBM year-end policy-rate anchors changed")
    return out


def parse_fx(body: str, year: int) -> float:
    rows = list(csv.reader(io.StringIO(body), delimiter=";"))
    if len(rows) < 5 or rows[0][0].strip() != "Average rates for:":
        raise ValueError("NBM FX export has no period header")
    if rows[0][1:3] != [f"01.01.{year}", f"31.12.{year}"]:
        raise ValueError(f"NBM FX period incorrect for {year}: {rows[0][:3]}")
    hdr = next((i for i, row in enumerate(rows)
                if row[:5] == ["Currency", "Code", "Abbr", "Rate", "Rates"]), None)
    if hdr is None:
        raise ValueError("NBM FX nominal quote header missing")
    matches = [row for row in rows[hdr + 1:] if len(row) >= 5 and row[2] == "USD"]
    if len(matches) != 1 or matches[0][1] != "840":
        raise ValueError(f"Expected exactly one USD currency row in {year}")
    nominal = as_decimal(matches[0][3])
    quote = as_decimal(matches[0][4])
    if nominal not in (1, 10, 100) or not 3 <= quote / nominal <= 50:
        raise ValueError(f"FX annual USD/MDL nominal units implausible in {year}")
    return quote / nominal


def render_policy(data: dict[int, tuple[float, float]]) -> str:
    lines = [
        "# National Bank of Moldova official base-rate changes; 2006-2025 completed years.",
        "# Mean: CALENDAR-DAY-weighted effective base rate, derived from NBM change dates.",
        "# End: NBM base rate in force on December 31; NOT an annual mean.",
        "# Publisher: https://www.bnm.md/en/export-base-rates?limit=1000",
        "year,policy_mean_pct,policy_dec31_pct",
    ]
    for year in range(START, END + 1):
        mean, last = data[year]
        lines.append(f"{year},{mean:.6f},{last:.2f}")
    return "\n".join(lines) + "\n"


def render_fx(data: dict[int, float]) -> str:
    lines = [
        "# NBM official published full-calendar-year USD exchange rate (2006-2025).",
        "# USD/MDL: MDL per exactly ONE USD; computed as 'Rates' / 'Rate' nominal.",
        "# Source: https://www.bnm.md/en/export-average-rates?date_from=01.01.YYYY&date_to=31.12.YYYY",
        "# NBM annual-average publication, not market spot and not partial 2026.",
        "year,mdl_per_usd_annual_avg",
    ]
    for year in range(START, END + 1):
        lines.append(f"{year},{data[year]:.6f}")
    return "\n".join(lines) + "\n"


def main() -> None:
    changes = parse_policy(fetch(BASE))
    policy = policy_by_year(changes)
    fx = {year: parse_fx(fetch(FX.format(year=year)), year)
          for year in range(START, END + 1)}
    if set(fx) != set(range(START, END + 1)):
        raise ValueError("Annual FX history incomplete")
    out = ROOT / "data" / "markets"
    out.mkdir(parents=True, exist_ok=True)
    (out / "policy_from_nbm.csv").write_text(render_policy(policy), encoding="utf-8")
    (out / "usd_mdl_from_nbm.csv").write_text(render_fx(fx), encoding="utf-8")
    print(f"NBM policy: {len(changes)} decisions, "
          f"{min(d for d, _ in changes)}..{max(d for d, _ in changes)}")
    print(f"2024 end={policy[2024][1]:.2f}, 2025 end={policy[2025][1]:.2f}")
    print(f"FX 2024={fx[2024]:.4f} MDL/USD, 2025={fx[2025]:.4f} MDL/USD")
    print("20 annual rows per review sidecar; curated CSVs untouched")


if __name__ == "__main__":
    main()
