#!/usr/bin/env python3
"""Stage official January-1 present population, preserving wartime suppression.

SSSU:DF_POPULATION_STRUCTURE(8.0.1), DSD_POPULATION_STR(3.0.0)
Exact national total:
  INDICATOR=PNMI_01 (estimated PRESENT population as at January 1)
  REGION=UA00000000000000000
  AGE=_T, GENDER=_T, TERRAIN_TYPE=_T, FREQ=A
  UNITS_OF_MEASURE=1760 (people), SCALE=0.

2006–2022: 17 observed values. January 2015–2022 population excludes
occupied Crimea/Sevastopol and certain occupied Donetsk/Luhansk areas.
The 2022 January 1 stock predates the full-scale invasion; it is NOT an
end-of-2022 population estimate. 2023–2025 are publisher-suppressed
OBS_FLAG=c, missing OBS_VALUE; suppression is NOT zero.

No artificial continuity, population denominators, interpolations,
all-Ukraine post-invasion population counts or survey imputations.
Refresh stages social/population_from_sssu.csv only; curated CSV unchanged.
"""
from __future__ import annotations
import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "social" / "population_from_sssu.csv"
BASE = ("https://stat.gov.ua/sdmx/workspaces/default:integration/registry/"
        "sdmx/3.0/data/dataflow/SSSU/DF_POPULATION_STRUCTURE/8.0.1/*")
FLOW = "SSSU:DF_POPULATION_STRUCTURE(8.0.1)"
DIMENSIONS = {
    "INDICATOR": "PNMI_01",
    "REGION": "UA00000000000000000",
    "AGE": "_T",
    "GENDER": "_T",
    "TERRAIN_TYPE": "_T",
    "FREQ": "A",
}
FIRST, LAST, LAST_OBSERVED = 2006, 2025, 2022
UNIT, SCALE = "1760", "0"
REFERENCE = {
    2006: 46929525,
    2014: 45426249,
    2015: 42929298,
    2021: 41588354,
    2022: 41167335,
}
FIELDS = ("year", "population_persons", "obs_flag")
REQUIRED = {"STRUCTURE_ID", "ACTION", "TIME_PERIOD", "OBS_VALUE",
            "UNITS_OF_MEASURE", "SCALE", "OBS_FLAG", *DIMENSIONS}
MAX_BYTES = 2_000_000


def source_url() -> str:
    filters = {"c[" + k + "]": v for k, v in DIMENSIONS.items()}
    return BASE + "?" + urllib.parse.urlencode(filters)


def download() -> bytes:
    req = urllib.request.Request(source_url(), headers={
        "Accept": "application/vnd.sdmx.data+csv;version=2.0.0;labels=id",
        "User-Agent": "WorldReports-Ukraine-Research/0.1",
    })
    with urllib.request.urlopen(req, timeout=50) as response:
        status = response.status
        mime = response.headers.get("Content-Type", "").lower()
        payload = response.read(MAX_BYTES + 1)
    if status != 200 or not payload or len(payload) > MAX_BYTES:
        raise ValueError("Ukrstat population response empty or oversized")
    if "sdmx.data+csv" not in mime:
        raise ValueError(f"Unexpected population representation {mime}")
    return payload


def parse_population(raw: bytes) -> list[dict[str, str]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("Ukrstat population must be UTF-8") from exc
    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        raise ValueError("Ukrstat population SDMX-CSV schema changed")
    out = {}
    for row in reader:
        if row["STRUCTURE_ID"] != FLOW or row["ACTION"] != "R":
            raise ValueError("Population source dataflow revision/action changed")
        if any(row[k] != expected for k, expected in DIMENSIONS.items()):
            raise ValueError("Non-national, wrong-age, gender or terrain population")
        if row["UNITS_OF_MEASURE"] != UNIT or row["SCALE"] != SCALE:
            raise ValueError("Ukrstat population unit or scale changed")
        if row.get("TERRITORIAL_COVERAGE") != "Ukraine, regions":
            raise ValueError("Population geographic coverage label needs review")
        try:
            year = int(row["TIME_PERIOD"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid population observation year") from exc
        if year < FIRST or year > LAST:
            continue
        if year in out:
            raise ValueError(f"Duplicate population total for {year}")
        flag = row["OBS_FLAG"]
        value = row["OBS_VALUE"]
        if year <= LAST_OBSERVED:
            if flag or not value:
                raise ValueError(f"Observed January-1 population missing or flagged {year}")
            try:
                n = Decimal(value)
            except (TypeError, ValueError, InvalidOperation) as exc:
                raise ValueError(f"Invalid population count in {year}") from exc
            if (not n.is_finite() or n != n.to_integral_value()
                    or not 20_000_000 < n < 70_000_000):
                raise ValueError(f"Implausible January-1 population in {year}")
            if year in REFERENCE and int(n) != REFERENCE[year]:
                raise ValueError(f"SSSU population anchor revised {year}")
            out[year] = {
                "year": str(year), "population_persons": str(int(n)),
                "obs_flag": "",
            }
        else:
            if flag != "c" or value:
                raise ValueError(f"2023–2025 suppressed census years changed: {year}")
            note = row.get("NOTES_OBS", "").lower()
            if "not released" not in note or "martial law" not in note:
                raise ValueError(f"Population suppression basis changed: {year}")
            out[year] = {
                "year": str(year), "population_persons": "", "obs_flag": "c",
            }
    if set(out) != set(range(FIRST, LAST + 1)):
        raise ValueError("Ukrstat national Jan-1 population selection incomplete")
    return [out[y] for y in sorted(out)]


def to_csv(rows: list[dict[str, str]]) -> str:
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def main() -> None:
    csv_text = to_csv(parse_population(download()))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(csv_text, encoding="utf-8")
    tmp.replace(OUTPUT)
    print(f"SSSU Jan-1 present population {FIRST}–{LAST}: "
          f"observed through {LAST_OBSERVED}; 2023–2025 suppressed")
    print(f"Review sidecar only: {OUTPUT}")


if __name__ == "__main__":
    main()
