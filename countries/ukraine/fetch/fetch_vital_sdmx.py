#!/usr/bin/env python3
"""Rebuild a review-only SSSU national birth/death/fertility snapshot.

Official, distinct source dataflows:
 * DF_POPULATION_BIRTH(5.0.1): PNMI_17, PNMI_32, PNMI_3341.
 * DF_POPULATION_MORTALITY(5.0.1): PNMI_19, PNMI_46.
Exact code labels: CL_POPULATION_INDICATOR(6.0.1).
Units: 1760=persons; 2860=per 1000 present population;
       2840=per woman (children/woman fertility rate).

No estimates, interpolations, denominators or API calls from rendering.
Output: data/demography/vital_ukrstat_from_sssu.csv, a review sidecar.
Never overwrite the accepted vital_ukrstat.csv.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "demography" / "vital_ukrstat_from_sssu.csv"
BASE = ("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
        "sdmx/3.0/data/dataflow/SSSU/")
REGION = "UA00000000000000000"
BIRTH = "DF_POPULATION_BIRTH/5.0.1"
DEATH = "DF_POPULATION_MORTALITY/5.0.1"
ALL, NA = "_T", "_Z"
YEARS = tuple(range(2006, 2026))
SUPPRESSED = frozenset(range(2022, 2026))
MAX_BYTES = 2_000_000

BIRTH_DIMS = {
    "REGION": REGION, "AGE": ALL, "MOTHER_AGE": ALL,
    "FATHER_AGE": ALL, "GENDER": ALL, "TERRAIN_TYPE": ALL,
    "FAMILY_STATUS": NA, "MONTH_REGISTRATION": ALL,
    "CITIZENSHIP_FEMALE": ALL, "CITIZENSHIP_MALE": ALL,
    "FREQ": "A",
}
DEATH_DIMS = {
    "REGION": REGION, "AGE": ALL, "GENDER": ALL,
    "TERRAIN_TYPE": ALL, "MONTH_REGISTRATION": NA,
    "NUM_DAY_LIVED": NA, "NUM_MON_LIVED": NA,
    "PERIOD_PERINATAL": NA, "CASE_TYPE": NA,
    "CITIZENSHIP": NA, "FREQ": "A",
}
# name -> publisher flow / indicator / unit / fixed dimensions
SPECS = {
    "live_births": (BIRTH, "PNMI_17", "1760", BIRTH_DIMS),
    "deaths": (DEATH, "PNMI_19", "1760", DEATH_DIMS),
    "birth_rate_per_1000": (BIRTH, "PNMI_32", "2860", BIRTH_DIMS),
    "death_rate_per_1000": (DEATH, "PNMI_46", "2860", DEATH_DIMS),
    "total_fertility": (BIRTH, "PNMI_3341", "2840", BIRTH_DIMS),
}
EXPECTED = {
    "live_births": {2006: "460368", 2014: "465882", 2021: "271983", 2025: "167801"},
    "deaths": {2006: "758092", 2021: "714263", 2025: "485290"},
    "birth_rate_per_1000": {2006: "9.8", 2021: "7.3"},
    "death_rate_per_1000": {2006: "16.2", 2021: "18.5"},
    "total_fertility": {2006: "1.254", 2021: "1.16"},
}
OUTPUT_FIELDS = (
    "year", "live_births", "deaths", "birth_rate_per_1000",
    "death_rate_per_1000", "total_fertility", "birth_rate_flag",
    "death_rate_flag", "fertility_flag",
)


def source_url(name: str) -> str:
    flow, indicator, _, dims = SPECS[name]
    filters = {"c[INDICATOR]": indicator}
    filters.update({f"c[{key}]": value for key, value in dims.items()})
    return BASE + flow + "/*?" + urllib.parse.urlencode(filters)


def fetch(name: str) -> bytes:
    request = urllib.request.Request(source_url(name), headers={
        "Accept": "application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent": "WorldReports-Ukraine-Official-Demography/1.0",
    })
    with urllib.request.urlopen(request, timeout=50) as res:
        content_type = res.headers.get("Content-Type", "").lower()
        status = res.status
        raw = res.read(MAX_BYTES + 1)
    if status != 200 or not raw or len(raw) > MAX_BYTES:
        raise ValueError(f"Empty/oversized/non-200 SSSU vital response: {name}")
    if "sdmx.data+csv" not in content_type or raw.lstrip().startswith((b"<", b"{")):
        raise ValueError(f"Unexpected SSSU vital content type: {content_type}")
    return raw


def decode(name: str, raw: bytes) -> dict[int, dict[str, str]]:
    flow, indicator, unit, dims = SPECS[name]
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError(f"Non-UTF8 response: {name}") from exc
    reader = csv.DictReader(StringIO(text))
    header = set(reader.fieldnames or ())
    required = (
        {"STRUCTURE_ID", "ACTION", "INDICATOR", "TIME_PERIOD",
         "OBS_VALUE", "OBS_FLAG", "UNITS_OF_MEASURE", "SCALE",
         "TERRITORIAL_COVERAGE"} | set(dims)
    )
    if not required.issubset(header):
        raise ValueError(f"{name}: unexpected SDMX fields {sorted(required-header)}")
    records = {}
    for row in reader:
        if (row["STRUCTURE_ID"] != f"SSSU:{flow.replace('/', '(')})"
                or row["ACTION"] != "R"
                or row["INDICATOR"] != indicator
                or any(row[k] != v for k, v in dims.items())
                or row["UNITS_OF_MEASURE"] != unit
                or row["SCALE"] != "0"
                or row["TERRITORIAL_COVERAGE"] != "Ukraine, regions"):
            raise ValueError(f"{name}: mixed source, unit, geography, indicator or action")
        try:
            year = int(row["TIME_PERIOD"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Bad SSSU vital calendar year") from exc
        if year not in YEARS:
            continue
        if year in records:
            raise ValueError(f"{name}: duplicate annual observation in {year}")
        value, flag = (row["OBS_VALUE"] or "").strip(), (row["OBS_FLAG"] or "").strip()
        if name not in ("live_births", "deaths") and year in SUPPRESSED:
            note = (row.get("NOTES_OBS") or "").lower()
            if value or flag != "c" or not ("not released" in note and "martial law" in note):
                raise ValueError(f"{name}: wrong suppressed 2022–25 value/flag/notes {year}")
        else:
            if not value or flag:
                raise ValueError(f"{name}: unexpectedly absent/flagged {year}")
            try:
                num = Decimal(value)
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ValueError(f"{name}: unparseable number in {year}") from exc
            if not num.is_finite() or num <= 0:
                raise ValueError(f"{name}: invalid number in {year}")
            if name in ("live_births", "deaths"):
                if num != int(num) or not 100000 <= num <= 900000:
                    raise ValueError(f"{name}: invalid annual national count in {year}")
            elif name == "total_fertility" and num >= 5:
                raise ValueError(f"Implausible fertility rate in {year}")
            elif name != "total_fertility" and num >= 40:
                raise ValueError(f"Implausible crude rate in {year}")
            anchor = EXPECTED.get(name, {}).get(year)
            if anchor is not None and num != Decimal(anchor):
                raise ValueError(f"{name}: source anchor revised in {year}")
        records[year] = {"value": value, "flag": flag}
    if set(records) != set(YEARS):
        raise ValueError(f"{name}: missing actual calendar-year records")
    return records


def combine(records: dict[str, dict[int, dict[str, str]]]) -> list[dict[str, str]]:
    if set(records) != set(SPECS):
        raise ValueError("Not all SSSU live birth/mortality indicators are present")
    out = []
    for year in YEARS:
        row = {"year": str(year)}
        for key in SPECS:
            row[key] = records[key][year]["value"]
        row["birth_rate_flag"] = records["birth_rate_per_1000"][year]["flag"]
        row["death_rate_flag"] = records["death_rate_per_1000"][year]["flag"]
        row["fertility_flag"] = records["total_fertility"][year]["flag"]
        out.append(row)
    return out


def to_csv(rows: list[dict[str, str]]) -> str:
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def main() -> None:
    records = {name: decode(name, fetch(name)) for name in SPECS}
    staged = to_csv(combine(records))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(staged, encoding="utf-8")
    tmp.replace(OUTPUT)
    print("SSSU official vital snapshot 2006–2025 (rate/TFR 2022–25 suppressed)")
    print("Review sidecar only:", OUTPUT)


if __name__ == "__main__":
    main()
