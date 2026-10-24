#!/usr/bin/env python3
"""Inspect a specific Ukrstat national-accounts series without publishing it.

Only SSSU SDMX dataflow DF_ANNUAL_NATIONAL_ACCOUNTS/7.0.0 is queried.
Write response metadata and bounded raw CSV into ignored cache/ for review.
Do not use a result as accepted data until schema, version, years, unit,
territory and publisher's 2022 real GDP growth anchor are validated.

Run: python countries/ukraine/fetch/probe_gdp.py --live
"""
from __future__ import annotations

import argparse
import csv
from io import StringIO
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
BASE = (
    "https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
    "sdmx/3.0/data/dataflow/SSSU/DF_ANNUAL_NATIONAL_ACCOUNTS/7.0.0/*"
)
INDICATOR = "GDP_CUR_PRC"
PRICE_TYPE = "IDX_VOL_PY"
REGION = "UA00000000000000000"
BREAKDOWN = "_T"
SECTOR = "S_1"
FREQ = "A"
EXPECTED_ANCHOR = -28.8
MAX_BYTES = 2_000_000


def candidate_urls() -> dict[str, str]:
    filters = {
        "c[INDICATOR]": INDICATOR,
        "c[PRICE_TYPE]": PRICE_TYPE,
        "c[REGION]": REGION,
        "c[BREAKDOWN_CATEGORY]": BREAKDOWN,
        "c[BREAKDOWN]": BREAKDOWN,
        "c[SECTOR_ECONOMY]": SECTOR,
        "c[FREQ]": FREQ,
    }
    selected = f"{BASE}?{urllib.parse.urlencode(filters)}"
    # Retain both variants: the second is a control to distinguish a
    # too-restrictive geographic/breakdown selection from API failure.
    control = f"{BASE}?{urllib.parse.urlencode({key: val for key, val in filters.items() if key not in {'c[REGION]', 'c[BREAKDOWN_CATEGORY]', 'c[BREAKDOWN]'}})}"
    return {"exact": selected, "control": control}


def fetch(url: str) -> tuple[str, bytes, int]:
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent": "WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        content_type = response.headers.get("Content-Type", "")
        status = response.status
        payload = response.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError("SDMX response too large for probe")
    if status != 200 or not payload:
        raise ValueError(f"SDMX returned HTTP {status} / empty payload")
    if "html" in content_type.lower() or re.match(br"\s*<(html|!doctype)", payload, re.I):
        raise ValueError("HTML error page returned instead of SDMX CSV")
    return content_type, payload, status


def inspect_csv(payload: bytes) -> dict:
    """Never coerce absent numeric values into zero."""
    txt = payload.decode("utf-8-sig")
    rows = list(csv.DictReader(StringIO(txt)))
    cols = list(rows[0]) if rows else list(csv.reader(StringIO(txt)).__next__())
    if not rows:
        raise ValueError("SDMX returned headers but no observations")
    if not any(x in cols for x in ("TIME_PERIOD", "TIME_PERIOD_NAME")):
        raise ValueError(f"Missing time dimension; columns were {cols}")
    if not any(x in cols for x in ("OBS_VALUE", "OBS_VALUE_NAME")):
        raise ValueError(f"Missing observed value; columns were {cols}")
    return {
        "status": "candidate_csv_not_yet_curated",
        "columns": cols,
        "row_count": len(rows),
        "sample_first": rows[:3],
        "sample_last": rows[-3:],
    }


def main() -> None:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--live", action="store_true")
    options = args.parse_args()
    if not options.live:
        print("No network called; pass --live for bounded API probes.")
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    records = {}
    for name, url in candidate_urls().items():
        try:
            mime, raw, status = fetch(url)
            (CACHE / f"gdp_probe_{name}.csv").write_bytes(raw)
            record = {
                "endpoint": url,
                "mime": mime,
                "bytes": len(raw),
                "http_status": status,
                "preview": raw[:500].decode("utf-8-sig", "replace"),
            }
            try:
                record.update(inspect_csv(raw))
            except (UnicodeError, ValueError, csv.Error) as exc:
                record["parse_status"] = f"unverified: {type(exc).__name__}: {exc}"
            records[name] = record
        except Exception as exc:
            records[name] = {"endpoint": url, "status": "unverified",
                             "error": f"{type(exc).__name__}: {exc}"}
        print(f"GDP probe {name}: {records[name].get('status', records[name].get('parse_status', 'unverified'))}")
    (CACHE / "gdp_probe_manifest.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
