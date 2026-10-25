#!/usr/bin/env python3
"""Probe BNS Moldova national public-budget execution (FIN010100).

    python3 countries/moldova/fetch/fetch_bns_budget.py

The BNS 2016–2026 PxWeb table republishes Ministry of Finance national public
budget execution. Select January–December, million MDL, 2016–2025 only.
This is a NATIONAL PUBLIC BUDGET cash-basis series, NOT IMF harmonised
general-government accrual fiscal statistics; its stated geographic coverage
excludes the left-bank Nistru districts and Bender.

Only a review sidecar is written: data/fiscal/public_budget_from_bns.csv.
No curated dataset or plate is automatically modified. Metadata is
re-checked against the publisher at every run, and anchor changes fail closed.
"""
from __future__ import annotations

import json
import math
import sys
from itertools import product
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
API = ("https://statbank.statistica.md/PxWeb/api/v1/en/"
       "40%20Statistica%20economica/25%20FIN/FIN010100.px")
METADATA_SNAPSHOT = Path(__file__).with_name("fin010100_metadata.json")
OUTPUT = ROOT / "data" / "fiscal" / "public_budget_from_bns.csv"
YEAR_FROM, YEAR_TO = 2016, 2025

# BNS integer category codes, not positional label guesses. DO NOT include
# child revenue tax rows (1..18) in any total, or the revenues double-count.
INDICATORS = {
    "0": "revenue_mdl_mn",
    "19": "expenditure_mdl_mn",
    "30": "balance_mdl_mn",
    "20": "general_services_mdl_mn",
    "21": "defense_mdl_mn",
    "22": "public_order_mdl_mn",
    "23": "economic_affairs_mdl_mn",
    "24": "environment_mdl_mn",
    "25": "housing_mdl_mn",
    "26": "health_mdl_mn",
    "27": "culture_mdl_mn",
    "28": "education_mdl_mn",
    "29": "social_protection_mdl_mn",
}
FUNCTIONS = list(INDICATORS)[3:]
CODE_LABELS = {"0": "Revenues", "19": "Expenditures and non-financial assets",
               "30": "Surplus (+), deficit (-)"}
VARIABLES = ["Indicatori", "Ani", "Perioade", "Unitatea de masura"]


def get_json(url: str, request_body: object | None = None) -> dict:
    headers = {"User-Agent": "worldreports-moldova-research/1.0",
               "Accept": "application/json"}
    body = None
    if request_body is not None:
        body = json.dumps(request_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    with urlopen(Request(url, data=body, headers=headers), timeout=60) as response:
        if response.status != 200:
            raise ValueError(f"BNS HTTP {response.status}")
        content = response.read()
        if len(content) > 10_000_000:
            raise ValueError("BNS response unexpectedly large")
        return json.loads(content)


def validate_metadata(payload: dict) -> dict[str, dict[str, str]]:
    """Map value *codes* to labels, and refuse changed dimension semantics."""
    variables = payload.get("variables")
    if not isinstance(variables, list) or [v.get("code") for v in variables] != VARIABLES:
        raise ValueError("BNS table dimensions have changed")
    mapping: dict[str, dict[str, str]] = {}
    for var in variables:
        values = var.get("values")
        labels = var.get("valueTexts")
        if (not isinstance(values, list) or not isinstance(labels, list)
                or len(values) != len(labels) or len(values) != len(set(values))):
            raise ValueError("BNS malformed coded dimension " + var["code"])
        mapping[var["code"]] = dict(zip(values, labels))
    if any(mapping["Indicatori"].get(k) != v for k, v in CODE_LABELS.items()):
        raise ValueError("BNS fiscal totals changed semantic meaning")
    years = mapping["Ani"]
    if not set(str(y) for y in range(YEAR_FROM, YEAR_TO + 1)).issubset(years.values()):
        raise ValueError("BNS missing full historical years")
    if mapping["Perioade"].get("3") != "January-December":
        raise ValueError("BNS period 3 is no longer full year")
    if mapping["Unitatea de masura"].get("0") != "Million lei":
        raise ValueError("BNS unit 0 is no longer million MDL")
    return mapping


def query(metadata: dict[str, dict[str, str]]) -> dict:
    year_codes = [code for code, text in metadata["Ani"].items()
                  if text.isdigit() and YEAR_FROM <= int(text) <= YEAR_TO]
    assert len(year_codes) == YEAR_TO - YEAR_FROM + 1
    return {
        "query": [
            {"code": "Indicatori", "selection": {"filter": "item",
                                                "values": list(INDICATORS)}},
            {"code": "Ani", "selection": {"filter": "item", "values": year_codes}},
            {"code": "Perioade", "selection": {"filter": "item", "values": ["3"]}},
            {"code": "Unitatea de masura", "selection": {"filter": "item",
                                                       "values": ["0"]}},
        ],
        "response": {"format": "json-stat2"},
    }


def category_code_position(dimension: dict, key: str) -> dict[str, int]:
    node = dimension.get(key, {})
    cat = node.get("category", {})
    ix = cat.get("index")
    if isinstance(ix, dict):
        return {str(code): int(pos) for code, pos in ix.items()}
    if isinstance(ix, list):
        return {str(code): pos for pos, code in enumerate(ix)}
    raise ValueError("Invalid JSON-stat category index " + key)


def decode_jsonstat(payload: dict, year_mapping: dict[str, str]
                    ) -> dict[int, dict[str, float]]:
    """Decode a JSON-stat2 cube using dimension IDs, not assumed positions."""
    ids = payload.get("id")
    sizes = payload.get("size")
    dimension = payload.get("dimension")
    values = payload.get("value")
    if (payload.get("class") != "dataset" or
            not isinstance(ids, list) or set(ids) != set(VARIABLES)
            or not isinstance(sizes, list) or len(sizes) != len(ids)
            or not isinstance(dimension, dict)
            or not isinstance(values, (list, dict))):
        raise ValueError("Invalid BNS json-stat2 shape")
    count = math.prod(sizes)
    if count > 10_000 or count == 0:
        raise ValueError("BNS returned unexpected cell count")
    if isinstance(values, list) and len(values) != count:
        raise ValueError("Truncated BNS JSON-stat2 values")
    if isinstance(values, dict) and any(not str(k).isdigit() or int(k) >= count
                                         for k in values):
        raise ValueError("Malformed sparse BNS values")
    positions = {id_: category_code_position(dimension, id_) for id_ in ids}
    for idx, size in zip(ids, sizes):
        if sorted(positions[idx].values()) != list(range(size)):
            raise ValueError("BNS category dimension index mismatch")
    if set(positions["Indicatori"]) != set(INDICATORS):
        raise ValueError("BNS indicator set no longer matches request")
    if set(positions["Perioade"]) != {"3"} or set(positions["Unitatea de masura"]) != {"0"}:
        raise ValueError("BNS nonannual or non-MDL data in response")
    assert set(positions["Ani"]).issubset(year_mapping)
    rows: dict[int, dict[str, float]] = {}
    for code, column in INDICATORS.items():
        for year_code in positions["Ani"]:
            coords = {"Indicatori": code, "Ani": year_code,
                      "Perioade": "3", "Unitatea de masura": "0"}
            offset = 0
            for dim_id, size in zip(ids, sizes):
                offset = offset * size + positions[dim_id][coords[dim_id]]
            raw = values[offset] if isinstance(values, list) else values.get(str(offset))
            year = int(year_mapping[year_code])
            if not YEAR_FROM <= year <= YEAR_TO:
                raise ValueError("BNS unexpected publication year")
            if raw is None:
                raise ValueError(f"BNS missing mandatory {column} for {year}")
            if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
                raise ValueError(f"BNS nonnumeric {column} for {year}")
            rows.setdefault(year, {})[column] = float(raw)
    if set(rows) != set(range(YEAR_FROM, YEAR_TO + 1)):
        raise ValueError("BNS annual year grid incomplete")
    return rows


def verify_budget(rows: dict[int, dict[str, float]]) -> None:
    """Cross-check full-year totals and classification sums, not substitutes."""
    for year, row in rows.items():
        rev, exp, bal = (row[c] for c in ("revenue_mdl_mn", "expenditure_mdl_mn",
                                          "balance_mdl_mn"))
        if abs(rev - exp - bal) > 0.25:
            raise ValueError(f"{year}: BNS deficit identity broken: {rev} - {exp} != {bal}")
        if abs(sum(row[INDICATORS[c]] for c in FUNCTIONS) - exp) > 2:
            raise ValueError(f"{year}: national functional totals do not reconcile")
    anchors = {
        2024: (110338.5, 122962.6, -12624.1),
        2025: (125602.0, 139856.4, -14254.4),
    }
    for year, expected in anchors.items():
        actual = tuple(rows[year][c] for c in
                       ("revenue_mdl_mn", "expenditure_mdl_mn", "balance_mdl_mn"))
        if any(abs(a - b) > 2 for a, b in zip(actual, expected)):
            raise ValueError(f"{year}: BNS snapshot revised; inspect before curation: {actual}")


def render(rows: dict[int, dict[str, float]]) -> str:
    columns = list(INDICATORS.values())
    lines = [
        "# BNS FIN010100 Jan-Dec completed budget, million MDL; 2025 preliminary.",
        "# Excludes left-bank Nistru districts and Bender (source note).",
        "# National public budget cash perimeter, not IMF general-government accrual.",
        "year," + ",".join(columns),
    ]
    for year in sorted(rows):
        lines.append(str(year) + "," +
                     ",".join(f"{rows[year][col]:.1f}" for col in columns))
    return "\n".join(lines) + "\n"


def main() -> None:
    saved = json.loads(METADATA_SNAPSHOT.read_text(encoding="utf-8"))
    saved_mapping = validate_metadata(saved)
    current_mapping = validate_metadata(get_json(API))
    for key in VARIABLES:
        for code in saved_mapping[key]:
            if code in current_mapping[key] and saved_mapping[key][code] != current_mapping[key][code]:
                raise ValueError(f"Publisher changed code {key}/{code}: investigate")
    request = query(current_mapping)
    rows = decode_jsonstat(get_json(API, request), current_mapping["Ani"])
    verify_budget(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(rows), encoding="utf-8")
    print(f"{OUTPUT.relative_to(ROOT)}: {len(rows)} annual rows; REVIEW ONLY")
    print("No curated fiscal series was modified.")


if __name__ == "__main__":
    main()
