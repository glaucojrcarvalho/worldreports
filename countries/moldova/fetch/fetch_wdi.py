#!/usr/bin/env python3
"""Fetch Moldova's World Bank WDI comparables into review-only sidecars.

    python3 countries/moldova/fetch/fetch_wdi.py
    python3 countries/moldova/fetch/fetch_wdi.py --refresh

The country is in source-research phase, not yet published. No network calls
are made by a site build, and this fetcher *never* modifies the reviewed
data/*.csv. A human inspects diffs from *_from_wb.csv before accepting data.

Publisher: World Bank WDI API (source=2), country MDA. Historical window
2006..2025; 2026 is running and no 2026 flows are accepted. A missing
observation is a blank cell, never zero, interpolation or a carried value.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
YEAR_FROM = 2006
YEAR_TO = 2025
SOURCE = "https://api.worldbank.org/v2/country/MDA/indicator/{code}?format=json&per_page=100&date=2006:2025"

# (output file, (column name, WDI indicator code) ...).  The exact same
# files, columns and metadata are documented in ../SOURCES.yaml.
GROUPS: dict[str, tuple[tuple[str, str], ...]] = {
    "macro/economy.csv": (
        ("gdp_growth_pct", "NY.GDP.MKTP.KD.ZG"),
        ("cpi_inflation_pct", "FP.CPI.TOTL.ZG"),
        ("unemployment_pct", "SL.UEM.TOTL.ZS"),
        ("gfcf_pct_gdp", "NE.GDI.FTOT.ZS"),
    ),
    "world/world.csv": (
        ("gdp_usd", "NY.GDP.MKTP.CD"),
        ("gdp_per_person_usd", "NY.GDP.PCAP.CD"),
        ("reserves_usd", "FI.RES.TOTL.CD"),
    ),
    "people/gini.csv": (("gini", "SI.POV.GINI"),),
    # Financial-corporation claims to all private borrowers, not households.
    "credit/private_credit.csv": (
        ("private_credit_pct_gdp", "FS.AST.PRVT.GD.ZS"),
    ),
    "trade/trade.csv": (
        ("exports_pct_gdp", "NE.EXP.GNFS.ZS"),
        ("imports_pct_gdp", "NE.IMP.GNFS.ZS"),
    ),
    "demography/demography.csv": (
        ("population", "SP.POP.TOTL"),
        ("fertility", "SP.DYN.TFRT.IN"),
        ("birth_rate_per_1000", "SP.DYN.CBRT.IN"),
        ("death_rate_per_1000", "SP.DYN.CDRT.IN"),
    ),
    "mortality/mortality.csv": (
        ("death_rate_per_1000", "SP.DYN.CDRT.IN"),
        ("life_expectancy", "SP.DYN.LE00.IN"),
    ),
    "security/security.csv": (
        ("homicide_per_100k", "VC.IHR.PSRC.P5"),
        ("suicide_per_100k", "SH.STA.SUIC.P5"),
        ("road_deaths_per_100k", "SH.STA.TRAF.P5"),
    ),
    "migration/migration.csv": (
        ("net_migration", "SM.POP.NETM"),
        ("migrant_stock", "SM.POP.TOTL"),
    ),
}


def validate_wdi_payload(payload: object, code: str) -> tuple[dict[int, float], str]:
    """Reject truncated pages, error objects, duplicate years or wrong codes."""
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError(f"{code}: expected WDI [metadata, rows] response")
    meta, rows = payload
    if not isinstance(meta, dict) or not isinstance(rows, list):
        raise ValueError(f"{code}: bad WDI response shapes")
    if (meta.get("pages") != 1 or meta.get("page") != 1
            or str(meta.get("sourceid")) != "2"
            or meta.get("total") != len(rows)):
        raise ValueError(f"{code}: incomplete pages/source mismatch: {meta}")
    updated = meta.get("lastupdated")
    if not isinstance(updated, str) or len(updated) != 10:
        raise ValueError(f"{code}: missing source vintage")
    values: dict[int, float] = {}
    seen: set[int] = set()
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError(f"{code}: invalid observation")
        if (item.get("indicator", {}).get("id") != code
                or item.get("countryiso3code") != "MDA"):
            raise ValueError(f"{code}: wrong country or series in response")
        year_text = item.get("date")
        if not isinstance(year_text, str) or not year_text.isdigit():
            raise ValueError(f"{code}: unexpected period {year_text!r}")
        year = int(year_text)
        if year in seen:
            raise ValueError(f"{code}: duplicate year {year}")
        seen.add(year)
        if not YEAR_FROM <= year <= YEAR_TO:
            raise ValueError(f"{code}: out-of-window year {year}")
        if item.get("obs_status") == "F":
            raise ValueError(f"{code}: forecast value {year} in observed CSV")
        number = item.get("value")
        if number is not None:
            if isinstance(number, bool) or not isinstance(number, (float, int)):
                raise ValueError(f"{code}: nonnumeric value in {year}")
            if not math.isfinite(number):
                raise ValueError(f"{code}: non-finite value in {year}")
            values[year] = float(number)
    if not values or len(seen) < 4:
        raise ValueError(f"{code}: too few WDI observations")
    return values, updated


def fetch_indicator(code: str, *, refresh: bool = False) -> tuple[dict[int, float], str]:
    """Cache *validated* payloads and retry network failures; fail closed."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"wdi_{code}.json"
    if path.exists() and not refresh:
        return validate_wdi_payload(json.loads(path.read_text("utf-8")), code)

    for attempt in range(3):
        try:
            request = Request(SOURCE.format(code=code),
                              headers={"User-Agent": "worldreports-moldova-research/1.0"})
            with urlopen(request, timeout=45) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}")
                payload = json.load(response)
            parsed = validate_wdi_payload(payload, code)
            path.write_text(json.dumps(payload, ensure_ascii=False) + "\n",
                            encoding="utf-8")
            return parsed
        except (HTTPError, URLError, OSError, ValueError, KeyError) as exc:
            print(f"  {code}, attempt {attempt + 1}: {exc}", file=sys.stderr)
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{code}: source could not be verified")


def sidecar_text(columns: tuple[tuple[str, str], ...],
                 data: dict[str, dict[int, float]], vintage: str) -> str:
    """Every year is explicit, gaps remain blank, float precision is fixed."""
    all_years = range(YEAR_FROM, YEAR_TO + 1)
    header = [
        "# World Bank WDI source=2, country=MDA, retrieved into review sidecar.",
        f"# WDI lastupdated={vintage}; indicators=" + ", ".join(code for _, code in columns),
        "# NOT a BNS national series. Check territory and publisher scope.",
        "year," + ",".join(col for col, _ in columns),
    ]
    for year in all_years:
        cells = [
            f"{data[code][year]:.6f}" if year in data[code] else ""
            for _, code in columns
        ]
        header.append(f"{year}," + ",".join(cells))
    return "\n".join(header) + "\n"


def verify_anchors(data: dict[str, dict[int, float]]) -> None:
    """Publisher sample checks for material data/schema shifts."""
    growth = data["NY.GDP.MKTP.KD.ZG"]
    population = data["SP.POP.TOTL"]
    assert abs(growth[2025] - 2.41649734575) < 0.1, "WDI growth 2025 revised"
    assert abs(growth[2024] - 0.2706704555) < 0.1, "WDI growth 2024 revised"
    assert abs(population[2024] - 2_402_306) < 20_000, "WDI population 2024 revised"
    assert abs(population[2025] - 2_360_527) < 20_000, "WDI population 2025 revised"
    # Migration stocks are point-in-time snapshots, never an annual series.
    stock = data["SM.POP.TOTL"]
    assert set(stock) == {2010, 2015, 2020, 2024}, "WDI migrant-stock years changed"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true",
                        help="ignore validated cache; retrieve latest API snapshot")
    args = parser.parse_args()
    codes = sorted({code for spec in GROUPS.values() for _, code in spec})
    fetched = {code: fetch_indicator(code, refresh=args.refresh) for code in codes}
    series = {code: response[0] for code, response in fetched.items()}
    verify_anchors(series)
    for rel, columns in GROUPS.items():
        vintages = {fetched[code][1] for _, code in columns}
        if len(vintages) != 1:
            raise RuntimeError(f"{rel}: different indicator vintages: {vintages}")
        base = ROOT / "data" / rel
        sidecar = base.with_name(base.stem + "_from_wb.csv")
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text(sidecar_text(columns, series, vintages.pop()),
                           encoding="utf-8")
        print(f"{sidecar.relative_to(ROOT)}: {YEAR_TO - YEAR_FROM + 1} years")
    print("Review diffs against committed data/*.csv; no curated file modified.")


if __name__ == "__main__":
    main()
