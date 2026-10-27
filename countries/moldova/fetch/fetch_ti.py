#!/usr/bin/env python3
"""Audit TI CPI 2025's Moldova time series from its official XLSX workbook.

Publisher: https://images.transparencycdn.org/images/CPI2025_Results.xlsx
The 2025 workbook includes comparable CPI scores only from 2012 onward.
The output is a REVIEW-ONLY sidecar: never changes the curated site data.
No third-party spreadsheet library is needed (standard-library OOXML).
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import io
from pathlib import Path
import posixpath
import re
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "https://images.transparencycdn.org/images/CPI2025_Results.xlsx"
DEST = ROOT / "data/world/cpi_from_ti.csv"
YEARS = range(2012, 2026)
ANCHORS = {2023: 42, 2024: 43, 2025: 42}
NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _sheet_rows(z: ZipFile, name: str, shared: list[str]) -> list[dict[str, str]]:
    """Read cached cell values, not formulas, preserving original cell positions."""
    root = ET.fromstring(z.read(name))
    output: list[dict[str, str]] = []
    for row in root.findall(".//m:sheetData/m:row", NS):
        cells: dict[str, str] = {}
        for cell in row.findall("m:c", NS):
            address = cell.get("r", "")
            match = re.fullmatch(r"([A-Z]+)[0-9]+", address)
            if not match:
                raise ValueError(f"Bad XLSX cell address {address!r}")
            col = match.group(1)
            kind = cell.get("t")
            value = cell.find("m:v", NS)
            if kind == "inlineStr":
                token = "".join(n.text or "" for n in cell.findall(".//m:is//m:t", NS))
            elif value is None:
                token = ""
            elif kind == "s":
                try:
                    token = shared[int(value.text or "")]
                except (IndexError, ValueError) as exc:
                    raise ValueError("Invalid shared string index") from exc
            elif kind == "e":
                raise ValueError(f"Publisher sheet has Excel error in {address}")
            else:
                token = value.text or ""
            cells[col] = token.strip()
        output.append(cells)
    return output


def _timeseries_rows(payload: bytes) -> list[dict[str, str]]:
    if not 2_000 < len(payload) < 15_000_000 or not payload.startswith(b"PK"):
        raise ValueError("Expected complete official XLSX, not HTML/truncated response")
    try:
        z = ZipFile(io.BytesIO(payload))
        names = z.namelist()
        if len(names) > 300 or sum(i.file_size for i in z.infolist()) > 60_000_000:
            raise ValueError("Unexpected XLSX archive expansion")
        if "xl/workbook.xml" not in names or "xl/_rels/workbook.xml.rels" not in names:
            raise ValueError("Missing XLSX workbook or relationship map")
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        relroot = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rels = {rel.get("Id"): rel.get("Target") for rel in
                relroot.findall("p:Relationship", NS)}
        sheets = [
            (sheet.get("name", ""), sheet.get(f"{{{NS['r']}}}id"))
            for sheet in workbook.findall(".//m:sheets/m:sheet", NS)
        ]
        candidates = [(name, rid) for name, rid in sheets
                      if "cpi" in name.lower() and
                      ("timeseries" in name.lower() or "time series" in name.lower())]
        if len(candidates) != 1:
            raise ValueError(f"Expected one CPI time-series worksheet, got {sheets}")
        sheetname, rid = candidates[0]
        target = rels.get(rid)
        if not target or "://" in target:
            raise ValueError(f"Missing/internal worksheet relation for {sheetname}")
        path = (target.lstrip("/") if target.startswith("/xl/") else
                posixpath.normpath(posixpath.join("xl", target)))
        if not path.startswith("xl/worksheets/") or path not in names:
            raise ValueError(f"Unsafe/unresolved CPI sheet target {target!r}")
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in item.findall(".//m:t", NS))
                      for item in root.findall("m:si", NS)]
        rows = _sheet_rows(z, path, shared)
    except (BadZipFile, ET.ParseError, KeyError) as exc:
        raise ValueError("Malformed publisher XLSX XML/ZIP") from exc
    if not (150 <= len(rows) <= 1500):
        raise ValueError(f"Unexpected CPI time-series worksheet length {len(rows)}")
    return rows


def _year(header: str) -> int | None:
    compact = re.sub(r"[^a-z0-9]", "",header.casefold())
    if any(x in compact for x in
           ("rank", "source", "error", "confidence", "change", "difference",
            "lower", "upper", "interval", "significan")):
        return None
    for year in YEARS:
        y = str(year)
        if compact in (y, "cpi" + y, "score" + y, y + "score",
                       "cpi" + y + "score", "cpiscore" + y,
                       y + "cpiscore", "score" + y + "cpi"):
            return year
    return None


def parse_release(payload: bytes) -> list[tuple[int, int]]:
    """Fail closed on time-series headers, missing years, decimals and anchors."""
    rows = _timeseries_rows(payload)
    header_candidates: list[tuple[int, str, dict[int, str]]] = []
    for n, row in enumerate(rows[:45]):
        labels = {col: v.casefold().replace("/", " ").replace("-", " ").strip()
                  for col, v in row.items()}
        country_cols = [col for col, name in labels.items()
                        if name in ("country", "country territory", "country name",
                                    "country or territory")]
        year_cols: dict[int, str] = {}
        for col, label in row.items():
            y = _year(label)
            if y is not None:
                if y in year_cols:
                    raise ValueError(f"Duplicate 2025-vintage CPI column {y}")
                year_cols[y] = col
        if len(country_cols) == 1 and len(year_cols) == 14:
            header_candidates.append((n, country_cols[0], year_cols))
    if len(header_candidates) != 1:
        raise ValueError(f"Expected one complete CPI 2012–2025 header, found {len(header_candidates)}")
    start, country_col, cols = header_candidates[0]
    matches = [row for row in rows[start + 1:]
               if row.get(country_col, "").strip().casefold() in
               ("moldova", "republic of moldova")]
    if len(matches) != 1:
        raise ValueError(f"Moldova must appear exactly once, got {len(matches)}")
    country = matches[0]
    result: list[tuple[int, int]] = []
    for year in YEARS:
        raw = country.get(cols[year], "")
        try:
            score = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError(f"CPI {year} absent or not numeric: {raw!r}") from exc
        if not score.is_finite() or score != score.to_integral_value() or not 0 <= score <= 100:
            raise ValueError(f"CPI {year} outside whole-score 0–100 scale: {raw!r}")
        observed = int(score)
        if year in ANCHORS and observed != ANCHORS[year]:
            raise ValueError(f"CPI {year} inconsistent with publisher's own annual page: {observed}")
        result.append((year, observed))
    return result


def render_sidecar(observations: list[tuple[int, int]], source: bytes) -> str:
    lines = [
        "# Transparency International CPI 2025; Moldova (official historical workbook).",
        "# 0=highly corrupt, 100=very clean; expert/business perceptions, NOT measured cases.",
        "# 2012 is the first comparable CPI year; 2006-2011 must stay absent.",
        "# Licensed CC BY-ND 4.0; attribution required; this file is for research review.",
        f"# Source: {SOURCE}",
        f"# Original publisher XLSX SHA256: {hashlib.sha256(source).hexdigest()}",
        "year,cpi_score",
    ]
    lines.extend(f"{y},{score}" for y, score in observations)
    return "\n".join(lines) + "\n"


def fetch_release() -> bytes:
    req = Request(SOURCE, headers={
        "User-Agent": "WorldReports-Moldova-TI-source-audit/1.0",
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    })
    with urlopen(req, timeout=55) as response:
        return response.read(15_000_001)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path, default=DEST)
    args = p.parse_args()
    target = args.out.resolve()
    if target.name != "cpi_from_ti.csv":
        raise SystemExit("Refusing to replace any curated CPI or non-review file")
    raw = fetch_release()
    rows = parse_release(raw)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_sidecar(rows, raw), encoding="utf-8")
    print(f"Verified official TI 2025: {len(rows)} scores; "
          f"2012={rows[0][1]}; 2023–25={rows[-3:]}")
    print(f"Publisher SHA256={hashlib.sha256(raw).hexdigest()}")
    print(f"Review-only sidecar: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
