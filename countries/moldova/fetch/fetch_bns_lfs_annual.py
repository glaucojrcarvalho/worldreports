#!/usr/bin/env python3
"""Read-only BNS annual unemployment extraction with survey-break segmentation.

ONLY the publisher's MUN160100_2025 coded four-dimension table, for
Both sexes / Whole country / Annual average / 2019–2025. The 2025
national figure has a new EMDOS-3/2024-census-weighting methodology;
never connect 2024 to 2025, splice 2000–18 surveys, or overwrite
the separate WDI ILO-modelled unemployment chart.

Writes a CSV review sidecar, not an atlas publication dataset.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

from countries.moldova.fetch import fetch_bns_lfs as metadata

OUT = Path(__file__).resolve().parents[1] / (
    "data/macro/national_lfs_from_bns.csv")
ANCHOR_2025 = 3.8


def _dimension(variables: list[dict], name: str) -> dict:
    selected = [v for v in variables if v["name"].casefold() == name.casefold()]
    if len(selected) != 1:
        raise ValueError("BNS unemployment dimension changed: " + name)
    return selected[0]


def _unique_code(variable: dict, label: str) -> str:
    values = [x["code"] for x in variable["categories"]
              if x["label"].casefold() == label.casefold()]
    if len(values) != 1:
        raise ValueError(f"Ambiguous BNS {variable['name']} = {label!r}")
    return values[0]


def selection(variables: list[dict]) -> tuple[dict, dict, dict]:
    by = {v["name"]: v["code"] for v in variables}
    if len(by) != 4:
        raise ValueError("Expected four independent BNS dimensions")
    chosen = {
        _dimension(variables, "Sex")["code"]:
            [_unique_code(_dimension(variables, "Sex"), "Both sexes")],
        _dimension(variables, "Area")["code"]:
            [_unique_code(_dimension(variables, "Area"), "Whole country")],
        _dimension(variables, "Quarters")["code"]:
            [_unique_code(_dimension(variables, "Quarters"), "Annual average")],
        _dimension(variables, "Years")["code"]:
            [x["code"] for x in _dimension(variables, "Years")["categories"]
             if x["label"] in {str(y) for y in metadata.YEARS}],
    }
    years = _dimension(variables, "Years")
    label_map = {x["code"]: x["label"] for x in years["categories"]}
    if len(selection_years := chosen[years["code"]]) != len(metadata.YEARS):
        raise ValueError("Missing annual unemployment year codes")
    request = {
        "query": [
            {"code": v["code"], "selection": {
                "filter": "item", "values": chosen[v["code"]]}}
            for v in variables,
        ],
        "response": {"format": "json-stat2"},
    }
    return request, chosen, label_map


def _positions(node: dict, size: int) -> dict[str, int]:
    index = node.get("category", {}).get("index")
    if isinstance(index, list):
        parsed = {str(key): i for i, key in enumerate(index)}
    elif isinstance(index, dict):
        parsed = {str(k): int(v) for k, v in index.items()}
    else:
        raise ValueError("Missing BNS category indexes")
    if sorted(parsed.values()) != list(range(size)):
        raise ValueError("BNS dimension indexes are not a bijection")
    return parsed


def decode(payload: dict, chosen: dict, year_labels: dict) -> dict[int, float]:
    ids = payload.get("id")
    sizes = payload.get("size")
    dim = payload.get("dimension")
    values = payload.get("value")
    if (payload.get("class") != "dataset" or not isinstance(ids, list)
            or set(ids) != set(chosen) or len(ids) != 4
            or not isinstance(sizes, list) or len(sizes) != 4
            or not isinstance(dim, dict) or not isinstance(values, (dict, list))
            or any(not isinstance(n, int) or n < 1 for n in sizes)
            or math.prod(sizes) != len(metadata.YEARS)):
        raise ValueError("Wrong or incomplete BNS annual unemployment JSON-stat grid")
    indexes = {}
    for key, size in zip(ids, sizes):
        indexes[key] = _positions(dim.get(key, {}), size)
        if set(indexes[key]) != set(chosen[key]):
            raise ValueError("Unexpected BNS selection returned")
    if isinstance(values, list) and len(values) != len(metadata.YEARS):
        raise ValueError("Incomplete BNS unemployment annual values")
    if isinstance(values, dict) and any(
        not str(k).isdigit() or int(k) >= len(metadata.YEARS) for k in values
    ):
        raise ValueError("Invalid BNS sparse index")
    years_code = [key for key, vals in chosen.items()
                  if len(vals) == len(metadata.YEARS)]
    if len(years_code) != 1:
        raise ValueError("Could not identify annual BNS year axis")
    year_key = years_code[0]
    readings = {}
    for year_code in chosen[year_key]:
        coords = {key: vals[0] for key, vals in chosen.items()}
        coords[year_key] = year_code
        offset = 0
        for key, size in zip(ids, sizes):
            offset = offset * size + indexes[key][coords[key]]
        raw = values[offset] if isinstance(values, list) else values.get(str(offset))
        if (isinstance(raw, bool) or not isinstance(raw, (int, float))
                or not math.isfinite(raw) or not (0 <= raw <= 30)):
            raise ValueError("Invalid BNS unemployment value for " + year_labels[year_code])
        year = int(year_labels[year_code])
        readings[year] = float(raw)
    if set(readings) != set(metadata.YEARS):
        raise ValueError("BNS annual grid does not cover 2019–2025")
    if abs(readings[2025] - ANCHOR_2025) > 0.051:
        raise ValueError(
            f"BNS 2025 unemployment differs from independent published {ANCHOR_2025}%: "
            f"{readings[2025]}")
    return readings


def sidecar(readings: dict[int, float], source: str, meta_sha: str,
            data_sha: str) -> str:
    out = io.StringIO()
    out.write("# REVIEW ONLY: BNS AFM/LFS official 2019–2025 annual unemployment (%).\n")
    out.write("# Break before 2019: old national LFS survey not spliceable.\n")
    out.write("# Break at 2025: EMDOS 3 + 2024 census weights and 2025 AFM changes.\n")
    out.write("# Columns deliberately DISCONNECTED; never join 2024–2025.\n")
    out.write("# NOT harmonised WDI ILO-modelled unemployment.\n")
    out.write("# Source: " + source + "\n")
    out.write("# Original codebook SHA256: " + meta_sha + "\n")
    out.write("# Original data JSON-stat SHA256: " + data_sha + "\n")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["year", "bns_lfs_2019_2024_pct", "bns_lfs_2025_pct"])
    for year in metadata.YEARS:
        value = f"{readings[year]:.1f}"
        writer.writerow([year, value if year < 2025 else "",
                         value if year == 2025 else ""])
    return out.getvalue()


def main() -> None:
    url, variables, meta_sha = metadata.discover()
    request, chosen, labels = selection(variables)
    req = Request(url, data=json.dumps(request).encode("utf-8"), headers={
        "Content-Type": "application/json", "Accept": "application/json",
        "User-Agent": "worldreports-moldova-bns-lfs-source-audit/1.0",
    })
    with urlopen(req, timeout=45) as response:
        if response.status != 200 or "json" not in response.headers.get(
                "Content-Type", "").lower():
            raise ValueError("BNS annual LFS response not JSON 200")
        body = response.read(300_001)
    if len(body) > 300_000:
        raise ValueError("BNS LFS 7-year response unexpectedly too large")
    digest = hashlib.sha256(body).hexdigest()
    readings = decode(json.loads(body.decode("utf-8-sig")), chosen, labels)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(sidecar(readings, url, meta_sha, digest), encoding="utf-8")
    print("Official BNS unemployment seven annual observations audited.")
    print("2025 = 3.8%, isolated from 2019–2024 due to BNS method break.")
    print("Data SHA256:", digest, "sidecar:", OUT)
    print("No curated atlas CSV, graph or country registration changed.")


if __name__ == "__main__":
    main()
