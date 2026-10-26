#!/usr/bin/env python3
"""Retrieve two DIFFERENT IMF datasets for Moldova to review-only sidecars.

Usage:
    python3 countries/moldova/fetch/fetch_imf.py

DataMapper v2 is a convenient distribution interface, not a consistent
single WEO table. Its GGXCNL_NGDP and GGXWDG_NGDP are from the OCTOBER 2026
World Economic Outlook (WEO); its rev, exp, pb and ie are actually from
Public Finances in Modern History (FPP), DECEMBER 2025. They must never be
spliced into one source-labelled "WEO fiscal" observation.

Two independently attributed review CSVs are written:
    data/fiscal/weo_bal_debt_from_imf.csv
    data/fiscal/fpp_finances_from_imf.csv
No curated CSV is ever overwritten. Values from year >= the IMF's reported
projection-year are stored ONLY in *_proj columns. At the October 2026
WEO release the projection year starts in 2026; a 2025 WEO historical
estimate does not imply an audited final national outturn.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
START, END = 2006, 2026
COUNTRY = "MDA"
IMF_API = "https://www.imf.org/external/datamapper/api/v2/{code}/MDA?periods={years}"

# Dataset, publisher vintage and API code are checked on EVERY response.
SPECS = {
    "GGXCNL_NGDP": ("WEO", "World Economic Outlook (October 2026)", "balance_pct_gdp"),
    "GGXWDG_NGDP": ("WEO", "World Economic Outlook (October 2026)", "debt_pct_gdp"),
    "rev": ("FPP", "Public Finances in Modern History Database (Dec 2025)", "revenue_pct_gdp"),
    "exp": ("FPP", "Public Finances in Modern History Database (Dec 2025)", "expenditure_pct_gdp"),
    "pb": ("FPP", "Public Finances in Modern History Database (Dec 2025)", "primary_balance_pct_gdp"),
    "ie": ("FPP", "Public Finances in Modern History Database (Dec 2025)", "interest_pct_gdp"),
}
WEO_CODES = ("GGXCNL_NGDP", "GGXWDG_NGDP")
FPP_CODES = ("rev", "exp", "pb", "ie")


def validate(payload: object, code: str) -> tuple[dict[int, float], dict]:
    """Fail closed on wrong country, indicator, vintage, units and periods."""
    if code not in SPECS:
        raise ValueError(f"Unapproved IMF indicator {code}")
    if not isinstance(payload, dict):
        raise ValueError(f"{code}: IMF DataMapper response must be JSON object")
    fields = SPECS[code]
    indicator = payload.get("indicators", {}).get(code)
    if not isinstance(indicator, dict):
        raise ValueError(f"{code}: indicator metadata missing")
    if indicator.get("dataset") != fields[0] or indicator.get("source") != fields[1]:
        raise ValueError(f"{code}: publisher dataset/vintage mismatch")
    if indicator.get("unit") not in {"Percent of GDP", "% of GDP"}:
        raise ValueError(f"{code}: units must be % GDP")
    projection = indicator.get("projection-year")
    if fields[0] == "WEO":
        if projection != 2026:
            raise ValueError(f"{code}: unexpected WEO projection boundary")
    elif projection is not None:
        raise ValueError(f"{code}: FPP must not silently acquire forecasts")
    mapping = payload.get("values", {}).get(code)
    if not isinstance(mapping, dict) or COUNTRY not in mapping:
        raise ValueError(f"{code}: Moldova MDA series not found")
    source = mapping[COUNTRY]
    if not isinstance(source, dict):
        raise ValueError(f"{code}: invalid Moldova indicator values")
    data: dict[int, float] = {}
    for year_text, raw in source.items():
        if not (isinstance(year_text, str) and len(year_text) == 4
                and year_text.isdigit()):
            raise ValueError(f"{code}: invalid year key {year_text!r}")
        year = int(year_text)
        if not START <= year <= END:
            continue  # DataMapper may return extra years or other countries.
        if isinstance(raw, bool) or not isinstance(raw, (float, int)) or not math.isfinite(raw):
            raise ValueError(f"{code}: invalid numeric value for {year}")
        data[year] = float(raw)
    if len(data) < 15 or not all(y in data for y in range(2006, 2025)):
        raise ValueError(f"{code}: incomplete historical series")
    if fields[0] == "WEO":
        if not all(y in data for y in (2024, 2025, 2026)):
            raise ValueError(f"{code}: WEO missing 2024–2026 vintage window")
    else:
        if set(data) != set(range(2006, 2025)):
            raise ValueError(f"{code}: FPP country coverage changed; review first")
    return data, indicator


def fetch(code: str) -> tuple[dict[int, float], dict]:
    """Cache only validated payloads; retry transient transport failures."""
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / f"imf_{code}_MDA.json"
    if cached.exists():
        return validate(json.loads(cached.read_text(encoding="utf-8")), code)
    for attempt in range(3):
        try:
            years = ",".join(str(y) for y in range(START, END + 1))
            req = Request(IMF_API.format(code=code, years=years),
                          headers={"User-Agent": "worldreports-moldova/1.0",
                                   "Accept": "application/json"})
            with urlopen(req, timeout=80) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}")
                payload = json.load(response)
            validated = validate(payload, code)
            # Store Moldova-only slice, not every country's history.
            slim = {"indicators": {code: payload["indicators"][code]},
                    "values": {code: {COUNTRY: payload["values"][code][COUNTRY]}}}
            cached.write_text(json.dumps(slim, sort_keys=True) + "\n", encoding="utf-8")
            return validated
        except (OSError, HTTPError, URLError, ValueError, KeyError) as e:
            if attempt == 2:
                raise RuntimeError(f"{code}: IMF live fetch failed safely") from e
            time.sleep(attempt + 1)
    raise RuntimeError("Unreachable")


def render_weo(seen: dict[str, tuple[dict[int, float], dict]]) -> str:
    a, ma = seen["GGXCNL_NGDP"]
    b, mb = seen["GGXWDG_NGDP"]
    if ma["projection-year"] != mb["projection-year"]:
        raise ValueError("IMF WEO series have different projection boundaries")
    lines = [
        "# IMF World Economic Outlook, OCTOBER 2026, Moldova MDA, annual % GDP.",
        "# DataMapper v2 metadata: WEO, projection-year=2026.",
        "# 2026 WEO estimates are PROJECTIONS, not historical realised totals.",
        "# 2025 is in the pre-projection range but is NOT claimed final/audited.",
        "# National BNS cash budget is different scope; NEVER splice.",
        "year,balance_pct_gdp,balance_pct_gdp_proj,debt_pct_gdp,debt_pct_gdp_proj",
    ]
    for year in range(START, END + 1):
        ba = f"{a[year]:.6f}" if year in a else ""
        de = f"{b[year]:.6f}" if year in b else ""
        if year < ma["projection-year"]:
            cells = [ba, "", de, ""]
        else:
            cells = ["", ba, "", de]
        lines.append(f"{year}," + ",".join(cells))
    return "\n".join(lines) + "\n"


def render_fpp(seen: dict[str, tuple[dict[int, float], dict]]) -> str:
    lines = [
        "# IMF Public Finances in Modern History, DECEMBER 2025, Moldova MDA.",
        "# NOT IMF WEO; it is a separate dataset and vintage.",
        "# Annual % GDP through 2024 ONLY. 2025 is not published in this FPP snapshot.",
        "# Revenues - expenditure should reconcile with primary balance - interest",
        "# at source numerical precision; never force match to another WEO vintage.",
        "year,revenue_pct_gdp,expenditure_pct_gdp,primary_balance_pct_gdp,interest_pct_gdp",
    ]
    for year in range(START, 2025):
        cells = [f"{seen[code][0][year]:.6f}" for code in FPP_CODES]
        lines.append(f"{year}," + ",".join(cells))
    return "\n".join(lines) + "\n"


def verify(seen: dict[str, tuple[dict[int, float], dict]]) -> None:
    """Pin current publisher snapshots, not values from different vintages."""
    if set(seen) != set(SPECS):
        raise ValueError("Missing IMF indicators")
    weo = seen["GGXCNL_NGDP"][0]
    debt = seen["GGXWDG_NGDP"][0]
    if abs(weo[2024] - -4.0) > .2 or abs(weo[2025] - -3.9) > .2:
        raise ValueError("October 2026 WEO balance anchor revised; manual review")
    if abs(debt[2024] - 38.8) > .2 or abs(debt[2025] - 39.2) > .2:
        raise ValueError("October 2026 WEO debt anchor revised; manual review")
    for year in range(START, 2025):
        fpp = {code: seen[code][0][year] for code in FPP_CODES}
        if abs((fpp["rev"] - fpp["exp"]) - (fpp["pb"] - fpp["ie"])) > 0.1:
            raise ValueError(f"FPP {year}: within-dataset fiscal identities disagree")
    # An explicit non-equality guards against writing a fused series.
    fpp_2024 = seen["rev"][0][2024] - seen["exp"][0][2024]
    if abs(weo[2024] - fpp_2024) < 0.001:
        # Equality isn't inherently wrong, but a potential source/vintage
        # switch deserves human inspection before we accept it.
        raise ValueError("Unexpected agreement in 2024 WEO/FPP vintages: inspect")


def main() -> None:
    seen = {code: fetch(code) for code in SPECS}
    verify(seen)
    outputs = {
        "weo_bal_debt_from_imf.csv": render_weo(seen),
        "fpp_finances_from_imf.csv": render_fpp(seen),
    }
    for name, body in outputs.items():
        out = ROOT / "data" / "fiscal" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        print(f"{out.relative_to(ROOT)}: review-only, no curated CSV overwritten")


if __name__ == "__main__":
    main()
