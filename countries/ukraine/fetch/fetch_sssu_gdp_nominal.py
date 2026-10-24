#!/usr/bin/env python3
"""Stage Ukrstat nominal GDP at current prices as a review-only SDMX sidecar.

SDMX source: SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0).
Key: GDP_CUR_PRC / CURR_PRICES / UA00000000000000000 / _T / _T / S_1 / A.
Unit: UNITS_OF_MEASURE=1090 (national currency), SCALE=6 (millions UAH).

This is a nominal LEVEL, never annual GDP growth. Current API response
returns years 2010–2024, not 2025. Curated snapshot is unchanged by fetch.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "macro" / "gdp_nominal_from_sssu.csv"
BASE = ("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
        "sdmx/3.0/data/dataflow/SSSU/DF_ANNUAL_NATIONAL_ACCOUNTS/7.0.0/*")
STRUCTURE = "SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0)"
DIMENSIONS = {
    "INDICATOR": "GDP_CUR_PRC",
    "PRICE_TYPE": "CURR_PRICES",
    "REGION": "UA00000000000000000",
    "BREAKDOWN_CATEGORY": "_T",
    "BREAKDOWN": "_T",
    "SECTOR_ECONOMY": "S_1",
    "FREQ": "A",
}
ANCHORS = {
    2010: Decimal(1079346),
    2022: Decimal(5239114),
    2024: Decimal(7662376),
}
REQUIRED = {"STRUCTURE_ID", "ACTION", "TIME_PERIOD", "OBS_VALUE",
            "UNITS_OF_MEASURE", "SCALE", "OBS_FLAG", *DIMENSIONS}


def source_url() -> str:
    return BASE + "?" + urllib.parse.urlencode(
        {"c[" + key + "]": value for key, value in DIMENSIONS.items()}
    )


def retrieve() -> bytes:
    req = urllib.request.Request(source_url(), headers={
        "Accept": "application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent": "WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        mime = response.headers.get("Content-Type", "").lower()
        status = response.status
        data = response.read(2_000_001)
    if status != 200 or not data or len(data) > 2_000_000:
        raise ValueError("SSSU nominal GDP download failed or exceeded bounds")
    if "sdmx.data+csv" not in mime:
        raise ValueError(f"Unexpected source representation {mime}")
    return data


def parse_nominal_gdp(raw: bytes) -> list[dict[str, str]]:
    try:
        data = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("Nominal GDP CSV is not UTF-8") from exc
    reader = csv.DictReader(StringIO(data))
    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        raise ValueError("Incomplete SDMX-CSV structure")
    found: dict[int, dict[str, str]] = {}
    for row in reader:
        if row["STRUCTURE_ID"] != STRUCTURE or row["ACTION"] != "R":
            raise ValueError("Unexpected GDP dataflow vintage or action")
        for key, expected in DIMENSIONS.items():
            if row[key] != expected:
                raise ValueError(f"Unexpected GDP dimension {key}: {row[key]}")
        if row["UNITS_OF_MEASURE"] != "1090" or row["SCALE"] != "6":
            raise ValueError("Unexpected GDP national currency or scale")
        if row["OBS_FLAG"]:
            raise ValueError("Flagged GDP observation requires review")
        if row.get("TERRITORIAL_COVERAGE") != "Ukraine":
            raise ValueError("Unreviewed change to national coverage field")
        try:
            year = int(row["TIME_PERIOD"])
            amount = Decimal(row["OBS_VALUE"])
        except (TypeError, ValueError, InvalidOperation) as exc:
            raise ValueError("Malformed GDP year or nominal amount") from exc
        if not (2010 <= year <= 2025) or year in found:
            raise ValueError(f"Duplicate or out-of-range nominal GDP year {year}")
        if not amount.is_finite() or not 0 < amount < Decimal("100000000"):
            raise ValueError(f"Invalid nominal GDP figure in {year}")
        if amount != amount.to_integral_value():
            raise ValueError("Nominal GDP source changed million-UAH precision")
        if year in ANCHORS and amount != ANCHORS[year]:
            raise ValueError(f"Nominal GDP anchor {year} revised; manual review")
        found[year] = {"year": str(year), "nominal_uah_mn": str(int(amount))}
    if len(found) < 10 or not ANCHORS.keys() <= found.keys():
        raise ValueError("Nominal GDP selection is incomplete or missing anchors")
    return [found[y] for y in sorted(found)]


def to_csv(rows: list[dict[str, str]]) -> str:
    out = StringIO()
    writer = csv.DictWriter(out, ["year", "nominal_uah_mn"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def main() -> None:
    rows = parse_nominal_gdp(retrieve())
    staged = to_csv(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(staged, encoding="utf-8")
    tmp.replace(OUTPUT)
    print(f"Staged {len(rows)} nominal GDP years, {rows[0]['year']}–{rows[-1]['year']}")
    print("Review sidecar only; national-accounts territorial scope remains documented.")


if __name__ == "__main__":
    main()
