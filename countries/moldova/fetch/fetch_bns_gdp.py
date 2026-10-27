#!/usr/bin/env python3
"""Independently audit BNS *nominal MDL GDP* for a future national-budget denominator.

BNS CNT208100 publishes GDP, current prices, *thousand MDL*, 2014-2024.
The FIN010100 national public budget uses *million MDL*; both publishers'
metadata exclude the left-bank Nistru districts and Bender. This fetcher
DOES NOT compute spending shares or modify curated data, plates or country
registration. It writes review-only fiscal/nominal_gdp_from_bns.csv.

2025 belongs to a DIFFERENT publisher release (BNS 2026-03-11 GDP press
release, provisional 353,520.9 million MDL) and MUST NOT be filled from
this 2014-2024 table or confused with WDI GDP in current USD.
"""
from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://statbank.statistica.md/PxWeb/api/v1/en/"
ROOT_TABLE = "40%20Statistica%20economica"
TARGET = "CNT208100.px"
OUTPUT = ROOT / "data" / "fiscal" / "nominal_gdp_from_bns.csv"
YEARS = tuple(range(2016, 2025))
# BNS CNT208100 table as verified in the publisher interface in Oct 2026.
ANCHORS_THOUSAND_MDL = {2023: 303554038.0, 2024: 323932494.0}


def fetch_json(url: str, payload: dict | None = None):
    headers = {"User-Agent": "worldreports-moldova-bns-gdp-source-audit/1.0",
               "Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    with urlopen(Request(url, headers=headers, data=data), timeout=60) as r:
        if r.status != 200 or "json" not in r.headers.get("Content-Type", "").lower():
            raise ValueError("BNS did not return JSON data")
        raw = r.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("BNS GDP API response unexpectedly large")
    return json.loads(raw)


def discover_api() -> tuple[str, dict]:
    """Try known PxWeb folder shapes; fall back to bounded official API tree."""
    candidates = [
        ROOT_TABLE + "/13%20CNT/CNT208/CNT208100.px",
        ROOT_TABLE + "/13%20CNT/CNT208100.px",
        ROOT_TABLE + "/CNT208/CNT208100.px",
        ROOT_TABLE + "/CNT208100.px",
    ]
    for path in candidates:
        try:
            body = fetch_json(BASE + path)
            if isinstance(body, dict) and isinstance(body.get("variables"), list):
                return BASE + path, body
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    queue = [ROOT_TABLE]
    visited = set()
    while queue and len(visited) < 100:
        path = queue.pop(0)
        if path in visited:
            continue
        visited.add(path)
        try:
            entries = fetch_json(BASE + path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if not isinstance(entries, list):
            continue
        for item in entries:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            ident = item["id"]
            next_path = path + "/" + quote(ident, safe="")
            if ident.lower() == TARGET.lower():
                payload = fetch_json(BASE + next_path)
                if isinstance(payload, dict) and isinstance(payload.get("variables"), list):
                    return BASE + next_path, payload
            if item.get("type") == "l" and len(next_path.split("/")) < 7:
                # Only descend into national-accounts branches, not every
                # economic topic in the statistical database.
                if "cnt" in ident.lower() or "national" in str(item.get("text", "")).lower():
                    queue.append(next_path)
    raise ValueError("CNT208100 was not found in the BNS API; do not synthesize GDP")


def metadata_codes(payload: dict) -> tuple[str, str, str, dict]:
    variables = payload.get("variables")
    if not isinstance(variables, list) or len(variables) != 2:
        raise ValueError("CNT208100 dimensions changed")
    maps = {}
    for var in variables:
        codes, texts = var.get("values"), var.get("valueTexts")
        if not isinstance(codes, list) or not isinstance(texts, list) or len(codes) != len(texts):
            raise ValueError("Invalid BNS GDP metadata")
        if len(set(str(x) for x in codes)) != len(codes):
            raise ValueError("Duplicate BNS GDP category codes")
        maps[var["code"]] = dict(zip(map(str, codes), map(str, texts)))
    indicator_dims = [k for k, m in maps.items()
                      if any("GDP, current prices, thousand Lei" == v.strip()
                             for v in m.values())]
    year_dims = [k for k, m in maps.items()
                 if set(map(str, YEARS)).issubset(set(m.values()))]
    if len(indicator_dims) != 1 or len(year_dims) != 1 or indicator_dims == year_dims:
        raise ValueError("Missing nominal-MDL GDP indicator or 2016-24 years")
    indicator_dim, year_dim = indicator_dims[0], year_dims[0]
    gdp_codes = [code for code, label in maps[indicator_dim].items()
                 if label.strip() == "GDP, current prices, thousand Lei"]
    if len(gdp_codes) != 1:
        raise ValueError("Ambiguous GDP definition or thousand-Lei unit")
    return indicator_dim, year_dim, gdp_codes[0], maps


def decode(payload: dict, indicator_dim: str, year_dim: str,
           indicator_code: str, maps: dict) -> dict[int, float]:
    ids, sizes = payload.get("id"), payload.get("size")
    dims, cells = payload.get("dimension"), payload.get("value")
    if (payload.get("class") != "dataset" or not isinstance(ids, list)
            or set(ids) != {indicator_dim, year_dim}
            or not isinstance(sizes, list) or len(sizes) != 2
            or not isinstance(dims, dict) or not isinstance(cells, (dict, list))):
        raise ValueError("Invalid BNS GDP JSON-stat response")
    positions = {}
    for name, size in zip(ids, sizes):
        category = dims.get(name, {}).get("category", {})
        index = category.get("index")
        if isinstance(index, dict):
            positions[name] = {str(k): int(v) for k, v in index.items()}
        elif isinstance(index, list):
            positions[name] = {str(k): i for i, k in enumerate(index)}
        else:
            raise ValueError("Missing JSON-stat category index")
        if sorted(positions[name].values()) != list(range(size)):
            raise ValueError("JSON-stat position mismatch")
    expected_year_codes = {code for code, label in maps[year_dim].items()
                           if label in set(map(str, YEARS))}
    if set(positions[indicator_dim]) != {indicator_code} or set(positions[year_dim]) != expected_year_codes:
        raise ValueError("Unexpected indicator or incomplete year selection")
    n = math.prod(sizes)
    if n != len(YEARS) or (isinstance(cells, list) and len(cells) != n):
        raise ValueError("Truncated year grid")
    result = {}
    for code in expected_year_codes:
        coord = {indicator_dim: indicator_code, year_dim: code}
        offset = 0
        for name, size in zip(ids, sizes):
            offset = offset * size + positions[name][coord[name]]
        raw = cells[offset] if isinstance(cells, list) else cells.get(str(offset))
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw) or raw <= 0:
            raise ValueError("Missing or invalid nominal GDP in year " + maps[year_dim][code])
        year = int(maps[year_dim][code])
        result[year] = float(raw)
    if set(result) != set(YEARS):
        raise ValueError("BNS GDP coverage differs from requested completed years")
    return result


def verify_anchors(rows: dict[int, float]) -> None:
    for year, expected in ANCHORS_THOUSAND_MDL.items():
        if abs(rows[year] - expected) > 1.1:
            raise ValueError(f"Published BNS GDP anchor changed for {year}: {rows[year]}; "
                             "review revisions before adopting")


def sidecar(rows: dict[int, float], api_url: str) -> str:
    buffer = io.StringIO()
    buffer.write("# REVIEW ONLY BNS CNT208100 current-price GDP, thousand MDL, NOT USD.\n")
    buffer.write("# 2016-2024: source table; 2025 preliminary is a separate press release.\n")
    buffer.write("# Geography: excludes left-bank Nistru districts and municipality Bender.\n")
    buffer.write("# Source: " + api_url + "\n")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["year", "gdp_mdl_mn"])
    for year in sorted(rows):
        writer.writerow([year, f"{rows[year] / 1000:.3f}"])
    return buffer.getvalue()


def main() -> None:
    url, metadata = discover_api()
    indicator_dim, year_dim, indicator_code, maps = metadata_codes(metadata)
    selected_years = [code for code, label in maps[year_dim].items()
                      if label in set(map(str, YEARS))]
    request = {
        "query": [
            {"code": indicator_dim, "selection": {"filter": "item",
                                                  "values": [indicator_code]}},
            {"code": year_dim, "selection": {"filter": "item",
                                             "values": selected_years}},
        ],
        "response": {"format": "json-stat2"},
    }
    rows = decode(fetch_json(url, request), indicator_dim, year_dim, indicator_code, maps)
    verify_anchors(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(sidecar(rows, url), encoding="utf-8")
    print(f"Verified BNS CNT208100 nominal GDP, {len(rows)} annual rows 2016-24")
    for year in (2023, 2024):
        print(f"{year}: {rows[year]/1000:.3f} million MDL (BNS PxWeb)")
    print("2025: NOT in this API edition; see BNS 2026-03-11 provisional press.")
    print("REVIEW SIDECAR ONLY. No canonical spending plate or published registry changed.")


if __name__ == "__main__":
    main()
