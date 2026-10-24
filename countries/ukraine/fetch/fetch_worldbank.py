#!/usr/bin/env python3
"""Stage World Bank WDI comparison observations as a review-only sidecar.

This is a HARMONIZED/REDISTRIBUTED candidate source, not an official national
series. It MUST be declared official: false if ever promoted to SOURCES.yaml.
No existing curated CSV is overwritten, and no chart reads this sidecar.
Use: python3 countries/ukraine/fetch/fetch_worldbank.py
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
SIDE_CAR = ROOT / "data" / "harmonised" / "macro_from_wb.csv"
FIRST, LAST = 2006, 2025

# Data is for UKR (not regional UA estimates). Do not extrapolate missing years.
INDICATORS = {
    "gdp_growth_pct": "NY.GDP.MKTP.KD.ZG",
    "gdp_per_capita_usd": "NY.GDP.PCAP.CD",
    "gdp_nominal_usd": "NY.GDP.MKTP.CD",
    "exports_gs_pct_gdp": "NE.EXP.GNFS.ZS",
    "imports_gs_pct_gdp": "NE.IMP.GNFS.ZS",
    "population": "SP.POP.TOTL",
}
BASE = "https://api.worldbank.org/v2/country/UKR/indicator"


def indicator_url(code: str) -> str:
    if code not in INDICATORS.values():
        raise ValueError(f"Unexpected WDI indicator {code!r}")
    params = urllib.parse.urlencode({
        "format": "json", "date": f"{FIRST}:{LAST}", "per_page": "100",
    })
    return f"{BASE}/{code}?{params}"


def download_json(url: str, *, limit: int = 3_000_000):
    req = urllib.request.Request(url, headers={
        "User-Agent": "WorldReports-Ukraine-Research/0.1",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        status = response.getcode()
        ctype = response.headers.get("Content-Type", "").lower()
        payload = response.read(limit + 1)
    if status != 200 or not payload or len(payload) > limit or "html" in ctype:
        raise ValueError("Unexpected WDI status, size or content type")
    try:
        return json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("WDI returned malformed JSON") from exc


def parse_series(payload, code: str) -> dict[int, float | None]:
    """Check pagination, indicator and country; preserve missing years."""
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError("WDI response must be [metadata, observations]")
    meta, observations = payload
    if not isinstance(meta, dict) or not isinstance(observations, list):
        raise ValueError("Invalid WDI metadata/observation shape")
    if int(meta.get("pages", 0)) != 1:
        raise ValueError("WDI pagination changed; refusing partial series")
    result: dict[int, float | None] = {}
    for row in observations:
        if not isinstance(row, dict):
            raise ValueError("Malformed WDI observation")
        if (row.get("indicator") or {}).get("id") != code:
            raise ValueError("WDI wrong indicator in response")
        if row.get("countryiso3code") != "UKR":
            raise ValueError("WDI country scope changed")
        yr = str(row.get("date", ""))
        if not yr.isdigit() or len(yr) != 4:
            raise ValueError("Expected annual WDI observation")
        year = int(yr)
        if not FIRST <= year <= LAST:
            raise ValueError("Observation outside requested window")
        if year in result:
            raise ValueError("Duplicate WDI year")
        value = row.get("value")
        if value is None:
            result[year] = None
        else:
            num = float(value)
            if not math.isfinite(num):
                raise ValueError("Non-finite WDI value")
            result[year] = num
    if len(result) < 10:
        raise ValueError("WDI returned an unexpectedly short series")
    return result


def to_csv_text(series_by_name: dict[str, dict[int, float | None]]) -> str:
    from io import StringIO
    out = StringIO()
    fields = ["year", *INDICATORS]
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for year in range(FIRST, LAST + 1):
        row: dict[str, str | int] = {"year": year}
        for name in INDICATORS:
            value = series_by_name[name].get(year)
            row[name] = "" if value is None else str(value)
        writer.writerow(row)
    return out.getvalue()


def run() -> None:
    series = {}
    for name, code in INDICATORS.items():
        raw = download_json(indicator_url(code))
        series[name] = parse_series(raw, code)
        available = sum(value is not None for value in series[name].values())
        print(f"{name}: {available} of {FIRST}-{LAST} observations available")
    # All network and schema checks succeeded before writing a sidecar.
    SIDE_CAR.parent.mkdir(parents=True, exist_ok=True)
    temp = SIDE_CAR.with_suffix(".tmp")
    temp.write_text(to_csv_text(series), encoding="utf-8")
    temp.replace(SIDE_CAR)
    print(f"Review-only WDI sidecar: {SIDE_CAR}")
    print("Do not commit as an accepted dataset before checking publication vintage, scope and definitions.")


if __name__ == "__main__":
    run()
