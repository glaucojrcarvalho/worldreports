#!/usr/bin/env python3
"""Audit UNDP HDR 2025's restated Moldova Human Development Index history.

Official, frozen 2025 release:
  https://hdr.undp.org/sites/default/files/2025_HDR/
  HDR25_Composite_indices_complete_time_series.csv

This fetcher writes a *review-only* data/world/hdi_from_undp.csv sidecar.
It never alters a published or curated dataset, and the atlas never fetches
from the network during a render. Historical years are comparable within
this ONE UNDP report vintage, not arbitrarily spliced from earlier reports.
The last year in the 2025 edition is 2023, not 2025 or 2026.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SOURCE = (
    "https://hdr.undp.org/sites/default/files/2025_HDR/"
    "HDR25_Composite_indices_complete_time_series.csv"
)
FIRST = 2006
LAST = 2023
YEARS = range(FIRST, LAST + 1)
DEST = ROOT / "data/world/hdi_from_undp.csv"
# UNDP Moldova press release, 2025-05-06, reports both official anchors:
# https://www.undp.org/moldova/press-releases/age-ai-moldova-faces-key-choices-ensure-human-development-progress-says-new-undp-report
ANCHORS = {2022: 0.763, 2023: 0.785}


def parse_release(data: bytes) -> list[tuple[int, str]]:
    """Strictly accept UNDP's complete, CP1252 wide-form 2025 dataset."""
    if len(data) < 100_000 or len(data) > 5_000_000:
        raise ValueError("Official CSV payload has unexpected byte length")
    text = data.decode("cp1252")
    if text.lstrip().startswith(("<", "{")):
        raise ValueError("Received HTML or JSON instead of the UNDP CSV")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    needed = {"iso3", "country", "hdicode", "region"} | {
        f"hdi_{year}" for year in YEARS}
    if reader.fieldnames is None or not needed.issubset(reader.fieldnames):
        raise ValueError(f"2025 UNDP header mismatch: {reader.fieldnames}")
    rows = list(reader)
    if len(rows) != 206:
        raise ValueError(f"Expected 206 country/aggregate rows, got {len(rows)}")
    if any(None in row for row in rows):
        raise ValueError("Malformed CSV has unheaded surplus columns")
    matches = [row for row in rows if row["iso3"].strip() == "MDA"]
    if len(matches) != 1:
        raise ValueError(f"Moldova ISO3 must appear exactly once, got {len(matches)}")
    country = matches[0]
    if "moldov" not in country["country"].lower():
        raise ValueError(f"Unexpected ISO3 country mapping: {country['country']!r}")
    result = []
    for year in YEARS:
        token = country[f"hdi_{year}"].strip()
        if not token:
            raise ValueError(f"UNDP {year}: missing is not zero/interpolated")
        try:
            number = float(token)
        except ValueError as exc:
            raise ValueError(f"UNDP {year}: bad numeric cell {token!r}") from exc
        if not 0.5 <= number <= 1:
            raise ValueError(f"UNDP {year}: HDI out of unit interval: {token}")
        if year in ANCHORS and abs(number - ANCHORS[year]) > 0.00051:
            raise ValueError(
                f"2025 publisher-vintage anchor mismatch for {year}: "
                f"{number} != {ANCHORS[year]}")
        result.append((year, token))
    return result


def render_sidecar(observations: list[tuple[int, str]], payload: bytes) -> str:
    sha = hashlib.sha256(payload).hexdigest()
    lines = [
        "# UNDP Human Development Report 2025 composite indices; country MDA.",
        "# HDI revised retrospectively within one vintage; do not splice older editions.",
        "# Years 2006-2023 only; no fabricated 2024-2026 observations.",
        f"# Source: {SOURCE}",
        f"# Official release SHA256: {sha}",
        "year,hdi",
    ]
    lines += [f"{year},{raw}" for year, raw in observations]
    return "\n".join(lines) + "\n"


def fetch_release() -> bytes:
    req = Request(SOURCE, headers={
        "User-Agent": "WorldReports-Moldova-source-audit/1.0",
        "Accept": "text/csv,application/octet-stream;q=0.9,*/*;q=0.1",
    })
    with urlopen(req, timeout=45) as stream:
        content = stream.read(5_000_001)
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=DEST,
                        help="review-only output path, never a curated dataset")
    args = parser.parse_args()
    target = args.out.resolve()
    if target.name != "hdi_from_undp.csv":
        raise SystemExit("Refusing to overwrite anything except hdi_from_undp.csv")
    if not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    raw = fetch_release()
    rows = parse_release(raw)
    target.write_text(render_sidecar(rows, raw), encoding="utf-8")
    print(f"Validated official HDR 2025: {len(rows)} Moldova HDI values "
          f"{rows[0][0]}-{rows[-1][0]}; "
          f"2022={dict(rows)[2022]}, 2023={dict(rows)[2023]}")
    print(f"Original publisher bytes SHA256={hashlib.sha256(raw).hexdigest()}")
    print(f"Review-only sidecar: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
