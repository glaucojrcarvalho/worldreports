#!/usr/bin/env python3
"""One-time bounded metadata probe of public National Bank of Moldova CSV exports.

No rate is curated by this program. Inspect field names and publication
coverage before designing permanent parsers; no third-party provider used.
"""
from __future__ import annotations

import csv
import io
import urllib.request
from urllib.error import HTTPError, URLError

SOURCES = [
    ("policy_1000", "https://www.bnm.md/en/export-base-rates?limit=1000"),
    ("policy_12", "https://www.bnm.md/en/export-base-rates?limit=12"),
    ("fx_2024", "https://www.bnm.md/en/export-average-rates?date_from=01.01.2024&date_to=31.12.2024"),
]
for name, url in SOURCES:
    print(f"----- {name} -----", flush=True)
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "worldreports-moldova-source-audit/1.0",
                     "Accept": "text/csv,text/plain,*/*"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read(1_500_001)
            typ = response.headers.get("Content-Type", "")
            final = response.geturl()
        if len(body) > 1_500_000:
            raise ValueError("Export above 1.5MB limit")
        if "bnm.md" not in final:
            raise ValueError("Unexpected redirect outside BNM")
        if body.lstrip().lower().startswith((b"<!doctype", b"<html")):
            raise ValueError("HTML response masquerading as CSV")
        # UTF-8 BOM and UTF-8 required; other encodings must be reviewed.
        txt = body.decode("utf-8-sig")
        first = txt[:150]
        sample = txt.splitlines()[:9]
        print(f"url={final}; type={typ}; bytes={len(body)}; lines={len(txt.splitlines())}",flush=True)
        print(f"prefix={first!r}",flush=True)
        for line in sample:
            print(f"example={line[:240]!r}",flush=True)
    except Exception as err:
        print(f"source-probe-error={type(err).__name__}: {err}",flush=True)
