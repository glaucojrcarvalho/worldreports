#!/usr/bin/env python3
"""Research-only Ukrstat live birth/death/fertility SDMX source selection.

This script NEVER modifies any curated data. It stages exact SDMX-CSV v2
responses and an annotated JSON audit under ignored countries/ukraine/cache/.
It fails closed when the publisher changes dimensions, record scope or units.

Publisher: State Statistics Service of Ukraine (SSSU).
Indicator code labels are pinned to:
 SSSU:CL_POPULATION_INDICATOR(6.0.1), retrieved 2026-10-24.
 BIRTH flow: SSSU:DF_POPULATION_BIRTH(5.0.1);
 DEATH flow: SSSU:DF_POPULATION_MORTALITY(5.0.1).
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from io import StringIO
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache" / "demography_vital"
BASE = ("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
        "sdmx/3.0/data/dataflow/SSSU/")
NATIONAL = "UA00000000000000000"
MAX_BYTES = 3_000_000
ALL = "_T"
NA = "_Z"
BIRTH = "DF_POPULATION_BIRTH/5.0.1"
DEATH = "DF_POPULATION_MORTALITY/5.0.1"

# No value is inferred by summing oblasts, sexes or age groups. These
# exact publisher aggregation cells are candidates requiring real-data QA.
BIRTH_DIMS = {
    "REGION": NATIONAL, "AGE": ALL, "MOTHER_AGE": ALL,
    "FATHER_AGE": ALL, "GENDER": ALL, "TERRAIN_TYPE": ALL,
    "FAMILY_STATUS": NA, "MONTH_REGISTRATION": ALL,
    "CITIZENSHIP_FEMALE": ALL, "CITIZENSHIP_MALE": ALL,
    "FREQ": "A",
}
DEATH_DIMS = {
    "REGION": NATIONAL, "AGE": ALL, "GENDER": ALL,
    "TERRAIN_TYPE": ALL, "MONTH_REGISTRATION": NA,
    "NUM_DAY_LIVED": NA, "NUM_MON_LIVED": NA,
    "PERIOD_PERINATAL": NA, "CASE_TYPE": NA,
    "CITIZENSHIP": NA, "FREQ": "A",
}
SPECS = {
    "live_births": (BIRTH, "PNMI_17", BIRTH_DIMS,
                    "Number of live births (persons)"),
    "crude_birth_rate": (BIRTH, "PNMI_32", BIRTH_DIMS,
                         "Total/crude birth rate, not fertility"),
    "total_fertility": (BIRTH, "PNMI_3341", BIRTH_DIMS,
                        "Total fertility rate, children per woman"),
    "deaths": (DEATH, "PNMI_19", DEATH_DIMS,
               "Number of deaths (persons)"),
    "crude_death_rate": (DEATH, "PNMI_46", DEATH_DIMS,
                         "Total/crude death rate, not age-specific"),
}


def source_url(spec):
    flow, indicator, dims, _ = SPECS[spec]
    query = {"c[INDICATOR]": indicator, **{
        f"c[{name}]": code for name, code in dims.items()
    }}
    return BASE + flow + "/*?" + urllib.parse.urlencode(query)


def fetch_csv(spec):
    url = source_url(spec)
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent": "WorldReports-Ukraine-Reproducible-Research/1.0",
    })
    with urllib.request.urlopen(request, timeout=55) as response:
        status = response.status
        mime = response.headers.get("Content-Type", "").lower()
        data = response.read(MAX_BYTES + 1)
    if status != 200 or not data or len(data) > MAX_BYTES:
        raise ValueError(f"Missing, empty or oversize SSSU response: {url}")
    if "sdmx.data+csv" not in mime:
        raise ValueError(f"Expected SDMX-CSV for {spec}, received {mime}")
    if data.lstrip().startswith((b"<", b"{")):
        raise ValueError("HTML/XML/JSON error response, not SDMX-CSV")
    return data


def audit(spec, raw):
    flow, indicator, dims, description = SPECS[spec]
    try:
        source = raw.decode("utf-8-sig")
    except UnicodeError as err:
        raise ValueError(f"Non-UTF8 source {spec}") from err
    reader = csv.DictReader(StringIO(source))
    if not reader.fieldnames:
        raise ValueError("Missing SDMX-CSV header")
    header = reader.fieldnames
    fields = set(header)
    needed = {"INDICATOR", "TIME_PERIOD", "OBS_VALUE", "FREQ",
              "REGION", "UNITS_OF_MEASURE", "SCALE",
              "OBS_FLAG"} | set(dims)
    if not needed.issubset(fields):
        raise ValueError("Missing expected fields " + str(sorted(needed-fields)))
    rows = list(reader)
    for row in rows:
        if row.get("INDICATOR") != indicator:
            raise ValueError(f"Mixed or unexpected indicator in {spec}")
        for name, value in dims.items():
            if row.get(name) != value:
                raise ValueError(f"{spec}: returned {name}={row.get(name)!r}, expected {value!r}")
        if row["REGION"] != NATIONAL or row["FREQ"] != "A":
            raise ValueError("Non-national or non-annual series")
    year_counts = Counter(row["TIME_PERIOD"] for row in rows)
    if any(n != 1 for n in year_counts.values()):
        raise ValueError(f"{spec}: duplicate year observations: {dict(year_counts)}")
    observations = [
        {"year":r["TIME_PERIOD"], "value":r["OBS_VALUE"],
         "flag":r["OBS_FLAG"], "unit":r["UNITS_OF_MEASURE"],
         "scale":r["SCALE"], "notes":(r.get("NOTES_OBS") or "")[:220]}
        for r in sorted(rows, key=lambda r: r["TIME_PERIOD"])
    ]
    return {
        "publisher": "State Statistics Service of Ukraine",
        "source": source_url(spec),
        "description": description,
        "dataflow": flow,
        "indicator": indicator,
        "dimensions": dims,
        "code_list": "SSSU:CL_POPULATION_INDICATOR(6.0.1)",
        "status": "candidate_requires_definition_and_observation_review",
        "row_count": len(rows),
        "period_range": [observations[0]["year"], observations[-1]["year"]]
                        if observations else [],
        "fields": header,
        "units": sorted(set(r["unit"] for r in observations)),
        "scale_codes": sorted(set(r["scale"] for r in observations)),
        "observed": sum(bool(r["value"]) for r in observations),
        "suppressed": sum(not r["value"] and bool(r["flag"]) for r in observations),
        "observations": observations,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true",
                        help="Only --live contacts official SSSU API")
    args = parser.parse_args()
    if not args.live:
        print("Source probe has no implicit network requests; add --live")
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    report = {}
    for spec in SPECS:
        try:
            raw = fetch_csv(spec)
            (CACHE / (spec + "_sdmx.csv")).write_bytes(raw)
            report[spec] = audit(spec, raw)
            print(spec, "rows:", report[spec]["row_count"],
                  "observed:", report[spec]["observed"],
                  "units:", report[spec]["units"])
        except Exception as exc:
            report[spec] = {
                "status": "unverified",
                "source": source_url(spec),
                "error": f"{type(exc).__name__}: {exc}",
            }
            print(spec, "UNVERIFIED", report[spec]["error"])
    (CACHE / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    # Do not report success unless every exact publisher aggregation responds.
    missing = [k for k, v in report.items() if v["status"] == "unverified"
               or v.get("row_count", 0) == 0]
    if missing:
        raise SystemExit("Not yet chart-ready: " + ", ".join(missing))


if __name__ == "__main__":
    main()
