#!/usr/bin/env python3
"""Stage Ukraine real GDP growth from the SSSU's exact annual SDMX series.

The source publishes GDP's previous-year volume index (100 = no growth).
Transform to year-on-year growth as `OBS_VALUE - 100`. A 2022 index of
71.2 is -28.8%, NOT +71.2% or nominal growth.

The source is restricted to:
  SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0)
  GDP_CUR_PRC / IDX_VOL_PY / UA00000000000000000 / _T / _T / S_1 / A

Do not backfill 2006–2010, nor mix the separate 2025 press-release figure
into this vintage. The fetcher writes only a review-only sidecar. Accepted
CSV is curated manually after comparing every revision and scope note.

Run: python3 countries/ukraine/fetch/fetch_sssu_gdp.py
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "macro" / "gdp_growth_from_sssu.csv"
BASE = ("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
        "sdmx/3.0/data/dataflow/SSSU/DF_ANNUAL_NATIONAL_ACCOUNTS/7.0.0/*")
EXPECTED_STRUCTURE = "SSSU:DF_ANNUAL_NATIONAL_ACCOUNTS(7.0.0)"
DIMENSIONS = {
    "INDICATOR": "GDP_CUR_PRC",
    "PRICE_TYPE": "IDX_VOL_PY",
    "REGION": "UA00000000000000000",
    "BREAKDOWN_CATEGORY": "_T",
    "BREAKDOWN": "_T",
    "SECTOR_ECONOMY": "S_1",
    "FREQ": "A",
}
# Source index is reported at one decimal precision.
ANCHORS = {2022: Decimal("71.2"), 2023: Decimal("105.5"),
           2024: Decimal("103.2")}
MAX_BYTES = 2_000_000
REQUIRED_COLS = {"STRUCTURE_ID", "ACTION", "TIME_PERIOD", "OBS_VALUE",
                 "UNITS_OF_MEASURE", "SCALE", "OBS_FLAG", *DIMENSIONS}


def data_url() -> str:
    return BASE + "?" + urllib.parse.urlencode({
        "c[" + key + "]": value for key, value in DIMENSIONS.items()
    })


def download() -> bytes:
    req = urllib.request.Request(data_url(), headers={
        "Accept": "application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent": "WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        status = response.status
        ctype = response.headers.get("Content-Type", "").lower()
        payload = response.read(MAX_BYTES + 1)
    if status != 200 or not payload or len(payload) > MAX_BYTES:
        raise ValueError("SSSU GDP download failed, was empty or oversized")
    if "sdmx.data+csv" not in ctype or payload.lstrip().lower().startswith(b"<html"):
        raise ValueError(f"Unexpected SSSU GDP content type {ctype!r}")
    return payload


def parse_annual_growth(raw: bytes) -> list[dict[str, str]]:
    """Validate all observed rows, preserving gaps and original index."""
    try:
        txt = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("SSSU GDP response must be UTF-8") from exc
    reader = csv.DictReader(StringIO(txt))
    if not reader.fieldnames or not REQUIRED_COLS.issubset(reader.fieldnames):
        raise ValueError("Unexpected SDMX GDP column schema")
    values: dict[int, dict[str, str]] = {}
    for row in reader:
        if row["STRUCTURE_ID"] != EXPECTED_STRUCTURE:
            raise ValueError("SDMX dataset vintage does not match pinned version")
        if row["ACTION"] != "R":
            raise ValueError("SDMX update action changed; manual review required")
        for dim, code in DIMENSIONS.items():
            if row[dim] != code:
                raise ValueError(f"Unexpected dimension {dim}: {row[dim]}")
        if row["UNITS_OF_MEASURE"] != "1010" or row["SCALE"] != "0":
            raise ValueError("GDP volume index unit or scaling changed")
        if row["OBS_FLAG"]:
            raise ValueError("Flagged or suppressed GDP observation requires review")
        try:
            year = int(row["TIME_PERIOD"])
            volume_index = Decimal(row["OBS_VALUE"])
        except (TypeError, ValueError, InvalidOperation) as exc:
            raise ValueError("Missing or malformed GDP year or volume index") from exc
        if not 2011 <= year <= 2025 or year in values:
            raise ValueError(f"Off-range or duplicate GDP year {year}")
        if not volume_index.is_finite() or not 0 < volume_index < 200:
            raise ValueError(f"Implausible GDP volume index in {year}")
        if year in ANCHORS and volume_index != ANCHORS[year]:
            raise ValueError(f"Official GDP {year} anchor changed: {volume_index}")
        if row.get("TERRITORIAL_COVERAGE") not in ("Ukraine",):
            raise ValueError("GDP publisher coverage label changed")
        growth = volume_index - Decimal(100)
        values[year] = {
            "year": str(year),
            "real_growth": f"{growth:.1f}",
            "volume_index_py": f"{volume_index:.1f}",
        }
    if len(values) < 10 or not ANCHORS.keys() <= values.keys():
        raise ValueError("SSSU GDP selection is too short or lacks control years")
    # If 2025 appears in a later revision, it stays a staging sidecar and is
    # NOT implicitly promoted into the curated file.
    return [values[y] for y in sorted(values)]


def render_csv(rows: list[dict[str, str]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output, fieldnames=("year", "real_growth", "volume_index_py"),
        lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def main() -> None:
    rows = parse_annual_growth(download())
    staged = render_csv(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(staged, encoding="utf-8")
    tmp.replace(OUTPUT)
    print(f"SSSU GDP staged {rows[0]['year']}–{rows[-1]['year']} "
          f"({len(rows)} observations): {OUTPUT}")
    print("Sidecar only. Do not publish without reviewing differences and geographic scope.")


if __name__ == "__main__":
    main()
