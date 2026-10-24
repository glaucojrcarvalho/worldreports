#!/usr/bin/env python3
"""Read-only SSSU population SDMX observation discovery.

Official dataflow:
 SSSU:DF_POPULATION_STRUCTURE(8.0.1)
 DSD urn SSSU:DSD_POPULATION_STR(3.0.0)
 PNMI_01 = estimated PRESENT population at 1 January.
 PNMI_02 = estimated PERMANENT population at 1 January.
The census was last conducted in 2001, and geographic collection scope
is discontinuous after Crimea's occupation and the full-scale invasion.

Do not stage an accepted demographic CSV until all remaining SDMX
dimensions, units, actual annual observations and scope annotations
are checked. An SDMX *availability* range is not an observed value.

Save only ignored cache/ metadata and raw source samples for review.
Usage: python countries/ukraine/fetch/probe_population.py --live
"""
from __future__ import annotations

import argparse
import csv
from io import StringIO
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"
BASE = (
    "https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
    "sdmx/3.0/data/dataflow/SSSU/DF_POPULATION_STRUCTURE/8.0.1/*"
)
DIMENSIONS = {
    "REGION": "UA00000000000000000",
    "FREQ": "A",
}
INDICATORS = ("PNMI_01", "PNMI_02")
MAX_BYTES = 2_000_000


def source_url(indicator: str) -> str:
    if indicator not in INDICATORS:
        raise ValueError("Unrecognized Ukrstat population measure")
    q = {"c[INDICATOR]": indicator}
    q.update({"c[" + k + "]": v for k, v in DIMENSIONS.items()})
    q["firstNObservations"] = "50"
    return BASE + "?" + urllib.parse.urlencode(q)


def read_only_probe(indicator: str) -> dict:
    url = source_url(indicator)
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent": "WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(request, timeout=45) as response:
        status = response.status
        mime = response.headers.get("Content-Type", "").lower()
        raw = response.read(MAX_BYTES + 1)
    if status != 200 or not raw or len(raw) > MAX_BYTES:
        raise ValueError("SSSU population response empty or oversized")
    if "sdmx.data+csv" not in mime:
        raise ValueError(f"Expected SDMX CSV, got {mime!r}")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(text))
    rows = list(reader)
    if not rows or "INDICATOR" not in rows[0] or "OBS_VALUE" not in rows[0]:
        raise ValueError("Population CSV has no usable observations")
    if any(row["INDICATOR"] != indicator for row in rows):
        raise ValueError("Population source mixed indicator definitions")
    if any(row.get(key) != val for row in rows for key, val in DIMENSIONS.items()):
        raise ValueError("Population source mixed national region/frequency")
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / f"population_{indicator.lower()}_raw.csv").write_bytes(raw)
    fields = list(rows[0])
    return {
        "url": url,
        "mime": mime,
        "bytes": len(raw),
        "status": "candidate_not_curated",
        "indicator": indicator,
        "columns": fields,
        "sample_count": len(rows),
        "observed_year_labels": [r.get("TIME_PERIOD") for r in rows],
        "sample_first": rows[:3],
        "sample_last": rows[-3:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    options = parser.parse_args()
    if not options.live:
        print("No network calls; use --live for official population probes")
        return
    manifest = {}
    for indicator in INDICATORS:
        try:
            manifest[indicator] = read_only_probe(indicator)
        except Exception as exc:
            manifest[indicator] = {
                "url": source_url(indicator),
                "status": "unverified",
                "error": f"{type(exc).__name__}: {exc}",
            }
        print(indicator, manifest[indicator]["status"])
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "population_probe_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
